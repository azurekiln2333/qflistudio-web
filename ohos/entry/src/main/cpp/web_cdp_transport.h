#ifndef QFLI_WEB_CDP_TRANSPORT_H
#define QFLI_WEB_CDP_TRANSPORT_H

#include <stddef.h>
#include <stdint.h>

#if defined(__GNUC__)
#define QFLI_WEB_CDP_EXPORT __attribute__((visibility("default")))
#else
#define QFLI_WEB_CDP_EXPORT
#endif

#ifdef __cplusplus
extern "C" {
#endif

enum {
  QFLI_WEB_CDP_MAX_TRANSFER = 64 * 1024,
  QFLI_WEB_CDP_MAX_CONNECTIONS = 8,
};

/*
 * Raw, nonblocking client transport only. This API does not enable ArkWeb,
 * implement CDP/WebSocket, create a listener, or prove debugger availability.
 * The only endpoint is the abstract Unix socket
 * "webview_devtools_remote_<getpid()>". No caller-selected address is accepted.
 *
 * open_self returns a positive opaque handle, or negative POSIX errno. A handle
 * may initially be connecting: read/write then return -EAGAIN until readiness.
 * An AF_UNIX connect returning EAGAIN has NOT queued a pending connection:
 * open_self closes it and returns -EAGAIN; the caller may retry open_self later.
 * Every connected peer must expose SO_PEERCRED and have the caller's own UID.
 * This outbound peer check says nothing about ArkWeb's inbound authorization.
 *
 * At most MAX_CONNECTIONS handles exist. Handles never repeat in this library
 * lifetime; exhaustion returns -EOVERFLOW. They are not descriptors. The caller
 * owns every successful handle, including pending/failed ones, until close.
 */
QFLI_WEB_CDP_EXPORT int64_t qfli_web_cdp_open_self(void);

/*
 * buffer must point to capacity writable bytes; capacity must be 1..MAX_TRANSFER.
 * The API validates pointer non-nullness and the length, not the allocation
 * behind a native pointer. It retains no caller memory after returning.
 * Result: positive actual bytes, 0 EOF, -EAGAIN pending/no data, or negative errno.
 * EOF is sticky for reads but does not prevent writes to a half-closed peer.
 */
QFLI_WEB_CDP_EXPORT int qfli_web_cdp_read(
    int64_t handle, uint8_t *buffer, size_t capacity);

/*
 * bytes must point to length readable bytes; length must be 1..MAX_TRANSFER.
 * Result: actual accepted bytes (possibly a short write), -EAGAIN pending/full,
 * or negative errno. The caller retries only the unaccepted suffix. EINTR is
 * returned without an internal retry loop. No process signal handler is changed.
 */
QFLI_WEB_CDP_EXPORT int qfli_web_cdp_write(
    int64_t handle, const uint8_t *bytes, size_t length);

/*
 * Idempotent for every positive closed/unknown handle; nonpositive is -EINVAL.
 * Retires the handle before closing its descriptor, even if close reports an
 * error. Never retries close on EINTR, which could close a reused descriptor.
 * Read/write with an inactive handle return -EBADF. Calls are mutex-serialized;
 * close cannot race a descriptor's reuse inside another transport operation.
 */
QFLI_WEB_CDP_EXPORT int qfli_web_cdp_close(int64_t handle);

#ifdef __cplusplus
}
#endif

#undef QFLI_WEB_CDP_EXPORT
#endif
