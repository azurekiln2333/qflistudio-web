/// Pure decision policy for the product-owned static preview and static debug.
///
/// This is a pure policy, not an ArkWeb integration. It uses `dart:core` only:
/// no platform channel, no FFI and no engine access. Until the owned component
/// actually runs, no offline isolation may be claimed from this file.
///
/// The two predicates are total, so the accept/reject table below can be
/// diffed against the code and the unit test without a device, SDK or build.
///
/// Decision order for [classifyOwnedResource] (first match wins):
///
/// 1. target syntax and scheme -> [OwnedPreviewDecision.invalidTarget]
/// 2. origin argument validity -> [OwnedPreviewDecision.invalidTarget]
/// 3. origin ownership -> [OwnedPreviewDecision.forbidden]
/// 4. method -> [OwnedPreviewDecision.methodNotAllowed]
/// 5. otherwise -> [OwnedPreviewDecision.allow]
///
/// Ownership is checked before the method so a foreign target reports
/// `forbidden` and never echoes this page's method policy to it.
///
/// The broker maps decisions to status codes: `forbidden` to 403,
/// `methodNotAllowed` to 405 and `invalidTarget` to 400.
///
/// Accept/reject table for [classifyOwnedResource]:
///
/// | Input | Decision |
/// | --- | --- |
/// | HTTP(S) URL on the exact session origin, `GET` or `HEAD` | allow |
/// | HTTP(S) URL on another origin, port or scheme | forbidden |
/// | prefix lookalike (`127.0.0.1.example`), `localhost`, `127.12.34.56` | forbidden |
/// | `POST`, `PUT`, `DELETE`, `PATCH`, `OPTIONS`, `TRACE`, `CONNECT` | methodNotAllowed |
/// | relative or unparsable URL, `data:`, `blob:`, `about:`, `file:`, `resource:`, custom scheme | invalidTarget |
/// | userinfo (`http://user@host/`) | invalidTarget |
/// | fragment (`#...`) on a broker request URL | invalidTarget |
/// | raw backslash, whitespace, C0/C1 control, DEL | invalidTarget |
/// | malformed percent escape | invalidTarget |
/// | escape decoding to a C0, DEL or C1 control | invalidTarget |
/// | decoded backslash in the path | invalidTarget |
/// | percent-encoded slash `%2F` in the path | invalidTarget |
/// | decoded path segment `.`, `..`, or a hidden segment except `.well-known` | invalidTarget |
/// | invalid origin argument | invalidTarget |
///
/// Escapes are decoded before judging, so UTF-8 text and an encoded space stay
/// valid: `%E4%B8%AD%E6%96%87.html` and `%E4%B8%AD%E6%96%87%20a.html` are owned
/// resources. Raw text passes through unchanged, so a literal `中文.html` path is
/// owned too. A single octet is never rejected for being above `0x7F`, because
/// that would reject every multibyte character. Escape runs are decoded as UTF-8
/// and a malformed or overlong sequence is refused.
///
/// Separator and dot-segment checks read the decoded path only. A percent-
/// encoded slash is refused in the path, because it would add a separator the
/// served path never shows. A query may carry `%2F`, `%2E`, `%2E%2E`, `%5C` or
/// `%20` without becoming a traversal. Decoding happens once, so `%252F` stays
/// a literal `%2F` and is not re-decoded here.
///
/// The fragment rule belongs to the HTTP broker boundary only. A same-page
/// anchor is not an external destination and never becomes a resource request,
/// so [isOwnedNavigationAllowed] compares the URL with its fragment removed.
///
/// Resource kind is untrusted. The policy never reads MIME, an extension,
/// `Accept` or `isMainFrame`, because a native callback may omit that field and
/// page content can influence it. A sample asset type is never promoted to a
/// trusted signal. Type limits are expressed as CSP directives instead of
/// branches here.
///
/// Type limits carried by [buildOwnedContentSecurityPolicy]:
///
/// * `connect-src` `'none'`: fetch, XHR, WebSocket and EventSource are refused.
/// * `worker-src` `'none'`: Worker and SharedWorker stay unsupported.
/// * `frame-src` `'none'`: subframes stay unsupported.
/// * `form-action` `'none'`: no form submission leaves the page.
/// * Service Worker: the extra policy grants no token for it.
/// * Redirects: this policy cannot observe a 30x. The broker must not follow
///   one and must re-run [classifyOwnedResource] on the `Location` target.
library;

