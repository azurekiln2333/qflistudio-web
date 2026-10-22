# Project-level configuration.
cmake_minimum_required(VERSION 3.14)
project(qfli_web LANGUAGES CXX)

# The name of the executable created for the application. Change this to change
# the on-disk name of your application.
set(BINARY_NAME "qfli_web")

# Explicitly opt in to modern CMake behaviors to avoid warnings with recent
# versions of CMake.
cmake_policy(VERSION 3.14...3.25)

# Define build configuration option.
get_property(IS_MULTICONFIG GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)
if(IS_MULTICONFIG)
  set(CMAKE_CONFIGURATION_TYPES "Debug;Profile;Release"
    CACHE STRING "" FORCE)
else()
  if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE "Debug" CACHE
      STRING "Flutter build mode" FORCE)
    set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS
      "Debug" "Profile" "Release")
  endif()
endif()
# Define settings for the Profile build mode.
set(CMAKE_EXE_LINKER_FLAGS_PROFILE "${CMAKE_EXE_LINKER_FLAGS_RELEASE}")
set(CMAKE_SHARED_LINKER_FLAGS_PROFILE "${CMAKE_SHARED_LINKER_FLAGS_RELEASE}")
set(CMAKE_C_FLAGS_PROFILE "${CMAKE_C_FLAGS_RELEASE}")
set(CMAKE_CXX_FLAGS_PROFILE "${CMAKE_CXX_FLAGS_RELEASE}")

# Use Unicode for all projects.
add_definitions(-DUNICODE -D_UNICODE)

# Compilation settings that should be applied to most targets.
#
# Be cautious about adding new options here, as plugins use this function by
# default. In most cases, you should add new options to specific targets instead
# of modifying this function.
function(APPLY_STANDARD_SETTINGS TARGET)
  target_compile_features(${TARGET} PUBLIC cxx_std_17)
  target_compile_options(${TARGET} PRIVATE /W4 /WX /wd"4100")
  target_compile_options(${TARGET} PRIVATE /EHsc)
  target_compile_definitions(${TARGET} PRIVATE "_HAS_EXCEPTIONS=0")
  target_compile_definitions(${TARGET} PRIVATE "$<$<CONFIG:Debug>:_DEBUG>")
endfunction()

# Flutter library and tool build rules.
set(FLUTTER_MANAGED_DIR "${CMAKE_CURRENT_SOURCE_DIR}/flutter")
add_subdirectory(${FLUTTER_MANAGED_DIR})

# Application build; see runner/CMakeLists.txt.
add_subdirectory("runner")

# QuickJS uses GCC/Clang extensions and must not inherit the MSVC toolchain.
# Build its pinned C sources separately, then ship the DLL beside the runner.
find_program(QFLI_SYNTAX_PYTHON NAMES python3 python)
find_program(QFLI_SYNTAX_CC NAMES clang gcc)
if(NOT QFLI_SYNTAX_PYTHON OR NOT QFLI_SYNTAX_CC)
  message(FATAL_ERROR "Offline JavaScript diagnostics require Python and GCC/Clang (QFLI_SYNTAX_CC)")
endif()
set(QFLI_SYNTAX_WINDOWS_SYSROOT "" CACHE PATH "Optional MinGW sysroot for a standalone Clang compiler")
set(QFLI_SYNTAX_LINK_CC "" CACHE FILEPATH "Optional MinGW GCC link driver for standalone Clang")
set(QFLI_SYNTAX_EXTRA_ARGS)
if(QFLI_SYNTAX_WINDOWS_SYSROOT)
  list(APPEND QFLI_SYNTAX_EXTRA_ARGS --sdk "${QFLI_SYNTAX_WINDOWS_SYSROOT}")
endif()
if(QFLI_SYNTAX_LINK_CC)
  list(APPEND QFLI_SYNTAX_EXTRA_ARGS --link-cc "${QFLI_SYNTAX_LINK_CC}")
