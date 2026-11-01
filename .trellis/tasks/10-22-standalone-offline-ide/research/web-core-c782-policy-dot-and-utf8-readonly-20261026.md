# Read-only check: C782 policy failures, `a..` dots and raw UTF-8 URLs

Date: 2026-10-26. Author: Pi. Mode: read-only. No test, SDK, browser or device was
run. No file under `lib/` or `test/` was modified. No channel message was sent.

Artifacts inspected, with the state each conclusion is bound to:

| File | Size | SHA256 |
| --- | ---: | --- |
| `lib/services/owned_preview_policy.dart` (final) | 16038 | `9f0319afd64e20322bdefd7085a1927e3fda28f4e6f33a70ae317b0c39715802` |
| `test/owned_preview_policy_test.dart` | 17688 | `9324590b14b57bea5483c3aaa6fee2df9f0f89aad0baf1c47b17cd667062b639` |
| Dart SDK `lib/core/uri.dart`, `lib/convert/utf.dart` | - | `D:/ProgramFiles/flutter_ohos/bin/cache/dart-sdk/lib/` |

p3 edited both files repeatedly while this check ran: the policy went 15003 ->
17301 (hand-written UTF-8 decoder) -> 16038 (this final version), and the test
16927 -> 17688. The verdict in §1 and the review in §4 are bound to the final
16038-byte policy. §4 records the earlier hand-written decoder only as history,
because it was superseded.

## 1 Verdict summary

1. `/a%2E%2E/page.html` is a **legal** `a..` filename segment. It must be
   **allowed**. Rejecting it would break the contract and would also reject
   ordinary authored files such as `a..b.html`.
2. Both C782 failures have **one** root cause: a raw, un-escaped UTF-8 character
   above `0x7F` in the URL. The old decoder called `Uri.decodeComponent`, which
   throws for every such character. **The failures are not caused by the dot
   rule**, and the dot rule must not be changed to make them pass.
3. The landed fix is the minimal scheme: raw text is copied through, and only an
   ASCII escape run is handed to `Uri.decodeComponent`. On a static trace it
   restores both failing entries, keeps `a..` allowed, and keeps `/%2E%2E/` and
   `/a/%2E%2E/` refused. No rejection rule is widened.

## 2 Why `a..` must be allowed

The contract is stated in the file header (`owned_preview_policy.dart:40`) and in
the separator paragraph (`:49-52`): a decoded path segment is invalid only when it
is exactly `.`, exactly `..`, or a hidden segment starting with `.` other than
`.well-known`.

The implementation matches, using **exact equality** (`:274-280`):

```dart
for (final segment in decodedPath.split('/')) {
  if (segment == '.' || segment == '..') {
    return null;
  }
  if (segment.startsWith('.') && segment != '.well-known') {
    return null;
  }
}
```

Trace for the URL in question:

| Step | Result |
| --- | --- |
| `_hasOnlyPlainCharacters(url)` (`:230`) | all ASCII printable, passes |
| `_areEscapesWellFormed(url)` | `%2E` is two hex digits, passes |
| `_rawPathOf(url)` (`:259`) | `/a%2E%2E/page.html` |
| `_hasEncodedSlash(rawPath)` (`:264`) | no `%2F`, passes |
| `_decodeChecked(rawPath)` (`:267`) | `/a../page.html` |
| segments (`:274`) | `''`, `a..`, `page.html` |
| `a..` vs rules | not `.`, not `..`, does not start with `.` |
| **verdict** | **allow** |

Independent reasons, beyond "the code says so":

- RFC 3986 defines dot-segments as exactly `.` and `..`. `a..` is not one.
- Rejecting it also rejects `a..b.html`, `v1.2..3/page.html` and `notes..html`,
  which are legitimate filenames. That is the forbidden widening of a traversal
  rule into a filename rule.
- `a..` is a single literal segment. It carries no parent reference, so it cannot
  climb out of the document root by itself. Escape prevention rests on the exact
  `..` refusal plus the server-side containment guard at
  `lib/services/web_dev_server.dart:237` (`p.isWithin(config.root, resolved)`).
- Encoding does not change the judgement, because the check runs on the **decoded**
  path. A segment that decodes to exactly `..` is still refused (the reject list at
  `test/owned_preview_policy_test.dart:426-427` covers `/%2E%2E/page.html` and
  `/a/%2E%2E/page.html`), and a `%2F` in the path is refused before decoding.

