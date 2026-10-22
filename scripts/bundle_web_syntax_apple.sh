#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ "$(uname -s)" == Darwin ]] || { printf 'Web syntax backend requires Xcode\n' >&2; exit 1; }
command -v python3 >/dev/null || { printf 'Python 3 is required for pinned source verification\n' >&2; exit 1; }
case "${PLATFORM_NAME:?Run from an Apple Runner target}" in
  iphoneos|iphonesimulator) platform=ios; library=libqfli_web_syntax.a ;;
  macosx) platform=macos; library=libqfli_web_syntax.dylib ;;
  *) printf 'Unsupported Apple syntax backend platform\n' >&2; exit 1 ;;
esac
output="${BUILT_PRODUCTS_DIR:?}/qfli-web-syntax"
mkdir -p "$output"
libraries=()
for arch in ${ARCHS:?}; do
  arch_output="$output/$PLATFORM_NAME/$arch"
  python3 "$root/scripts/build_web_syntax.py" --platform "$platform" \
    --apple-sdk "$PLATFORM_NAME" --arch "$arch" --output "$arch_output"
  xcrun lipo -verify_arch "$arch" "$arch_output/$library"
  # Inspect each object so an arm64 device archive cannot masquerade as an
  # arm64 simulator archive (architecture alone cannot distinguish the two).
  inspect="$arch_output"
  if [[ "$platform" == ios ]]; then
    inspect="$(mktemp -d "$arch_output/inspect.XXXXXX")"
    (cd "$inspect" && xcrun ar -x "$arch_output/$library")
  fi
  : > "$arch_output/platform.txt"
  for object in "$inspect"/*.o; do
    xcrun vtool -show-build "$object" >> "$arch_output/platform.txt"
  done
  expected=MACOS
  if [[ "$PLATFORM_NAME" == iphoneos ]]; then expected=IOS; fi
  if [[ "$PLATFORM_NAME" == iphonesimulator ]]; then expected=IOSSIMULATOR; fi
  awk -v expected="$expected" '
    $1 == "platform" {seen++; if ($2 != expected) bad=1}
    END {exit (!seen || bad)}
  ' "$arch_output/platform.txt"
  libraries+=("$arch_output/$library")
done
xcrun lipo -create "${libraries[@]}" -output "$output/$library"
if [[ "$platform" == macos ]]; then
  bundle="${TARGET_BUILD_DIR:?}/${CONTENTS_FOLDER_PATH:?}"
  mkdir -p "$bundle/Frameworks"
  installed="$bundle/Frameworks/$library"
  install -m 755 "$output/$library" "$installed"
  install_name_tool -id "@rpath/$library" "$installed"
  identity="${EXPANDED_CODE_SIGN_IDENTITY:--}"
  if [[ -z "$identity" ]]; then identity=-; fi
  options=()
  if [[ "$identity" != - ]]; then options+=(--timestamp --options runtime); fi
  codesign --force --sign "$identity" "${options[@]}" "$installed"
fi
