cmake_minimum_required(VERSION 3.16)
project(qfli_nginx_napi C CXX)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Compile-only JavaScript diagnostics are loaded through dart:ffi. This target
# is a shared library, not an executable, and is packaged for each selected ABI.
add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/../../../../../native/web_syntax"
  "${CMAKE_CURRENT_BINARY_DIR}/web_syntax")

# The embedded engine is produced per ABI by
#   scripts/build_nginx_embedded.sh ohos <out> <sdk-native-root> <abi>
# and retained as a plain static archive (no executableBinaryPaths). Selecting
# it here keeps the HAP free of a standalone PIE binary, which HarmonyOS rejects
# at install time (ERR_INSTALL_CHECK_BIN_FILE_FAILED).
if(OHOS_ARCH STREQUAL "arm64-v8a")
  set(QFLI_NGINX_ARCHIVE "${CMAKE_CURRENT_SOURCE_DIR}/prebuilt/arm64-v8a/libqfli_nginx.a")
elseif(OHOS_ARCH STREQUAL "x86_64")
  set(QFLI_NGINX_ARCHIVE "${CMAKE_CURRENT_SOURCE_DIR}/prebuilt/x86_64/libqfli_nginx.a")
else()
  message(FATAL_ERROR "Unsupported HarmonyOS ABI: ${OHOS_ARCH}")
endif()
if(NOT EXISTS "${QFLI_NGINX_ARCHIVE}")
  message(FATAL_ERROR "Missing embedded Nginx archive: ${QFLI_NGINX_ARCHIVE}")
endif()

add_library(qfli_nginx_embedded STATIC IMPORTED)
set_target_properties(qfli_nginx_embedded PROPERTIES
  IMPORTED_LOCATION "${QFLI_NGINX_ARCHIVE}"
  INTERFACE_INCLUDE_DIRECTORIES "${CMAKE_CURRENT_SOURCE_DIR}/include")

add_library(qfli_nginx_napi SHARED nginx_napi.cpp)
target_include_directories(qfli_nginx_napi PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include")
target_link_libraries(qfli_nginx_napi PUBLIC libace_napi.z.so qfli_nginx_embedded)
# libc supplies the upstream ngx_abort() dependency; pthread backs the worker.
target_link_libraries(qfli_nginx_napi PUBLIC pthread)
