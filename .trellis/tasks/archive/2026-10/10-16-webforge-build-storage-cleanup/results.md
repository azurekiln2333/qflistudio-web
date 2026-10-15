# WebForge storage cleanup — 2026-10-16

Workspace size fell from **39.505 GiB to 4.763 GiB** after cleanup and both build checks, a net reduction of **34.742 GiB** in measured file lengths. Directory measurements do not follow reparse points.

## Cleanup boundary

Removed only two ignored generated directories with no tracked files:

| Directory | Previous bytes | Purpose |
| --- | ---: | --- |
| `build/native/platform-audit` | 35,100,978,991 | Historical cross-product source exports, temporary builds, downloaded runtimes and test AVD |
| `build/native/validation` | 2,245,184,766 | Temporary validation AVD and old test evidence |

Preserved `build/app`, `build/native/nginx`, `.dart_tool`, Android Gradle cache, all OHOS build/dependency directories, Node dependencies, final packages, retained native source and packaged libraries. Normal WebForge build sources contain no dependency on either deleted tree. No `flutter clean`, device commands or sibling-workspace modifications were performed.

The cleanup verified exact absolute targets and ancestors, then removed 86 symlinks/junctions/WSL reparse points themselves without traversing SDK or Pub Cache targets. Independent review confirmed those external targets still exist.

## Local preservation archive

Archived 7,355 historical source/evidence files including all **48 patches** (47 audit patches and one validation patch), then verified each archived file's SHA-256 and the complete ZIP hash before deletion.

- Path: `.trellis/.runtime/storage-cleanup-2026-10-16/historical-audit-source-and-evidence.zip`
- Bytes: 39,823,443 (about 38 MiB)
- SHA-256: `85f12ea1465f37702140ebe90481988c9a1c0c26b1d38c1f7f05a37a4a20be89`
- The archive and per-file manifest remain local; original historical task records are preserved in place.

The four previously dirty audit documents retain the same diff hash. All 114 original non-task untracked files remain present. Cleanup changed no application source, build configuration or shared core files.

## Build verification

Used the installed `D:/ProgramFiles/flutter_ohos/bin/flutter.bat`, serialized the builds and kept pub enabled.

| Check | Result |
| --- | --- |
| `flutter build apk --release` | Exit 0; fresh release APK generated; 137.33 s |
| `flutter build hap --release` | Fresh release unsigned HAP generated; 85.95 s; wrapper exits 1 at missing WebForge signing |
| Retained native inputs | SHA-256 checks 21/21 |
| Both output archives | Freshness and ZIP CRC checks pass |
| Product curriculum and license bytes | Both archives match current source for both JSON catalogs and both retained licenses |
| Android native entries | ARM64, ARMv7 and x86_64 present |
| OHOS native entries | ARM64 and x86_64 embedded NAPI libraries present; obsolete process executable absent |

Fresh artifacts:

- APK: `build/app/outputs/flutter-apk/app-release.apk`; 32,413,285 bytes; SHA-256 `b3f975377fb1207100eccff258b25b07742fd55943325b568778046cb831f4e9`.
- HAP: `ohos/entry/build/default/outputs/default/entry-default-unsigned.hap`; 42,389,141 bytes; SHA-256 `41470b9b6c090d1dc40d6c254096af501287889c75dca668826713af807012ce`.

OHOS compilation and unsigned packaging work after cleanup. The pre-existing missing product signature still prevents a complete signed-release command/device verification; no signed or device pass is claimed. Signing configuration is unchanged. No runtime source changed, so verification focused on actual platform builds, retained input hashes, package bytes and cleanup integrity rather than rerunning unrelated UI/runtime suites.

Machine-readable evidence: `cleanup-report.json`, `artifact-audit.json`, `native-input-audit.json`, build result JSON and the two build logs. The release verification spec now documents the cache-preserving cleanup boundary.
