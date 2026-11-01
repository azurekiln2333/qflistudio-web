# OHOS CDP native window — source handoff

Status: **SOURCE ONLY / NATIVE EXECUTION UNRUN**, 2026-10-24. Preparation started
no compiler, CMake, Ninja, readelf, Flutter, browser, WSL, OHPM, Hvigor, HAP or
device command. It claimed no host slot, accepted no grant, sent no channel
message and made no core/product-source edit, commit or push.

## Boundary and pinned reuse

Only [run-web-native-window.py](run-web-native-window.py) and this report were
added. No worker is needed: future native phases launch exact existing CMake
and readelf applications directly. The new entry imports the frozen
[application supervisor](run-web-app-window.py) solely for its reviewed Job
execution, JSON, hash, time and helper-loading functions. Its guarded main never
runs application phases. Both that source and the unchanged
[owned-Job helper](run-web-owned-window.py) are checked against pinned SHA256
values before import/use, and included in the immutable input manifest:

```text
d80c46e1b1cf2abe7e7a582e61016ac36266354242de198a5623628659922a19  run-web-app-window.py
9df7a94399aae38951337d61693d65de6e3cef438d02d4e51c787242dfda7fbe  run-web-owned-window.py
```

This implements only the first phase of
[native-next-gate-20261024.md](native-next-gate-20261024.md). It follows the
[native CDP contract](../../../spec/backend/web-cdp-transport.md). NAPI runtime,
ArkTS/import resolution, Linux fixtures, HAP packaging, OHOS execution,
authorization and actual debugger behavior remain separate gates.

## Future command and limits

After root reviews this source and accepts a **new named 180-second native-only
handoff**, use the actual running Python application and a fresh evidence name:

```powershell
& 'D:/ProgramFiles/Python/Python313/python.exe' -B -X utf8 .trellis/tasks/10-22-standalone-offline-ide/research/run-web-native-window.py --grant ACTUAL_NEW_HANDOFF --run-name FRESH_NAME --next-owner NAMED_SUCCESSOR
```

The entry neither acquires a slot nor infers a grant from historical releases.
An existing run directory is refused. The application supervisor and helper
must still match the pins; a later source change requires explicit re-review
and re-freeze before adoption.

The only native target is `qfli_web_cdp_transport`. It runs arm64-v8a first,
then x86_64, sequentially, with `cmake --build EXISTING_RELEASE_CACHE --target
qfli_web_cdp_transport --parallel 1`. Each successful build is followed by
`llvm-readelf --wide --file-header --program-headers --dyn-syms --dynamic SO`
and independent Python validation of that exact ELF. Commands use cache-bound,
existing absolute application paths, with no shell command string or PATH
re-resolution. No configure/install/download, general application build or WSL
command is added; CMake may perform its normal local regeneration.

Each build has at most 65 seconds and needs at least 10 work seconds remaining;
each ELF inspection has at most 6 seconds and needs at least 1 second remaining.
Work ends at 150 seconds, validation cleanup at 170 seconds, publisher cleanup
at 180 seconds. A phase-start guard runs again immediately before launch:
**no native phase starts at or after 140 seconds**. The first failure/deadline
stops the sequence and leaves later phases **UNRUN**. These are process
scheduling deadlines; synchronous Python hashing/report I/O has no separate
hard wall-clock watchdog. Actual duration and cleanup remain unproven.

Every native command and the publisher start suspended in separate private
Windows Jobs, assigned before resume. A terminal root with descendants cannot
release. Only the owned Job is stopped at a deadline. Forced cleanup is
incomplete evidence. Unconfirmed cleanup records **HOLD/UNRELEASED** and retains
the exact handles in a live supervisor, including when final report/stdout
persistence fails.

Publication follows the reviewed two-step protocol: the contained publisher
sends **RELEASE_PENDING_PUBLISHER** or HOLD and explicitly **NO SUCCESSOR GRANT**.
Only after publisher terminal exit 0/empty Job can final `job.json`/stdout say
RELEASE, with `allOwnedJobsEmpty`, `terminalConfirmed`, `publication.delivered`
and `rootRelayRequired`. Root must relay that completed report as the actual
named handoff. Failed delivery with empty Jobs needs explicit root relay;
unconfirmed publisher cleanup stays HOLD. Cleanup RELEASE does not establish
a compilation pass.

