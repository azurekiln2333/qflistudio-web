import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:qfli_studio_core/content/content_repository.dart';
import 'package:qfli_studio_core/i18n/studio_localizations.dart';
import 'package:qfli_studio_core/pages/home_page.dart';
import 'package:qfli_studio_core/pages/local_content_pages.dart';
import 'package:qfli_studio_core/services/app_paths.dart';
import 'package:qfli_studio_core/services/code_import_service.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';
import 'package:qfli_studio_core/widgets/code_snippet.dart';
import 'package:qfli_studio_core/widgets/language_badge.dart';
import 'package:qfli_web/content/webforge_content_repository.dart';
import 'package:qfli_web/main.dart' show webProfile;

const _subjectCounts = {'html': 160, 'css': 160, 'javascript': 161};
const _subjectLabels = {
  'html': 'HTML',
  'css': 'CSS',
  'javascript': 'JavaScript',
};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late Directory directory;
  late PathProviderPlatform previousPaths;
  StudioProfile? previousProfile;
  late ContentCatalog catalog;
  late Map<String, ByteData> assetBytes;
  final assetRequests = <String>[];

  setUpAll(() async {
    // The transport is mocked; both documents are the actual shipped assets.
    // No core catalog or reduced widget fixture can satisfy these tests.
    final tutorials = File(
      WebForgeContentRepository.tutorialAsset,
    ).readAsBytesSync();
    final examples = File(
      WebForgeContentRepository.exampleAsset,
    ).readAsBytesSync();
    assetBytes = {
      WebForgeContentRepository.tutorialAsset: ByteData.sublistView(tutorials),
      WebForgeContentRepository.exampleAsset: ByteData.sublistView(examples),
    };
    catalog = ContentCatalog.fromJson(
      tutorialsSource: utf8.decode(tutorials),
      examplesSource: utf8.decode(examples),
    );
    directory = await Directory.systemTemp.createTemp('web-catalog-language-');
    previousPaths = PathProviderPlatform.instance;
    PathProviderPlatform.instance = _TemporaryPaths(directory.path);
    await AppPaths.storageDirectory();
    await AppPaths.projectsRoot(create: true);
  });

  setUp(() {
    previousProfile = StudioProfile.current;
    StudioProfile.current = webProfile;
    assetRequests.clear();
    rootBundle.clear();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMessageHandler('flutter/assets', (message) async {
          if (message == null) return null;
          final key = utf8.decode(
            message.buffer.asUint8List(
              message.offsetInBytes,
              message.lengthInBytes,
            ),
          );
          assetRequests.add(key);
          const productPrefix = 'packages/qfli_web/';
          final asset = key.startsWith(productPrefix)
              ? key.substring(productPrefix.length)
              : key;
          return assetBytes[asset];
        });
  });

  tearDown(() {
    StudioProfile.current = previousProfile;
    rootBundle.clear();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMessageHandler('flutter/assets', null);
  });

  tearDownAll(() async {
    PathProviderPlatform.instance = previousPaths;
    await directory.delete(recursive: true);
  });

  test(
    'Web profile factory retains 481 subjects with HTML import types',
    () async {
      final factory = webProfile.contentRepositoryFactory;
      expect(factory, isNotNull);
      final repository = factory!();
      expect(repository, isA<WebForgeContentRepository>());
      final loaded = await repository.load();
      expect(loaded.tutorials, hasLength(481));
      expect(loaded.examples, hasLength(481));
      for (final subject in _subjectCounts.keys) {
        final filter = ContentFilter(language: subject);
        expect(
          await repository.tutorials(filter: filter),
          hasLength(_subjectCounts[subject]!),
        );
        expect(
          await repository.examples(filter: filter),
          hasLength(_subjectCounts[subject]!),
        );
      }
      for (final entry in [...loaded.tutorials, ...loaded.examples]) {
        expect(entry.type, 'html', reason: entry.id);
        expect(
          CodeImportService.suggestedFileName(entry.type),
          'index.html',
          reason: entry.id,
        );
      }
      expect(
        await repository.examples(filter: const ContentFilter(type: 'css')),
        isEmpty,
      );
      _expectProductAssetRequests(assetRequests);
    },
  );

  for (final tutorials in [true, false]) {
    for (final narrow in [false, true]) {
      testWidgets(
        'Web ${tutorials ? 'tutorial' : 'example'} subject chips and title badges '
        '${narrow ? 'at 320px with 2x text' : 'on desktop'}',
        (tester) async {
          tester.view.physicalSize = narrow
              ? const Size(320, 1000)
              : const Size(1000, 1100);
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetDevicePixelRatio);
          final stores = _Stores(directory);
          addTearDown(() async {
            await tester.pumpWidget(const SizedBox.shrink());
            stores.dispose();
          });
          await tester.pumpWidget(_app(stores, scale: narrow ? 2 : 1));
          await tester.pumpAndSettle();

          // HomePage must obtain its repository from the real Web profile.
          // Both retained tabs use the same factory-produced product source.
          final navigation = narrow
              ? find.byType(NavigationBar)
              : find.byType(NavigationRail);
          await tester.tap(
            find.descendant(
              of: navigation,
              matching: find.byIcon(
                tutorials ? Icons.menu_book_outlined : Icons.code_outlined,
              ),
            ),
          );
          await tester.pump();
          await tester.pump(const Duration(milliseconds: 350));
          final tab = tutorials
              ? find.byType(LocalTutorialsTab)
              : find.byType(ExampleCodeTab);
          await _waitForCatalog(tester, tab);
          expect(
            MediaQuery.textScalerOf(tester.element(tab)).scale(10),
            narrow ? 20 : 10,
          );
          await _expectCount(tester, tab, tutorials: tutorials, count: 481);
          for (final subject in _subjectCounts.keys) {
            final chip = find.descendant(
              of: tab,
              matching: find.byKey(ValueKey('content-language-$subject')),
            );
            expect(chip, findsOneWidget, reason: '$subject subject chip');
            expect(
              find.descendant(
                of: chip,
                matching: find.text(_subjectLabels[subject]!),
              ),
              findsOneWidget,
            );
          }

          // CSS and JavaScript must remain separate from the executable HTML
          // format, including the deliberately unequal JavaScript total.
          for (final subject in ['css', 'javascript', 'html']) {
            await _tapControl(
              tester,
              tab,
              find.byKey(ValueKey('content-language-$subject')),
            );
            await _expectCount(
              tester,
              tab,
              tutorials: tutorials,
              count: _subjectCounts[subject]!,
            );
            await _tapControl(
              tester,
              tab,
              find.byKey(const ValueKey('content-language-all')),
            );
            await _expectCount(tester, tab, tutorials: tutorials, count: 481);
            await _tapControl(
              tester,
              tab,
              find.byKey(ValueKey('content-language-$subject')),
            );

            final title = tutorials
                ? catalog.tutorials
                      .firstWhere((entry) => entry.language == subject)
                      .lessons
                      .single
                      .title
                : catalog.examples
                      .firstWhere((entry) => entry.language == subject)
                      .title;
            final query = find.descendant(
              of: tab,
              matching: find.byKey(const ValueKey('content-query')),
            );
            await _showControl(tester, tab, query);
            await tester.enterText(query, title);
            await tester.pumpAndSettle();
            await _expectCount(tester, tab, tutorials: tutorials, count: 1);
            final row = find.descendant(
              of: tab,
              matching: find.widgetWithText(ListTile, title),
            );
            await tester.scrollUntilVisible(
              row,
              180,
              scrollable: _contentScrollable(tab),
            );
            _expectBadgeText(row, _subjectLabels[subject]!);
            await tester.tap(row);
            await tester.pumpAndSettle();
            _expectBadgeText(find.byType(AppBar), _subjectLabels[subject]!);

            // The visible subject badge must not alter the executable format
            // passed to the real code/import controls.
            // Scroll the real button rather than RawTooltip's layout surrogate,
            // whose bounds do not represent the tappable action at 2x text.
            final importButton = find.descendant(
              of: find.byType(CodeSnippet),
              matching: find.widgetWithIcon(
                IconButton,
                Icons.edit_note_outlined,
              ),
            );
            await tester.scrollUntilVisible(
              importButton,
              250,
              scrollable: find
                  .descendant(
                    of: find.byType(ListView).first,
                    matching: find.byType(Scrollable),
                  )
                  .first,
            );
            await tester.ensureVisible(importButton);
            await tester.pumpAndSettle();
            expect(importButton.hitTestable(), findsOneWidget);
            expect(find.byTooltip('Import into editor'), findsOneWidget);
            expect(
              find.descendant(
                of: find.byType(CodeSnippet),
                matching: find.text('html'),
              ),
              findsOneWidget,
            );
            await tester.tap(importButton);
            await tester.pumpAndSettle();
            expect(find.text('index.html'), findsOneWidget);
            await tester.tap(find.widgetWithText(TextButton, 'Cancel'));
            await tester.pumpAndSettle();
            await tester.pageBack();
            await tester.pumpAndSettle();

            await _tapControl(
              tester,
              tab,
              find.byKey(const ValueKey('content-reset')),
            );
            await _expectCount(tester, tab, tutorials: tutorials, count: 481);
            expect(find.byKey(const ValueKey('content-reset')), findsNothing);
            expect(tester.takeException(), isNull);
          }
          _expectProductAssetRequests(assetRequests);
        },
      );
    }
  }
}

