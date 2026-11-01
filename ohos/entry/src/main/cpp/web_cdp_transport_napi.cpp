#include "web_cdp_transport.h"

#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <new>

#include "napi/native_api.h"

namespace {

struct EnvironmentHandles {
  int64_t handles[QFLI_WEB_CDP_MAX_CONNECTIONS] = {};
};

napi_value Throw(napi_env env, const char *code, const char *message) {
  napi_throw_error(env, code, message);
  return nullptr;
}

bool Arguments(napi_env env, napi_callback_info info, size_t expected,
               napi_value args[3], EnvironmentHandles **owner) {
  size_t count = expected + 1;
  void *data = nullptr;
  if (napi_get_cb_info(env, info, &count, args, nullptr, &data) != napi_ok ||
      count != expected) {
    Throw(env, "INVALID_ARGUMENT", "Unexpected transport argument count");
    return false;
  }
  if (data == nullptr) {
    Throw(env, "CDP_TRANSPORT_NAPI", "Transport environment is unavailable");
    return false;
  }
  *owner = static_cast<EnvironmentHandles *>(data);
  return true;
}

bool Handle(napi_env env, napi_value value, int64_t *handle) {
  size_t length = 0;
  if (napi_get_value_string_utf8(env, value, nullptr, 0, &length) != napi_ok ||
      length == 0 || length > 19) {
    return false;
  }
  char text[20] = {};
  size_t written = 0;
  if (napi_get_value_string_utf8(env, value, text, sizeof(text), &written) !=
          napi_ok ||
      written != length || text[0] < '1' || text[0] > '9') {
    return false;
  }
  int64_t number = 0;
  for (size_t index = 0; index < length; ++index) {
    if (text[index] < '0' || text[index] > '9') {
      return false;
    }
    const int digit = text[index] - '0';
    if (number > (INT64_MAX - digit) / 10) {
      return false;
    }
    number = number * 10 + digit;
  }
  *handle = number;
  return true;
}

bool Capacity(napi_env env, napi_value value, size_t *capacity) {
  double number = 0;
  if (napi_get_value_double(env, value, &number) != napi_ok ||
      !(number >= 1 && number <= QFLI_WEB_CDP_MAX_TRANSFER)) {
    return false;
  }
  const size_t integer = static_cast<size_t>(number);
  if (number != static_cast<double>(integer)) {
    return false;
  }
  *capacity = integer;
  return true;
}

int64_t *OwnedHandle(EnvironmentHandles *owner, int64_t handle) {
  for (int64_t &owned : owner->handles) {
    if (owned == handle) {
      return &owned;
    }
  }
  return nullptr;
}

void Release(EnvironmentHandles *owner, int64_t handle) {
  int64_t *owned = OwnedHandle(owner, handle);
  if (owned != nullptr) {
    *owned = 0;
    qfli_web_cdp_close(handle);
  }
}

napi_value Status(napi_env env, int status) {
  napi_value value = nullptr;
  if (napi_create_int32(env, status, &value) != napi_ok) {
    return Throw(env, "CDP_TRANSPORT_NAPI", "Cannot create transport status");
  }
  return value;
}

napi_value OpenSelf(napi_env env, napi_callback_info info) {
  napi_value args[3] = {};
  EnvironmentHandles *owner = nullptr;
  if (!Arguments(env, info, 0, args, &owner)) {
    return nullptr;
  }

  int64_t handle = qfli_web_cdp_open_self();
  if (handle > 0) {
    int64_t *slot = OwnedHandle(owner, 0);
    if (slot == nullptr) {
      qfli_web_cdp_close(handle);
      handle = -EMFILE;
    } else {
      *slot = handle;
    }
  }
  char text[20] = {};
  if (handle > 0) {
    std::snprintf(text, sizeof(text), "%lld", static_cast<long long>(handle));
  }
  const int status = handle > 0 ? 0 : (handle < 0 ? static_cast<int>(handle) : -EIO);
  napi_value result = nullptr;
  napi_value status_value = nullptr;
  napi_value handle_value = nullptr;
  if (napi_create_object(env, &result) != napi_ok ||
      napi_create_int32(env, status, &status_value) != napi_ok ||
      napi_create_string_utf8(env, text, NAPI_AUTO_LENGTH, &handle_value) != napi_ok ||
      napi_set_named_property(env, result, "status", status_value) != napi_ok ||
      napi_set_named_property(env, result, "handle", handle_value) != napi_ok) {
    if (handle > 0) {
      Release(owner, handle);
    }
    return Throw(env, "CDP_TRANSPORT_NAPI", "Cannot create transport open result");
  }
  return result;
}

napi_value Read(napi_env env, napi_callback_info info) {
  napi_value args[3] = {};
  EnvironmentHandles *owner = nullptr;
  if (!Arguments(env, info, 2, args, &owner)) {
    return nullptr;
  }
  int64_t handle = 0;
  size_t capacity = 0;
  if (!Handle(env, args[0], &handle) || !Capacity(env, args[1], &capacity)) {
    return Throw(env, "INVALID_ARGUMENT", "Expected a handle and capacity 1..65536");
  }

  uint8_t scratch[QFLI_WEB_CDP_MAX_TRANSFER];
  const int status = OwnedHandle(owner, handle) == nullptr
      ? -EBADF : qfli_web_cdp_read(handle, scratch, capacity);
  const size_t length = status > 0 ? static_cast<size_t>(status) : 0;
  napi_value result = nullptr;
  napi_value status_value = nullptr;
  napi_value bytes_value = nullptr;
  void *bytes = nullptr;
  if (napi_create_object(env, &result) != napi_ok ||
      napi_create_int32(env, status, &status_value) != napi_ok ||
      napi_create_arraybuffer(env, length, &bytes, &bytes_value) != napi_ok ||
      (length > 0 && bytes == nullptr)) {
    // A failed result allocation after recv must not silently lose stream bytes.
    Release(owner, handle);
    return Throw(env, "CDP_TRANSPORT_NAPI", "Cannot create transport read result");
  }
  if (length > 0) {
    std::memcpy(bytes, scratch, length);
  }
  // Finish copying before publishing the buffer to any ArkTS property setter.
  if (napi_set_named_property(env, result, "status", status_value) != napi_ok ||
      napi_set_named_property(env, result, "bytes", bytes_value) != napi_ok) {
    Release(owner, handle);
    return Throw(env, "CDP_TRANSPORT_NAPI", "Cannot publish transport read result");
  }
  return result;
}

napi_value Write(napi_env env, napi_callback_info info) {
  napi_value args[3] = {};
  EnvironmentHandles *owner = nullptr;
  if (!Arguments(env, info, 2, args, &owner)) {
    return nullptr;
  }
  int64_t handle = 0;
  bool is_array_buffer = false;
  void *bytes = nullptr;
  size_t length = 0;
  if (!Handle(env, args[0], &handle) ||
      napi_is_arraybuffer(env, args[1], &is_array_buffer) != napi_ok ||
      !is_array_buffer ||
      napi_get_arraybuffer_info(env, args[1], &bytes, &length) != napi_ok ||
      bytes == nullptr || length == 0 || length > QFLI_WEB_CDP_MAX_TRANSFER) {
    return Throw(env, "INVALID_ARGUMENT", "Expected a handle and ArrayBuffer of 1..65536 bytes");
  }
  const int status = OwnedHandle(owner, handle) == nullptr
      ? -EBADF : qfli_web_cdp_write(handle, static_cast<const uint8_t *>(bytes), length);
  napi_value result = Status(env, status);
  if (result == nullptr) {
    // send may have accepted bytes: force the caller to restart on result loss.
    Release(owner, handle);
  }
  return result;
}

napi_value Close(napi_env env, napi_callback_info info) {
  napi_value args[3] = {};
  EnvironmentHandles *owner = nullptr;
  if (!Arguments(env, info, 1, args, &owner)) {
    return nullptr;
  }
  int64_t handle = 0;
  if (!Handle(env, args[0], &handle)) {
    return Throw(env, "INVALID_ARGUMENT", "Expected a positive decimal handle");
  }
  int status = 0;
  int64_t *owned = OwnedHandle(owner, handle);
  if (owned != nullptr) {
    *owned = 0;
    status = qfli_web_cdp_close(handle);
  }
  return Status(env, status);
}

void Cleanup(void *data) {
  auto *owner = static_cast<EnvironmentHandles *>(data);
  for (int64_t handle : owner->handles) {
    if (handle > 0) {
      qfli_web_cdp_close(handle);
    }
  }
  delete owner;
}

napi_value Init(napi_env env, napi_value exports) {
  auto *owner = new (std::nothrow) EnvironmentHandles;
  if (owner == nullptr) {
    return Throw(env, "CDP_TRANSPORT_NAPI", "Cannot allocate transport environment");
  }
  if (napi_add_env_cleanup_hook(env, Cleanup, owner) != napi_ok) {
    delete owner;
    return Throw(env, "CDP_TRANSPORT_NAPI", "Cannot register transport cleanup");
  }
  napi_property_descriptor properties[] = {
      {"openSelf", nullptr, OpenSelf, nullptr, nullptr, nullptr, napi_default, owner},
      {"read", nullptr, Read, nullptr, nullptr, nullptr, napi_default, owner},
      {"write", nullptr, Write, nullptr, nullptr, nullptr, napi_default, owner},
      {"close", nullptr, Close, nullptr, nullptr, nullptr, napi_default, owner},
  };
  if (napi_define_properties(env, exports,
          sizeof(properties) / sizeof(properties[0]), properties) != napi_ok) {
    // The registered environment hook still owns data for any defined callbacks.
    return Throw(env, "CDP_TRANSPORT_NAPI", "Cannot export transport operations");
  }
  return exports;
}

napi_module module = {
    1, 0, nullptr, Init, "qfli_web_cdp_transport", nullptr, {0}};

}  // namespace

extern "C" __attribute__((constructor)) void RegisterQfliWebCdpTransportModule() {
  napi_module_register(&module);
}