## Input, cache and ELF evidence

Before and after snapshots freeze connector/NAPI sources and project headers,
CMake files, local module metadata/types, entry profile/manifest, both Nginx
configure-time archives, native syntax CMake plus every retained QuickJS hash
input, SDK NAPI headers, SDK/HMS metadata and toolchain CMake inputs. They also
hash actual C/C++ compiler, CMake, Ninja and readelf applications, both pinned
lifecycle sources and the new supervisor. This is not a hermetic hash of every
SDK system header, runtime library or CMake module.

Both caches must bind this checkout's source/cache/output paths, Release,
Ninja, OHOS and matching ABI; actual compiler paths come from the generated
C/C++ compiler records. CMake/readelf/Ninja and toolchain paths must match the
installed SDK. Compiler/linker flags and OHOS/HMOS/QFLI cache options are bound
semantically; generated `-ADVANCED` metadata is excluded from that contract.
These bindings are rechecked after each operation and in the final snapshot.

Raw `CMakeCache.txt`, `build.ninja`, rules and generated compiler/system CMake
records are preserved separately before/after. Their raw differences are
reported without causing a false immutable-input drift failure. Existing and
produced `.so` records are also separate generated-artifact evidence. A fresh
run retains each accepted `.so`, full SHA256/size, readelf output and ELF JSON.
The retained hash must match both the validated bytes and current output; a
later output change invalidates the checkpoint. This is an incremental target
build, not a claim of a clean rebuild.

The ELF validator requires ELF64 little endian, DYN, entry 0, AArch64 machine
183 or x86-64 machine 62 as appropriate; nonempty LOAD segments with power-of-two
alignment at least 0x4000, congruent offsets/addresses, valid file bounds and
file size no larger than memory size. All four `qfli_web_cdp_*` operations must
be unique defined GLOBAL/DEFAULT/FUNC dynamic exports. Undefined, weak or hidden
names cannot satisfy the gate. It records all dynamic dependencies and undefined
imports, requires the NAPI/C++ dependencies and actual NAPI/pthread imports,
and does not require a standalone `libpthread` dependency because libc may
provide those symbols. Exit 0 or a `.so` filename alone cannot pass.

## Lightweight preparation results

The following reads only files and hashes, and writes no reports or Jobs:

```powershell
& 'D:/ProgramFiles/Python/Python313/python.exe' -B -X utf8 .trellis/tasks/10-22-standalone-offline-ide/research/run-web-native-window.py --snapshot-only
```

- Python AST and snapshot-only preflight: **PASS**, 49 immutable input files,
  six generated records per ABI, both CDP output artifacts absent.
- Both actual cache bindings: **Release/Ninja/OHOS**, correct source/output/ABI,
  HMS wrapper and installed OpenHarmony Clang 15.0.4 records.
- Actual applications under
  `D:/ProgramFiles/Huawei/DevEco Studio/sdk/default/openharmony/native/`:
  `build-tools/cmake/bin/cmake.exe`, `build-tools/cmake/bin/ninja.exe`,
  `llvm/bin/clang.exe`, `llvm/bin/clang++.exe`, `llvm/bin/llvm-readelf.exe`.
- Synthetic ELF byte controls: **21/21**, including both good ABIs and rejection
  of wrong class/machine/entry, invalid LOAD ranges/alignment, hidden/weak/object/
  undefined exports, missing dependencies/imports and malformed tables. These
  used only Python byte fixtures in a temporary directory; no ELF, SDK utility,
  Job or subprocess was executed.

Frozen supervisor SHA256:

```text
63391cd84d72edc59ad5d497df11ee32520ae6208b1aac84d4812d5e44b9a6e7  run-web-native-window.py
```

Root's independent final read-only review found no additional material source
issue in cache/compiler bindings, immutable/generated evidence, ELF tables and
exports/imports, captured/final artifact equality, phase deadlines or the pending
publisher/terminal/root-relay sequence. Root independently reran snapshot-only:
49 immutable inputs, six generated records per ABI, both CDP outputs absent.
The runner hash above is unchanged. The first actual granted native run remains
required; this source preparation establishes no native compilation, NAPI
runtime, HAP/device or eleven-product acceptance.
