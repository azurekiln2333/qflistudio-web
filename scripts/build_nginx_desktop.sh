#!/usr/bin/env bash
set -euo pipefail

platform="${1:?Usage: build_nginx_desktop.sh linux|macos [OUTPUT]}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version=1.31.6
archive="$root/vendor/nginx/nginx-$version.tar.gz"
output="${2:-$root/assets/runtime/nginx/$platform/nginx}"
case "$output" in
  /*) ;;
  *) output="$PWD/$output" ;;
esac

cc_options=-O2
ld_options=
case "$platform:$(uname -s)" in
  linux:Linux)
    compiler="${CC:-cc}"
    checksum=(sha256sum)
    ;;
  macos:Darwin)
    compiler="$(xcrun --find clang)"
    checksum=(shasum -a 256)
    ld_options="-mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET:-10.15}"
    for arch in ${ARCHS:-$(uname -m)}; do
      case "$arch" in
        arm64|x86_64) ld_options="$ld_options -arch $arch" ;;
        *) printf 'Unsupported macOS architecture: %s\n' "$arch" >&2; exit 1 ;;
      esac
    done
    cc_options="$cc_options $ld_options"
    ;;
  *) printf 'Build %s on its native operating system\n' "$platform" >&2; exit 1 ;;
esac

expected="$(awk -v archive="vendor/nginx/nginx-$version.tar.gz" '$2 == archive {print $1}' "$root/vendor/nginx/HASHES.sha256")"
actual="$("${checksum[@]}" "$archive" | awk '{print $1}')"
if [[ -z "$expected" || "$actual" != "$expected" ]]; then
  printf 'Nginx source checksum mismatch\n' >&2
  exit 1
fi

build="${output}.build"
mkdir -p "$build" "$(dirname "$output")"
tar -xzf "$archive" -C "$build"
cd "$build/nginx-$version"
./configure \
  --prefix=. \
  --with-cc="$compiler" \
  --with-cc-opt="$cc_options" \
  --with-ld-opt="$ld_options" \
  --without-http_gzip_module \
  --without-http_rewrite_module \
  --without-http_auth_basic_module
make -j"${NGINX_BUILD_JOBS:-2}"
install -m 755 objs/nginx "$output"
printf 'Built native Nginx for %s: %s\n' "$platform" "$output"
