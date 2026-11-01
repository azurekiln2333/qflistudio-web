# C843 deadline timeout, fixture oracle diagnosis (PI3)

Source-only diagnosis. Nothing was executed. No command, SDK run, Job, grant or
channel message was issued. Readiness writes are paused; old 824 stays consumed
and 843 is this window. No product file and no test file was edited.

## 1. Observed failure

`web-app-c843-20261026/tests.stdout.log`, SHA256
`606C3C71000485279555D79CE33EF174369083A0F7542F783C000C4930E14B30`, 76511 bytes.

```
00:15 +148: ...owned_preview_resource_broker_test.dart: deadline aborts the owned request and releases in-flight accounting
00:16 +148 -1: ...owned_preview_resource_broker_test.dart: deadline aborts the owned request and releases in-flight accounting [E]
  TimeoutException after 0:00:01.000000: Future not completed
  dart:async  _startMicrotaskLoop
```

Total for the run: 320 PASS, 1 FAIL. The one failure is this test.

## 2. The actual failing await is unknown from the log

The stack holds one frame, `dart:async _startMicrotaskLoop`. It holds no test
file line and no await frame. `Future.timeout` reports its own stack, so the
trace cannot name which await expired.

The run's fixture version had three 1 s awaits in this test:

- `fetch(...).timeout(1s)` (pre-change line 477),
- `dispose().timeout(1s)` (pre-change line 486),
- `disconnected.future.timeout(1s)` (pre-change line 487).

So the log alone does not decide between them. Section 5 shows one of the three
cannot complete by construction, which is enough to fail this test regardless of
which await the log would have named.

## 3. Fixture drift and the applied cleanup

The test file changed between the 843 run and this diagnosis.

| Version | Bytes | SHA256 | Server `done` oracle |
| --- | --- | --- | --- |
| 843 run | 19454 | `6F41B71218CAF10D5DC4CEEA5D112475D562A9827E944FD7600DB4A091D8A913` | present at line 487 |
| current | 19030 | `FFB4E6EC0BBB532374BC5C25E3A04DC7EEE558FD13D8E83F0EDFC39151ACC3F8` | removed |

Root applied only a minimal fixture cleanup after the C851 release. It changed
three things and nothing else:

1. removed the `disconnected` completer,
2. removed the `request.response.done.then(...)` block,
3. removed the final `disconnected.future.timeout(...)`.

No broker edit was made. `owned_preview_resource_broker.dart` is still 11793
bytes with SHA256 `56FD917C…13D5`.

A byte check of the current test confirms the outcome: the token `disconnected`
is absent, and `response.done` does not appear at all.

The current fixture is UNRUN. C843 is a historical byte set. The cleanup is not
validated, and this note does not claim it is.

In the current file the `/slow` handler is only (lines 455 to 458):

```dart
request.response.write('still waiting');
await request.response.flush();
```

The `Completer<void> disconnected`, the `request.response.done.then(...)` and the
final `await disconnected.future.timeout(...)` are gone. The current 1 s awaits
are `fetch(...).timeout(1s)` at lines 465 to 466 and `dispose().timeout(1s)` at
line 475. The test name is still at line 449.

Broker under review: `lib/services/owned_preview_resource_broker.dart`, 11793
bytes, SHA256 `56FD917C3B4706E9DCF7B6328EC55F0E1DE5C76A6825190F98C90606E6AF13D5`.

## 4. SDK proof: `HttpResponse.done` is sink completion, not socket disconnect

Installed SDK root:
`D:/ProgramFiles/flutter_ohos/bin/cache/dart-sdk/lib`.

- `_http/http_impl.dart:1236` `class _HttpResponse extends _HttpOutboundMessage<HttpResponse> implements HttpResponse`.
- `_http/http_impl.dart:1082` `class _IOSinkImpl extends _StreamSinkImpl<List<int>> implements IOSink`.
- `_http/http_impl.dart:1025` `Future get done => _doneCompleter.future;`.
- `_http/http_impl.dart:1021` to `1023` the completer advances only through
  `_closeTarget()`, which is `_target.close().then(_completeDoneValue, onError: _completeDoneError);`.
- `_http/http_impl.dart:1005` to `1018` `close()` calls `_closeTarget()` when no
  controller exists, then returns `done`.
- `_HttpResponse` does not override `done`. A search for `get done` returns only
  lines 1025, 1531, 2031 and 3846; none is in the server response class.

So the server response `done` future completes when the response sink is closed,
or when closing it fails. It is not a socket disconnect promise.