One boundary worth recording, which does **not** change the verdict: Windows
Win32 strips trailing dots and spaces from a path component, so `a..` aliases the
name `a`. That is an aliasing/naming collision **inside** the root, not an escape.
If alias-free serving is ever wanted, it belongs in a separate rule with its own
justification, not in the dot-segment rule.

## 3 Root cause of the two failures: raw UTF-8 above `0x7F`

### The two failing entries are both raw Chinese

| Test | Line | Entry | Old outcome |
| --- | ---: | --- | --- |
| `accepts UTF-8 paths and an encoded space` (`:77`) | 80 | `http://127.0.0.1:3000/中文.html` | rejected |
| `allows a filename that merely contains dots` (`:440`) | 447 | `http://127.0.0.1:3000/中文.html` | rejected |

The second test's name is about dots, but **all of its dot entries pass**
(`:444` `a%2E%2E/page.html`, `:445` `a..b.html`, `:446` `v1.2..3/page.html`). Its
only failing entry is the Chinese one at `:447`. Since the loop stops at the first
failure, the observed failure looks like a dot-rule failure when it is not. This is
the single most important thing to avoid mis-reading in C782.

### Mechanism

The previous decoder was `Uri.decodeComponent(value)`. From the SDK source,
`D:/ProgramFiles/flutter_ohos/bin/cache/dart-sdk/lib/core/uri.dart`, `_uriDecode`:

```dart
if (codeUnit > 127 || codeUnit == _PERCENT || (plusToSpace && codeUnit == _PLUS)) {
  simple = false;
  break;
}
...
if (codeUnit > 127) {
  throw ArgumentError("Illegal percent encoding in URI");
}
```

So every raw character above `0x7F` makes the string "non-simple", and the
non-simple branch then throws for that same character. `Uri.decodeComponent` is a
**percent-decoder**: it is only defined for text that is already percent-encoded,
or plain ASCII.

Chain: `_decodeChecked` caught `ArgumentError` and returned `null` →
`_parseOwnedTarget` returned `null` (`:267`) → `classifyOwnedResource` (`:120`) and
`isOwnedNavigationAllowed` (`:144`) both report a non-allow decision.

The two helpers contradicted each other: `_hasOnlyPlainCharacters` (`:230`)
deliberately lets raw Chinese through by rejecting only `<= 0x20`, `0x7F`,
`0x80-0x9F` and backslash, while the decoder then refused the same text.

`Uri.decodeFull` is **not** an alternative fix: it calls the same `_uriDecode` with
`plusToSpace: false` and throws identically. Swapping one for the other does not
help, which is worth stating so it is not attempted.

## 4 Review of the landed minimal scheme

p3's final design is minimal: copy raw text verbatim, and hand **only** an ASCII
escape run to `Uri.decodeComponent`. That is sound, and the reason is a property
of the SDK, not of the caller.

### Why passing a run is safe

`_uriDecode` (`lib/core/uri.dart:3629`) does two things in order:

1. It sets `simple = false` if any code unit is `> 127`, is `%`, or is `+`. A run
   always contains `%`, so it always takes the non-simple branch.
2. The non-simple branch throws `ArgumentError` only for `codeUnit > 127`
   (`:3661-3662`), a truncated escape (`:3665-3666`), or bad hex
   (`_hexCharPairToByte`, `ArgumentError("Invalid URL encoding")`).

A run is, by construction, `%` plus hex digits: all ASCII. So the `> 127` throw
cannot fire, which is exactly why feeding a run is safe while feeding the whole
path is not. The remaining failure is `encoding.decode(bytes)` at `:3677`, and
`utf8` with `allowMalformed: false` throws `FormatException`
(`lib/convert/utf.dart:573`, and `_internal/vm/lib/convert_patch.dart:1467, 1860,
1964`). The code catches `FormatException` (`:337`), so malformed bytes are
refused rather than escaping.

### The three properties that make it correct

1. **The run contains no raw character.** `_decodeChecked` (`:317-352`) advances
   the run cursor only from a `%`, in steps of `3`, and stops at the first
   non-`%`. Combined with `_areEscapesWellFormed` running first (`:318`), every
   `%` in the run owns two hex digits. A raw character can never enter the run, so
   the `> 127` throw cannot be provoked by legal input.
2. **Bounds are safe.** `_areEscapesWellFormed` (`:381`) rejects when
   `index + 2 >= value.length`, so at each `%` the step to `index + 3` lands at
   most on `value.length`, and `substring(runStart, index)` is always valid.
