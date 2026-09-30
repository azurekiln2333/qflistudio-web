import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/local_web_server.dart';
import 'package:qfli_studio_core/store/project_store.dart';

import '../services/web_dev_server.dart';
import '../services/web_project_config.dart';

class WebToolsPage extends StatefulWidget {
  const WebToolsPage({super.key, required this.store});

  final ProjectStore store;

  @override
  State<WebToolsPage> createState() => _WebToolsPageState();
}

class _WebToolsPageState extends State<WebToolsPage> {
  WebDevServer? _server;
  StreamSubscription<WebRequestEvent>? _requests;
  StreamSubscription<String>? _debug;
  final _log = <String>[];
  String? _selectedPath;
  bool _busy = false;

  @override
  void dispose() {
    unawaited(_requests?.cancel());
    unawaited(_debug?.cancel());
    final server = _server;
    if (server != null) unawaited(server.stop());
    super.dispose();
  }

  void _append(String line) {
    if (!mounted) return;
    setState(() {
      _log.add(line);
      if (_log.length > 200) _log.removeRange(0, _log.length - 200);
    });
  }

  Future<void> _stop() async {
    if (_busy) return;
    final server = _server;
    if (server == null) return;
    setState(() => _busy = true);
    await _requests?.cancel();
    await _debug?.cancel();
    await server.stop();
    if (mounted) {
      setState(() {
        _server = null;
        _busy = false;
      });
    }
  }

  Future<void> _start(String path) async {
    if (_busy || _server != null) return;
    setState(() => _busy = true);
    try {
      final server = await WebDevServer.start(path);
      if (!mounted) {
        await server.stop();
        return;
      }
      _requests = server.requests.listen((event) => _append(event.toString()));
      _debug = server.debugStream.listen(_append);
      setState(() {
        _server = server;
        _busy = false;
      });
      _append('服务已启动 ${server.url}');
    } catch (error) {
      if (!mounted) return;
      setState(() => _busy = false);
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('启动失败：$error')));
    }
  }

  Future<void> _openBrowser() async {
    final url = _server?.url;
    if (url == null) return;
    try {
      if (Platform.isAndroid ||
          Platform.isIOS ||
          Platform.operatingSystem == 'ohos') {
        await const MethodChannel(
          'qflistudio/platform',
        ).invokeMethod<void>('openUrl', {'url': url});
      } else {
        await UrlOpener.open(url);
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('无法打开浏览器：$error')));
      }
    }
  }

  Future<void> _editSettings(String path) async {
    final saved = await showDialog<bool>(
      context: context,
      builder: (_) => _WebProjectSettingsDialog(projectPath: path),
    );
    if (saved == true) _append('项目服务配置已保存');
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Web 工具'),
          bottom: const TabBar(
            tabs: [
              Tab(text: '服务器'),
              Tab(text: 'HTTP'),
              Tab(text: '编解码'),
            ],
          ),
        ),
        body: TabBarView(
          children: [_serverTab(), const _HttpTool(), const _TextTool()],
        ),
      ),
    );
  }

  Widget _serverTab() {
    return ListenableBuilder(
      listenable: widget.store,
      builder: (context, _) {
        final projects = widget.store.projects
            .where((p) => !p.isCloud)
            .toList();
        final path = projects.any((p) => p.path == _selectedPath)
            ? _selectedPath
            : projects.isEmpty
            ? null
            : projects.first.path;
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    key: ValueKey(path),
                    initialValue: path,
                    decoration: const InputDecoration(
                      labelText: '项目',
                      border: OutlineInputBorder(),
                    ),
                    items: [
                      for (final project in projects)
                        DropdownMenuItem(
                          value: project.path,
                          child: Text(
                            project.name,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                    ],
                    onChanged: _server == null && !_busy
                        ? (value) => setState(() => _selectedPath = value)
                        : null,
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  tooltip: '项目服务设置',
                  onPressed: path == null || _busy || _server != null
                      ? null
                      : () => _editSettings(path),
                  icon: const Icon(Icons.tune),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                FilledButton.icon(
                  onPressed: path == null || _busy || _server != null
                      ? null
                      : () => _start(path),
                  icon: const Icon(Icons.play_arrow),
                  label: const Text('启动'),
                ),
                const SizedBox(width: 8),
                OutlinedButton.icon(
                  onPressed: _busy || _server == null ? null : _stop,
                  icon: const Icon(Icons.stop),
                  label: const Text('停止'),
                ),
                if (_busy) ...[
                  const SizedBox(width: 12),
                  const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ],
              ],
            ),
            if (_server case final server?) ...[
              const SizedBox(height: 18),
              Row(
                children: [
                  Expanded(child: SelectableText(server.url)),
                  IconButton(
                    tooltip: '复制地址',
                    onPressed: () =>
                        Clipboard.setData(ClipboardData(text: server.url)),
                    icon: const Icon(Icons.copy),
                  ),
                  IconButton(
                    tooltip: '在浏览器打开',
                    onPressed: _openBrowser,
                    icon: const Icon(Icons.open_in_browser),
                  ),
                ],
              ),
            ],
            const SizedBox(height: 20),
            Row(
              children: [
                Text('请求与控制台', style: Theme.of(context).textTheme.titleMedium),
                const Spacer(),
                IconButton(
                  tooltip: '清空记录',
                  onPressed: _log.isEmpty ? null : () => setState(_log.clear),
                  icon: const Icon(Icons.clear_all),
                ),
              ],
            ),
            const Divider(),
            for (final line in _log.reversed)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 5),
                child: SelectableText(
                  line,
                  style: const TextStyle(fontFamily: 'monospace'),
                ),
              ),
          ],
        );
      },
    );
  }
}

