# Execution

1. Review package/native specs and existing Apple builders.
2. Remove Linux delivery and add Apple jobs in parallel with packaging/doc changes.
3. Run actionlint, shell/Python syntax and Chinese prose lint.
4. Push the existing dedicated CI branch to the explicit GitHub URL.
5. Observe all affected workflows; fix native build defects and rerun.
6. Verify hosted job outcomes and downloadable archive contents/checksums.
7. Record platform-specific evidence and preserve app/device limitations.

No local platform builds: hosted runners are the requested validation environment.
