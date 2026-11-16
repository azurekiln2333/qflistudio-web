# Native builds on GitHub Actions

The user requests a current project/storage assessment, an actual GitHub native
build trial, and a clear artifact inventory and download location.

## Acceptance criteria

- Build the current native source on GitHub-hosted runners.
- Publish final native binaries, public headers, licenses and SHA-256 checksums.
- Run existing native behavior tests where the host can execute the output.
- Record cross-compilation separately from device/application acceptance.
- Report the exact run URL, job outcomes and artifacts.
- Explain which local directories are generated and how cloud builds affect space.
- Preserve local caches until a cleanup is explicitly requested.
- Use only the GitHub remote for this trial.

Application installers and store signing are outside this native build request.
