# Shared-core terminal audit (read-only)

Source tree: `D:/MyNewProjects/qfli_studio_core` (read-only sibling of
`qfli_web`). No file under `qfli_studio_core` was modified by this task.

Surfaces audited:

- `lib/editor/terminal_pane.dart` — in-editor shared terminal (69881 bytes).
- `lib/pages/terminax_terminal_page.dart` — standalone full-screen Terminax.
- `lib/terminal/**` — session model, shell backends, widgets.
- `lib/services/studio_profile.dart` — product wiring hooks.
- `lib/editor/editor_page.dart` — run/cancel/current-file/console wiring.

## 1. Web toolchain wiring

`StudioProfile.terminalCommandDelegate` is the single hook for language
toolchains (`studio_profile.dart:157`). `TerminalPane._backendFor`
(`terminal_pane.dart:440`) and `TerminaxTerminalPage` (`:42`, `:109`) both pass
`StudioProfile.current?.terminalCommandDelegate` into `createSandboxShell`.

**Web profile defines no delegate** (`qfli_web/lib/main.dart` `webProfile`),
which is correct: WebForge ships no host language toolchain. Unknown commands
must therefore reach `SandboxShellBackend.runExternal`
(`sandbox_shell_backend.dart:238`) and produce the honest
"当前平台的内置终端不支持该命令" message rather than a silent drop.

Verdict: correct. No shared-core change requested.

## 2. Built-in commands

`BaseShellBackend.handleBuiltin` (`shell_backend.dart`) owns cross-platform
built-ins `clear`/`cls`, `pwd`, `help`, `cd`. The sandbox adds the portable
file set via `PortableFilesystem` plus sandbox-specific `cp`/`mv`
(`sandbox_shell_backend.dart:169`). Compound syntax (pipe/redirect/`;`/glob) is
classified as `CommandSyntax.compound` and routed to `runExternal`, which emits
a construct-specific message (`_compoundConstruct`). Paths cannot escape
`sandboxRoot` (`resolveSandboxPath`, `SandboxEscapeException`).

Verdict: correct and well-covered by core `shell_command_test.dart`.

## 3. Execute / cancel / exit

- Execute: `TerminalPane._run` → `ShellBackend.execute`. `Busy` brackets the
  whole lifecycle; `_cancelRequested` is opened before the first async boundary
  (`shell_backend.dart`) so an interrupt in the same turn is not lost.
- Cancel: header Stop appears while `session.cancelAction != null`; local
  commands expose `backend.interrupt()` (`terminal_pane.dart`, `_run`).
  `TerminalSession.interrupt` delegates to the backend
  (`terminal_session.dart`).
- Exit: `TerminalSession.submit` intercepts `exit`/`quit` before executing and
  calls `onExitRequested` (`terminal_session.dart:180`). The manager wires it to
  `close(target.id)` (`terminal_manager.dart:57`). Terminax closes that tab; the
  pane closes the session (replacing the last tab instead of emptying the pane).

Verdict: correct.

## 4. Current-file preview

`EditorPage` long-press passes `entryOverride`; tap uses `server.url`. The
session's real document root resolves the URL via `urlForFile`, and failures are
explicit — no silent fallback to the default page (`editor_page.dart` ~
line 1017-1060). Console output is returned through
`server.debugStream.listen((line) => _terminalKey.currentState?.appendDebug(line))`
(`editor_page.dart:1046-1047`).

Verdict: correct; already covered by `qfli_web/test/web_preview_current_file_test.dart`.
This task re-asserts the terminal-side error回传 and preview interaction at the
release level.

## 5. Offline gating

`TerminalPane` gates the online terminal with
`onlineEnabled: StudioProfile.current?.offlineOnly != true`
(`editor_page.dart:1881`). The Web profile sets `isOffline: true`, and
`StudioProfile.offlineOnly` defaults to `isOffline`
(`studio_profile.dart`), so `offlineOnly == true`.

Consequently, in WebForge's terminal:

- The **online terminal** header button (`Icons.cloud_outlined`) is not built.
- `runOnlineProject` / `runCloudSql` no-op (`!widget.onlineEnabled` guards).
- `_runOnline` additionally refuses without a token ("请先登录后使用在线终端"),
  but is unreachable offline.
- The `.sql` cloud-MySQL branch is guarded by `offlineOnly != true`
  (`editor_page.dart:1001`).
- **Login/account surfaces** are hidden by the same flag at the shell level.

`TerminaxTerminalPage` creates only local `TerminalManager` sessions — it has no
online/cloud/login path at all, so it is offline-safe by construction.

### Git

`ShortcutBar` (`terminal/widgets/shortcut_bar.dart:143`) offers a
`git status` shortcut (hint "查看 Git 状态") **unconditionally** — it is not
gated on `offlineOnly`. `git` is not a built-in. On mobile/OHOS
`localShellAvailable()` is false (`local_shell_io.dart:57`), so
`createSandboxShell` has no `desktopShell` fallback and `git status` lands in
`runExternal` → the honest "不支持该命令" message. On desktop the real shell
would run git.

The honest runtime message does **not** excuse the visible entry: the user
requirement is that network-related Git entry points are hidden offline. See
finding 6.1 below.

## 6. Findings requiring coordination

### 6.1 Git shortcut is visible in the offline build (UI integrity gap)

**Severity: UI completeness gap, not cosmetic.**

`ShortcutBar` (`lib/terminal/widgets/shortcut_bar.dart:143`) unconditionally
renders a `git status` shortcut (hint "查看 Git 状态"). The WebForge profile is
`offlineOnly`, and the user requirement is explicit: **network-related Git
entry points must be hidden offline.** A release build that still shows a
`git status` affordance the user cannot use is a UI completeness defect, even
though the command itself fails with an honest message on mobile (no process
shell) rather than silently.

Requested direction (shared-core owner, general gate):

gate the `git` chip on the same `StudioProfile.current?.offlineOnly != true`
condition used for the online terminal
(`editor_page.dart:1881`), so **every** offline-only product hides it, not just
WebForge. Do not special-case the Web product by string.

This is a `qfli_studio_core` change and was therefore **out of scope** for this
task. Status: **accepted as a followup by the Go coordinator / core owner**
(reported by the main controller). This task did not modify the core and did not
add a Web-side workaround; a product-side patch would defeat the
general-gate requirement.

### 6.2 ToolsGrid large-text overflow (pre-existing)

`qfli_web/test/web_tools_navigation_test.dart` already documents a known core
defect: `ToolsGrid` overflows at 2.0 text scale. Recorded here so it is not
re-discovered as new; owned by the core/UI track.

### 6.3 No other blockers

Web toolchain delegate is intentionally absent; the terminal correctly reports
unsupported commands. Do not add a delegate to paper over this.
