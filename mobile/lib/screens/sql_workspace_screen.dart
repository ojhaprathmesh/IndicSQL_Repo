import 'dart:convert';
import 'dart:io';

import 'package:material_ui/material_ui.dart';
import 'package:flutter/services.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:re_editor/re_editor.dart';
import 'package:share_plus/share_plus.dart';

import '../api_client.dart';
import '../widgets/result_table.dart';
import '../widgets/sql_editor.dart';

class SqlWorkspaceScreen extends StatefulWidget {
  const SqlWorkspaceScreen({
    super.key,
    required this.api,
    this.initialSql = '',
  });

  final IndicSqlApi api;
  final String initialSql;

  @override
  State<SqlWorkspaceScreen> createState() => _SqlWorkspaceScreenState();
}

class _SqlWorkspaceScreenState extends State<SqlWorkspaceScreen> {
  late final CodeLineEditingController _controller =
      CodeLineEditingController.fromText(widget.initialSql);
  Map<String, dynamic>? _inspection;
  bool _isRunning = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _controller.addListener(_onSqlChanged);
  }

  void _onSqlChanged() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _controller.removeListener(_onSqlChanged);
    _controller.dispose();
    super.dispose();
  }

  Future<void> _execute() async {
    final sql = _controller.text.trim();
    if (sql.isEmpty || _isRunning) return;
    setState(() {
      _isRunning = true;
      _error = null;
      _inspection = null;
    });
    try {
      final result = await widget.api.inspectSql(sql);
      if (mounted) setState(() => _inspection = result);
    } catch (error) {
      if (mounted) setState(() => _error = '$error');
    } finally {
      if (mounted) setState(() => _isRunning = false);
    }
  }

  Future<void> _copySql() async {
    await Clipboard.setData(ClipboardData(text: _controller.text));
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('SQL copied to clipboard')),
      );
    }
  }

  Future<void> _copyResults(Map<String, dynamic> result) async {
    final columns = (result['columns'] as List? ?? const []).map((value) => '$value').toList();
    final rows = (result['rows'] as List? ?? const []).whereType<List>();
    final tsv = [
      columns.join('\t'),
      ...rows.map((row) => row.map((cell) => '${cell ?? ''}').join('\t')),
    ].join('\n');
    await Clipboard.setData(ClipboardData(text: tsv));
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Query results copied as TSV')),
      );
    }
  }

  Future<void> _exportResults(Map<String, dynamic> result) async {
    final columns = (result['columns'] as List? ?? const []).map((value) => '$value').toList();
    final rows = (result['rows'] as List? ?? const []).whereType<List>();
    String escape(Object? value) {
      final text = value == null ? '' : '$value';
      return '"${text.replaceAll('"', '""')}"';
    }

    final csv = [columns, ...rows]
        .map((row) => row.map(escape).join(','))
        .join('\r\n');
    final directory = await getTemporaryDirectory();
    final file = File(p.join(directory.path, 'indicsql-results.csv'));
    await file.writeAsString('\uFEFF$csv', encoding: utf8);
    await Share.shareXFiles(
      [XFile(file.path, mimeType: 'text/csv')],
      text: 'IndicSQL query results',
    );
  }

  @override
  Widget build(BuildContext context) {
    final inspection = _inspection;
    final execution = inspection?['execution_result'];
    final valid = inspection?['valid'] == true;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          'Run read-only DuckDB SQL against the configured IndicSQL sandbox.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 12),
        SqlEditor(controller: _controller, height: 300),
        const SizedBox(height: 10),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            OutlinedButton.icon(
              onPressed: _controller.text.trim().isEmpty ? null : _copySql,
              icon: const Icon(Icons.copy),
              label: const Text('Copy SQL'),
            ),
            FilledButton.icon(
              onPressed: _isRunning || _controller.text.trim().isEmpty
                  ? null
                  : _execute,
              icon: _isRunning
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.play_arrow),
              label: Text(_isRunning ? 'Running…' : 'Validate & run'),
            ),
          ],
        ),
        const SizedBox(height: 12),
        const Card(
          child: Padding(
            padding: EdgeInsets.all(12),
            child: Text(
              'The backend accepts read-only SELECT/WITH statements and enforces a result limit. '
              'Execution is performed by the existing DuckDB sandbox.',
            ),
          ),
        ),
        if (_error != null)
          _Notice(message: _error!, isError: true)
        else if (inspection != null) ...[
          _Notice(
            message: inspection['message'] as String? ?? 'SQL inspection completed.',
            isError: !valid,
          ),
          if (valid && execution is Map<String, dynamic>) ...[
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Execution time: ${execution['execution_time_ms'] ?? 'not reported'} ms',
                    style: Theme.of(context).textTheme.labelMedium,
                  ),
                ),
                IconButton(
                  tooltip: 'Copy results',
                  onPressed: () => _copyResults(execution),
                  icon: const Icon(Icons.copy_all),
                ),
                IconButton(
                  tooltip: 'Export CSV',
                  onPressed: () => _exportResults(execution),
                  icon: const Icon(Icons.ios_share),
                ),
              ],
            ),
            ResultTable(result: execution),
          ],
        ],
      ],
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice({required this.message, required this.isError});

  final String message;
  final bool isError;

  @override
  Widget build(BuildContext context) {
    final color = isError ? Theme.of(context).colorScheme.error : Colors.green.shade800;
    return Card(
      color: isError
          ? Theme.of(context).colorScheme.errorContainer
          : Colors.green.shade50,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(isError ? Icons.error_outline : Icons.check_circle_outline, color: color),
            const SizedBox(width: 10),
            Expanded(child: Text(message, style: TextStyle(color: color))),
          ],
        ),
      ),
    );
  }
}
