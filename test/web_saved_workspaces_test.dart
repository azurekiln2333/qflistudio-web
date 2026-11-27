import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
// Use the same temporary-path seam as the shared core's Home tests.
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:qfli_studio_core/app.dart';
import 'package:qfli_studio_core/editor/editor_controller.dart';
import 'package:qfli_studio_core/editor/editor_page.dart';
import 'package:qfli_studio_core/editor/editor_problems_bar.dart';
import 'package:qfli_studio_core/editor/file_explorer.dart';
import 'package:qfli_studio_core/editor/project_history.dart';
import 'package:qfli_studio_core/i18n/studio_localizations.dart';
import 'package:qfli_studio_core/layout/app_form_factor.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/pages/home_page.dart';
import 'package:qfli_studio_core/services/app_paths.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/services/task_activity_service.dart';
import 'package:qfli_studio_core/shell/large_screen_workbench.dart';
import 'package:qfli_studio_core/shell/workbench_chrome.dart';
import 'package:qfli_studio_core/shell/workbench_explorer.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';
import 'package:qfli_studio_core/workspace/saved_workspace.dart';
import 'package:qfli_studio_core/workspace/workspace_store.dart';
import 'package:qfli_web/main.dart' show webProfile;
// Inspect the real editor selection, rather than a parallel session model.
// ignore: depend_on_referenced_packages
import 'package:re_editor/re_editor.dart';

const _name = 'Web page workbench';
const _primarySource =
    '<!doctype html>\n<html lang="en">\n'
    '<body><h1>Primary site</h1></body>\n</html>';