endif()
set(QFLI_SYNTAX_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/..")
set(QFLI_SYNTAX_OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/web_syntax")
file(GLOB QFLI_SYNTAX_INPUTS CONFIGURE_DEPENDS
  "${QFLI_SYNTAX_ROOT}/native/web_syntax/*.c"
  "${QFLI_SYNTAX_ROOT}/native/web_syntax/*.h"
  "${QFLI_SYNTAX_ROOT}/vendor/quickjs/*.c"
  "${QFLI_SYNTAX_ROOT}/vendor/quickjs/*.h")
add_custom_command(
  OUTPUT "${QFLI_SYNTAX_OUTPUT}/qfli_web_syntax.dll"
  COMMAND "${QFLI_SYNTAX_PYTHON}" "${QFLI_SYNTAX_ROOT}/scripts/build_web_syntax.py"
    --platform windows --cc "${QFLI_SYNTAX_CC}" ${QFLI_SYNTAX_EXTRA_ARGS}
    --output "${QFLI_SYNTAX_OUTPUT}"
  DEPENDS ${QFLI_SYNTAX_INPUTS}
    "${QFLI_SYNTAX_ROOT}/scripts/build_web_syntax.py"
    "${QFLI_SYNTAX_ROOT}/vendor/quickjs/SOURCE.json"
  VERBATIM)
add_custom_target(web_syntax_runtime ALL
  DEPENDS "${QFLI_SYNTAX_OUTPUT}/qfli_web_syntax.dll")
add_dependencies(${BINARY_NAME} web_syntax_runtime)


# Generated plugin build rules, which manage building the plugins and adding
# them to the application.
include(flutter/generated_plugins.cmake)


# === Installation ===
# Support files are copied into place next to the executable, so that it can
# run in place. This is done instead of making a separate bundle (as on Linux)
# so that building and running from within Visual Studio will work.
set(BUILD_BUNDLE_DIR "$<TARGET_FILE_DIR:${BINARY_NAME}>")
# Make the "install" step default, as it's required to run.
set(CMAKE_VS_INCLUDE_INSTALL_TO_DEFAULT_BUILD 1)
if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
  set(CMAKE_INSTALL_PREFIX "${BUILD_BUNDLE_DIR}" CACHE PATH "..." FORCE)
endif()

set(INSTALL_BUNDLE_DATA_DIR "${CMAKE_INSTALL_PREFIX}/data")
set(INSTALL_BUNDLE_LIB_DIR "${CMAKE_INSTALL_PREFIX}")

install(FILES "${QFLI_SYNTAX_OUTPUT}/qfli_web_syntax.dll"
  DESTINATION "${INSTALL_BUNDLE_LIB_DIR}" COMPONENT Runtime)

install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/../assets/runtime/nginx/windows/nginx.exe"
  "${CMAKE_CURRENT_SOURCE_DIR}/../vendor/nginx/LICENSE"
  DESTINATION "${INSTALL_BUNDLE_DATA_DIR}/nginx" COMPONENT Runtime)

install(TARGETS ${BINARY_NAME} RUNTIME DESTINATION "${CMAKE_INSTALL_PREFIX}"
  COMPONENT Runtime)

install(FILES "${FLUTTER_ICU_DATA_FILE}" DESTINATION "${INSTALL_BUNDLE_DATA_DIR}"
  COMPONENT Runtime)

install(FILES "${FLUTTER_LIBRARY}" DESTINATION "${INSTALL_BUNDLE_LIB_DIR}"
  COMPONENT Runtime)

if(PLUGIN_BUNDLED_LIBRARIES)
  install(FILES "${PLUGIN_BUNDLED_LIBRARIES}"
    DESTINATION "${INSTALL_BUNDLE_LIB_DIR}"
    COMPONENT Runtime)
endif()

# Copy the native assets provided by the build.dart from all packages.
set(NATIVE_ASSETS_DIR "${PROJECT_BUILD_DIR}native_assets/windows/")
install(DIRECTORY "${NATIVE_ASSETS_DIR}"
   DESTINATION "${INSTALL_BUNDLE_LIB_DIR}"
   COMPONENT Runtime)

# Fully re-copy the assets directory on each build to avoid having stale files
# from a previous install.
set(FLUTTER_ASSET_DIR_NAME "flutter_assets")
install(CODE "
  file(REMOVE_RECURSE \"${INSTALL_BUNDLE_DATA_DIR}/${FLUTTER_ASSET_DIR_NAME}\")
  " COMPONENT Runtime)
install(DIRECTORY "${PROJECT_BUILD_DIR}/${FLUTTER_ASSET_DIR_NAME}"
  DESTINATION "${INSTALL_BUNDLE_DATA_DIR}" COMPONENT Runtime)

# Install the AOT library on non-Debug builds only.
install(FILES "${AOT_LIBRARY}" DESTINATION "${INSTALL_BUNDLE_DATA_DIR}"
  CONFIGURATIONS Profile;Release
  COMPONENT Runtime)
