#ifndef _GNU_SOURCE
#define _GNU_SOURCE 1
#endif

#include "web_cdp_transport.h"

#include <cerrno>
#include <climits>
#include <cstddef>
#include <cstdio>
#include <poll.h>
#include <pthread.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

namespace {

struct Connection {
  int64_t handle = 0;
  int fd = -1;
  int failure = 0;
  bool connecting = false;
  bool read_eof = false;
};

pthread_mutex_t connections_mutex = PTHREAD_MUTEX_INITIALIZER;
Connection connections[QFLI_WEB_CDP_MAX_CONNECTIONS];
uint64_t next_handle = 1;

class ConnectionLock {
 public:
  ConnectionLock() : error_(pthread_mutex_lock(&connections_mutex)) {}
  ~ConnectionLock() {
    if (error_ == 0) {
      pthread_mutex_unlock(&connections_mutex);
    }
  }

  ConnectionLock(const ConnectionLock &) = delete;
  ConnectionLock &operator=(const ConnectionLock &) = delete;
  int error() const { return error_; }

 private:
  int error_;
};

Connection *FindConnection(int64_t handle) {
  if (handle <= 0) {
    return nullptr;
  }
  for (Connection &connection : connections) {
    if (connection.handle == handle) {
      return &connection;
    }
  }
  return nullptr;
}

void CloseDescriptor(Connection &connection) {
  const int fd = connection.fd;
  connection.fd = -1;
  if (fd >= 0) {
    // close is deliberately not retried: an EINTR retry can hit a reused fd.
    close(fd);
  }
}

int FailConnection(Connection &connection, int error) {
  connection.failure = error;
  connection.connecting = false;
  CloseDescriptor(connection);
  return -error;
}

int ValidatePeer(int fd) {
#if defined(SO_PEERCRED) && (defined(__linux__) || defined(__OHOS__))
  struct ucred peer {};
  socklen_t size = sizeof(peer);
  if (getsockopt(fd, SOL_SOCKET, SO_PEERCRED, &peer, &size) != 0) {
    return -errno;
  }
  if (size != sizeof(peer)) {
    return -EPROTO;
  }
  // This validates the endpoint we connected to, not clients ArkWeb accepts.
  if (peer.uid != getuid()) {
    return -EACCES;
  }
  return 0;
#else
  (void)fd;
  return -ENOTSUP;
#endif
}

int FinishConnect(Connection &connection) {
  if (connection.failure != 0) {
    return -connection.failure;
  }
  if (!connection.connecting) {
    return 0;
  }

  struct pollfd readiness {};
  readiness.fd = connection.fd;
  readiness.events = POLLOUT;
  const int status = poll(&readiness, 1, 0);
  if (status == 0) {
    return -EAGAIN;
  }
  if (status < 0) {
    const int error = errno;
    return error == EINTR ? -EINTR : FailConnection(connection, error);
  }
  if ((readiness.revents & POLLNVAL) != 0) {
    return FailConnection(connection, EBADF);
  }

  int error = 0;
  socklen_t size = sizeof(error);
  if (getsockopt(connection.fd, SOL_SOCKET, SO_ERROR, &error, &size) != 0) {
    return FailConnection(connection, errno);
  }
  if (size != sizeof(error)) {
    return FailConnection(connection, EPROTO);
  }
  if (error == EINPROGRESS || error == EALREADY) {
    return -EAGAIN;
  }
  if (error != 0) {
    return FailConnection(connection, error);
  }

  const int peer_status = ValidatePeer(connection.fd);
  if (peer_status < 0) {
    return FailConnection(connection, -peer_status);
  }
  connection.connecting = false;
  return 0;
}

int TransferError(Connection &connection) {
  const int error = errno;
  if (error == EAGAIN || error == EWOULDBLOCK) {
    return -EAGAIN;
  }
  if (error == EINTR) {
    return -EINTR;
  }
  return FailConnection(connection, error);
}

}  // namespace