class _ProxyDraft {
  _ProxyDraft(String prefix, String target)
    : prefix = TextEditingController(text: prefix),
      target = TextEditingController(text: target);

  final TextEditingController prefix;
  final TextEditingController target;

  void dispose() {
    prefix.dispose();
    target.dispose();
  }
}

class _WebProjectSettingsDialog extends StatefulWidget {
  const _WebProjectSettingsDialog({required this.projectPath});

  final String projectPath;

  @override
  State<_WebProjectSettingsDialog> createState() =>
      _WebProjectSettingsDialogState();
}

class _WebProjectSettingsDialogState extends State<_WebProjectSettingsDialog> {
  final _root = TextEditingController();
  final _port = TextEditingController(text: '0');
  final _proxies = <_ProxyDraft>[];
  final _removedProxies = <_ProxyDraft>[];
  Map<String, dynamic> _original = {};
  bool _spaFallback = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    try {
      final file = File(p.join(widget.projectPath, '.qfli', 'web.json'));
      if (file.existsSync() && file.lengthSync() > 256 * 1024) {
        throw const FormatException('Web 配置文件过大');
      }
      final decoded = file.existsSync()
          ? jsonDecode(file.readAsStringSync())
          : <String, dynamic>{};
      if (decoded is! Map<String, dynamic>) {
        throw const FormatException('Web 配置必须是 JSON 对象');
      }
      _original = decoded;
      _root.text = decoded['root'] as String? ?? '';
      _port.text = '${decoded['port'] ?? 0}';
      _spaFallback = decoded['spaFallback'] as bool? ?? false;
      for (final item in decoded['proxies'] as List? ?? const []) {
        final rule = item as Map<String, dynamic>;
        _proxies.add(
          _ProxyDraft(rule['prefix'] as String, rule['target'] as String),
        );
      }
      WebProjectConfig.parse(widget.projectPath, decoded);
    } catch (error) {
      _error = '$error';
    }
  }

  void _save() {
    final port = int.tryParse(_port.text.trim());
    if (port == null) {
      setState(() => _error = '端口必须是 0 到 65535 的整数');
      return;
    }
    final data = Map<String, dynamic>.from(_original)
      ..remove('root')
      ..remove('port')
      ..remove('spaFallback')
      ..remove('proxies');
    if (_root.text.trim().isNotEmpty) data['root'] = _root.text.trim();
    if (port != 0) data['port'] = port;
    data['spaFallback'] = _spaFallback;
    data['proxies'] = [
      for (final draft in _proxies)
        {
          'prefix': draft.prefix.text.trim(),
          'target': draft.target.text.trim(),
        },
    ];
    try {
      WebProjectConfig.parse(widget.projectPath, data);
      final file = File(p.join(widget.projectPath, '.qfli', 'web.json'));
      file.parent.createSync(recursive: true);
      file.writeAsStringSync(
        const JsonEncoder.withIndent('  ').convert(data),
        flush: true,
      );
      Navigator.of(context).pop(true);
    } catch (error) {
      setState(() => _error = '$error');
    }
  }

  @override
  void dispose() {
    _root.dispose();
    _port.dispose();
    for (final draft in [..._proxies, ..._removedProxies]) {
      draft.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('项目服务设置'),
      content: SizedBox(
        width: 540,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextField(
                controller: _root,
                decoration: const InputDecoration(
                  labelText: '站点目录',
                  hintText: '自动识别',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _port,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: '端口（0 为自动分配）',
                  border: OutlineInputBorder(),
                ),
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('SPA 路由回退'),
                value: _spaFallback,
                onChanged: (value) => setState(() => _spaFallback = value),
              ),
              const Divider(),
              Row(
                children: [
                  Text('API 代理', style: Theme.of(context).textTheme.titleSmall),
                  const Spacer(),
                  IconButton(
                    tooltip: '添加代理',
                    onPressed: () =>
                        setState(() => _proxies.add(_ProxyDraft('', ''))),
                    icon: const Icon(Icons.add),
                  ),
                ],
              ),
              for (final draft in _proxies)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          children: [
                            TextField(
                              controller: draft.prefix,
                              decoration: const InputDecoration(
                                labelText: '路径前缀',
                                hintText: '/api',
                                border: OutlineInputBorder(),
                              ),
                            ),
                            const SizedBox(height: 8),
                            TextField(
                              controller: draft.target,
                              keyboardType: TextInputType.url,
                              decoration: const InputDecoration(
                                labelText: '目标 URL',
                                hintText: 'http://127.0.0.1:3000/',
                                border: OutlineInputBorder(),
                              ),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        tooltip: '删除代理',
                        onPressed: () => setState(() {
                          _proxies.remove(draft);
                          _removedProxies.add(draft);
                        }),
                        icon: const Icon(Icons.delete_outline),
                      ),
                    ],
                  ),
                ),
              if (_error != null)
                Text(
                  _error!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('取消'),
        ),
        FilledButton(onPressed: _save, child: const Text('保存')),
      ],
    );
  }
}

