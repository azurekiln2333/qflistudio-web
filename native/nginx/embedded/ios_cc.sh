#!/usr/bin/env bash
set -euo pipefail
exec "${QFLI_NGINX_CLANG:?}" -target "${QFLI_NGINX_TARGET:?}" \
  -isysroot "${QFLI_NGINX_SYSROOT:?}" "$@"
