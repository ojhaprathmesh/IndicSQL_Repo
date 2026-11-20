import 'package:material_ui/material_ui.dart';

import '../api_client.dart';

class SchemaScreen extends StatefulWidget {
  const SchemaScreen({super.key, required this.api});

  final IndicSqlApi api;

  @override
  State<SchemaScreen> createState() => _SchemaScreenState();
}

class _SchemaScreenState extends State<SchemaScreen> {
  final _searchController = TextEditingController();
  late Future<Map<String, dynamic>> _schemas;

  @override
  void initState() {
    super.initState();
    _schemas = widget.api.fetchSchemas();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _reload() => setState(() => _schemas = widget.api.fetchSchemas());

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _schemas,
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return _SchemaState(
            message: 'Could not load the live schema catalog.\n${snapshot.error}',
            icon: Icons.cloud_off,
            action: OutlinedButton.icon(
              onPressed: _reload,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          );
        }
        if (!snapshot.hasData) {
          return const Center(child: CircularProgressIndicator());
        }

        final response = snapshot.data!;
        final rawTables = response['tables'];
        if (rawTables is! Map) {
          return const _SchemaState(message: 'The schema endpoint returned an unexpected catalog.');
        }
        final tables = rawTables.entries
            .where((entry) => entry.value is Map)
            .map((entry) => MapEntry(
                  '${entry.key}',
                  Map<String, dynamic>.from(entry.value as Map),
                ))
            .where((entry) {
              final query = _searchController.text.toLowerCase();
              if (query.isEmpty) return true;
              return entry.key.toLowerCase().contains(query) ||
                  '${entry.value['domain'] ?? ''}'.toLowerCase().contains(query) ||
                  '${entry.value['description'] ?? ''}'.toLowerCase().contains(query);
            })
            .toList()
          ..sort((a, b) => a.key.compareTo(b.key));

        return Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 6),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _searchController,
                      decoration: const InputDecoration(
                        hintText: 'Search live tables and domains',
                        prefixIcon: Icon(Icons.search),
                        border: OutlineInputBorder(),
                      ),
                      onChanged: (_) => setState(() {}),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Refresh schemas',
                    onPressed: _reload,
                    icon: const Icon(Icons.refresh),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 6),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text('${response['count'] ?? rawTables.length} backend tables'),
              ),
            ),
            Expanded(
              child: tables.isEmpty
                  ? const Center(child: Text('No tables match this search.'))
                  : ListView.builder(
                      padding: const EdgeInsets.fromLTRB(12, 0, 12, 16),
                      itemCount: tables.length,
                      itemBuilder: (context, index) {
                        final table = tables[index];
                        final data = table.value;
                        final columns = _columns(data['columns']);
                        return Card(
                          child: ExpansionTile(
                            title: Text(table.key, style: const TextStyle(fontFamily: 'monospace')),
                            subtitle: Text(
                              [
                                if (data['domain'] != null) '${data['domain']}',
                                if (data['row_count'] != null) '${data['row_count']} rows',
                                '${columns.length} columns',
                              ].join(' · '),
                            ),
                            children: [
                              if (data['description'] != null)
                                Padding(
                                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                                  child: Align(
                                    alignment: Alignment.centerLeft,
                                    child: Text('${data['description']}'),
                                  ),
                                ),
                              if (columns.isEmpty)
                                const ListTile(title: Text('No column metadata returned.'))
                              else
                                ...columns.map(
                                  (column) => ListTile(
                                    dense: true,
                                    title: Text(column.key, style: const TextStyle(fontFamily: 'monospace')),
                                    trailing: Text(
                                      column.value,
                                      style: Theme.of(context).textTheme.labelSmall,
                                    ),
                                  ),
                                ),
                            ],
                          ),
                        );
                      },
                    ),
            ),
          ],
        );
      },
    );
  }

  List<MapEntry<String, String>> _columns(Object? value) {
    if (value is Map) {
      return value.entries.map((entry) => MapEntry('${entry.key}', '${entry.value}')).toList();
    }
    if (value is List) {
      return value.whereType<Map>().map((column) {
        return MapEntry(
          '${column['name'] ?? 'unknown'}',
          '${column['type'] ?? 'unknown'}',
        );
      }).toList();
    }
    return [];
  }
}

class _SchemaState extends StatelessWidget {
  const _SchemaState({required this.message, this.icon, this.action});

  final String message;
  final IconData? icon;
  final Widget? action;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (icon != null) Icon(icon, size: 36),
              Text(message, textAlign: TextAlign.center),
              if (action != null) ...[const SizedBox(height: 12), action!],
            ],
          ),
        ),
      );
}
