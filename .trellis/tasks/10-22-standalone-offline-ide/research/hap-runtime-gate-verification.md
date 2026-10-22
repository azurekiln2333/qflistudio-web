# HAP runtime gate and signing availability

## Later root verification

The root rebuilt explicitly for `ohos-arm64,ohos-x64`. The new 80,682,576-byte
production HAP (`7b16610e9efe667eb3c838a204fab1c53441f8d17e4e997c0a13325a455cd346`)
passes the complete archive gate, including both Flutter/runtime pairs. Ordinary
unsigned installation and normal Home launch succeeded on the actual x86_64
emulator. `ohos-481-initial.*` preserves its first full ArkWeb run: 443/481,
38 semantic failures, with cleanup corrected separately. These observations
supersede the older single-ABI rejection and pending emulator route below;
physical signing and a clean final native catalog run remain open.

## Earlier independent inspection

Snapshot inspected on 2026-10-22. This is archive/configuration evidence; no build,
signing, installation or device operation was performed during this inspection.

## Production runtime gate

`audit_hap.py` now requires both `libapp.so` and `libflutter.so` under each of
`libs/arm64-v8a/` and `libs/x86_64/`. Every required entry must contain a complete
ELF64 little-endian header with `ET_DYN` and the architecture's machine number
(183 and 62 respectively). Missing entries fail the audit with their exact paths.
The CLI writes the failure report and exits 1, so an older successful report is
not left behind when this gate rejects the current artifact.

The existing exact source/staging catalog checks, production/test source
separation, dual-ABI syntax-library exports, zero entry points, 16 KiB LOAD
alignment and QuickJS license checks remain in force.

The isolated `--self-test` passed one complete-pair ZIP fixture and rejected
eleven negative fixtures: each of the four missing entries, each entry with the
wrong machine, a truncated header, a non-ELF placeholder and `ET_EXEC`. These are
header-only fixtures for the gate, not real libraries or runtime evidence.

Current production archive:

- Path: `ohos/entry/build/default/outputs/default/entry-default-unsigned.hap`
- Bytes: 48,492,468
- SHA-256: `356370bf44d7680baf550e0cc6f7cf08925293df9dd0d2e3763dae0d02351176`
- Result: **failed**, missing `libs/x86_64/libapp.so` and
  `libs/x86_64/libflutter.so`.
- Exact catalogs and the syntax bridge for both ABIs pass their existing checks.

Current test archive:

- Path: `ohos/entry/build/default/outputs/ohosTest/entry-ohosTest-unsigned.hap`
- Bytes: 165,686,366
- SHA-256: `52629b271a34c598141a075422a246d77f6040a08adcebd59beb909c586afb8d`
- Result: passed the test archive's catalog, identity and source-separation checks.

Full machine-readable results are in `hap-481-inspection.json`. The final build
must explicitly request `--target-platform ohos-arm64,ohos-x64`; this inspection
did not run that build.

```powershell
python .trellis/tasks/10-22-standalone-offline-ide/research/audit_hap.py --self-test
python .trellis/tasks/10-22-standalone-offline-ide/research/audit_hap.py --production ohos/entry/build/default/outputs/default/entry-default-unsigned.hap --test ohos/entry/build/default/outputs/ohosTest/entry-ohosTest-unsigned.hap --readelf D:/ProgramFiles/Huawei/OpenHarmony/Sdk/23/native/llvm/bin/llvm-readelf.exe --report .trellis/tasks/10-22-standalone-offline-ide/research/hap-481-inspection.json
```

Python bytecode compilation and the scoped whitespace check also passed.

## Web signing material

The active `ohos/build-profile.json5` contains zero signing configurations; its
default product has no signing-config reference. Neither active build profile
configures certificate, provisioning-profile or keystore paths. The ignored
legacy local build-profile backup contains one old signing configuration, but
all three referenced material files are absent. The IDE project cache supplies
no alternative signing material reference.

All six global `.ohos/config` provisioning profiles were checked with the
official SDK `verify-profile` command in temporary directories. All six verified
cryptographically, but none binds `com.azurekiln.qfli.webforge`. No project-local
signing-material files or additional global `.ohos` signing locations were found.

The historical `build/ohos/hap/entry-default-signed.hap` passes official
`verify-app` and its exported profile passes `verify-profile`. That profile is
debug, binds exactly `com.azurekiln.qfli.webforge`, and is valid from
2026-09-22 08:44:36 UTC until 2027-09-22 08:44:36 UTC. Its profile SHA-256 is
`e3f2fbdaef634ce62bd340d9a2e7df5cb1e60b06aa0505b7940886ec9dd5bca1`.
Its non-CA application certificate has no certificate or public-key match among
the six current local certificate chains; only its root and intermediate match.
The historical profile's corresponding configured keystore path is absent.
Thus the inspected existing material does not supply a reusable Web signing key.
The historical HAP is stale-source evidence and cannot replace a fresh HAP.

Only availability, public bundle binding, public certificate validity and hashes
are recorded here. No credential, alias value, private identifier, private key or
full provisioning-profile content was persisted.

## Official emulator route

Huawei's current [HarmonyOS development introduction](https://developer.huawei.com/consumer/cn/develop-novice-guide/)
states that emulator/preview debugging does not require signing configuration;
physical devices require signed HAPs. The concrete supported route is DevEco
Studio Run with a local emulator selected and signing configuration left empty.
Its acceptance still needs actual current-emulator execution evidence.

The installed Hvigor 26 `SignUtil.getSigningConfig` and `executeSign` confirm
that an unconfigured CLI HAP build skips signing. The generic default-debug
keystore helper and SDK OpenHarmony test key do not prove a valid Web-bound
physical-HarmonyOS signature. The current catalog driver's strict signed-profile
preflight does not yet express the official unsigned-emulator route. Any explicit
emulator path needs separate design and verification; no signature requirement,
bundle identity or device setting was changed in this inspection.
