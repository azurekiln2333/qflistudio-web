import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:qfli_studio_core/content/content_repository.dart';

/// WebForge's product-owned offline content source.
///
/// The shared core aggregates every language's curriculum into one pair of
/// assets. WebForge shipped against those for a while, but the HTML/CSS/JS
/// slice there is machine-generated filler: 300 tutorials reuse 24 backend
/// titles and a single `explain` paragraph, and the 100 HTML examples are the
/// same document modulo a number (see
/// `.trellis/tasks/10-15-webforge-content-curriculum/research/content-audit.md`).
///
/// This repository reads WebForge's own curriculum instead. It implements the
/// unchanged core [ContentRepository] contract and reuses the core JSON parser,
/// so the shell, `LocalContentAdapter` and every offline page keep working. The
/// shared aggregate is left untouched for the other products that read it.
///
/// Wiring: `StudioProfile.contentRepositoryFactory = WebForgeContentRepository.new`
/// in `lib/main.dart` (owned elsewhere; the exact diff is recorded in the task
/// research). Without that line the shell falls back to the shared assets.
class WebForgeContentRepository implements ContentRepository {
  WebForgeContentRepository({AssetBundle? bundle})
    : _bundle = bundle ?? rootBundle;

  /// Product asset paths, declared in `pubspec.yaml`.
  static const tutorialAsset = 'assets/content/tutorials.json';
  static const exampleAsset = 'assets/content/examples.json';

  final AssetBundle _bundle;
  Future<ContentCatalog>? _catalogFuture;

  @override
  Future<ContentCatalog> load() => _catalogFuture ??= _load();

  @override
  Future<List<TutorialContent>> tutorials({
    ContentFilter filter = const ContentFilter(),
  }) async {
    final catalog = await load();
    return [
      for (final tutorial in catalog.tutorials)
        if (filter.matches(tutorial)) tutorial,
    ];
  }

  @override
  Future<List<ExampleContent>> examples({
    ContentFilter filter = const ContentFilter(),
  }) async {
    final catalog = await load();
    return [
      for (final example in catalog.examples)
        if (filter.matches(example)) example,
    ];
  }

  Future<ContentCatalog> _load() async {
    final sources = await Future.wait([
      _loadString(tutorialAsset),
      _loadString(exampleAsset),
    ]);
    // Parse off the UI isolate, mirroring AssetContentRepository.
    return compute(
      _parseCatalog,
      sources,
      debugLabel: 'parse-webforge-content',
    );
  }

  /// Loads an asset, tolerating the `packages/<pkg>/` prefix Flutter adds when
  /// the same path could be resolved through a dependency.
  Future<String> _loadString(String asset) async {
    final keys = <String>['packages/qfli_web/$asset', asset];
    final failures = <String>[];
    for (final key in keys) {
      try {
        return await _bundle.loadString(key);
      } on FlutterError catch (error) {
        failures.add('$key: ${error.message}');
      } on Exception catch (error) {
        failures.add('$key: $error');
      }
    }
    throw WebForgeContentAssetException(asset, failures);
  }
}

ContentCatalog _parseCatalog(List<String> sources) => ContentCatalog.fromJson(
  tutorialsSource: sources[0],
  examplesSource: sources[1],
);

/// Raised when WebForge's own content assets cannot be read.
class WebForgeContentAssetException implements Exception {
  const WebForgeContentAssetException(this.asset, this.failures);

  final String asset;
  final List<String> failures;

  @override
  String toString() =>
      'Unable to load WebForge content asset $asset: ${failures.join(' | ')}';
}
