# Read-only clue: core terminal pane hangs on the first stdout-error case

Date: 2026-10-26. Author: Pi. Mode: read-only on a sibling repository.

Symptom under investigation: the core terminal test file passes 36 cases in a
row, then the first stdout-error case stops making progress with no failure
output.

Files inspected, never modified:

```text
../qfli_studio_core/lib/editor/terminal_pane.dart    82279 bytes, 2266 lines
../qfli_studio_core/test/terminal_pane_test.dart     60445 bytes, 1709 lines
```

No test was run. No SDK, runner, device or `flutter test` process was started. No
channel message was sent. The sibling core repository was read only. Nothing
below is a confirmed diagnosis; each item is evidence plus the experiment that
would settle it.

## 0 Correction: no literal `fakeAsync`, but `testWidgets` supplies one

An earlier version of this note claimed that no fake-clock mechanism applied
because `fakeAsync` never appears in the file. That claim was wrong and is
withdrawn. The package `fakeAsync` and any literal `FakeAsync()` call do not
appear in `terminal_pane_test.dart` (0 occurrences), but `testWidgets` installs a
fake zone implicitly, so every case in this file runs on a fake clock.

Evidence from the installed framework,
`D:/ProgramFiles/flutter_ohos/packages/flutter_test/lib/src/binding.dart`
(109208 bytes, 2955 lines):

- `1405-1406`: "Call the testBody inside a [FakeAsync] scope on which [pump] can
  advance time." That is the `runTest` contract, and `testWidgets` calls it.
- `1918`: `FakeAsync? _currentFakeAsync; // set in runTest; cleared in postTest`
- `2182-2191`: `runTest` builds `final fakeAsync = FakeAsync();`, assigns
  `_currentFakeAsync = fakeAsync;`, then runs the whole body inside
  `fakeAsync.run((localFakeAsync) { ... testBodyResult = _runTest(...); });`.
- `1942`: `bool get inTest => _currentFakeAsync != null;`
- `1948-1963`: `AutomatedTestWidgetsFlutterBinding.pump` calls
  `_currentFakeAsync!.elapse(duration)` and then `flushMicrotasks()`. Frames and
  microtasks advance only through the fake clock.
- `2247-2252`: `postTest` clears `_currentFakeAsync` and `_clock`.
- `1968-2030`: `runAsync` forks a `realAsyncZone` whose `scheduleMicrotask`,
  `createTimer` and `createPeriodicTimer` delegate to `_rootDelegate`, which is
  how real asynchronous work escapes the fake clock.

So the boundary that matters for a hang is:

- `tester.pump()` runs inside the fake zone. Only work the fake clock advances or
  flushes will progress. A future whose completion needs a real timer or a real
  microtask chain will not move under `pump`.
- `tester.runAsync()` escapes to the real event loop for its callback.
- `addTearDown` inside `_TerminalFixture.mount` (`test:1672-1677`) unmounts the
  pane and then waits 20 ms of real time through `runAsync`.

Corrected statement: the test file does not import or call `fakeAsync`
explicitly, but `testWidgets` provides the fake zone, so the "fake clock never
advances" and "pump / runAsync boundary" hypotheses do apply to this file.

## 1 Which case is meant

The 36th `testWidgets` declaration is `test:1180`:

```dart
'$failingStream failure keeps ownership until exit and cleanup',
```

It is parameterized by `failingStream`, and `test:1212` sends the error:

```dart
(failingStream == 'stdout' ? stdout : stderr).addError(failure);
```

So the case that hangs is the `failingStream == 'stdout'` parameter of the 36th
declaration, matching "36 pass, then the first stdout-error case". The next
stdout-error case, `test:1254`, is a separate declaration and is not reached.

## 2 The pane stops listening to the errored stream

`terminal_pane.dart:1232-1258` is the only place a caller stream is consumed:

```dart
return stream
    .listen((line) { ... })
    .asFuture<void>()
    .then<void>(
      (_) {},
      onError: (Object error, StackTrace stackTrace) {
        fail(error, stackTrace);
      },
    );
```

`StreamSubscription.asFuture()` does not merely observe errors. On an error it
completes its future with that error, and it **cancels the subscription**,
clearing the internal `onDone` and `onError` handlers first. Consequences that
matter here:

1. After the error, the pane is no longer subscribed to the errored stream. It
   will never see that stream's `done` event.
2. The only thing the pane awaits per stream is the `asFuture` future, which has
   already completed with the error and been converted to a value by `.then`.

So for the errored stream the pane's bookkeeping is complete, while the source
`StreamController` is still open and unlistened. That is the exact state in
which `StreamController.close()` no longer has a listener to deliver `done` to.

Note the asymmetry this creates between the two parameters of the same test: in
the `stderr` parameter the healthy, still-subscribed stream is stdout, and in the
`stdout` parameter the healthy one is stderr. Whatever the close behaviour of an
errored-then-cancelled controller is, it is exercised only by one of the two.

## 3 Why "Future.wait registered before pump" cannot fix a hang

