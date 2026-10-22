import 'dart:async';

import 'package:flutter/material.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/store/project_store.dart';

import '../../services/web_markup_inspector.dart';
import 'web_tools_panel.dart';

/// Resource/link inspection for a real project document.
///
/// Picks one `.html` file from a local project and resolves every `href`,
/// `src`, `srcset` and CSS `url()` against the project root, reporting local
/// files, missing files, inline values and — important for an offline product —
/// every external URL. Directory discovery is asynchronous and bounded; disk
/// analysis runs on another isolate so a large project cannot freeze typing.
class WebSourceInspectorInlineView extends StatefulWidget {
  const WebSourceInspectorInlineView({super.key, required this.store});

  static const String title = '文档资源检查';

  final ProjectStore store;

  @override
  State<WebSourceInspectorInlineView> createState() =>
      _WebSourceInspectorInlineViewState();
}

class _WebSourceInspectorInlineViewState
    extends State<WebSourceInspectorInlineView> {
  static const int _maxListedReferences = 40;

  String? _projectPath;
  String? _documentPath;
  List<String> _documents = const [];
  WebDocumentInspection? _inspection;
  bool _scanning = false;
  bool _truncated = false;
  int _generation = 0;

  @override
  void initState() {
    super.initState();
    widget.store.addListener(_syncProjects);
    _syncProjects();
  }

  @override
  void didUpdateWidget(WebSourceInspectorInlineView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!identical(oldWidget.store, widget.store)) {
      oldWidget.store.removeListener(_syncProjects);
      widget.store.addListener(_syncProjects);
      _syncProjects();
    }
  }

  @override
  void dispose() {
    _generation++;
    widget.store.removeListener(_syncProjects);
    super.dispose();
  }

  List<Project> get _projects => [
    for (final project in widget.store.projects)
      if (!project.isCloud && project.path.isNotEmpty) project,
  ];

  void _syncProjects() {
    final projects = _projects;
    final current = projects.any((project) => project.path == _projectPath)
        ? _projectPath
        : projects.isEmpty
        ? null
        : projects.first.path;
    if (current != _projectPath || _documents.isEmpty) {
      _projectPath = current;
      unawaited(_scanDocuments());
    }
  }

  Future<void> _scanDocuments() async {
    final generation = ++_generation;
    final projectPath = _projectPath;
    if (projectPath == null) {
      setState(() {
        _documents = const [];
        _documentPath = null;
        _inspection = null;
        _scanning = false;
        _truncated = false;
      });
      return;
    }
    setState(() {
      _scanning = true;
      _inspection = null;
      _documents = const [];
    });
    final scan = await WebMarkupInspector.scanDocuments(projectPath);
    if (!mounted || generation != _generation) return;
    final found = scan.documents;
    final selected = found.contains(_documentPath)
        ? _documentPath
        : found.isEmpty
        ? null
        : found.first;
    final inspection = selected == null
        ? null
        : await WebMarkupInspector.inspectFileAsync(
            selected,
            rootPath: projectPath,
          );
    if (!mounted || generation != _generation) return;
    setState(() {
      _documents = found;
      _documentPath = selected;
      _inspection = inspection;
      _scanning = false;
      _truncated = scan.truncated;
    });
  }

  Future<void> _inspectSelected() async {
    final document = _documentPath;
    final project = _projectPath;
    if (document == null || project == null) return;
    final generation = ++_generation;
    setState(() {
      _scanning = true;
      _inspection = null;
    });
    final inspection = await WebMarkupInspector.inspectFileAsync(
      document,
      rootPath: project,
    );
    if (!mounted || generation != _generation) return;
    setState(() {
      _inspection = inspection;
      _scanning = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ListenableBuilder(
      listenable: widget.store,
      builder: (context, _) {
        if (_projects.isEmpty) {
          return Text(
            '还没有本地项目。先在项目页导入或新建一个站点，再回来检查引用。',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          );
        }
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    key: ValueKey('project-$_projectPath'),
                    initialValue: _projectPath,
                    isExpanded: true,
                    decoration: const InputDecoration(
                      labelText: '项目',
                      isDense: true,
                      border: OutlineInputBorder(),
                    ),
                    items: [
                      for (final project in _projects)
                        DropdownMenuItem(
                          value: project.path,
                          child: Text(
                            project.name,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                    ],
                    onChanged: (value) {
                      setState(() => _projectPath = value);
                      unawaited(_scanDocuments());
                    },
                  ),
                ),
                IconButton(
                  tooltip: '重新扫描项目文档',
                  onPressed: _scanning ? null : _refresh,
                  icon: const Icon(Icons.refresh),
                ),
              ],
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              key: ValueKey(
                'document-$_projectPath-$_documentPath-${_documents.length}',
              ),
              initialValue: _documents.contains(_documentPath)
                  ? _documentPath
                  : null,
              isExpanded: true,
              decoration: InputDecoration(
                labelText: '文档',
                helperText: _scanning
                    ? '正在本机扫描…'
                    : '扫描 ${_documents.length} 个 HTML 文件${_truncated ? '（已达扫描上限）' : ''}',
                isDense: true,
                border: const OutlineInputBorder(),
              ),
              items: [
                for (final document in _documents)
                  DropdownMenuItem(
                    value: document,
                    child: Text(
                      p.relative(document, from: _projectPath),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
              ],
              onChanged: _scanning
                  ? null
                  : (value) {
                      setState(() => _documentPath = value);
                      unawaited(_inspectSelected());
                    },
            ),
            if (_scanning)
              const Padding(
                padding: EdgeInsets.only(top: 8),
                child: LinearProgressIndicator(),
              ),
            if (_documents.isEmpty && !_scanning)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  '项目中还没有 .html 文件',
                  style: theme.textTheme.bodySmall,
                ),
              ),
            if (_inspection case final inspection?) ...[
              const SizedBox(height: 10),
              WebSummaryChips(
                entries: [
                  ('引用', inspection.references.length),
                  ('本地', inspection.localCount),
                  ('缺失', inspection.missingCount),
                  ('外部', inspection.externalCount),
                  ('内联', inspection.inlineCount),
                ],
              ),
              if (inspection.externalCount > 0)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        Icons.cloud_off_outlined,
                        size: 18,
                        color: theme.colorScheme.error,
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          '这些外部引用在离线版中不会加载，请改为本地资源。',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.error,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              WebToolOutput(
                title: '问题与提示',
                child: WebFindingList(findings: inspection.findings),
              ),
              if (inspection.references.isNotEmpty)
                WebToolOutput(
                  title: '引用明细',
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      for (final reference in inspection.references.take(
                        _maxListedReferences,
                      ))
                        WebValueRow(
                          label:
                              '${reference.kindLabel} · ${reference.origin == null ? '' : '${reference.origin}:'}${reference.location.label}',
                          value:
                              '${reference.element}[${reference.attribute}] '
                              '${reference.rawValue}'
                              '${reference.resolvedPath == null ? '' : ' → ${reference.resolvedPath}'}',
                          color: reference.isNetwork || reference.isMissing
                              ? theme.colorScheme.error
                              : null,
                        ),
                      if (inspection.references.length > _maxListedReferences)
                        Text(
                          '还有 ${inspection.references.length - _maxListedReferences} 条引用未显示',
                          style: theme.textTheme.bodySmall,
                        ),
                    ],
                  ),
                ),
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(
                  inspection.isOfflineClean
                      ? '已识别的静态引用均可本机加载，可直接离线预览；脚本动态请求需在预览日志中确认。'
                      : '离线检查未通过：请处理问题或未检查的引用后再预览。',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: inspection.isOfflineClean
                        ? theme.colorScheme.primary
                        : theme.colorScheme.error,
                  ),
                ),
              ),
            ],
          ],
        );
      },
    );
  }

  Future<void> _refresh() => _scanDocuments();
}