/// Broker bound: intercepted requests allowed in flight at once.
const int kOwnedPreviewMaxInFlight = 16;

/// Broker bound: bytes served for one static response (2 MiB).
const int kOwnedPreviewMaxResponseBytes = 2 << 20;

/// Broker bound: bytes retained for the whole session (16 MiB).
const int kOwnedPreviewMaxRetainedBytes = 16 << 20;

/// Debug bound: authored HTML/JS text captured for one source (128 KiB).
const int kOwnedPreviewMaxDebugTextBytes = 128 << 10;

/// Broker bound: deadline for one resource request.
const Duration kOwnedPreviewRequestDeadline = Duration(seconds: 5);

/// Extra policy sent beside the shipped baseline, never merged into it.
///
/// This value is one serialized policy list. Per the CSP serialized policy list
/// grammar, sending it as a second policy value or as a comma-separated list
/// makes the user agent enforce each policy on its own, which yields the
/// intended intersection. Only a repeated directive inside a single policy
/// would keep an earlier value instead.
const String kOwnedPreviewExtraPolicy =
    "connect-src 'none'; worker-src 'none'; frame-src 'none'; "
    "form-action 'none'";

/// Ownership verdict for one broker request.
enum OwnedPreviewDecision { allow, forbidden, methodNotAllowed, invalidTarget }

/// Classifies one HTTP request target against the exact session origin.
///
/// `origin` is the runtime origin the Dart owner registered, for example
/// `http://127.0.0.1:3000`. Only the literal loopbacks `127.0.0.1` and `::1`
/// are valid hosts, and DNS names such as `localhost` are rejected. The port
/// may be omitted: the scheme default then applies, so `http://127.0.0.1` means
/// port 80 and `https://127.0.0.1` means port 443. An explicit default port is
/// equivalent to an omitted one. Comparison uses the parsed [Uri] and the
/// effective port, never a string prefix.
OwnedPreviewDecision classifyOwnedResource({
  required String url,
  required String method,
  required String origin,
}) {
  final target = _parseOwnedTarget(url, allowFragment: false);
  if (target == null) {
    return OwnedPreviewDecision.invalidTarget;
  }
  final session = _parseOwnedOrigin(origin);
  if (session == null) {
    return OwnedPreviewDecision.invalidTarget;
  }
  if (!_isSameOrigin(target, session)) {
    return OwnedPreviewDecision.forbidden;
  }
  if (!_isAcceptedMethod(method)) {
    return OwnedPreviewDecision.methodNotAllowed;
  }
  return OwnedPreviewDecision.allow;
}

/// Whether a page navigation may proceed inside the owned session.
///
/// Same-document anchors are page behaviour, not external destinations, so the
/// fragment is removed before the origin comparison. Everything else must still
/// match the exact origin, and a foreign origin stays refused even when it
/// carries a fragment.
bool isOwnedNavigationAllowed({required String url, required String origin}) {
  final target = _parseOwnedTarget(url, allowFragment: true);
  if (target == null) {
    return false;
  }
  final session = _parseOwnedOrigin(origin);
  if (session == null) {
    return false;
  }
  return _isSameOrigin(target, session);
}

/// Returns the shipped baseline followed by the extra policy.
///
/// The baseline bytes come back unchanged: no directive is rewritten, and no
/// scheme is added to `script-src` or to any other directive. The two values
/// are separated by a comma, the CSP serialized policy list form, so a user
/// agent parses two policies and enforces both.
///
/// `base` is the shipped baseline constant. It is not user input, and the
/// broker never passes a project string. A value that already contains a comma
/// or a line break would smuggle a third policy, so this function rejects it
/// with [ArgumentError] instead of guessing. An empty or blank baseline is
/// rejected as well: dropping it would drop `default-src` and loosen the result.
String buildOwnedContentSecurityPolicy(String base) {
  final trimmed = base.trim();
  if (trimmed.isEmpty) {
    throw ArgumentError.value(base, 'base', '基线策略不能为空，否则会丢掉 default-src');
  }
  if (base.contains(',') ||
      base.contains('\n') ||
      base.contains('\r') ||
      base.contains('\u0000')) {
    throw ArgumentError.value(base, 'base', '基线策略只能是内置常量，不能携带策略列表分隔符');
  }
  return '$trimmed, $kOwnedPreviewExtraPolicy';
}

