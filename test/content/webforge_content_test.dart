import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/content/content_repository.dart';
import 'package:qfli_studio_core/content/content_validator.dart';
import 'package:qfli_studio_core/services/code_import_service.dart';
import 'package:qfli_web/content/webforge_content_repository.dart';

/// WebForge 专属内容的契约测试。
///
/// 这些测试直接读取产品资源文件，验证：数量、类型覆盖、结构合法、ID 唯一、
/// 字段非空、正文无重复、示例与教程关联完整。它是内容质量的守门人——
/// 任何占位或套壳内容都会在这里失败。
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late String tutorialsSource;
  late String examplesSource;

  setUpAll(() {
    // Tests run from the product root; read the real shipped assets.
    final root = Directory.current;
    tutorialsSource = File(
      p.join(root.path, 'assets', 'content', 'tutorials.json'),
    ).readAsStringSync();
    examplesSource = File(
      p.join(root.path, 'assets', 'content', 'examples.json'),
    ).readAsStringSync();
  });

  ContentCatalog loadCatalog() => ContentCatalog.fromJson(
    tutorialsSource: tutorialsSource,
    examplesSource: examplesSource,
  );

  group('shipped assets', () {
    test('parse with the core catalog parser', () {
      final catalog = loadCatalog();
      expect(catalog.schemaVersion, 1);
      expect(catalog.tutorials, isNotEmpty);
      expect(catalog.examples, isNotEmpty);
    });

    test('ship at least 100 tutorials and 100 examples', () {
      final catalog = loadCatalog();
      expect(catalog.tutorials.length, greaterThanOrEqualTo(100));
      expect(catalog.examples.length, greaterThanOrEqualTo(100));
    });

    test('cover html, css and javascript', () {
      final catalog = loadCatalog();
      for (final subject in const ['html', 'css', 'javascript']) {
        expect(
          catalog.tutorials.where((t) => t.language == subject).length,
          greaterThanOrEqualTo(100),
          reason: 'missing $subject tutorials',
        );
        expect(
          catalog.examples.where((e) => e.language == subject).length,
          greaterThanOrEqualTo(100),
          reason: 'missing $subject examples',
        );
      }
    });

    test('pass the core release validator for web types', () {
      final result = ContentCatalogValidator.validate(
        loadCatalog(),
        enforceReleaseMinimum: true,
        requiredTypes: const {'html'},
      );
      expect(
        result.issues,
        isEmpty,
        reason: result.issues.map((i) => i.toString()).join('\n'),
      );
    });

    test('all subjects import as complete previewable HTML documents', () {
      final catalog = loadCatalog();
      for (final entry in [...catalog.tutorials, ...catalog.examples]) {
        expect(entry.type, 'html', reason: entry.id);
        expect(
          CodeImportService.suggestedFileName(entry.type),
          endsWith('.html'),
        );
      }
      for (final example in catalog.examples) {
        expect(
          example.code.toLowerCase(),
          contains('<!doctype html>'),
          reason: example.id,
        );
        expect(
          example.code.toLowerCase(),
          contains('</html>'),
          reason: example.id,
        );
      }
    });
  });

  group('quality: no placeholders', () {
    test('tutorial titles are distinct', () {
      final titles = loadCatalog().tutorials.map((t) => t.title).toList();
      expect(titles.toSet().length, titles.length);
    });

    test('every lesson explain and output is distinct', () {
      final catalog = loadCatalog();
      final explains = <String>[];
      final outputs = <String>[];
      for (final t in catalog.tutorials) {
        for (final l in t.lessons) {
          explains.add(l.explain);
          outputs.add(l.output);
        }
      }
      expect(
        explains.toSet().length,
        explains.length,
        reason: 'reused explain',
      );
      expect(outputs.toSet().length, outputs.length, reason: 'reused output');
    });

    test('example bodies are distinct after number normalisation', () {
      String normalise(String s) => s
          .replaceAll(RegExp(r'\d+'), 'N')
          .replaceAll(RegExp(r'\s+'), ' ')
          .trim();
      final bodies = loadCatalog().examples
          .map((e) => normalise(e.code))
          .toList();
      expect(bodies.toSet().length, bodies.length, reason: 'template bodies');
    });

    test('every lesson is substantive', () {
      final catalog = loadCatalog();
      for (final t in catalog.tutorials) {
        for (final l in t.lessons) {
          expect(l.code.trim().length, greaterThan(40), reason: l.id);
          expect(l.explain.trim().length, greaterThan(40), reason: l.id);
          expect(l.concepts, isNotEmpty, reason: l.id);
          expect(l.exercises, isNotEmpty, reason: l.id);
          expect(l.pitfalls, isNotEmpty, reason: l.id);
        }
      }
    });
  });

  group('referential integrity', () {
    test('ids are unique across tutorials and examples', () {
      final catalog = loadCatalog();
      final ids = <String>[
        for (final t in catalog.tutorials) t.id,
        for (final e in catalog.examples) e.id,
      ];
      expect(ids.toSet().length, ids.length);
    });

    test('every example links to an existing lesson', () {
      final catalog = loadCatalog();
      final lessonIds = <String>{
        for (final t in catalog.tutorials)
          for (final l in t.lessons) l.id,
      };
      for (final e in catalog.examples) {
        expect(e.sourceLessonId, isNotNull, reason: e.id);
        expect(lessonIds.contains(e.sourceLessonId), isTrue, reason: e.id);
      }
    });

    test('every runnable lesson matches its complete example document', () {
      String normalize(String source) => source
          .replaceAll(
            RegExp(r'\s*<output id="webforge-check"[^>]*>ok</output>\s*'),
            '\n',
          )
          .replaceAll(RegExp(r'\s+'), ' ')
          .trim();
      final catalog = loadCatalog();
      final lessons = {
        for (final tutorial in catalog.tutorials)
          for (final lesson in tutorial.lessons) lesson.id: lesson,
      };
      expect(
        catalog.examples.map((e) => e.sourceLessonId).toSet().length,
        lessons.length,
      );
      for (final example in catalog.examples) {
        expect(
          normalize(example.code),
          normalize(lessons[example.sourceLessonId]!.code),
          reason: example.id,
        );
      }
    });

    test('example expected output is never empty', () {
      for (final e in loadCatalog().examples) {
        expect(e.expectedOutput.trim(), isNotEmpty, reason: e.id);
      }
    });
  });

  group('repository', () {
    test('loads from the product assets via a bundle', () async {
      final bundle = _StringBundle({
        WebForgeContentRepository.tutorialAsset: tutorialsSource,
        WebForgeContentRepository.exampleAsset: examplesSource,
      });
      final repo = WebForgeContentRepository(bundle: bundle);
      final catalog = await repo.load();
      expect(catalog.tutorials.length, greaterThanOrEqualTo(100));
      expect(catalog.examples.length, greaterThanOrEqualTo(100));
    });

    test('applies the shared ContentFilter semantics', () async {
      final bundle = _StringBundle({
        WebForgeContentRepository.tutorialAsset: tutorialsSource,
        WebForgeContentRepository.exampleAsset: examplesSource,
      });
      final repo = WebForgeContentRepository(bundle: bundle);
      final css = await repo.tutorials(
        filter: const ContentFilter(language: 'css'),
      );
      expect(css, isNotEmpty);
      expect(css.length, greaterThanOrEqualTo(100));
      expect(css.every((t) => t.language == 'css' && t.type == 'html'), isTrue);
      expect(
        await repo.tutorials(filter: const ContentFilter(type: 'css')),
        isEmpty,
      );

      final web = await repo.examples(
        filter: ContentFilter.forProduct('webforge'),
      );
      expect(web, isNotEmpty);
      expect(web.length, loadCatalog().examples.length);
      expect(
        web.every((e) => const {'html', 'css', 'javascript'}.contains(e.type)),
        isTrue,
      );
    });

    test('reports an explicit error for a missing asset', () async {
      final repo = WebForgeContentRepository(bundle: _StringBundle(const {}));
      await expectLater(repo.load(), throwsA(isA<Exception>()));
    });
  });
}

/// Minimal AssetBundle backed by an in-memory string map.
class _StringBundle extends CachingAssetBundle {
  _StringBundle(this._strings);

  final Map<String, String> _strings;

  @override
  Future<ByteData> load(String key) async {
    final value = _strings[key];
    if (value == null) {
      throw FlutterError('Asset not found: $key');
    }
    return ByteData.sublistView(Uint8List.fromList(utf8.encode(value)));
  }
}
