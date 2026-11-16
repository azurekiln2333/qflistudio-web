# Design boundary

The initial native workflow omitted Apple and published Linux libraries that the
user does not need. Reuse existing Apple builders/bundle wrappers, keeping the
existing source hashes and embedded forbidden-symbol checks.

- native-build.yml: keep Linux regression builds/tests, remove desktop build and
  native package upload; preserve Android jobs.
- native-apple-build.yml: native macOS hosts and iOS cross targets with explicit
  architecture/platform checks, smoke tests and artifact upload.
- package_native_artifacts.py: Android/OHOS/macOS/iOS package membership and unique
  SDK/architecture labels. Never combine device and simulator archives.
- docs/native-builds.md and native-runtime spec: align delivery targets and evidence.
- README.md, README.en.md and README.zh-Hant.md: align the GPL v3 declaration with
  the main project while preserving existing vendor and curriculum licenses.

No Flutter UI, app installer, signing identity, shared core, or cache cleanup change.
Source compatibility fixes may be made in an owning Apple builder if actual CI
exposes a defect. Do not weaken native validation to obtain a green run.
