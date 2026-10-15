# Android native integration result

2026-10-15, OPD2413 ARM64, direct ADB endpoint192.168.68.236:35991.

`flutter test --no-pub -d 192.168.68.236:35991 integration_test/nginx_runtime_test.dart --reporter expanded`: **1/1 passed**.

```text
[NGINX_SMOKE] PASS HTML CSS 404 proxy WebSocket SSE diagnostics log port-conflict stop restart auto
00:01 +1: All tests passed!
```

The test uses the actual packaged libnginx_exec.so. Startup/version, real loopback transport and native lifecycle are exercised; this is not mock channel evidence. Android recursive watch and SSE both run successfully.

First actual run exposed a duplicate watcher assertion in the capability probe. The probe now watches its own directory while WebDevServer continues to watch the real root. No AssertionError is swallowed and no Android skip was added.

Install confirmation was completed through the normal Oplus installer. Earlier install-wait and failed-probe logs remain in the parent task runtime evidence. OHOS signing and Apple device gates remain separate.