MaterialApp _app(_Stores stores, {required double scale}) => MaterialApp(
  locale: const Locale('en'),
  supportedLocales: StudioLocalizations.supportedLocales,
  localizationsDelegates: const [StudioLocalizations.delegate],
  builder: (context, child) => MediaQuery(
    data: MediaQuery.of(context).copyWith(textScaler: TextScaler.linear(scale)),
    child: child!,
  ),
  home: HomePage(
    store: stores.projects,
    auth: stores.auth,
    settings: stores.settings,
  ),
);

Future<void> _waitForCatalog(WidgetTester tester, Finder tab) async {
  final query = find.descendant(
    of: tab,
    matching: find.byKey(const ValueKey('content-query')),
  );
  for (var attempt = 0; attempt < 500; attempt++) {
    // Repository parsing runs in a real isolate and examples load real local
    // storage; fake clock advancement alone cannot complete either operation.
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
    await tester.pump(const Duration(milliseconds: 30));
    if (query.evaluate().isNotEmpty) return;
  }
  fail('The real WebForge catalog did not appear');
}

Finder _contentScrollable(Finder tab) => find
    .descendant(
      of: find.descendant(of: tab, matching: find.byType(ListView)).first,
      matching: find.byType(Scrollable),
    )
    .first;

Future<void> _showControl(
  WidgetTester tester,
  Finder tab,
  Finder control,
) async {
  await tester.scrollUntilVisible(
    control,
    -220,
    scrollable: _contentScrollable(tab),
  );
  await tester.ensureVisible(control);
  await tester.pumpAndSettle();
}

