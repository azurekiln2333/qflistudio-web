# Android ARM64 OpenJDK Package Recovery

## Scope And Inputs

Owning repository: D:/MyNewProjects/qfli_java, native recipe baseline ea7b4df.
The corrected source recipe had not refreshed the generated ARM64 package.
The old owning package audit rejected 39 native files for 4 KiB LOAD alignment,
including both launchers, the JVM and the old spawn library. Retain this failed
audit separately from the successful replacement.

Built actual OpenJDK 17.0.20 with the owning pinned recipe, Termux patch commit
d0f94da1e578a0c9550a84d408bc8ed0003882ec, Clang 18.1.3 and Android NDK
27.0.12077973. Source archive SHA-256:
ba3ac4b9d7f2c050f46ddcec39b4258660a3f09836f5a71617fd3f7311d06c0b.
WSL distro qfli-java-build; independent work root /root/qfli-android-arm64-16k;
boot JDK /usr/lib/jvm/java-17-openjdk-amd64; two build jobs. The build completed
make images and exported dereferenced files without changing the old source tree.

Orchestration: build/native/platform-audit/java-android/rebuild-arm64-16k.sh.
Evidence root: build/native/platform-audit/java-android/arm64-16k.

## Native And Package Checks

| Input | Native files | Result |
| --- | ---: | --- |
| Fresh complete ARM64 image, excluding debug-info ELF files | 71 | ARM64 ELF64, 16 KiB LOAD alignment/congruence, complete dependency closure |
| Retained complete x64 image, including unstaged CLI tools | 72 | x64 ELF64, 16 KiB LOAD alignment/congruence, complete dependency closure |
| Owning staged ARM64 package | 44 | Same checks and hashes matching the new image |
| Owning dual-ABI APK JDK packages | 44 ARM64 + 45 x64 | Same checks and hashes matching exact Gradle-transformed staged inputs |
| Additional APK Flutter framework files | 2 ARM64 + 1 x64 | Correct ABI, dependencies and 16 KiB LOAD alignment/congruence |

The audit uses NDK llvm-readobj JSON for ELF/program headers and NeededLibraries.
Do not combine --dynamic-table with this JSON mode: that option emits embedded
plain text. Dependencies resolve against the complete image/package and the
NDK's public API 28 system library stubs. Each ELF must have a nonempty LOAD set.

Staging used the existing native/openjdk/stage.ps1 with only android/arm64-v8a.
All 215 recorded x64 and HarmonyOS generated input hashes remained unchanged.
Previous ARM64 generated files were retained under previous-package before the
replacement. Manifest version is 1, with 43 link records. The data ZIP contains
276 entries, including modules, security configuration, release and spawn license.
Native launchers, helpers and SO files are not placed in the writable data ZIP.

ARM64 content ID:
android-arm64-v8a-3ec0741400e73a0d83bcc960614b3850ca0595235d2795a0e4fb3d8bc48c3cff

ARM64 data ZIP SHA-256:
a83113383a1b5aad2bebe58fbd8d474f565360f4e5f383f80950a090426c2eef

The APK audit's first direct comparison with unstripped staged libraries failed
on 36 ARM64 hashes. All those files already had valid LOAD/dependency checks.
Existing Gradle logs confirm NDK llvm-strip --strip-unneeded; the owning Gradle
keepDebugSymbols rule preserves only libqfli_*.so. Reproducing that exact step
makes every packaged JDK hash match. No packaging source was changed to obtain
this result. Both APK JDK JSON and ZIP assets match staged assets directly.

Ordinary owning debug APK:
D:/MyNewProjects/qfli_java/build/app/outputs/apk/debug/app-debug.apk

APK SHA-256: 323edb123a54ae46f12a2c7c4db7f8b65ce093bf451c8fce308e9f1863f7b101

APK size: 230170194 bytes. A serial JBR 21/1 GiB Gradle build of lib/main.dart
for android-arm64,android-x64 passed. ZIP check zipalign -c -P 16 4 passed.
Temporary memory settings were command parameters. Owning build settings and
preexisting startup/OHOS work were preserved.

## Ordinary Android Editor

Reused task-owned Qfli_Native_Audit_20261002 as emulator-5562, API 37, 16384-byte
pages. Original emulator-5560 and its apps/projects were preserved. Installed
the ordinary dual-ABI APK; package manager selected primaryCpuAbi=x86_64.
The installed data marker is the unchanged android-x86_64 content ID.

The first fresh application launch stayed on its Flutter startup screen when
inspected several minutes later. JDK data had already installed; the small main
log buffer no longer retained the initial diagnostics. Enlarged only this test
emulator's main log buffer and restarted the app. Java/javac probes ran and the
ordinary home screen opened. Created AndroidDualAbiJava with the Java template,
opened src/Main.java and clicked the ordinary Run action. It printed
Hello, QFLIStudio+! and finished with exit code 0. Actual source uses
System.out.println. This is an ordinary x64 runtime pass for the new dual-ABI APK.

To check the unexplained initial startup observation, preserved the generated
JDK cache by renaming files/usr to files/usr-cold-audit-backup in this task-only
app, then launched it again. Fresh JDK installation reached home and retained
AndroidDualAbiJava. Opened the project through the ordinary UI and ran it again;
the same greeting and exit 0 passed. The initial startup observation was not
reproduced and is not claimed as a fixed source defect. No other application or
project data was removed. The task-owned emulator was stopped after capture;
the original emulator remained connected.

Evidence includes owning-editor-run.png/XML, cold-start-ui.xml,
cold-editor-run.png/XML and app logs. The initial x64 eight-case smoke evidence
from ea7b4df remains separate; those cases were not unnecessarily repeated for
this generated ARM64 fix.

## Source Delivery And Limits

Applied checked java-arm64-evidence.patch to the owning runtime README, Android
README and existing ignored local mobile-jdk spec. Only the two READMEs are
tracked changes; generated inputs and the local ignored spec are not force-added.
Their commit is pending the project-required plan confirmation. No new Java,
Kotlin or Flutter product source was needed. Both evidence scripts parse cleanly;
the real old package is the negative case and actual images/packages/APK are the
positive cases. Owning and root narrow diff checks pass.

No native ARM Android device or API 28 emulator is available. Their execution was
not run or inferred from x64/translation. Apple builds/execution are unavailable;
native iOS JVM hosting remains an unresolved whole-goal requirement. These checks
close the stale ARM64 package defect, not the complete cross-product goal.

## Reproduce

Use research/java-android-elf-audit.ps1 with -Mode image for the export and with
-Mode package -ExpectedRoot IMAGE for the staged native directory. Use
research/java-android-apk-audit.ps1 with the ordinary APK, owning native/build/android
PackageRoot and an isolated EvidenceDirectory. Retained JSON reports include every
native LOAD, SHA-256, dependency, expected hash and APK data archive hash.
