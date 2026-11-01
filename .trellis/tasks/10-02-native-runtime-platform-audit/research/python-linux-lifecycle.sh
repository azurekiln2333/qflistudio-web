#!/usr/bin/env bash
set -euo pipefail
root=/mnt/d/MyNewProjects/qfli_python
evidence=/mnt/d/MyNewProjects/qfli_web/build/native/platform-audit
research=/mnt/d/MyNewProjects/qfli_web/.trellis/tasks/10-02-native-runtime-platform-audit/research
output=/root/qfli-python-lifecycle-final
mkdir -p "$output"
cmake -S "$root/native/desktop" -B "$output/build" -DCMAKE_BUILD_TYPE=Release > "$output/configure.log" 2>&1
cmake --build "$output/build" --parallel 1 > "$output/build.log" 2>&1
gcc -std=gnu99 -O2 -I "$root/native/src" "$root/native/tests/smoke.c" \
  -L "$output/build" -Wl,-rpath,"$output/build" -lqfli_py_ffi \
  -lm -lpthread -o "$output/native-smoke"
"$output/native-smoke" | tee "$evidence/python-linux-native-final.log"
timeout 30s python3 "$research/python-linux-lifecycle.py" \
  "$output/build/libqfli_py_ffi.so" | tee "$evidence/python-linux-lifecycle-final.log"