Global note 759 says the newest fixture already registers the wait before the
pump. In `test:1218-1221` the order is indeed:

```dart
final streamsClosed = Future.wait([stdout.close(), stderr.close()]);
await tester.pump();
await streamsClosed;
```

Registering early fixes a lost-event problem: if you close first and only then
attach the listener, you can miss the event. It does not fix a `done` future that
has no route to completion. `Future.wait` waits for every member, so if either
`close()` future cannot complete, the `await` at `test:1221` hangs no matter when
the `wait` was created. In other words: ordering can fix delivery, ordering
cannot manufacture completion.

This is the single most important structural point for the investigation. If the
hang is at `test:1221`, the trigger is a `close()` whose `done` never resolves,
and moving the `Future.wait` earlier or later will not change that.

## 4 The strongest candidate: a would-be failure converted into a teardown hang

This is the mechanism I would check first, because it explains a hang with no
failure message.

`fail()` at `terminal_pane.dart:1184-1215` requests cancellation but does not
await it:

```dart
unawaited(
  session.interrupt().then<void>(
    (_) => _notifyRunningWorkChanged(),
    onError: (Object cleanupError, StackTrace cleanupStack) { ... },
  ),
);
```

`session.interrupt()` at `terminal_pane.dart:2125-2149` **caches** the in-flight
future and hands the same instance to every later caller:

```dart
Future<void> interrupt() {
  final existing = _pendingCancellation;
  if (existing != null) return existing;
  ...
  pending = Future<void>.sync(cancel).then<void>((_) { ... }).whenComplete(() { ... });
  return _pendingCancellation = pending;
}
```

`_pendingCancellation` is cleared only inside `whenComplete`, which runs only
when `cancel` itself completes.

Now the test's cancel callback, `test:1193-1196`:

```dart
cancel: () async {
  cancellations++;
  await cleanup.future;
},
```

`cleanup` is a `Completer<void>` that the test completes at `test:1227`, after
the awaited `result` at `test:1223`. So between the first `addError` and
`test:1227`, `interrupt()` is an unfinished future that waits on a
test-controlled completer.

The pairing that makes this dangerous is the teardown installed by
`_TerminalFixture.mount` (`test:1671-1676`):

```dart
addTearDown(() async {
  await tester.pumpWidget(const SizedBox.shrink());
  await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
});
```

Unmounting the pane runs `dispose()`. That cleanup list (`terminal_pane.dart:2183`)
includes `interrupt()`:

```dart
cleanup.add(interrupt());
```

and then waits for everything (`terminal_pane.dart:2248`):

```dart
pending = Future.wait<void>(cleanup, eagerError: false).then<void>(...);
return _disposeFuture = pending;
```

With `eagerError: false`, `Future.wait` waits for **all** members.
`interrupt()` here returns the cached `_pendingCancellation`, which still awaits
`cleanup.future`.

Resulting loop: an assertion that fails before `test:1227` aborts the test body,
the test framework runs `addTearDown`, the pane disposes, dispose awaits
`interrupt()`, `interrupt()` awaits the test's `cleanup` completer, and that
completer is only completed on a line the aborted body never reached. The runner
shows a hang rather than the underlying assertion failure.

This matches the reported shape exactly: a long run of passes, then a case that
stops producing output instead of failing. The diagnostic experiment is to
temporarily wrap the body so `cleanup.complete()` runs in a `finally`, or to give
the cancel callback a bounded wait. If the case then fails fast with a real
assertion message, the hang is this teardown loop rather than a stream problem.

### Why this is asymmetric even though it looks symmetric

Both parameters issue exactly one `interrupt()` (guarded by `cancellationRequested`
at `terminal_pane.dart:1186-1195`), so both cache a pending interrupt. What
differs is which assertion can fire first. The `stdout` parameter is the one that
adds its follow-up line to `stderr` and then asserts on stream-derived state
(`test:1213-1216`); a mismatch there aborts before `cleanup.complete()`.

## 5 Second candidate: the errored controller's `close()` never completes

If the hang is at `test:1221` and the body does reach `cleanup.complete()`, then
the blocking member is a `close()` future. The relevant fact from §2 is that for
the errored stream the pane cancelled its subscription via `asFuture`, so the
controller has no listener at close time, while for the healthy stream `done` is
delivered normally. Only one of the two members can be in the "closed with no
listener" state, which is why one parameter could pass and the other stall.

The exact Dart core behaviour here (whether `_StreamController.close()` completes
`done` immediately once the subscription was cancelled through `asFuture`) is not
something I can settle by reading this repository, and I will not assert it. The
experiment that settles it is a three-line unit test on a bare
`StreamController`: listen, `asFuture()`, `addError`, then `await close()`.

## 6 Third candidate: `runAsync` crossing back into the fake zone

`test:1223` awaits through `tester.runAsync`:

```dart
expect(await tester.runAsync(() async => await result), same(failure));
```

`runAsync` runs its callback on the real event loop while the fake clock is
paused. If `result` (`terminal_pane.dart:1269`) is waiting on anything that needs
a frame, `runAsync` will not return:

