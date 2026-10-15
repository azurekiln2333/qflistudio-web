#include <cstdint>
#include <string>
#include <vector>

#include "napi/native_api.h"
#include "qfli_nginx.h"

// NAPI bridge for the embedded Nginx lifecycle ABI.
//
// Mirrors ios/Runner/EmbeddedNginxBridge.swift: the Dart host talks to a single
// MethodChannel ('qflistudio/nginx') whose payloads are forwarded here. The
// embedded engine runs on one owned pthread; Dart owns stop/release ordering.

namespace {

bool ReadString(napi_env env, napi_value value, std::string *out) {
  size_t length = 0;
  if (napi_get_value_string_utf8(env, value, nullptr, 0, &length) != napi_ok) {
    return false;
  }
  // napi_get_value_string_utf8 writes the string plus a trailing NUL, so the
  // destination must own length + 1 bytes. std::string::data() is only length
  // bytes after resize(), so copy through a scratch buffer.
  std::vector<char> buffer(length + 1, '\0');
  size_t written = 0;
  if (napi_get_value_string_utf8(env, value, buffer.data(), buffer.size(), &written) != napi_ok) {
    return false;
  }
  out->assign(buffer.data(), written);
  return true;
}

bool ReadInt64(napi_env env, napi_value value, int64_t *out) {
  return napi_get_value_int64(env, value, out) == napi_ok;
}

napi_value Throw(napi_env env, const char *code, const char *message, int64_t detail) {
  napi_throw_error(env, code, message);
  (void)detail;
  return nullptr;
}

napi_value GetProperty(napi_env env, napi_value object, const char *name) {
  bool present = false;
  napi_has_named_property(env, object, name, &present);
  if (!present) {
    return nullptr;
  }
  napi_value value = nullptr;
  if (napi_get_named_property(env, object, name, &value) != napi_ok) {
    return nullptr;
  }
  return value;
}

napi_value Version(napi_env env, napi_callback_info info) {
  napi_value result = nullptr;
  napi_create_string_utf8(env, qfli_nginx_version(), NAPI_AUTO_LENGTH, &result);
  return result;
}

napi_value Start(napi_env env, napi_callback_info info) {
  size_t argc = 1;
  napi_value args[1] = {nullptr};
  if (napi_get_cb_info(env, info, &argc, args, nullptr, nullptr) != napi_ok || argc < 1) {
    return Throw(env, "INVALID_ARGUMENT", "Invalid Nginx start arguments", 0);
  }
  napi_value prefix_value = GetProperty(env, args[0], "prefix");
  napi_value test_value = GetProperty(env, args[0], "test");
  std::string prefix;
  bool test = false;
  if (prefix_value == nullptr || !ReadString(env, prefix_value, &prefix) ||
      prefix.find('\0') != std::string::npos) {
    return Throw(env, "INVALID_ARGUMENT", "Invalid Nginx start arguments", 0);
  }
  if (test_value != nullptr) {
    napi_get_value_bool(env, test_value, &test);
  }
  const int64_t token = qfli_nginx_start(prefix.c_str(), test ? 1 : 0);
  if (token < 0) {
    return Throw(env, "NGINX_START", "Native Nginx start failed", token);
  }
  napi_value result = nullptr;
  napi_create_int64(env, token, &result);
  return result;
}

napi_value Poll(napi_env env, napi_callback_info info) {
  size_t argc = 1;
  napi_value args[1] = {nullptr};
  if (napi_get_cb_info(env, info, &argc, args, nullptr, nullptr) != napi_ok || argc < 1) {
    return Throw(env, "INVALID_ARGUMENT", "Invalid Nginx token", 0);
  }
  napi_value token_value = GetProperty(env, args[0], "token");
  int64_t token = 0;
  if (token_value == nullptr || !ReadInt64(env, token_value, &token) || token <= 0) {
    return Throw(env, "INVALID_ARGUMENT", "Invalid Nginx token", 0);
  }
  int exit_code = 0;
  const int status = qfli_nginx_poll(token, &exit_code);
  if (status < 0) {
    return Throw(env, "NGINX_SESSION", "Native Nginx lifecycle failed", status);
  }
  if (status == 0) {
    napi_value result = nullptr;
    napi_get_null(env, &result);
    return result;
  }
  napi_value result = nullptr;
  napi_create_int32(env, exit_code, &result);
  return result;
}

napi_value LifecycleCall(napi_env env, napi_callback_info info, bool is_stop) {
  size_t argc = 1;
  napi_value args[1] = {nullptr};
  if (napi_get_cb_info(env, info, &argc, args, nullptr, nullptr) != napi_ok || argc < 1) {
    return Throw(env, "INVALID_ARGUMENT", "Invalid Nginx token", 0);
  }
  napi_value token_value = GetProperty(env, args[0], "token");
  int64_t token = 0;
  if (token_value == nullptr || !ReadInt64(env, token_value, &token) || token <= 0) {
    return Throw(env, "INVALID_ARGUMENT", "Invalid Nginx token", 0);
  }
  const int status = is_stop ? qfli_nginx_stop(token) : qfli_nginx_release(token);
  if (status < 0) {
    return Throw(env, "NGINX_SESSION", "Native Nginx lifecycle failed", status);
  }
  napi_value result = nullptr;
  napi_get_null(env, &result);
  return result;
}

napi_value Stop(napi_env env, napi_callback_info info) {
  return LifecycleCall(env, info, true);
}

napi_value Release(napi_env env, napi_callback_info info) {
  return LifecycleCall(env, info, false);
}

napi_value Init(napi_env env, napi_value exports) {
  napi_property_descriptor properties[] = {
      {"version", nullptr, Version, nullptr, nullptr, nullptr, napi_default, nullptr},
      {"start", nullptr, Start, nullptr, nullptr, nullptr, napi_default, nullptr},
      {"poll", nullptr, Poll, nullptr, nullptr, nullptr, napi_default, nullptr},
      {"stop", nullptr, Stop, nullptr, nullptr, nullptr, napi_default, nullptr},
      {"release", nullptr, Release, nullptr, nullptr, nullptr, napi_default, nullptr},
  };
  napi_define_properties(env, exports, sizeof(properties) / sizeof(properties[0]), properties);
  return exports;
}

  napi_module module = {1, 0, nullptr, Init, "qfli_nginx_napi", nullptr, {0}};

}  // namespace

extern "C" __attribute__((constructor)) void RegisterQfliNginxModule() {
  napi_module_register(&module);
}
