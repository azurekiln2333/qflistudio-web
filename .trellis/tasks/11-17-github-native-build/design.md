# Design

The missing behavior is a hosted build and artifact delivery path. Native builders
already exist in scripts/ and use retained source under vendor/.

- Add .github/workflows/native-build.yml to orchestrate existing builders.
- Add scripts/package_native_artifacts.py to publish only explicit final files,
  provenance, licenses and portable relative checksums inside tar.gz archives.
- Add docs/native-builds.md and a README pointer for downloads and storage facts.
- Change an existing compiler wrapper only if hosted compilation demonstrates
  an environment-specific defect.

Start with Linux and Android. Extend supported native targets when the official
toolchain is available without secrets. OHOS SDK availability is under research.
Do not modify Flutter runtime behavior, sibling core, signing or local caches.

Use a dedicated CI branch from the current clean source. The local source is seven
commits ahead of the GitHub feature branch. Push the dedicated branch directly to
the GitHub URL. Do not invoke the multi-remote origin push configuration.

The workflow uses read-only repository permissions and a bounded job timeout.
Artifacts expire after 14 days. Archive permissions are preserved using tar.gz.
Compilation failures remain failures; do not substitute tracked prebuilt outputs.
