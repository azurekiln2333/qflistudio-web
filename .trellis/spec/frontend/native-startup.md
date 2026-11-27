# Native Startup Contract

## 1. Scope / Trigger

Read before changing `lib/main.dart`, OHOS `EntryAbility`, `Index.ets`, or
startup resources. The reference is sibling `qfli_java` (JVMX): OHOS shows an
ArkUI loading layer until Flutter submits the initialized destination frame.

## 2. Signatures

- Channel: `qflistudio/platform`.
- Method: `startupProgress`, arguments: `{ "progress": double }`; success: null.
- Native event: `EVENT_STARTUP_PROGRESS(number)` on the ability event hub.
- View: `FlutterPage({ viewId, splashScreenView: this.startupSplash })`.
- Shared bootstrap: `AppBootstrap.run(..., onProgress: ValueChanged<double>?)`.

## 3. Contracts

`startWindowIcon` and `startWindowBackground` configure the system launch
window only. They do not replace the Flutter loading screen during bootstrap.
The native `StartupSplash` must be wired through `splashScreenView` too.

On OHOS, call `deferFirstFrame()` before `runApp`. Start bootstrap after the
first framework build, which still executes while engine submission is
deferred. Allow 160 ms for the ArkUI event subscription, report 0.05, then map
the three local store completions to `0.05 + progress * 0.95`. WebForge has no
JDK preparation stage; do not copy JVMX's runtime preparation or its 0.25 offset.

Match JVMX's minimum display of 1100 ms and 320 ms after local bootstrap.
Await `binding.endOfFrame` after bootstrap and these delays so home (or a
restore-status destination) has completed layout before `allowFirstFrame()`.
Release deferral in `finally`. `FlutterPage.onFirstFrame` removes the native
loading layer; reaching progress 1 does not remove it.

`EntryAbility` accepts finite numeric progress and clamps it to `[0, 1]` before
emitting. `StartupSplash` multiplies it by 100, subscribes in `aboutToAppear`,
and removes that same handler in `aboutToDisappear`. Reuse the product icon
and light/dark background resources, with the reference progress bar and fade.

Android and other targets render the shared Flutter loading screen immediately;
they neither defer the first frame nor report OHOS progress.

## 4. Validation & Error Matrix

| Condition | Required behavior |
| --- | --- |
| Finite progress outside `[0, 1]` | Clamp before emitting |
| Missing, nonnumeric, NaN, infinite progress | `INVALID_PROGRESS`; emit nothing |
| Missing native progress bridge | Ignore `MissingPluginException`; finish startup |
| Progress bridge throws `PlatformException` | Log code; finish startup |
| Shared local-store load fails | Retain shared bootstrap's per-store fallback |
| Bootstrap throws unexpectedly | Release first-frame deferral in `finally` |

## 5. Good / Base / Bad Cases

- Good: OHOS native icon and progress remain until the laid-out destination
  becomes the first submitted Flutter frame.
- Base: Android displays the existing Flutter loading screen while stores load.
- Bad: only changing system launch resources, or releasing the native layer
  as soon as progress reaches 100 percent, exposes the Flutter loading page.

## 6. Tests Required

`test/startup_test.dart` runs the real product entry point with temporary
path-provider storage. Check monotonic progress reaching 1, engine submission
remaining deferred through home layout, successful release, missing/error
progress bridges, and immediate Android loading without OHOS channel calls.

Run analysis and affected Flutter tests. Build a release HAP to compile the
ArkUI component and platform handler. Follow the backend release-verification
contract: an unsigned HAP proves packaging, not installation or visual startup
on a device. Device visual claims require the freshly built, correctly signed
artifact and an unobscured cold-start transition.

## 7. Wrong vs Correct

Wrong: set the native window background and call `runApp`; assume initialization
is now displayed natively.

Correct: supply the ArkUI `splashScreenView`, bridge real bootstrap progress,
and defer Flutter frame submission until the destination has completed layout.