/// HTTP methods are case-sensitive, so the token is compared exactly.
/// Normalizing it here could accept a token the client never sends.
bool _isAcceptedMethod(String method) {
  return method == 'GET' || method == 'HEAD';
}

Uri? _parseOwnedOrigin(String origin) {
  if (!_hasOnlyPlainCharacters(origin) || !_areEscapesWellFormed(origin)) {
    return null;
  }
  if (_decodeChecked(origin) == null) {
    return null;
  }
  final Uri session;
  try {
    session = Uri.parse(origin);
  } on FormatException {
    return null;
  }
  final scheme = session.scheme.toLowerCase();
  if (scheme != 'http' && scheme != 'https') {
    return null;
  }
  if (!session.hasAuthority || session.userInfo.isNotEmpty) {
    return null;
  }
  if (session.hasQuery || session.hasFragment) {
    return null;
  }
  final path = session.path;
  if (path.isNotEmpty && path != '/') {
    return null;
  }
  if (!_isOwnedLoopbackHost(session.host)) {
    return null;
  }
  // An omitted port is legal: the effective port comes from the scheme.
  if (session.hasPort && (session.port < 1 || session.port > 65535)) {
    return null;
  }
  return session;
}

bool _isOwnedLoopbackHost(String host) {
  final normalized = host.toLowerCase();
  return normalized == '127.0.0.1' || normalized == '::1';
}

Uri? _parseOwnedTarget(String url, {required bool allowFragment}) {
  if (!_hasOnlyPlainCharacters(url)) {
    return null;
  }
  if (!_areEscapesWellFormed(url)) {
    return null;
  }
  final lower = url.toLowerCase();
  if (!lower.startsWith('http://') && !lower.startsWith('https://')) {
    return null;
  }
  final Uri target;
  try {
    target = Uri.parse(url);
  } on FormatException {
    return null;
  }
  final scheme = target.scheme.toLowerCase();
  if (scheme != 'http' && scheme != 'https') {
    return null;
  }
  if (!target.hasAuthority || target.host.isEmpty) {
    return null;
  }
  if (target.userInfo.isNotEmpty) {
    return null;
  }
  if (!allowFragment && target.hasFragment) {
    return null;
  }
  final rawPath = _rawPathOf(url);
  if (rawPath == null) {
    return null;
  }
  // An encoded slash would add a separator the served path never shows.
  if (_hasEncodedSlash(rawPath)) {
    return null;
  }
  final decodedPath = _decodeChecked(rawPath);
  if (decodedPath == null) {
    return null;
  }
  if (decodedPath.contains('\\')) {
    return null;
  }
  for (final segment in decodedPath.split('/')) {
    if (segment == '.' || segment == '..') {
      return null;
    }
    if (segment.startsWith('.') && segment != '.well-known') {
      return null;
    }
  }
  // A query may hold encoded separators; only its control characters matter.
  final rawQuery = _rawQueryOf(url);
  if (rawQuery != null && _decodeChecked(rawQuery) == null) {
    return null;
  }
  // A fragment may follow the path, so drop it before returning the target.
  return allowFragment && target.hasFragment ? target.removeFragment() : target;
}

/// Rejects raw whitespace, backslash and C0/C1 controls before parsing.
bool _hasOnlyPlainCharacters(String value) {
  for (final unit in value.codeUnits) {
    if (unit <= 0x20 || unit == 0x7F) {
      return false;
    }
    if (unit >= 0x80 && unit <= 0x9F) {
      return false;
    }
    if (unit == 0x5C) {
      return false;
    }
  }
  return true;
}