3. **Raw text is preserved.** `rawStart` tracking writes the segments between runs
   verbatim, so `中文.html` reaches the assembled string unchanged. The control
   check then runs on the whole assembled string, not per run, so decoded and raw
   text are judged by one rule.

### Trace of every case that matters

| Input path | Run(s) passed to `decodeComponent` | Assembled | Verdict |
| --- | --- | --- | --- |
| `/中文.html` | none | `/中文.html` | allow |
| `/%E4%B8%AD%E6%96%87.html` | `%E4%B8%AD%E6%96%87` | `/中文.html` | allow |
| `/a%2E%2E/page.html` | `%2E%2E` | `/a../page.html` | allow, `a..` unchanged |
| `/a..b.html` | none | `/a..b.html` | allow |
| `/v1.2..3/page.html` | none | `/v1.2..3/page.html` | allow |
| `/%2E%2E/page.html` | `%2E%2E` | `/../page.html` | refuse, segment `..` |
| `/a/%2E%2E/page.html` | `%2E%2E` | `/a/../page.html` | refuse, segment `..` |
| `/a%2Eb.js` | `%2E` | `/a.b.js` | allow |
| `page.html?p=%2E%2E` | `%2E%2E` | query `..`, no control | allow |
| `/a%252E%252E/x` | `%25` | `/a%2E%2E/x` | allow, literal name, one decode |
| `/x?q=%E4%B8%AD%08` | `%E4%B8%AD%08` | `中\u0008` | refuse, control `0x08` |
| `/%85` | `%85` | throws `FormatException` | refuse |
| `/%C0%AF` | `%C0%AF` | throws `FormatException` | refuse, overlong |
| `/%ED%A0%80` | `%ED%A0%80` | throws `FormatException` | refuse, surrogate |
| `/%E4%B8` | `%E4%B8` | throws `FormatException` | refuse, truncated |
| `/%00` | `%00` | `\u0000` | refuse, control |

The `a..` verdict is unchanged because the run `%2E%2E` is appended after the raw
prefix `a` and the dot loop (`:274-280`) still compares with exact equality. One
decode is preserved because a decoded run is written to the buffer and never
re-scanned, so `%25` becomes a literal `%` and the following `2E` stays raw.

### One hardening note, not a defect

`ArgumentError` is not caught, and in the current code it is **unreachable**:
both of its sources are pre-empted by `_areEscapesWellFormed`. The risk is
coupling, not behaviour: if that pre-check were ever weakened or reordered, the
failure mode would be an uncaught exception leaving `classifyOwnedResource`, not a
rejection. Catching `ArgumentError` next to `FormatException` costs one line and
removes that coupling. It changes no verdict, and it does not touch any acceptance
rule.

The contract header (`:43-48`) matches the code: raw text passes through, a
literal `中文.html` path is owned, and a single octet is never refused merely for
being above `0x7F`.

## 5 Residual observations

1. **Same root cause elsewhere.** `lib/services/web_markup_inspector.dart:1035`
   calls `Uri.decodeFull(withoutQuery)` and catches `ArgumentError` to mark the
   reference `WebResourceKind.invalid`. A raw Chinese `src`/`href` is therefore
   classified invalid rather than resolved. Same cause, graceful degradation, still
   wrong. `lib/pages/web_tools_page.dart:772` uses `Uri.decodeComponent` inside a
   try/catch, so raw Chinese input there yields "转换失败". Both are candidates for
   the same treatment, outside C782's test scope.
2. **No coverage in the broker tests.** `test/owned_preview_resource_broker_test.dart`
   contains no `中文`, `%2E` or `a..` case, so the byte-serving path does not
   re-verify either judgement. The policy test is the only guard.
3. **`a..` is not covered at the broker layer.** The policy allows it, and the
   server resolves it, but no test asserts the end-to-end outcome for a file whose
   name contains trailing dots on Windows.
4. **Do not touch the dot rule for C782.** Both failures are UTF-8 decoding
   failures. Any change to the `.`/`..` comparison to make the dots test pass would
   be a wrong fix that breaks `a..b.html`.

## 6 Non-claims

I did not run the tests, so I cannot state that C782 now passes; I claim only that
on a static trace both previously failing entries decode successfully and that the
`a..` verdict is unchanged. The policy file was under active edit by p3 during this
check, so re-read it before acting on a line number. I made no edit to `lib/` or
`test/`, created no task, and sent nothing to any coordinator.
