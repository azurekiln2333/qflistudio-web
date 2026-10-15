#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ "$(uname -s)" == Darwin ]] || { printf 'iOS Nginx requires Xcode\n' >&2; exit 1; }
case "${PLATFORM_NAME:?Run from the iOS Runner target}" in
  iphoneos|iphonesimulator) sdk="$PLATFORM_NAME" ;;
  *) printf 'Unsupported Apple platform\n' >&2; exit 1 ;;
esac
output="${BUILT_PRODUCTS_DIR:?}/qfli-nginx"
mkdir -p "$output"
archives=()
for arch in ${ARCHS:?}; do
  arch_output="$output/$arch"
  bash "$root/scripts/build_nginx_embedded.sh" ios "$arch_output" "$arch" "$sdk"
  # Both architecture and platform must match before linking into the app.
  xcrun lipo -verify_arch "$arch" "$arch_output/libqfli_nginx.a"
  inspect="$(mktemp -d "$arch_output/inspect.XXXXXX")"
  (cd "$inspect" && xcrun ar -x "$arch_output/libqfli_nginx.a")
  : > "$arch_output/platform.txt"
  for object in "$inspect"/*.o; do
    xcrun vtool -show-build "$object" >> "$arch_output/platform.txt"
  done
  expected=IOS
  if [[ "$sdk" == iphonesimulator ]]; then expected=IOSSIMULATOR; fi
  awk -v expected="$expected" '
    $1 == "platform" {seen++; if ($2 != expected) bad=1}
    END {exit (!seen || bad)}
  ' "$arch_output/platform.txt"
  archives+=("$arch_output/libqfli_nginx.a")
done
xcrun lipo -create "${archives[@]}" -output "$output/libqfli_nginx.a"
license="${TARGET_BUILD_DIR:?}/${UNLOCALIZED_RESOURCES_FOLDER_PATH:?}/nginx"
mkdir -p "$license"
cp "$root/vendor/nginx/LICENSE" "$license/LICENSE"
shasum -a 256 "$output/libqfli_nginx.a" > "$license/HASHES.sha256"
