#!/usr/bin/env bash
set -euo pipefail

# Native SDK compiler entry point shared by Android and OpenHarmony builds.

compiler=("$NGINX_CLANG")
if [[ "$NGINX_CLANG" == *.exe && -n "${WSL_INTEROP:-}" ]]; then
  # Supply argv[0] explicitly when using WSL's executable interpreter.
  compiler=(/init "$NGINX_CLANG" clang.exe)
fi
"${compiler[@]}" --target="$NGINX_TARGET" --sysroot="$NGINX_SYSROOT" \
  -DIOV_MAX=1024 -D__USE_GNU=1 -fPIE "$@" 2>&1 | tr -d '\r'
