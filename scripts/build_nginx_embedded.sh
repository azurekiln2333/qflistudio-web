#!/usr/bin/env bash
set -euo pipefail

platform="${1:?Usage: build_nginx_embedded.sh linux|ios|ohos OUTPUT [ARCH SDK|SDK_ROOT]}"
output="${2:?Pass an absolute output directory}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version=1.31.6
[[ "$output" == /* ]] || { printf 'Output must be absolute\n' >&2; exit 1; }
export QFLI_NGINX_IOS=0
configure_options=()
compiler="${CC:-cc}"
# Array form for direct invocation; a compiler string like "bash foo.sh"
# must not be passed as a single command name.
compiler_cmd=("${CC:-cc}")
archiver="${AR:-ar}"
symbol_tool="${NM:-nm}"
checksum=(sha256sum)
case "$platform:$(uname -s)" in
  linux:Linux) ;;
  ohos:Linux)
    sdk="${3:?Pass the installed OpenHarmony native SDK root}"
    arch="${4:?Pass arm64-v8a or x86_64}"
    case "$arch" in
      arm64-v8a) triple=aarch64-linux-ohos ;;
      x86_64) triple=x86_64-linux-ohos ;;
      *) printf 'Unsupported HarmonyOS ABI: %s\n' "$arch" >&2; exit 1 ;;
    esac
    # The embedded patch gates all cross-target runtime probes behind
    # QFLI_NGINX_IOS=1. HarmonyOS arm64-v8a/x86_64 share the iOS/Linux 64-bit
    # type sizes, so the same static sizes apply; only the compiler differs.
    export QFLI_NGINX_IOS=1
    export QFLI_NGINX_CLANG="$sdk/llvm/bin/clang"
    export QFLI_NGINX_SYSROOT="$sdk/sysroot"
    export QFLI_NGINX_TARGET="$triple"
    if [[ -f "$QFLI_NGINX_CLANG.exe" ]]; then
      export QFLI_NGINX_CLANG="$QFLI_NGINX_CLANG.exe"
    fi
    compiler="bash $root/native/nginx/embedded/ohos_cc.sh"
    compiler_cmd=(bash "$root/native/nginx/embedded/ohos_cc.sh")
    export QFLI_NGINX_COMPAT_HEADER="$root/vendor/nginx/ohos_socket_compat.h"
    archiver="ar"
    symbol_tool="nm"
    checksum=(sha256sum)
    configure_options+=("--crossbuild=Linux:5.10:${arch%%-*}")
    # The HarmonyOS native SDK ships Windows clang.exe. Under WSL that compiler
    # resolves relative source/output paths against the Windows CWD, so the
    # build tree must live on a Windows-visible mount (/mnt/...). A WSL-only
    # path such as /tmp makes configure fail with a bare
    # "C compiler ... is not found". Require an explicit visible build root.
    if [[ "$QFLI_NGINX_CLANG" == *.exe && -n "${WSL_INTEROP:-}" ]]; then
      case "${QFLI_NGINX_BUILD_ROOT:-${TMPDIR:-/tmp}}" in
        /mnt/*) ;;
        *) printf 'Set QFLI_NGINX_BUILD_ROOT to a Windows-visible path (e.g. /mnt/d/...); the HarmonyOS compiler is a Windows binary\n' >&2; exit 1 ;;
      esac
    fi
    ;;
  ios:Darwin)
    arch="${3:?Pass arm64 or x86_64}"
    sdk="${4:?Pass iphoneos or iphonesimulator}"
    case "$sdk:$arch" in
      iphoneos:arm64|iphonesimulator:arm64|iphonesimulator:x86_64) ;;
      *) printf 'Unsupported iOS SDK/architecture\n' >&2; exit 1 ;;
    esac
    export QFLI_NGINX_IOS=1
    export QFLI_NGINX_CLANG="$(xcrun --sdk "$sdk" --find clang)"
    export QFLI_NGINX_SYSROOT="$(xcrun --sdk "$sdk" --show-sdk-path)"
    export QFLI_NGINX_TARGET="$arch-apple-ios${IPHONEOS_DEPLOYMENT_TARGET:-13.0}"
    if [[ "$sdk" == iphonesimulator ]]; then
      QFLI_NGINX_TARGET="$QFLI_NGINX_TARGET-simulator"
    fi
    compiler="bash $root/native/nginx/embedded/ios_cc.sh"
    compiler_cmd=(bash "$root/native/nginx/embedded/ios_cc.sh")
    archiver="$(xcrun --find ar)"
    symbol_tool="$(xcrun --find nm)"
    checksum=(shasum -a 256)
    configure_options+=("--crossbuild=Darwin:iOS:$arch")
    ;;
  *) printf 'Build %s on its native build host\n' "$platform" >&2; exit 1 ;;
esac
archive="$root/vendor/nginx/nginx-$version.tar.gz"
expected="$(awk -v archive="vendor/nginx/nginx-$version.tar.gz" '$2 == archive {print $1}' "$root/vendor/nginx/HASHES.sha256")"
actual="$("${checksum[@]}" "$archive" | awk '{print $1}')"
[[ -n "$expected" && "$expected" == "$actual" ]] || {
  printf 'Nginx source checksum mismatch\n' >&2; exit 1;
}
mkdir -p "$output" "${QFLI_NGINX_BUILD_ROOT:-${TMPDIR:-/tmp}}"
build="$(mktemp -d "${QFLI_NGINX_BUILD_ROOT:-${TMPDIR:-/tmp}}/qfli-nginx-embedded.XXXXXX")"
printf '%s\n' "$build" > "$output/build-directory.txt"
tar -xzf "$archive" -C "$build"
cd "$build/nginx-$version"
patch --batch -p1 < "$root/vendor/nginx/patches/embedded.patch"
patch --batch -p1 < "$root/vendor/nginx/patches/embedded-time-cache.patch"
flags="-O2 -fPIC -fvisibility=hidden -std=gnu11 -DQFLI_NGINX_EMBEDDED=1"
if [[ "${QFLI_NGINX_SANITIZE:-0}" == 1 ]]; then
  flags="$flags -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer"
fi
./configure --prefix=. --with-cc="$compiler" --with-cc-opt="$flags" "${configure_options[@]}" \
  --without-http_gzip_module --without-http_rewrite_module \
  --without-http_auth_basic_module --without-http-cache \
  --add-module="$root/native/nginx/embedded"
objects=()
while IFS= read -r object; do objects+=("$object"); done < <(
  awk '
    take && /^$/ {exit}
    /^objs\/nginx:/ {take=1; sub(/^objs\/nginx:/, "")}
    take {for (i=1; i<=NF; i++) if ($i ~ /\.o$/) print $i}
  ' objs/Makefile
)
[[ ${#objects[@]} -gt 20 ]] || { printf 'Missing Nginx object graph\n' >&2; exit 1; }
for object in "${objects[@]}"; do
  case "$object" in
    */ngx_process.o|*/ngx_process_cycle.o|*/ngx_daemon.o|*/ngx_setproctitle.o)
      printf 'Process-management object in embedded build: %s\n' "$object" >&2
      exit 1
      ;;
  esac
done
make -f objs/Makefile -j"${NGINX_BUILD_JOBS:-2}" "${objects[@]}"
# Start a fresh archive so removed objects cannot survive a repeated Xcode build.
"$archiver" rcs "$build/libqfli_nginx.a" "${objects[@]}"
"$symbol_tool" -u "$build/libqfli_nginx.a" > "$output/undefined-symbols.txt"
awk '
  {
    symbol=$NF; sub(/^_/, "", symbol)
    if (symbol ~ /^(fork|vfork|exec[a-z]*|posix_spawn[a-z_]*|kill|raise|system|popen|exit|abort|setproctitle)$/) {
      print "Forbidden embedded process dependency: " $NF > "/dev/stderr"
      bad=1
    }
  }
  END {exit bad}
' "$output/undefined-symbols.txt"
cp "$build/libqfli_nginx.a" "$output/libqfli_nginx.a"
if [[ "$platform" == linux || "$platform" == ohos ]]; then
  "${compiler_cmd[@]}" $flags -shared -Wl,-z,defs -Wl,-z,max-page-size=16384 \
    -o "$output/libqfli_nginx.so" "${objects[@]}" -lpthread
fi
if [[ "$platform" == linux ]]; then
  "$compiler" $flags -I"$root/native/nginx/embedded" \
    "$root/native/nginx/embedded/test_lifecycle.c" "$output/libqfli_nginx.a" \
    -lpthread -o "$output/test_lifecycle"
fi
cp objs/ngx_auto_config.h "$output/ngx_auto_config.h"
cp "$root/native/nginx/embedded/qfli_nginx.h" "$output/qfli_nginx.h"
cp "$root/vendor/nginx/LICENSE" "$output/LICENSE"
"${checksum[@]}" "$archive" "$root/vendor/nginx/patches/embedded.patch" \
  "$root/vendor/nginx/patches/embedded-time-cache.patch" \
  "$root/native/nginx/embedded/qfli_nginx.c" "$root/native/nginx/embedded/qfli_nginx.h" \
  "$root/native/nginx/embedded/qfli_nginx_internal.h" "$root/native/nginx/embedded/config" \
  "$output/libqfli_nginx.a" > "$output/HASHES.sha256"
printf 'Built upstream Nginx %s embedded library: %s\n' "$version" "$output"
