# Embedded access-log regression: -t then serve (2026-10-12)

## Symptom

The embedded Linux engine served HTTP 200 but wrote nothing to `access.log`
when a configuration check (`nginx -t`) ran before the server in the same
process. `npm`-free reproduction: `server-only` and `server-then-server`
logged 63 bytes; `test-then-server` logged 0.

This is the exact sequence the editor uses: `NginxSession.validate()` runs the
embedded `-t` job, then `start()` runs the server job.

## Diagnosis path (evidence, not guesses)

1. Syscall trace (`strace -f -e trace=write ...`): the failing mode never issues
   `write()` to the access-log fd; the fd is opened to the correct path.
2. Handler instrumentation: `ngx_http_log_handler` **enters** with
   `off=0, logs->nelts=1`, correct `file->fd`, correct `file->name`, but
   returns before the write. The printed `ngx_time()` was `0`.
3. Root cause: `ngx_http_log_handler` skips a line when
   `ngx_time() == log[l].disk_full_time`; `disk_full_time` is zero-initialized
   and `ngx_time()` was 0.
4. Why `ngx_time()` was 0: `ngx_time_init()` sets
   `ngx_cached_time = &cached_time[0]` **without resetting the static slot
   cursor**. `ngx_time_update()` early-returns when
   `cached_time[slot].sec == sec` and, on that path, never repoints
   `ngx_cached_time`. A second cycle in the same second therefore left
   `ngx_cached_time` on the zeroed slot 0.

## Fix

`vendor/nginx/patches/embedded-time-cache.patch`: in the early-return branch of
`ngx_time_update()`, set `ngx_cached_time = tp;` so the cached-time pointer
always matches the live slot.

An earlier attempt that reset the time statics at run entry
(`qfli_nginx_reset_time`) did **not** fix it and broke all modes; it was
removed. The `embedded.patch` `ngx_times.c` section is removed and the patch is
regenerated cleanly.

## Regression

`native/nginx/embedded/access_log_probe.py` +
`native/nginx/embedded/run_access_log_regression.sh` assert the access log is
written across four sequences: `server-only`, `test-then-server`,
`server-then-server`, `test-then-restart` (`-t` then serve then stop then serve
again). Command:

```bash
QFLI_NGINX_BUILD_ROOT=<windows-visible-dir> \
  bash scripts/build_nginx_embedded.sh linux "$PWD/build/native/nginx/embedded-linux"
bash native/nginx/embedded/run_access_log_regression.sh \
  "$PWD/build/native/nginx/embedded-linux/libqfli_nginx.so"
```

Result: `ACCESS_LOG_PROBE PASS: server-only, test-then-server,
server-then-server, test-then-restart`.

## Files

- `vendor/nginx/patches/embedded.patch` — regenerated (reset hunks removed).
- `vendor/nginx/patches/embedded-time-cache.patch` — new, the fix.
- `vendor/nginx/HASHES.sha256` — embedded patch hashes updated.
- `scripts/build_nginx_embedded.sh` — applies the time-cache patch, hashes it.
- `native/nginx/embedded/access_log_probe.py` — regression with PASS/FAIL.
- `native/nginx/embedded/run_access_log_regression.sh` — runner.
- `native/nginx/embedded/qfli_nginx_internal.h` — reset prototype removed.
