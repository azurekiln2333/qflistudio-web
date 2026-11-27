# Publish mobile and Apple native builds

## Goal

Focus native artifact delivery on Android, OHOS, iOS and macOS; keep Linux as regression tests, add and verify Apple builds on GitHub.

## Requirements

- Publish native components for Android, OHOS, iOS and macOS.
- Use installed compiler toolchains. Do not build GCC, Clang, NDK or Xcode.
- Stop publishing Linux libraries; retain Linux native regression tests.
- Continue using the existing Windows Nginx prebuilt binary.
- Run Apple builds on GitHub and report actual results and download links.
- Align the project GPL v3 declaration with `D:/MyNewProjects/qflistudio`.
- Show Conventional Commit messages, commit and push to the GitHub CI branch.

## Acceptance Criteria

- [x] Android/OHOS publishing still passes.
- [x] iOS device ARM64 and simulator ARM64/x86_64 static libraries compile.
- [x] macOS ARM64/x86_64 Nginx and syntax libraries compile and pass host smoke.
- [ ] Mach-O architectures/platforms and artifact checksums are verified.
- [x] Linux publishes logs only, with its native regression tests retained.
- [x] Documentation explains toolchain versus project library and download scope.
- [x] Three README license declarations match the main project's scope.
- [x] Root GPL v3 text remains byte-identical to the main project's LICENSE.
- [x] Requested changes are committed and pushed to GitHub.

## Notes

GitHub Actions [run 45827112830](https://github.com/azurekiln2333/qflistudio-web/actions/runs/45827112830) passed all five native Apple jobs on `3b947c83c4f2ab15f74fdbef3cca1cdb3ea6ffb2` on November 26, 2026.
The jobs checked Mach-O targets and generated checksums. Independent verification of the uploaded archive bytes remains open.

The user explicitly authorized commits and push on 2026-11-17. Read the sibling
main project only as a license reference; preserve separately licensed vendor
code and CC BY 4.0 curriculum. Root LICENSE already matches the main project.