```dart
await Future.wait<void>([outDone, errDone, observedExit]);
```

`errDone`/`outDone` are `asFuture` futures (§2) and `observedExit` is the
test's `exit.future`, so on paper all three settle without a frame. But note
`_scrollToBottom` (`terminal_pane.dart:1298` and its definition at 2075-2085)
schedules `WidgetsBinding.instance.addPostFrameCallback`, and
`terminal_pane.dart:1814` arms a real `Timer` for double-tap. Anything that ends
up awaited while only frame- or timer-driven work can complete will stall inside
`runAsync`. Line 174 of the pane carries an explicit comment about creating a
pending timer under the test binding, which shows this class of problem is known
in this file.

## 7 What is not a problem, and worth recording

- `fail()` uses `unawaited`, so the returned `attachOutput` future is **not**
  blocked by cancellation. The pane's design comment at 1161-1163 states this
  intent, and the code matches it.
- `fail()` is idempotent in effect: `cancellationRequested` plus `firstError ??=`
  mean only one interrupt is issued and only the first error is kept.
- `Future.wait(cleanup, eagerError: false)` in `dispose` is deliberate: a cleanup
  pass should attempt everything. The cost is that one stuck member blocks the
  whole dispose, which is what makes §4 lethal rather than merely slow.
- `const Stream.empty()` used by neighbouring cases cannot exercise any of this,
  because it completes immediately and is never errored.

## 8 Ranking and next steps

| # | Hypothesis | Where it would block | Confidence |
| --- | --- | --- | --- |
| 1 | Cached `interrupt()` awaiting the test's `cleanup` completer, reached through `addTearDown` → `dispose` | teardown after an earlier assertion failure | highest, explains "hang with no failure" |
| 2 | Errored controller's `close()` future never completes | `test:1221` | medium, needs the 3-line probe |
| 3 | `runAsync` waiting on frame- or timer-driven work | `test:1223` | lower, all members should settle without a frame |

Cheapest discriminating experiments, none of which need the SDK suite:

1. Make the cancel callback bounded, or complete `cleanup` in a `finally`. If the
   case turns into a normal assertion failure, hypothesis 1 is confirmed.
2. Bare-controller probe for `asFuture` + `addError` + `close()`. If `close()`
   never completes, hypothesis 2 is confirmed and the test's own
   `Future.wait([...close()])` is the bug, not the pane.
3. Add a `timeout` to `await streamsClosed` and to the `runAsync` call. Whichever
   reports `TimeoutException` names the blocking await.

## Non-claims

I did not reproduce the hang, did not run any test, and did not modify either
file or anything else in the sibling repository. The three mechanisms above are
derived from reading this exact revision of the two files; the line numbers are
valid for the sizes recorded at the top. Hypothesis 2 in particular depends on
Dart core `StreamController` completion rules that live outside this repository,
so it is stated as a question with a probe, not as a conclusion.

## 9 Revision note: the test file moved three times during this read

`terminal_pane_test.dart` changed under this review more than once: 60445 bytes
and 48 declarations, then 62315 bytes (1773 lines, 44 declarations, `debugPrint`
checkpoints added), then 60310 bytes (1776 lines, checkpoints removed, `.done`
based close). `terminal_pane.dart` never changed (82279 bytes). Line numbers here
are a snapshot; the code shapes are the durable part.

Current anchors, verified by search in the 60310-byte revision:

| Marker | Line |
| --- | ---: |
| `testWidgets(` for the 36th case | 1180 |
| case name string | 1181 |
| `stdoutDone` / `stderrDone` bound from `StreamController.done` | 1184, 1186 |
| `addError(failure)` | 1220 |
| `final streamsClosed = Future.wait([stdoutDone, stderrDone]);` | 1231 |
| `unawaited(stdout.close()); unawaited(stderr.close());` | 1232-1233 |
| `await tester.pump();` then `await streamsClosed;` | 1234-1235 |
| `cleanup.complete();` | 1240 |
| `addTearDown` in `mount` | 1672 |
| next stdout-error case | 1264 |

The current revision no longer awaits `result` through `runAsync`; it captures the
value and asserts it:

```dart
Object? resultValue;
unawaited(result.then<void>((value) { resultValue = value; }));
...
expect(resultValue, same(failure));
```

Effects on the hypotheses:

- Hypothesis 3 (`runAsync` crossing into the fake zone) does not bind the 36th
  case in this revision, because nothing there awaits `result` through `runAsync`.
  The `pump` / fake-clock boundary described in §0 still governs every await in
  the body, so a future that only a real timer or a real microtask chain can
  complete will not progress under `pump`.
- Hypothesis 1 still stands: if an assertion fails before `cleanup.complete()`,
  teardown disposes the pane, dispose awaits the cached `interrupt()`, and that
  awaits the never-completed `cleanup` completer.
- This revision closes through pre-captured `StreamController.done` futures plus
  `unawaited(close())`. That is an attempt to defuse hypothesis 2, and whether it
  succeeds is exactly the empirical question I cannot answer read-only.

Re-read the file before acting on any line number in this note.
