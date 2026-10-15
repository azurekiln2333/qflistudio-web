# Physical-device verification

## Android

OPD2413, ARM64, direct endpoint `192.168.68.236:35991`.

- Native Nginx integration: 1/1 passes. Actual HTML/CSS, 404, proxy, WebSocket,
  SSE live reload, diagnostics/access logs, port conflict, stop, restart and
  auto engine selection. See `android-native-device-final.log`.
- Content integration: 1/1 passes. Tutorials/examples × editor/new project,
  edited source, custom filename, existing project entry retention, and an
  advanced example per subject with unchanged `.html` default filename, active
  editor source, persisted file and actual Nginx HTML response. See
  `android-content-device-final.log`.
- Normal release app installed and started; the five Home/Tools/Tutorials/
  Examples/Profile pages were visually reviewed. The shared NavigationRail
  contains exactly five entries, tools appear together, and Profile has no
  account login. `ui-five-pages-redacted.jpg` combines the captures; its dark
  upper-right rectangle obscures a picture-in-picture overlay from another app.
  Original captures remain local under `.trellis/.runtime/ui-review/`.

Flutter also logged a discovery failure for a separate mDNS serial containing
spaces. The explicit direct-endpoint test connections succeeded. Installation
required the device's normal Oplus confirmation screen. No security setting,
other app/data or shared ADB service was changed.

Device ownership was released to SQL `wC:p5` in the global coordination channel
(sequence44). These tests preceded the final self-contained lesson media fixes;
all 301 final documents are separately verified in Chromium, and final archive
auditing compares the packaged assets byte-for-byte with the frozen source.

## OHOS

HarmonyOS7 / API26 device `192.168.68.207:46551`. Installing the newly built
unsigned WebForge HAP was actually attempted and rejected with code9568320,
`no signature file`. Local signing profiles bind other products and cannot sign
`com.azurekiln.qfli.webforge`. A matching profile/certificate was requested from
the user; no matching signing material has been received.

The signed HAP under `build/ohos/hap/` is an older 2026-10-12 artifact and is not
the current release. The historical embedded-Nginx device pass belongs to the
10-11 task; it does not establish current-package device success.

Current OHOS installation, runtime and UI verification remain blocked on the
WebForge signature. No Android ARMv7, new Linux-native or Apple platform run is
claimed.
