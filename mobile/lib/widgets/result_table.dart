import 'package:material_ui/material_ui.dart';

class ResultTable extends StatelessWidget {
  const ResultTable({super.key, required this.result, this.maxRows = 100});

  final Map<String, dynamic> result;
  final int maxRows;

  @override
  Widget build(BuildContext context) {
    final columns = (result['columns'] as List? ?? const []).map((value) => '$value').toList();
    final rows = (result['rows'] as List? ?? const []).whereType<List>().toList();
    if (columns.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '${result['row_count'] ?? rows.length} result rows',
          style: Theme.of(context).textTheme.labelLarge,
        ),
        const SizedBox(height: 8),
        if (rows.isEmpty)
          const Text('The query returned no rows.')
        else
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              columns: columns.map((column) => DataColumn(label: Text(column))).toList(),
              rows: rows.take(maxRows).map((row) {
                return DataRow(
                  cells: List.generate(
                    columns.length,
                    (index) => DataCell(
                      SelectableText(index < row.length ? '${row[index] ?? '—'}' : '—'),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        if (rows.length > maxRows)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text('Showing the first $maxRows of ${rows.length} returned rows.'),
          ),
      ],
    );
  }
}
