#!/usr/bin/env bash
set -euo pipefail

# OpenHarmony embedded-engine compiler entry point.
#
# The installed HarmonyOS native SDK ships Windows clang.exe. Two constraints
# follow:
#   1. Under WSL the executable-interpreter form must supply argv[0] explicitly.
#   2. clang.exe resolves paths on the Windows side, so every path-shaped
#      argument and the sysroot must be translated with wslpath -m.
# CR is stripped from output so nginx's `clang -v` probe writes a valid
# NGX_COMPILER string. The embedded engine is a shared library, so PIC replaces
# the standalone PIE flag from scripts/nginx_cc.sh.

clang="${QFLI_NGINX_CLANG:?}"
sysroot_raw="${QFLI_NGINX_SYSROOT:?}"
case "$sysroot_raw" in
  /*) sysroot="$(wslpath -m "$sysroot_raw")" ;;
  *)  sysroot="$sysroot_raw" ;;
esac

# Translate WSL paths to Windows form, but leave flags and bare names alone.
args=()
if [[ -n "${QFLI_NGINX_COMPAT_HEADER:-}" ]]; then
  args+=("-include" "$(wslpath -m "$QFLI_NGINX_COMPAT_HEADER")")
fi
for arg in "$@"; do
  case "$arg" in
    /*) args+=("$(wslpath -m "$arg")") ;;
    *)  args+=("$arg") ;;
  esac
done

if [[ "$clang" == *.exe && -n "${WSL_INTEROP:-}" ]]; then
  /init "$clang" clang.exe \
    --target="${QFLI_NGINX_TARGET:?}" --sysroot="$sysroot" \
    -DIOV_MAX=1024 -D__USE_GNU=1 -fPIC "${args[@]}" 2>&1 | tr -d '\r'
  exit "${PIPESTATUS[0]}"
fi
"$clang" \
  --target="${QFLI_NGINX_TARGET:?}" --sysroot="$sysroot" \
  -DIOV_MAX=1024 -D__USE_GNU=1 -fPIC "${args[@]}" 2>&1 | tr -d '\r'
exit "${PIPESTATUS[0]}"
