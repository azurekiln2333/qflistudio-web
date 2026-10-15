#!/usr/bin/env bash
# Access-log regression runner for the Linux embedded engine.
#
# Reproduces the editor's real sequence — configuration check, then server, then
# a restart — and fails unless every scenario writes its access log. This guards
# the ngx_time cache regression where a -t run in the same process left
# ngx_cached_time pointing at a zeroed slot, so the access-log handler skipped
# every line.
#
# Usage:
#   QFLI_NGINX_BUILD_ROOT=<windows-visible-dir> \
#     bash scripts/build_nginx_embedded.sh linux "$PWD/build/native/nginx/embedded-linux"
#   bash native/nginx/embedded/run_access_log_regression.sh \
#     "$PWD/build/native/nginx/embedded-linux/libqfli_nginx.so"
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
so="${1:?Usage: run_access_log_regression.sh <libqfli_nginx.so>}"
[[ -f "$so" ]] || { echo "missing $so; build the Linux embedded engine first" >&2; exit 1; }
exec python3 "$root/native/nginx/embedded/access_log_probe.py" "$so"
