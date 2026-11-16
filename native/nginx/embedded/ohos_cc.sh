#!/usr/bin/env bash
set -euo pipefail

# OpenHarmony embedded-engine compiler entry point.
#
# Linux SDK paths stay in their native form. When WSL invokes Windows clang.exe:
#   1. Under WSL the executable-interpreter form must supply argv[0] explicitly.
#   2. clang.exe resolves paths on the Windows side, so every path-shaped
#      argument and the sysroot must be translated with wslpath -m.
# CR is stripped from output so nginx's `clang -v` probe writes a valid
# NGX_COMPILER string. The embedded engine is a shared library, so PIC replaces
# the standalone PIE flag from scripts/nginx_cc.sh.

clang="${QFLI_NGINX_CLANG:?}"
windows_compiler=0
if [[ "$clang" == *.exe && -n "${WSL_INTEROP:-}" ]]; then
  windows_compiler=1
fi

compiler_path() {
  if [[ "$windows_compiler" == 1 && "$1" == /* ]]; then
    wslpath -m "$1"
  else
    printf '%s\n' "$1"
  fi
}

sysroot="$(compiler_path "${QFLI_NGINX_SYSROOT:?}")"

# Translate WSL paths to Windows form, but leave flags and bare names alone.
args=()
if [[ -n "${QFLI_NGINX_COMPAT_HEADER:-}" ]]; then
  args+=("-include" "$(compiler_path "$QFLI_NGINX_COMPAT_HEADER")")
fi
for arg in "$@"; do
  args+=("$(compiler_path "$arg")")
done

if [[ "$windows_compiler" == 1 ]]; then
  /init "$clang" clang.exe \
    --target="${QFLI_NGINX_TARGET:?}" --sysroot="$sysroot" \
    -DIOV_MAX=1024 -D__USE_GNU=1 -fPIC "${args[@]}" 2>&1 | tr -d '\r'
  exit "${PIPESTATUS[0]}"
fi
"$clang" \
  --target="${QFLI_NGINX_TARGET:?}" --sysroot="$sysroot" \
  -DIOV_MAX=1024 -D__USE_GNU=1 -fPIC "${args[@]}" 2>&1 | tr -d '\r'
exit "${PIPESTATUS[0]}"
