#!/usr/bin/env bash
set -euo pipefail
root=/mnt/d/MyNewProjects/qfli_web/build/native/platform-audit/nginx-linux
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
mkdir -p "$root/logs" "$root/site"
cp "$here/nginx-linux-smoke.conf" "$root/nginx-smoke.conf"
cp "$here/nginx-linux-marker.txt" "$root/site/marker.txt"
server_pid=
cleanup() {
    if [[ -n "$server_pid" ]]; then
        kill "$server_pid" 2>/dev/null || true
        wait "$server_pid" 2>/dev/null || true
    fi
}
trap cleanup EXIT
"$root/nginx" -v
"$root/nginx" -p "$root/" -c nginx-smoke.conf -t
"$root/nginx" -p "$root/" -c nginx-smoke.conf &
server_pid=$!
for ((attempt=0; attempt<50; attempt++)); do
    if curl --silent --fail http://127.0.0.1:18479/marker.txt > /dev/null; then break; fi
    sleep 0.1
done
[[ $(curl --silent --fail http://127.0.0.1:18479/marker.txt) == QFLI_NATIVE_LINUX_NGINX ]]
printf 'PASS native Linux static response\n'
headers=$(curl --silent --fail -D - http://127.0.0.1:18479/proxy/marker.txt)
[[ "$headers" == *'X-Qfli-Upstream: native'* && "$headers" == *QFLI_NATIVE_LINUX_NGINX* ]]
printf 'PASS native Linux HTTP proxy\n'
[[ $(curl --silent --output /dev/null --write-out '%{http_code}' http://127.0.0.1:18479/missing.txt) == 404 ]]
printf 'PASS native Linux missing-file status\n'
"$root/nginx" -p "$root/" -c nginx-smoke.conf -s quit
wait "$server_pid"
server_pid=
if curl --silent --fail --max-time 2 http://127.0.0.1:18479/marker.txt > /dev/null; then
    printf 'Server still accepts requests after stop\n' >&2
    exit 1
fi
printf 'PASS native Linux stop closes listener\n'
