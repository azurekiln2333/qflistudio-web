#!/usr/bin/env bash
set -euo pipefail

abi="${1:?Usage: build_nginx_android.sh ABI NDK_ROOT}"
ndk="${2:?Pass the installed Android NDK root}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version=1.31.6
case "$abi" in
  arm64-v8a) triple=aarch64-linux-android; crossfile=64; arch=aarch64 ;;
  armeabi-v7a) triple=armv7a-linux-androideabi; crossfile=32; arch=arm ;;
  x86_64) triple=x86_64-linux-android; crossfile=64; arch=x86_64 ;;
  *) printf 'Unsupported Android ABI: %s\n' "$abi" >&2; exit 1 ;;
esac

archive="$root/vendor/nginx/nginx-$version.tar.gz"
printf '%s  %s\n' 974ed5298a5e398e008704ed5db284e655fc270c596493dbccada452448fc9f1 "$archive" | sha256sum --check
host=linux-x86_64
suffix=
if [[ -f "$ndk/toolchains/llvm/prebuilt/windows-x86_64/bin/clang.exe" ]]; then
  host=windows-x86_64
  suffix=.exe
fi
toolchain="$ndk/toolchains/llvm/prebuilt/$host"
export NGINX_CLANG="$toolchain/bin/clang$suffix"
export NGINX_TARGET="${triple}24"
export NGINX_SYSROOT="$toolchain/sysroot"
glob_include="$root/vendor/nginx/android-glob"
if [[ "$host" == windows-x86_64 ]]; then
  export NGINX_SYSROOT="$(wslpath -m "$NGINX_SYSROOT")"
  glob_include="$(wslpath -m "$glob_include")"
fi

build="$root/build/native/nginx/android-$abi"
mkdir -p "$build"
source="$build/nginx-$version"
if [[ ! -f "$source/.prepared" ]]; then
  tar -xzf "$archive" -C "$build"
  cd "$source"
  patch --batch -p1 < "$root/vendor/nginx/patches/cross-compile-nginx.patch"
  patch --batch -p1 < "$root/vendor/nginx/patches/Android-crossfile.patch$crossfile"
  for name in src-core-ngx_file.c src-event-modules-ngx_epoll_module.c src-os-unix-ngx_setaffinity.h; do
    patch --batch -p1 < "$root/vendor/nginx/patches/$name.patch"
  done
  touch .prepared
fi
cd "$source"
if [[ ! -f .stat-size-prepared ]]; then
  patch --batch -p1 < "$root/vendor/nginx/patches/android-stat-size.patch"
  touch .stat-size-prepared
fi
if [[ ! -f .socklen-prepared ]]; then
  patch --batch -p1 < "$root/vendor/nginx/patches/android-socklen.patch"
  touch .socklen-prepared
fi
if [[ ! -f .stat-blocks-prepared ]]; then
  patch --batch -p1 < "$root/vendor/nginx/patches/android-stat-blocks.patch"
  touch .stat-blocks-prepared
fi
bash "$root/scripts/nginx_cc.sh" -O2 -I"$glob_include" -c "$glob_include/glob.c" -o glob.o
archiver=("$toolchain/bin/llvm-ar$suffix")
if [[ "$host" == windows-x86_64 && -n "${WSL_INTEROP:-}" ]]; then
  archiver=(/init "${archiver[0]}" llvm-ar.exe)
fi
"${archiver[@]}" rcs libandroid-glob.a glob.o

./configure \
  --prefix=. \
  --crossbuild="Linux:4.19:$arch" \
  --crossfile=auto/cross/Android \
  --with-cc="bash $root/scripts/nginx_cc.sh" \
  --with-cc-opt="-O2 -I$glob_include" \
  --with-ld-opt="-L. -landroid-glob -Wl,-z,max-page-size=16384" \
  --without-http_rewrite_module \
  --without-http_auth_basic_module
make -j"${NGINX_BUILD_JOBS:-4}"
destination="$root/android/app/src/main/jniLibs/$abi"
mkdir -p "$destination"
cp objs/nginx "$destination/libnginx_exec.so"
printf 'Built native Nginx for %s: %s\n' "$abi" "$destination/libnginx_exec.so"