const _secondarySource =
    '<!doctype html>\n<html lang="en">\n'
    '<body><h1>Secondary site</h1></body>\n</html>';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _Fixture fixture;
  late PathProviderPlatform previousPaths;
  StudioProfile? previousProfile;

  setUpAll(() async {
    fixture = await _Fixture.create();
    previousPaths = PathProviderPlatform.instance;
    PathProviderPlatform.instance = _TemporaryPaths(fixture.directory.path);
    // Home uses WorkspaceStore.instance. Resolve its real AppPaths dependency
    // into this file's isolated temporary directory before mounting any UI.
    expect(await AppPaths.storageDirectory(), fixture.directory.path);
    await TaskActivityService.instance.initialize();
    await WorkspaceStore.instance.load();
  });

  setUp(() {
    previousProfile = StudioProfile.current;
    StudioProfile.current = webProfile;
  });
  tearDown(() => StudioProfile.current = previousProfile);
  tearDownAll(() async {
    PathProviderPlatform.instance = previousPaths;
    fixture.disposeStores();
    await fixture.directory.delete(recursive: true);
  });

  testWidgets(
    'real Web Home saves a named workspace and reopens both owners after app reconstruction',
    (tester) async {
      tester.view.physicalSize = const Size(1100, 850);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(() => fixture.unmountAndDrain(tester));
      expect(StudioProfile.current, same(webProfile));
      expect(webProfile.productKey, StudioProductCatalog.webForgeKey);
      expect(webProfile.offlineOnly, isTrue);
      expect(webProfile.supportsSavedWorkspaces, isTrue);
      expect(isMainStudioRelease, isFalse);

      await fixture.mountHome(tester);
      final home = find.byType(HomeTab);
      final homeTabs = find.descendant(of: home, matching: find.byType(Tab));
      final labels = StudioLocalizations.of(tester.element(home));
      // Phone Home includes the local Agents scope in addition to the four
      // project/workspace scopes. Desktop uses an Explorer filter, not Tabs.
      expect(homeTabs, findsNWidgets(5));
      for (final scope in ['history', 'workspace', 'all', 'favorite', 'agents']) {
        expect(
          find.descendant(
            of: home,
            matching: find.byKey(ValueKey('home-scope-tab-$scope')),
          ),
          findsOneWidget,
        );
      }
      expect(find.byType(HomePage), findsOneWidget);
      expect(find.byType(LargeScreenWorkbench), findsNothing);
      expect(
        find.descendant(of: home, matching: find.text(labels.cloudProjects)),
        findsNothing,
      );
      expect(find.byType(FilterChip), findsNothing);
      await tester.tap(find.text(fixture.primary.name).hitTestable());
      await _until(
        tester,
        () => fixture.editor(tester)?.files.length == 1,
        'Opening the Web Home project did not restore its primary document.',
      );
      await fixture.showTree(tester);
      expect(find.byType(FileExplorer).hitTestable(), findsOneWidget);

      // This must be the named dialog exposed by the actual child profile.
      // A legacy membership-only dialog has no name field and fails here.
      final workspaceAction = find.descendant(
        of: find.byType(FileExplorer),
        matching: find.byWidgetPredicate(
          (widget) => widget is IconButton && widget.tooltip == '工作区项目',
        ),
      );
      await _until(
        tester,
        () => workspaceAction.hitTestable().evaluate().isNotEmpty,
        'The actual workspace settings button did not become interactive.',
      );
      await tester.tap(workspaceAction.hitTestable());
      final nameField = find.byKey(const ValueKey('workspace-name-field'));
      await _until(
        tester,
        () => nameField.evaluate().isNotEmpty,
        'The real Web profile did not expose named workspace saving.',
      );
      await tester.pump(const Duration(milliseconds: 300));
      final secondaryChoice = find.byKey(
        ValueKey('workspace-project-${fixture.secondary.id}'),
      );
      expect(tester.widget<CheckboxListTile>(secondaryChoice).value, isFalse);
      await tester.tap(secondaryChoice);
      await tester.enterText(nameField, _name);
      await tester.tap(find.widgetWithText(FilledButton, '保存'));
      await _until(
        tester,
        () =>
            WorkspaceStore.instance.workspaces.length == 1 &&
            find.byType(AlertDialog).evaluate().isEmpty &&
            fixture.root(fixture.secondary).evaluate().isNotEmpty,
        'Saving the Web workspace did not attach both project roots.',
      );
      await tester.pump(const Duration(milliseconds: 300));
      final saved = WorkspaceStore.instance.workspaces.single;
      expect(saved.name, _name);
      expect(saved.memberPaths, [fixture.primary.path, fixture.secondary.path]);
      expect(fixture.document(saved).existsSync(), isTrue);
      expect(
        tester.widget<EditorPage>(find.byType(EditorPage)).workspace?.id,
        saved.id,
      );
      await fixture.drain(tester);
      final projectHistory = fixture.history.readAsBytesSync();

      // Both file operations and tree changes go through the actual editor.
      await fixture.expand(tester, fixture.primary);
      await fixture.expand(tester, fixture.secondary);
      await tester.tap(fixture.entry(fixture.secondary, 'index.html'));
      await _until(
        tester,
        () =>
            fixture.editor(tester)?.files.length == 2 &&
            fixture.editor(tester)?.current?.projectRootPath ==
                fixture.secondary.path,
        'The secondary index.html did not open with its own owner.',
      );
      final editor = fixture.editor(tester)!;
      expect(editor.files.map((file) => file.path), [
        fixture.source(fixture.primary).path,
        fixture.source(fixture.secondary).path,
      ]);
      editor.files.first.controller.selection =
          const CodeLineSelection.collapsed(index: 1, offset: 3);
      editor.files.last.controller.selection =
          const CodeLineSelection.collapsed(index: 2, offset: 4);
      await tester.pump();
      await tester.tap(find.byTooltip('收起文件树').hitTestable());
      await tester.pump(const Duration(milliseconds: 300));
      await fixture.showTree(tester);
      expect(fixture.entry(fixture.primary, 'detail.html'), findsOneWidget);
      expect(fixture.entry(fixture.secondary, 'detail.html'), findsOneWidget);

      // Destroy QfliApp and its retained editor controller, not just the sidebar.
      await fixture.unmountAndDrain(tester);
      final latest = WorkspaceStore.instance.byId(saved.id)!;
      expect(latest.session.documents.map((document) => document.projectPath), [
        fixture.primary.path,
        fixture.secondary.path,
      ]);
      expect(latest.session.documents.map((document) => document.isActive), [
        false,
        true,
      ]);
      expect(latest.session.documents.first.cursor.baseIndex, 1);
      expect(latest.session.documents.first.cursor.baseOffset, 3);
      expect(latest.session.documents.last.cursor.baseIndex, 2);
      expect(latest.session.documents.last.cursor.baseOffset, 4);
      for (final project in [fixture.primary, fixture.secondary]) {
        expect(latest.session.expandedDirs[project.path], contains('nested'));
      }
      // Named sessions own their state; editing their tabs/tree does not
      // overwrite the project's pre-existing standalone history.
      expect(fixture.history.readAsBytesSync(), orderedEquals(projectHistory));
      fixture.expectSourceBytes();

      var previousEditor = editor;
      for (final formFactor in [AppFormFactor.phone, AppFormFactor.desktop]) {
        await tester.runAsync(() async {
          await WorkspaceStore.instance.load(force: true);
          await fixture.recreateStores();
        });
        await fixture.mountHome(tester, formFactor: formFactor);
        await fixture.openWorkspaceScope(tester, formFactor: formFactor);
        await _until(
          tester,
          () => find.text(_name).hitTestable().evaluate().isNotEmpty,
          'The ${formFactor.name} workspace entry did not list the saved document.',
        );
        await tester.tap(find.text(_name).hitTestable());
        await fixture.showTree(tester);
        await _until(
          tester,
          () =>
              fixture.editor(tester)?.files.length == 2 &&
              fixture.editor(tester)?.current?.projectRootPath ==
                  fixture.secondary.path,
          'The ${formFactor.name} card did not reconstruct the named Web session.',
        );
        final restored = fixture.editor(tester)!;
        expect(restored, isNot(same(previousEditor)));
        expect(
          tester.widget<EditorPage>(find.byType(EditorPage)).workspace?.id,
          saved.id,
        );
        expect(restored.files.map((file) => file.path), [
          fixture.source(fixture.primary).path,
          fixture.source(fixture.secondary).path,
        ]);
        expect(restored.files.map((file) => file.ownerProjectName), [
          fixture.primary.name,
          fixture.secondary.name,
        ]);
        expect(
          restored.files.every((file) => file.projectType == 'html'),
          isTrue,
        );
        expect(restored.files.every((file) => !file.dirty), isTrue);
        expect(restored.files.first.controller.text, _primarySource);
        expect(restored.files.last.controller.text, _secondarySource);
        expect(restored.files.first.controller.selection.baseIndex, 1);
        expect(restored.files.first.controller.selection.baseOffset, 3);
        expect(restored.current!.controller.selection.baseIndex, 2);
        expect(restored.current!.controller.selection.baseOffset, 4);
        await _until(
          tester,
          () =>
              fixture.entry(fixture.primary, 'detail.html').evaluate().isNotEmpty &&
              fixture.entry(fixture.secondary, 'detail.html').evaluate().isNotEmpty,
          'The named workspace did not restore both roots\' expanded directories.',
        );
        fixture.expectSourceBytes();
        expect(fixture.history.readAsBytesSync(), orderedEquals(projectHistory));
        expect(StudioProfile.current, same(webProfile));
        expect(tester.takeException(), isNull);
        previousEditor = restored;
        await fixture.unmountAndDrain(tester);
      }
    },
  );
}