Future<void> _tapControl(
  WidgetTester tester,
  Finder tab,
  Finder matching,
) async {
  final control = find.descendant(of: tab, matching: matching);
  await _showControl(tester, tab, control);
  await tester.tap(control);
  await tester.pumpAndSettle();
}

Future<void> _expectCount(
  WidgetTester tester,
  Finder tab, {
  required bool tutorials,
  required int count,
}) async {
  final label = find.descendant(
    of: tab,
    matching: find.text('$count ${tutorials ? 'lessons' : 'examples'}'),
  );
  await _showControl(tester, tab, label);
  expect(label, findsOneWidget);
}

void _expectBadgeText(Finder parent, String label) {
  final badge = find.descendant(
    of: parent,
    matching: find.byType(LanguageBadge),
  );
  expect(badge, findsOneWidget);
  expect(
    find.descendant(of: badge, matching: find.text(label)),
    findsOneWidget,
  );
}

void _expectProductAssetRequests(List<String> requests) {
  for (final asset in [
    WebForgeContentRepository.tutorialAsset,
    WebForgeContentRepository.exampleAsset,
  ]) {
    expect(requests, contains('packages/qfli_web/$asset'));
  }
  expect(
    requests.where((key) => key.contains('packages/qfli_studio_core/assets/')),
    isEmpty,
  );
}

class _Stores {
  _Stores(Directory directory)
    : projects = ProjectStore(
        storageFile: File('${directory.path}/projects.json'),
      ),
      auth = AuthStore(storageFile: File('${directory.path}/auth.json')),
      settings = SettingsStore(
        storageFile: File('${directory.path}/settings.json'),
      );

  final ProjectStore projects;
  final AuthStore auth;
  final SettingsStore settings;

  void dispose() {
    projects.dispose();
    auth.dispose();
    settings.dispose();
  }
}

class _TemporaryPaths extends PathProviderPlatform {
  _TemporaryPaths(this.path);

  final String path;

  @override
  Future<String?> getApplicationSupportPath() async => path;

  @override
  Future<String?> getApplicationDocumentsPath() async => path;

  @override
  Future<String?> getExternalStoragePath() async => path;
}
