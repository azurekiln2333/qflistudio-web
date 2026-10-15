#!/usr/bin/env bash
set -euo pipefail
output="${1:?Pass the Linux library output directory}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "${QFLI_NGINX_SANITIZE:-0}" == 1 ]]; then
  ASAN_OPTIONS=detect_leaks=0 LD_PRELOAD="$("${CC:-cc}" -print-file-name=libasan.so)" \
    python3 -X faulthandler "$root/native/nginx/embedded/test_embedded.py" "$output/libqfli_nginx.so"
else
  python3 -X faulthandler "$root/native/nginx/embedded/test_embedded.py" "$output/libqfli_nginx.so"
fi
ASAN_OPTIONS=detect_leaks=1 "$output/test_lifecycle"
