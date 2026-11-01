# Owned static-preview resource broker boundary — 2026-10-26

Parent: `10-22-standalone-offline-ide`. Source-only implementation. Runtime checks are UNRUN.

The current product has no asynchronous resource broker between an owned ArkWeb interception callback and its registered loopback runtime. This slice adds that missing Dart owner. It reuses `owned_preview_policy.dart`, which Pi3 owns, and the shipped `WebProjectConfig.offlineContentSecurityPolicy`.

Owned files:

- `lib/services/owned_preview_resource_broker.dart`: asynchronous GET/HEAD forwarding to one literal loopback origin, bounded response leases, cancellation and disposal.
- `test/owned_preview_resource_broker_test.dart`: real-loopback fixtures for requests, a second-port escape sentinel, redirects, limits, timeout and disposal.
- This boundary record.

Each active request owns a dedicated HttpClient. The client uses DIRECT proxy routing, rechecks the exact origin in connectionFactory, requests identity encoding and never follows redirects. A timeout aborts the request when available and force-closes that same owned client. Disposal cancels all active operations and revokes retained response leases. No foreign client, listener, runtime or process is stopped.

The broker reserves its per-response byte allowance before starting a request. Reservations plus retained successful response bytes cannot exceed the aggregate bound. A returned fetched response stays leased until its caller calls release(). Accessing its bytes after release is an error. Generated errors use small fixed bodies and do not occupy the retained-byte budget. The caller must not keep body references after release.

All returned statuses carry the shipped CSP plus the stricter static-mode policy, no-store and nosniff. Only upstream Content-Type is retained. Upstream report endpoints, CSP, Location, cookies and arbitrary headers cannot weaken the generated response.

This slice does not mount ArkWeb, register platform channels, start a WebRuntimeSession, disable the server's injected reload bridge, register native CDP, enforce document navigation, or prove target network isolation. The eventual owner must reject proxy configuration and disable the injected bridge before mounting initial static Debug. SDK/Flutter/Dart/browser/native/device execution is not authorized for this subtask. The tests are authored but UNRUN.

## Verification status

Authored 21 tests. All remain UNRUN, including formatting and analysis. Static review checked the installed Dart source for the HttpClient connectionFactory signature and HttpHeaders constants without running the SDK. The CSP header uses a literal name because the installed HttpHeaders has no contentSecurityPolicyHeader constant. No SDK, browser, Job, device or application runtime was started.

Potential runtime concerns to resolve with the authorized tests include cancellation completion on the installed Dart IO implementation and the server-side disconnect observation used by the deadline fixture. No passing claim follows from source review.

## Focused source revision

The 128 KiB debug text limit now applies only to HTML/XHTML and JavaScript/ECMAScript MIME types. CSS and plain text use the normal response limit. New fixture cases distinguish those responses and check both JavaScript and MJS MIME forms.

Response leases now store Uint8List.asUnmodifiableView() over an owned payload. BytesBuilder accumulates bounded chunks before takeBytes(), avoiding a generic List<int> retention copy. The copying builder owns incoming chunks rather than assuming the IO producer never mutates them. The byte limits measure payload bytes; they do not claim an exact Dart heap-allocation ceiling.

The immutability test now attempts indexed mutation. Uint8List.add() would also fail on a writable fixed-length typed list, so that old assertion did not prove immutability. New failure cases check that an over-limit request relinquishes its reservation before a valid request, and that a connection failure leaves neither active work nor retained bytes. All 21 tests, formatting and analysis remain UNRUN.