class _HttpTool extends StatefulWidget {
  const _HttpTool();

  @override
  State<_HttpTool> createState() => _HttpToolState();
}

class _HttpToolState extends State<_HttpTool> {
  final _url = TextEditingController();
  final _headers = TextEditingController();
  final _body = TextEditingController();
  String _method = 'GET';
  String? _result;
  bool _busy = false;
  HttpClient? _client;

  @override
  void dispose() {
    _client?.close(force: true);
    _url.dispose();
    _headers.dispose();
    _body.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final method = _method;
    final body = _body.text;
    final uri = Uri.tryParse(_url.text.trim());
    if (uri == null ||
        !{'http', 'https'}.contains(uri.scheme) ||
        uri.host.isEmpty) {
      setState(() => _result = '请输入有效的 HTTP(S) 地址');
      return;
    }
    final Map<String, dynamic> headers;
    try {
      final decoded = _headers.text.trim().isEmpty
          ? <String, dynamic>{}
          : jsonDecode(_headers.text);
      if (decoded is! Map<String, dynamic> ||
          decoded.values.any((value) => value is! String)) {
        throw const FormatException('请求头必须是字符串映射');
      }
      headers = decoded;
    } catch (error) {
      setState(() => _result = '请求头格式错误：$error');
      return;
    }
    setState(() {
      _busy = true;
      _result = null;
    });
    final client = HttpClient()
      ..connectionTimeout = const Duration(seconds: 10);
    _client = client;
    final started = DateTime.now();
    try {
      final outgoing = await client
          .openUrl(method, uri)
          .timeout(const Duration(seconds: 10));
      headers.forEach(
        (key, value) => outgoing.headers.set(key, value as String),
      );
      if (method != 'GET' && method != 'HEAD') outgoing.write(body);
      final incoming = await outgoing.close().timeout(
        const Duration(seconds: 20),
      );
      final bytes = <int>[];
      await for (final chunk in incoming.timeout(const Duration(seconds: 20))) {
        bytes.addAll(chunk);
        if (bytes.length > 2 * 1024 * 1024) {
          throw const FormatException('响应超过 2 MB');
        }
      }
      final headerLines = <String>[];
      incoming.headers.forEach(
        (name, values) => headerLines.add('$name: ${values.join(', ')}'),
      );
      final elapsed = DateTime.now().difference(started).inMilliseconds;
      if (mounted) {
        setState(
          () => _result =
              '${incoming.statusCode} ${incoming.reasonPhrase}  $elapsed ms\n'
              '${headerLines.join('\n')}\n\n${utf8.decode(bytes, allowMalformed: true)}',
        );
      }
    } catch (error) {
      if (mounted) setState(() => _result = '请求失败：$error');
    } finally {
      client.close(force: true);
      if (identical(_client, client)) _client = null;
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        TextField(
          controller: _url,
          keyboardType: TextInputType.url,
          decoration: const InputDecoration(
            labelText: 'URL',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'GET', label: Text('GET')),
              ButtonSegment(value: 'POST', label: Text('POST')),
              ButtonSegment(value: 'PUT', label: Text('PUT')),
              ButtonSegment(value: 'PATCH', label: Text('PATCH')),
              ButtonSegment(value: 'DELETE', label: Text('DELETE')),
            ],
            selected: {_method},
            onSelectionChanged: (value) =>
                setState(() => _method = value.first),
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _headers,
          maxLines: 3,
          decoration: const InputDecoration(
            labelText: '请求头 JSON',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _body,
          maxLines: 4,
          enabled: _method != 'GET',
          decoration: const InputDecoration(
            labelText: '请求体',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        Align(
          alignment: Alignment.centerLeft,
          child: FilledButton.icon(
            onPressed: _busy ? null : _send,
            icon: const Icon(Icons.send),
            label: const Text('发送'),
          ),
        ),
        if (_busy) const LinearProgressIndicator(),
        if (_result case final result?) ...[
          const SizedBox(height: 16),
          Row(
            children: [
              Text('响应', style: Theme.of(context).textTheme.titleMedium),
              const Spacer(),
              IconButton(
                tooltip: '复制响应',
                onPressed: () => Clipboard.setData(ClipboardData(text: result)),
                icon: const Icon(Icons.copy),
              ),
            ],
          ),
          const Divider(),
          SelectableText(
            result,
            style: const TextStyle(fontFamily: 'monospace'),
          ),
        ],
      ],
    );
  }
}

class _TextTool extends StatefulWidget {
  const _TextTool();