class _Fixture {
  _Fixture(this.directory, this.primary, this.secondary);

  final Directory directory;
  final Project primary;
  final Project secondary;
  late ProjectStore store;
  late AuthStore auth;
  late SettingsStore settings;

  File get registry => File(p.join(directory.path, 'projects.json'));
  File get history => File(p.join(primary.path, 'history.json'));
  File source(Project project) => File(p.join(project.path, 'index.html'));
  File document(SavedWorkspace workspace) =>
      File(p.join(directory.path, 'workspaces', '${workspace.id}.json'));
  Finder root(Project project) =>
      find.byKey(ValueKey('workspace-root-${project.path}'));
  Finder entry(Project project, String name) =>
      find.descendant(of: root(project), matching: find.text(name));

  static Future<_Fixture> create() async {
    final directory = await Directory.systemTemp.createTemp('web_named_ws_');
    Project project(String name, String folder) => Project.create(
      name: name,
      path: p.join(directory.path, folder),
      language: 'HTML',
      type: 'html',
    );
    final fixture = _Fixture(
      directory,
      project('Primary site', 'primary'),
      project('Secondary site', 'secondary'),
    );
    for (final project in [fixture.primary, fixture.secondary]) {
      await Directory(p.join(project.path, 'nested')).create(recursive: true);
      await File(
        p.join(project.path, 'nested', 'detail.html'),
      ).writeAsString('<p>Nested page</p>');
    }
    await fixture.source(fixture.primary).writeAsString(_primarySource);
    await fixture.source(fixture.secondary).writeAsString(_secondarySource);
    await fixture.registry.writeAsString(
      jsonEncode({
        'projects': [fixture.primary.toJson(), fixture.secondary.toJson()],
      }),
    );
    await ProjectHistory.save(
      fixture.primary.path,
      cursors: const {},
      openFiles: const ['index.html'],
      activeFile: 'index.html',
    );
    await fixture._createStores();
    return fixture;
  }

