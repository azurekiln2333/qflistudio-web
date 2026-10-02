# Oracle MySQL Windows And Linux Backend Delivery

## Delivered Scope

Owning repository: `D:/MyNewProjects/qfli_sql`.
Commit: `0e02cb2` (`feat(mysql): add native Windows and Linux server lifecycle`).

This adds the real Oracle C client JSON ABI, worker-isolate FFI, local server
initialization/ownership/readiness/stop, private credentials/transport and full
desktop runtime packaging. It reuses the existing Oracle prepared/script
implementation and preserves all old OHOS C++ symbols. Cloud preferences,
workspace/runner changes and startup/OHOS work were preserved.

The product's ordinary engine preference still selects SQLite/cloud. Desktop
`NativeMySqlDatabase` calls now have a real backend; adding a local-MySQL choice
and connecting it consistently to the workbench/editor is subsequent work.

## Upstream Inputs

- Windows: official Oracle MySQL 8.4.6 x64 ZIP, 260,772,595 bytes.
- URL: `https://cdn.mysql.com/archives/mysql-8.4/mysql-8.4.6-winx64.zip`.
- SHA256: `b6c152f9f3aaa7294eb47db698e47974d37b261bf3cab4f90dc1243bb5ecd204`.
- Linux: installed Oracle MySQL 8.0.46 from Ubuntu, C client 21.2.46. MariaDB is
  explicitly rejected; the real server version is pinned in initialization data.
- RapidJSON: retained headers from the previously verified Oracle 8.4.6 source.
- Compiler: GCC 13 on Linux and MinGW GCC 13 cross-build for Windows. The actual
  Windows Oracle DLL/service and Linux Oracle executable were then run.

Windows downloads through Schannel failed; the official ZIP was retrieved using
WSL curl and verified before extraction. The final stage-windows.ps1 also passed
its hash and complete-distribution checks. Linux staging retained real server,
resources/plugins and resolved native dependencies; host libc remains required.

## Runtime Contract

Successful upstream initialization precedes publication of the datadir/marker.
Exact version and random local credential are retained; mismatch or orphan data
returns unavailable instead of replacing user data. Windows uses private named
pipes and RSA exchange required by caching_sha2_password; Linux uses 700 socket
parents and Unix sockets. TCP, mysqlx, LOCAL INFILE and filesystem import/export
are disabled. Queries and shutdown are serialized.

Windows assigns mysqld to a lifetime Job Object at process creation and monitors
the app handle. Linux validates its parent and uses PDEATHSIG. Graceful shutdown
uses Oracle's C API with bounded owned-process termination. Data persists for
InnoDB recovery, including abrupt application death.

## Verification

| Check | Result |
| --- | --- |
| Staged Windows complete installed bundle, actual Oracle | 11/11 |
| Staged Linux complete installed bundle, actual Oracle | 11/11 |
| Owning Windows rebuild/complete install and real lifecycle | 11/11 |
| Owning Linux rebuild/complete install and real lifecycle | 11/11 |
| Staged Flutter suite, including actual Oracle typed adapter | 51/51 |
| Owning Flutter suite, including actual Oracle typed adapter | 51/51, concurrency 1 |
| Staged/owning changed-source static analysis | No issues |
| Narrow delivery patch and whitespace review | Passed |

Lifecycle assertions cover actual upstream initialization, private transport,
exclusive ownership, exact BIGINT/DECIMAL, UTF-8, NULL/binary metadata, prepared
parameter and SQL errors, matched unchanged updates, scripts/rollback/partial
failure, display caps and complete result draining, credentials/no TCP fallback,
persistence/restart, version rejection, app death and subsequent InnoDB recovery.
Application adapter tests verify typed results and ordered script failures.

A simultaneous owning Flutter run exhausted Windows virtual memory: Flutter
reported `Out of memory` and a test process closed before loading. A standalone
native check still passed. Sequential owning test execution then passed 51/51.
The earlier low-memory child-fixture failure now reports its exit/stderr and
terminates a timed-out owned child; no missing-child result is treated as a pass.

Generated evidence is under `build/native/platform-audit/mysql-desktop`, including
`owning-lifecycle.log`, `owning-linux-lifecycle.log`, `owning-tests-serial.log`,
staged logs, SDK/source snapshots, installed bundles and delivery patch. The
owning lifecycle fixtures were `D:/AppData/Local/Temp/qfli-mysql-test-3484685c`
and `/tmp/qfli-mysql-test-YKCUQH`. They retain diagnostics and data, not running
servers. Credentials are in private fixture storage and are not printed.

## Remaining Requirements

- Android actual Oracle server build/package and application lifecycle.
- Local engine selection shared by the SQL workbench and editor Run.
- macOS bundle/signing integration; portable runtime/launcher source alone is
  not a packaged application delivery.
- Native iOS Oracle hosting; subprocess desktop logic is not an iOS solution.
- Full Windows Flutter GUI requires unavailable MSVC tools. Full Linux GUI and
  Apple build/execution were not run and have no pass claim.

The complete cross-product native-runtime goal remains active.