## 5. SDK proof: a client disconnect never completes that future

- `_http/http_impl.dart:3363` the server connection does
  `_streamFuture = outgoing.done.then(...)`. The connection waits on the response
  sink, it does not feed it.
- `_http/http_impl.dart:3392` to `3398` the parser `onDone` and `onError` both
  call `destroy()`.
- `_http/http_impl.dart:3408` to `3414` `destroy()` calls `_socket.destroy()`,
  `_httpServer._connectionClosed(this)` and removes the connection. It never
  completes `outgoing.done`.

Therefore a client abort destroys the socket, and the response sink is left open
with `_doneCompleter` uncompleted. With `flush()` and no `close()`, the server
never calls `_closeTarget()`. `request.response.done` stays pending forever, and
`disconnected.future` can never complete. That oracle cannot be satisfied by any
correct broker behaviour.

## 6. SDK proof: the broker's `abort()` after `close()` is a no-op

- `_http/http.dart:1864` to `1872`: "Aborts the client connection. If the
  connection has not yet completed, the request is aborted and the `done` future
  (also returned by `close`) is completed with the provided `exception`. If the
  `done` future has already completed, aborting has no effect."
- `_http/http_impl.dart:1702` to `1709`:

```dart
void abort([Object? exception, StackTrace? stackTrace]) {
  _aborted = true;
  if (!_responseCompleter.isCompleted) {
    exception ??= HttpException("Request has been aborted");
    _responseCompleter.completeError(exception, stackTrace);
    _httpClientConnection.destroy();
  }
}
```

The connection is destroyed only when `_responseCompleter` is still open.
- `_http/http_impl.dart:1531` `done` is
  `Future.wait([_responseCompleter.future, super.done])`.
- `_http/http_impl.dart:1536` to `1542` `close()` returns `done`.

The broker does `final incoming = await request.close();`
(`owned_preview_resource_broker.dart:202`), so `_responseCompleter` is already
completed before any abort. The broker's `operation.request?.abort(...)` at
broker line 290 therefore cannot interrupt the body read. Only
`operation.client.close(force: true)` at broker line 291 does anything.

## 7. `_perform` is not shown to hang

- `_http/http_impl.dart:2895` to `2898` `close(force)` calls
  `_closeConnections(force)`.
- `_http/http_impl.dart:3156` to `3160` calls `_ConnectionTarget.close(force)`.
- `_http/http_impl.dart:2637` to `2643` force close calls `destroyFromExternal()`
  for every `_active` connection.
- `_http/http_impl.dart:2446` to `2450` `destroyFromExternal()` calls
  `_connectionClosedNoFurtherClosing(this)` and `_socket.destroy()`.

Destruction ends the body stream, so `await for (final chunk in incoming)` at
broker line 244 terminates, the `finally` at broker lines 274 to 281 runs, and
`operation.result` completes with the 504 built by `_cancel`. Nothing in this
path is shown to wait without a terminator. The timeout timer at broker line 164
is 200 ms and is cancelled in that same `finally`.

## 8. Conclusion

1. The server-side `done` oracle is invalid. `HttpResponse.done` is response sink
   completion, so with a fixture that flushes and never closes, the future never
   completes. The 843 failure is consistent with the test failing at that await.
2. A `fetch` or `_perform` hang is not supported by the source. The force close
   ends the read, so the 504 result completes.
3. The exact failing await remains unknown from the log. This diagnosis does not
   override that.
4. An independent review by `preview_broker` reached the same reading of the SDK
   source: the server `done` oracle is invalid. Two independent source readings
   agree. Neither of them names the expired await.

## 9. Recommendation, no edits made

Primary, minimal fixture fix: the three removals above. The fixture no longer
waits on a server-side `done`. That fix is applied but UNRUN, so it is source-only
and unvalidated.

If a disconnect observation is still wanted later, take it from a path the server
can actually see, for example a write or flush after the abort that is expected
to throw, and complete the observer from that error. Either way, assert
broker-side accounting (`activeRequests`, `retainedBytes`) for the release claim.

Secondary, diagnostics only: if a 1 s timeout recurs, separate the awaits so the
trace can name one. Use distinct durations, or a marker before each await,
because `Future.timeout` yields no test frame on its own.

## 10. Not proven

- No test, formatter, analysis or gate phase was run for this note.
- The failure was not reproduced.
- Which await expired in the 843 run is unknown.
- The current fixture is UNRUN, so its pass state is unknown. The minimal cleanup
  is source-only and unvalidated.
- The broker's `abort()` no-op is a source observation, not a task to change here.