  Future<void> _createStores() async {
    store = ProjectStore(storageFile: registry);
    auth = AuthStore();
    settings = SettingsStore();
    await store.load();
  }

  Future<void> recreateStores() async {
    disposeStores();
    await _createStores();
  }

  void disposeStores() {
    store.dispose();
    auth.dispose();
    settings.dispose();
  }

  Future<void> mountHome(
    WidgetTester tester, {
    AppFormFactor formFactor = AppFormFactor.phone,
  }) async {
    await tester.pumpWidget(
      QfliApp(
        store: store,
        auth: auth,
        settings: settings,
        formFactor: formFactor,
      ),
    );
    final project = formFactor == AppFormFactor.phone
        ? find.text(primary.name)
        : find.byKey(ValueKey('workbench-project-${primary.id}'));
    await _until(
      tester,
      () => project.hitTestable().evaluate().isNotEmpty,
      'The actual ${formFactor.name} Home did not show its registered project.',
    );
    if (formFactor == AppFormFactor.desktop) {
      expect(find.byType(LargeScreenWorkbench), findsOneWidget);
      expect(find.byType(HomePage), findsNothing);
      expect(find.byType(WorkbenchProjectsPanel), findsOneWidget);
      expect(find.byKey(const ValueKey('workbench-project-search')), findsOneWidget);
      expect(
        find.descendant(of: find.byType(HomeTab), matching: find.byType(Tab)),
        findsNothing,
      );
    }
  }

  Future<void> openWorkspaceScope(
    WidgetTester tester, {
    required AppFormFactor formFactor,
  }) async {
    if (formFactor == AppFormFactor.phone) {
      final tab = find.byKey(const ValueKey('home-scope-tab-workspace'));
      expect(tab, findsOneWidget);
      await tester.ensureVisible(tab);
      await tester.tap(tab);
    } else {
      final filter = find.descendant(
        of: find.byType(WorkbenchProjectsPanel),
        matching: find.widgetWithIcon(IconButton, Icons.filter_list),
      );
      expect(filter.hitTestable(), findsOneWidget);
      await tester.tap(filter);
      await tester.pump();
      final labels = StudioLocalizations.of(tester.element(find.byType(HomeTab)));
      final workspace = find.widgetWithText(
        MenuItemButton,
        labels.isEnglish ? 'Workspaces' : '工作区',
      );
      expect(workspace.hitTestable(), findsOneWidget);
      await tester.tap(workspace);
    }
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
  }