/// Decodes the percent escapes in [value] and rejects Unicode controls.
///
/// Raw text passes through unchanged, so a literal `中文.html` path stays valid.
/// Every escape run is ASCII, so it can go to `Uri.decodeComponent`, which applies
/// strict UTF-8: `%E4%B8%AD` is one character, while a lone `%85` or an overlong
/// `%C0%AF` raises `FormatException` and is refused.
///
/// `Uri.decodeComponent` must never receive raw text. It throws `ArgumentError`
/// for every character above `0x7F`, so a whole `中文.html` path would become an
/// invalid target. Only the ASCII escape run is passed here.
String? _decodeChecked(String value) {
  if (!_areEscapesWellFormed(value)) {
    return null;
  }
  final out = StringBuffer();
  var rawStart = 0;
  var index = 0;
  while (index < value.length) {
    if (value.codeUnitAt(index) != 0x25) {
      index++;
      continue;
    }
    out.write(value.substring(rawStart, index));
    final runStart = index;
    while (index < value.length && value.codeUnitAt(index) == 0x25) {
      index += 3;
    }
    final String run;
    try {
      run = Uri.decodeComponent(value.substring(runStart, index));
    } on FormatException {
      return null;
    }
    out.write(run);
    rawStart = index;
  }
  out.write(value.substring(rawStart));
  final decoded = out.toString();
  for (final rune in decoded.runes) {
    if (rune <= 0x1F || rune == 0x7F) {
      return null;
    }
    if (rune >= 0x80 && rune <= 0x9F) {
      return null;
    }
  }
  return decoded;
}

/// Detects a percent-encoded slash in a raw path.
///
/// Only the path is checked, so a query may still carry `%2F`.
bool _hasEncodedSlash(String rawPath) {
  var index = 0;
  while (index + 2 < rawPath.length) {
    if (rawPath.codeUnitAt(index) == 0x25 &&
        rawPath.codeUnitAt(index + 1) == 0x32 &&
        (rawPath.codeUnitAt(index + 2) == 0x46 ||
            rawPath.codeUnitAt(index + 2) == 0x66)) {
      return true;
    }
    index++;
  }
  return false;
}

/// Requires every `%` to introduce exactly two hexadecimal digits.
bool _areEscapesWellFormed(String value) {
  var index = 0;
  while (index < value.length) {
    if (value.codeUnitAt(index) != 0x25) {
      index++;
      continue;
    }
    if (index + 2 >= value.length) {
      return false;
    }
    final high = _hexValue(value.codeUnitAt(index + 1));
    final low = _hexValue(value.codeUnitAt(index + 2));
    if (high < 0 || low < 0) {
      return false;
    }
    index += 3;
  }
  return true;
}

int _hexValue(int unit) {
  if (unit >= 0x30 && unit <= 0x39) {
    return unit - 0x30;
  }
  if (unit >= 0x41 && unit <= 0x46) {
    return unit - 0x41 + 10;
  }
  if (unit >= 0x61 && unit <= 0x66) {
    return unit - 0x61 + 10;
  }
  return -1;
}

/// Extracts the raw query, or null when the URL has none.
String? _rawQueryOf(String url) {
  final start = url.indexOf('?');
  if (start < 0) {
    return null;
  }
  final hash = url.indexOf('#');
  final end = hash > start ? hash : url.length;
  return url.substring(start + 1, end);
}

/// Extracts the raw path, stopping at the query or the fragment.
String? _rawPathOf(String url) {
  final schemeEnd = url.indexOf('://');
  if (schemeEnd < 0) {
    return null;
  }
  var index = schemeEnd + 3;
  while (index < url.length) {
    final unit = url.codeUnitAt(index);
    if (unit == 0x2F || unit == 0x3F || unit == 0x23) {
      break;
    }
    index++;
  }
  if (index >= url.length || url.codeUnitAt(index) != 0x2F) {
    return '';
  }
  final start = index;
  while (index < url.length) {
    final unit = url.codeUnitAt(index);
    if (unit == 0x3F || unit == 0x23) {
      break;
    }
    index++;
  }
  return url.substring(start, index);
}

bool _isSameOrigin(Uri target, Uri session) {
  if (target.scheme.toLowerCase() != session.scheme.toLowerCase()) {
    return false;
  }
  if (target.host.toLowerCase() != session.host.toLowerCase()) {
    return false;
  }
  return _effectivePort(target) == _effectivePort(session);
}

int _effectivePort(Uri uri) {
  if (uri.hasPort) {
    return uri.port;
  }
  return uri.scheme.toLowerCase() == 'https' ? 443 : 80;
}