  @override
  State<_TextTool> createState() => _TextToolState();
}

class _TextToolState extends State<_TextTool> {
  final _input = TextEditingController();
  String _kind = 'JSON';
  String? _output;

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  void _convert(bool encode) {
    try {
      final value = _input.text;
      final result = switch ((_kind, encode)) {
        ('JSON', true) => const JsonEncoder.withIndent(
          '  ',
        ).convert(jsonDecode(value)),
        ('JSON', false) => jsonEncode(jsonDecode(value)),
        ('URL', true) => Uri.encodeComponent(value),
        ('URL', false) => Uri.decodeComponent(value),
        ('Base64', true) => base64Encode(utf8.encode(value)),
        ('Base64', false) => utf8.decode(base64Decode(value.trim())),
        _ => value,
      };
      setState(() => _output = result);
    } catch (error) {
      setState(() => _output = '转换失败：$error');
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        SegmentedButton<String>(
          segments: const [
            ButtonSegment(value: 'JSON', label: Text('JSON')),
            ButtonSegment(value: 'URL', label: Text('URL')),
            ButtonSegment(value: 'Base64', label: Text('Base64')),
          ],
          selected: {_kind},
          onSelectionChanged: (value) => setState(() {
            _kind = value.first;
            _output = null;
          }),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _input,
          minLines: 6,
          maxLines: 12,
          decoration: const InputDecoration(
            labelText: '输入',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          children: [
            FilledButton(
              onPressed: () => _convert(true),
              child: Text(_kind == 'JSON' ? '格式化' : '编码'),
            ),
            OutlinedButton(
              onPressed: () => _convert(false),
              child: Text(_kind == 'JSON' ? '压缩' : '解码'),
            ),
          ],
        ),
        if (_output case final output?) ...[
          const SizedBox(height: 16),
          Row(
            children: [
              Text('结果', style: Theme.of(context).textTheme.titleMedium),
              const Spacer(),
              IconButton(
                tooltip: '复制结果',
                onPressed: () => Clipboard.setData(ClipboardData(text: output)),
                icon: const Icon(Icons.copy),
              ),
            ],
          ),
          const Divider(),
          SelectableText(
            output,
            style: const TextStyle(fontFamily: 'monospace'),
          ),
        ],
      ],
    );
  }
}