  EditorController? editor(WidgetTester tester) {
    final tree = find.byType(FileExplorer).hitTestable();
    if (tree.evaluate().isNotEmpty) {
      return tester.widget<FileExplorer>(tree).editor;
    }
    final bar = find.byType(EditorProblemsBar).hitTestable();
    if (bar.evaluate().isEmpty) return null;
    return tester.widget<EditorProblemsBar>(bar).analysis.editor;
  }

  Future<void> showTree(WidgetTester tester) async {
    if (find.byType(LargeScreenWorkbench).evaluate().isNotEmpty) {
      await _until(
        tester,
        () => root(primary).hitTestable().evaluate().isNotEmpty,
        'The actual workbench did not reveal the restored project tree.',
      );
      expect(find.byType(WorkbenchExplorer), findsOneWidget);
      return;
    }
    await _until(
      tester,
      () =>
          find.byTooltip('打开文件树').hitTestable().evaluate().isNotEmpty ||
          find.byTooltip('收起文件树').hitTestable().evaluate().isNotEmpty,
      'The editor tree toggle did not become interactive.',
    );
    final closed = find.byTooltip('打开文件树').hitTestable();
    if (closed.evaluate().isNotEmpty) await tester.tap(closed);
    // Start AnimatedAlign at the current fake time before advancing it. A
    // single duration pump starts the animation at its end time; the root's
    // center can then be visible while the settings button is still clipped.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    await _until(
      tester,
      () => root(primary).hitTestable().evaluate().isNotEmpty,
      'The primary project tree did not open.',
    );
  }

  Future<void> expand(WidgetTester tester, Project project) async {
    await _until(
      tester,
      () => entry(project, 'nested').evaluate().isNotEmpty,
      'The ${project.name} folder did not load.',
    );
    await tester.tap(entry(project, 'nested'));
    await _until(
      tester,
      () => entry(project, 'detail.html').evaluate().isNotEmpty,
      'The ${project.name} folder did not expand.',
    );
  }

  Future<void> unmountAndDrain(WidgetTester tester) async {
    FocusManager.instance.primaryFocus?.unfocus();
    await tester.pump();
    await tester.pumpWidget(const SizedBox.shrink());
    await drain(tester);
  }

  Future<void> drain(WidgetTester tester) async {
    var done = false;
    final pending = Future.wait([
      WorkspaceStore.instance.settle(),
      ProjectHistory.load(primary.path),
      store.refresh(),
    ]);
    pending.then((_) => done = true);
    await _until(
      tester,
      () => done,
      'Queued workspace/history writes did not drain.',
    );
    await pending;
  }

  void expectSourceBytes() {
    expect(source(primary).readAsBytesSync(), utf8.encode(_primarySource));
    expect(source(secondary).readAsBytesSync(), utf8.encode(_secondarySource));
    for (final project in [primary, secondary]) {
      expect(
        File(p.join(project.path, 'nested', 'detail.html')).readAsBytesSync(),
        utf8.encode('<p>Nested page</p>'),
      );
    }
  }
}

class _TemporaryPaths extends PathProviderPlatform {
  _TemporaryPaths(this.root);
  final String root;

  @override
  Future<String?> getApplicationSupportPath() async => root;
  @override
  Future<String?> getApplicationDocumentsPath() async => root;
  @override
  Future<String?> getTemporaryPath() async => p.join(root, 'tmp');
}

Future<void> _until(
  WidgetTester tester,
  bool Function() complete,
  String reason,
) async {
  for (var attempt = 0; attempt < 240; attempt++) {
    await tester.pump(const Duration(milliseconds: 20));
    if (complete()) return;
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
  }
  expect(complete(), isTrue, reason: reason);
}
