#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bundle="${TARGET_BUILD_DIR:?}/${CONTENTS_FOLDER_PATH:?}"
executable="$bundle/Helpers/nginx"
bash "$root/scripts/build_nginx_desktop.sh" macos \
  "${DERIVED_FILE_DIR:?}/nginx/nginx"
mkdir -p "$bundle/Helpers" "$bundle/Resources/nginx"
install -m 755 "$DERIVED_FILE_DIR/nginx/nginx" "$executable"
install -m 644 "$root/vendor/nginx/LICENSE" "$bundle/Resources/nginx/LICENSE"
identity="${EXPANDED_CODE_SIGN_IDENTITY:--}"
if [[ -z "$identity" ]]; then identity=-; fi
sign_options=()
if [[ "$identity" != - ]]; then sign_options+=(--timestamp --options runtime); fi
codesign --force --sign "$identity" "${sign_options[@]}" \
  --entitlements "$root/macos/Runner/Nginx.entitlements" "$executable"
lipo -verify_arch ${ARCHS:-$(uname -m)} "$executable"
