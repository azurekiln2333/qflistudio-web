import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_studio_core/editor/terminal_pane.dart';
import 'package:qfli_studio_core/pages/terminax_terminal_page.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/terminal/models/terminal_session.dart';
import 'package:qfli_studio_core/terminal/shell/local_shell.dart';
import 'package:qfli_studio_core/terminal/widgets/terminal_output.dart';

import 'package:qfli_web/main.dart' show webProfile;

/// WebForge terminal release verification.
///
/// Drives the *shared* terminal surfaces (`TerminalPane` in the editor and the
/// standalone `TerminaxTerminalPage`) from this product's suite, with the real
/// Web profile installed, so the offline-only wiring is what a store build
/// ships. The shared implementation is read-only (see
/// `.trellis/tasks/10-15-webforge-terminal-integrity/research/core-terminal-findings.md`);
/// this suite proves the observable contract, it does not re-implement it.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('WebForge profile terminal contract', () {
    test('the Web profile is offline-only with no host toolchain', () {
      // The whole offline gating story hangs off these two facts. If either
      // changes, every assertion below about the absent online terminal is
      // invalid, so pin them first.
      expect(webProfile.offlineOnly, isTrue);
      expect(webProfile.terminalCommandDelegate, isNull);
      expect(webProfile.supportedFileExtensions, ['.html', '.css', '.js']);
    });
  });

  group('Editor TerminalPane (offline Web profile)', () {
    late _PaneFixture fixture;

    setUp(() => fixture = _PaneFixture());
    tearDown(() => fixture.dispose());

    testWidgets('built-in commands run against the real sandbox', (
      tester,
    ) async {
      await fixture.mount(tester);

      await fixture.submit(tester, 'pwd');
      await _pumpIoUntil(tester, () => !fixture.pane.busy);
      expect(
        _lineContains('pwd'),
        findsWidgets,
        reason: 'the command echo must be visible',
      );
      expect(
        _lineContains(fixture.directory.path),
        findsOneWidget,
        reason: 'pwd must print the real working directory',
      );

      await fixture.submit(tester, 'help');
      await _pumpIoUntil(tester, () => !fixture.pane.busy);
      // The transcript is a lazy ListView, so assert on a line near the bottom
      // of the help text (the top scrolls out of the built range).
      expect(_lineContains('其它系统命令在当前平台不可用'), findsOneWidget);

      await fixture.submit(tester, 'clear');
      await _pumpIoUntil(tester, () => !fixture.pane.busy);
      await tester.pumpAndSettle();
      expect(
        find.byType(ListView),
        findsOneWidget,
        reason: 'clear keeps the transcript mounted, just empty',
      );
      expect(_lineContains('文件命令'), findsNothing);
      expect(_lineContains(fixture.directory.path), findsNothing);
      expect(tester.takeException(), isNull);
    });

    testWidgets('an unknown command reports honestly instead of silently', (
      tester,
    ) async {
      await fixture.mount(tester);
      await fixture.submit(tester, 'webforge_no_such_tool_7q3');
      await _pumpIoUntil(tester, () => !fixture.pane.busy);
      expect(_lineContains('不支持该命令'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('a nonzero exit keeps its integer; success stays silent', (
      tester,
    ) async {
      await fixture.mount(tester);

      final ok = fixture.pane.attachOutput(
        title: 'webforge-ok',
        stdout: Stream.value('preview ready'),
        stderr: const Stream.empty(),
        exitCode: Future.value(0),
      );
      await tester.pump();
      expect(await ok, 0);
      await tester.pumpAndSettle();
      expect(_line('preview ready'), findsOneWidget);
      expect(_line('exit code 0'), findsNothing);

      final bad = fixture.pane.attachOutput(
        title: 'webforge-fail',
        stdout: const Stream.empty(),
        stderr: Stream.value('main.dart:1: error'),
        exitCode: Future.value(127),
      );
      await tester.pump();
      expect(await bad, 127);
      await tester.pumpAndSettle();
      expect(_line('main.dart:1: error'), findsOneWidget);
      expect(_line('exit code 127'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('the Stop control cancels a running command', (tester) async {
      // The sandbox has no external shell; cancellation is exercised through a
      // profile delegate, the same path a host toolchain would use. The Web
      // profile has no delegate, so install one for this test only.
      final previous = StudioProfile.current;
      final cancel = Completer<void>();
      StudioProfile.current = StudioProfile(
        id: 'web-cancel-test',
        appTitle: 'Web cancel test',
        templates: const [],
        isOffline: true,
        terminalCommandDelegate: (backend, command) async {
          if (!command.startsWith('slowcmd')) return false;
          await backend.runStreams(
            title: 'slowcmd',
            stdout: const Stream<String>.empty(),
            stderr: const Stream<String>.empty(),
            exitCode: cancel.future.then((_) => 130),
            cancel: () async => cancel.complete(),
          );
          return true;
        },
      );
      addTearDown(() => StudioProfile.current = previous);

      await fixture.mount(tester);
      await fixture.submit(tester, 'slowcmd');
      await _pumpIoUntil(tester, () => fixture.pane.busy);
      expect(fixture.pane.busy, isTrue);

      final stop = find.byTooltip('停止');
      expect(stop, findsOneWidget);
      await tester.tap(stop);
      await _pumpIoUntil(tester, () => !fixture.pane.busy, attempts: 400);

      expect(fixture.pane.busy, isFalse);
      expect(find.byTooltip('停止'), findsNothing);
      expect(find.byType(TextField), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('interruptActive is a safe no-op with nothing running', (
      tester,
    ) async {
      await fixture.mount(tester);
      await fixture.pane.interruptActive();
      await _pumpFrames(tester, 3);
      expect(tester.takeException(), isNull);
      expect(find.byType(TextField), findsOneWidget);
    });

    testWidgets('console error output is returned to the transcript', (
      tester,
    ) async {
      await fixture.mount(tester);
      fixture.pane.appendDebug(
        '[ERROR] Uncaught ReferenceError: x is not defined',
      );
      await tester.pumpAndSettle();
      expect(
        _lineContains('Uncaught ReferenceError'),
        findsOneWidget,
        reason: 'web console output must land in the shared transcript',
      );
      expect(tester.takeException(), isNull);
    });

    testWidgets(
      'offline gating hides the online terminal and blocks showOnline',
      (tester) async {
        await fixture.mount(tester);
        // The Web profile is offlineOnly, which is the condition EditorPage uses
        // to pass onlineEnabled: false. Model it exactly.
        expect(fixture.onlineEnabled, isFalse);
        expect(find.byIcon(Icons.cloud_outlined), findsNothing);

        await fixture.pane.showOnline();
        await _pumpFrames(tester, 3);
        expect(
          fixture.pane.sessionCount,
          1,
          reason: 'showOnline must not open an online session when disabled',
        );
        expect(find.byIcon(Icons.cloud_outlined), findsNothing);
        expect(tester.takeException(), isNull);
      },
    );
  });

  group('Standalone Terminax (offline Web profile)', () {
    testWidgets('opens a local session and runs a built-in', (tester) async {
      final previous = StudioProfile.current;
      StudioProfile.current = webProfile;
      final storage = Directory.systemTemp.createTempSync('webforge-terminax-');
      final store = ProjectStore(storageFile: File('${storage.path}/p.json'));
      addTearDown(() {
        StudioProfile.current = previous;
        store.dispose();
        if (storage.existsSync()) storage.deleteSync(recursive: true);
      });

      tester.view.physicalSize = const Size(420, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(() async {
        await tester.pumpWidget(const SizedBox.shrink());
        await tester.pump();
      });

      await tester.pumpWidget(
        MaterialApp(home: TerminaxTerminalPage(store: store)),
      );
      await _pumpIoUntil(
        tester,
        () => find.byType(TerminalOutputView).evaluate().isNotEmpty,
      );

      // Exactly one local session is auto-created.
      expect(find.byType(TerminalOutputView), findsOneWidget);
      // No online/cloud/login affordance exists in the standalone terminal.
      expect(find.byIcon(Icons.cloud_outlined), findsNothing);
      expect(find.text('在线终端'), findsNothing);

      final field = find.byType(TextField);
      expect(field, findsOneWidget);
      await tester.enterText(field, 'help');
      await tester.testTextInput.receiveAction(TextInputAction.done);
      await _pumpIoUntil(
        tester,
        () => _lineContains('其它系统命令在当前平台不可用').evaluate().isNotEmpty,
      );
      expect(_lineContains('其它系统命令在当前平台不可用'), findsWidgets);
      expect(tester.takeException(), isNull);
    });
  });

  group('TerminalSession exit contract', () {
    test('exit and quit request a session close without executing', () async {
      final directory = Directory.systemTemp.createTempSync('webforge-exit-');
      final backend = createSandboxShell(
        sandboxRoot: directory.path,
        startDirectory: directory.path,
      );
      final session = TerminalSession(
        id: 'exit-test',
        title: 'exit test',
        backend: backend,
      );
      addTearDown(() {
        session.dispose();
        if (directory.existsSync()) directory.deleteSync(recursive: true);
      });

      TerminalSession? requested;
      session.onExitRequested = (target) => requested = target;

      await session.submit('pwd');
      expect(requested, isNull, reason: 'a normal command must not close');

      await session.submit('exit');
      expect(requested, same(session));

      requested = null;
      await session.submit('quit');
      expect(requested, same(session));
    });
  });
}

Finder _line(String text) => find.text(text);

/// Substring match over the transcript.
///
/// The editor `TerminalPane` renders each row as `SelectableText` and the
/// standalone `TerminalOutputView` renders `Text.rich`; `find.textContaining`
/// covers both (plus `EditableText`), unlike a raw `Text.data` predicate.
Finder _lineContains(String text) => find.textContaining(text);

Future<void> _pumpFrames(WidgetTester tester, int frames) async {
  for (var i = 0; i < frames; i++) {
    await tester.pump(const Duration(milliseconds: 16));
  }
}

Future<void> _pumpIoUntil(
  WidgetTester tester,
  bool Function() condition, {
  int attempts = 300,
}) async {
  for (var attempt = 0; attempt < attempts; attempt++) {
    await tester.pump(const Duration(milliseconds: 20));
    if (condition()) return;
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
  }
  expect(condition(), isTrue, reason: 'The terminal operation did not finish.');
}

/// Mounts a real [TerminalPane] the way the offline Web profile does:
/// `onlineEnabled: false` and no host toolchain delegate.
class _PaneFixture {
  final directory = Directory.systemTemp.createTempSync('webforge_terminal_');
  final auth = AuthStore();
  final key = GlobalKey<TerminalPaneState>();

  /// Mirrors `EditorPage._buildTerminalPanel` for the offline profile.
  bool onlineEnabled = false;

  TerminalPaneState get pane => key.currentState!;

  Future<void> mount(WidgetTester tester) async {
    addTearDown(() async {
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 20)),
      );
    });
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Align(
            alignment: Alignment.topLeft,
            child: SizedBox.fromSize(
              size: const Size(600, 300),
              child: TerminalPane(
                key: key,
                workingDirectory: directory.path,
                auth: auth,
                onlineEnabled: onlineEnabled,
              ),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
  }

  /// Types [command] and submits it through the real prompt, exactly as a user
  /// pressing Return does.
  Future<void> submit(WidgetTester tester, String command) async {
    final field = find.byType(TextField);
    await tester.enterText(field, command);
    await tester.testTextInput.receiveAction(TextInputAction.done);
    await tester.pump();
  }

  void dispose() {
    auth.dispose();
    if (directory.existsSync()) directory.deleteSync(recursive: true);
  }
}
