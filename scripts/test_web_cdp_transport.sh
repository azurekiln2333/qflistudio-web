#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != Linux ]]; then
  echo "This real abstract-AF_UNIX regression requires Linux." >&2
  exit 2
fi
output="${1:?Pass an explicit Linux output directory}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
compiler="${CXX:-c++}"
mkdir -p "$output"

# Compile the exact portable connector. The SDK-only NAPI wrapper is checked by
# the separate OHOS build and own-application ArkWeb acceptance, never faked here.
"$compiler" -std=c++17 -O2 -g -Wall -Wextra -Werror -fPIC -fvisibility=hidden \
  -shared -pthread "$root/ohos/entry/src/main/cpp/web_cdp_transport.cpp" \
  -o "$output/libqfli_web_cdp_transport_test.so"
timeout --signal=TERM 30s python3 -X faulthandler \
  "$root/test/native/test_web_cdp_transport.py" \
  "$output/libqfli_web_cdp_transport_test.so"