extern "C" int64_t qfli_web_cdp_open_self(void) {
  ConnectionLock lock;
  if (lock.error() != 0) {
    return -lock.error();
  }

  Connection *available = nullptr;
  for (Connection &connection : connections) {
    if (connection.handle == 0) {
      available = &connection;
      break;
    }
  }
  if (available == nullptr) {
    return -EMFILE;
  }
  if (next_handle > static_cast<uint64_t>(INT64_MAX)) {
    return -EOVERFLOW;
  }

#if defined(SOCK_NONBLOCK) && defined(SOCK_CLOEXEC) && defined(MSG_NOSIGNAL)
  struct sockaddr_un address {};
  address.sun_family = AF_UNIX;
  const int name_length = std::snprintf(
      address.sun_path + 1, sizeof(address.sun_path) - 1,
      "webview_devtools_remote_%ld", static_cast<long>(getpid()));
  if (name_length <= 0 ||
      static_cast<size_t>(name_length) >= sizeof(address.sun_path) - 1) {
    return -ENAMETOOLONG;
  }
  // Include the abstract namespace's leading NUL, exclude a trailing NUL.
  const socklen_t address_length = static_cast<socklen_t>(
      offsetof(struct sockaddr_un, sun_path) + 1 + name_length);
  const int fd = socket(AF_UNIX, SOCK_STREAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
  if (fd < 0) {
    return -errno;
  }

  bool connecting = false;
  if (connect(fd, reinterpret_cast<const struct sockaddr *>(&address),
              address_length) != 0) {
    const int error = errno;
    if (error != EINPROGRESS) {
      // AF_UNIX EAGAIN means retry a fresh connect, not a queued connection.
      close(fd);
      return -(error == EWOULDBLOCK ? EAGAIN : error);
    }
    connecting = true;
  }
  if (!connecting) {
    const int peer_status = ValidatePeer(fd);
    if (peer_status < 0) {
      close(fd);
      return peer_status;
    }
  }

  available->handle = static_cast<int64_t>(next_handle++);
  available->fd = fd;
  available->failure = 0;
  available->connecting = connecting;
  available->read_eof = false;
  return available->handle;
#else
  return -ENOTSUP;
#endif
}

extern "C" int qfli_web_cdp_read(
    int64_t handle, uint8_t *buffer, size_t capacity) {
  if (buffer == nullptr || capacity == 0 || capacity > QFLI_WEB_CDP_MAX_TRANSFER) {
    return -EINVAL;
  }
  ConnectionLock lock;
  if (lock.error() != 0) {
    return -lock.error();
  }
  Connection *connection = FindConnection(handle);
  if (connection == nullptr) {
    return -EBADF;
  }
  const int status = FinishConnect(*connection);
  if (status < 0) {
    return status;
  }
  if (connection->read_eof) {
    return 0;
  }
  const ssize_t count = recv(connection->fd, buffer, capacity, 0);
  if (count < 0) {
    return TransferError(*connection);
  }
  if (count == 0) {
    connection->read_eof = true;
  }
  return static_cast<int>(count);
}

extern "C" int qfli_web_cdp_write(
    int64_t handle, const uint8_t *bytes, size_t length) {
  if (bytes == nullptr || length == 0 || length > QFLI_WEB_CDP_MAX_TRANSFER) {
    return -EINVAL;
  }
  ConnectionLock lock;
  if (lock.error() != 0) {
    return -lock.error();
  }
  Connection *connection = FindConnection(handle);
  if (connection == nullptr) {
    return -EBADF;
  }
  const int status = FinishConnect(*connection);
  if (status < 0) {
    return status;
  }
#if defined(MSG_NOSIGNAL)
  const ssize_t count = send(connection->fd, bytes, length, MSG_NOSIGNAL);
  return count < 0 ? TransferError(*connection) : static_cast<int>(count);
#else
  return -ENOTSUP;
#endif
}

extern "C" int qfli_web_cdp_close(int64_t handle) {
  if (handle <= 0) {
    return -EINVAL;
  }
  ConnectionLock lock;
  if (lock.error() != 0) {
    return -lock.error();
  }
  Connection *connection = FindConnection(handle);
  if (connection == nullptr) {
    return 0;
  }
  const int fd = connection->fd;
  *connection = Connection{};
  if (fd >= 0 && close(fd) != 0) {
    return -errno;
  }
  return 0;
}
