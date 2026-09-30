#!/usr/bin/env bash
set -euo pipefail

abi="${1:?Usage: build_nginx_ohos.sh ABI NATIVE_SDK_ROOT}"
sdk="${2:?Pass the installed OpenHarmony native SDK root}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version=1.31.6
case "$abi" in
  arm64-v8a) triple=aarch64-linux-ohos; arch=aarch64 ;;
  x86_64) triple=x86_64-linux-ohos; arch=x86_64 ;;
  *) printf 'Unsupported HarmonyOS ABI: %s\n' "$abi" >&2; exit 1 ;;
esac
archive="$root/vendor/nginx/nginx-$version.tar.gz"
printf '%s  %s\n' 974ed5298a5e398e008704ed5db284e655fc270c596493dbccada452448fc9f1 "$archive" | sha256sum --check
export NGINX_CLANG="$sdk/llvm/bin/clang"
export NGINX_SYSROOT="$sdk/sysroot"
export NGINX_TARGET="$triple"
compat_header="$root/vendor/nginx/ohos_socket_compat.h"
if [[ -f "$NGINX_CLANG.exe" ]]; then
  export NGINX_CLANG="$NGINX_CLANG.exe"
  export NGINX_SYSROOT="$(wslpath -m "$NGINX_SYSROOT")"
  compat_header="$(wslpath -m "$compat_header")"
fi
build="$root/build/native/nginx/ohos-$abi"
mkdir -p "$build"
source="$build/nginx-$version"
if [[ ! -f "$source/.prepared" ]]; then
  tar -xzf "$archive" -C "$build"
  cd "$source"
  patch --batch -p1 < "$root/vendor/nginx/patches/cross-compile-nginx.patch"
  patch --batch -p1 < "$root/vendor/nginx/patches/Android-crossfile.patch64"
  touch .prepared
fi
cd "$source"
./configure \
  --prefix=. \
  --crossbuild="Linux:5.10:$arch" \
  --crossfile=auto/cross/Android \
  --with-cc="bash $root/scripts/nginx_cc.sh" \
  --with-cc-opt="-O2 -include $compat_header" \
  --with-ld-opt=-Wl,-z,max-page-size=16384 \
  --without-http_rewrite_module \
  --without-http_auth_basic_module
make -j"${NGINX_BUILD_JOBS:-4}"
destination="$root/ohos/entry/libs/$abi"
mkdir -p "$destination"
cp objs/nginx "$destination/libnginx_exec.so"
printf 'Built native Nginx for %s: %s\n' "$abi" "$destination/libnginx_exec.so"
