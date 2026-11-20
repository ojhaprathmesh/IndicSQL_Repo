import 'package:fl_chart/fl_chart.dart';
import 'package:material_ui/material_ui.dart';

import '../api_client.dart';

class AnalyticsScreen extends StatefulWidget {
  const AnalyticsScreen({
    super.key,
    required this.api,
    required this.section,
  });

  final IndicSqlApi api;
  final String section;

  @override
  State<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends State<AnalyticsScreen> {
  late Future<Map<String, dynamic>> _analytics;

  @override
  void initState() {
    super.initState();
    _analytics = widget.api.fetchAnalytics();
  }

  void _reload() => setState(() => _analytics = widget.api.fetchAnalytics());

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _analytics,
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.cloud_off, size: 38),
                  const SizedBox(height: 12),
                  Text(
                    'Could not load checked-in evaluation data.\n${snapshot.error}',
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    onPressed: _reload,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry'),
                  ),
                ],
              ),
            ),
          );
        }
        if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
        return _buildSection(snapshot.data!);
      },
    );
  }

  Widget _buildSection(Map<String, dynamic> data) {
    final benchmark = _map(data['benchmark']);
    final metrics = _map(benchmark['overall_metrics']);
    final scorecards = _map(benchmark['language_scorecards']);
    final failures = _map(data['failures']);
    final models = _map(_map(data['models'])['models']);

    return switch (widget.section) {
      'language' => _languageView(scorecards),
      'models' => _modelsView(models),
      'failures' => _failuresView(failures),
      'benchmark' => _benchmarkView(data, benchmark, metrics),
      _ => _overviewView(benchmark, metrics, scorecards),
    };
  }

  Widget _overviewView(
    Map<String, dynamic> benchmark,
    Map<String, dynamic> metrics,
    Map<String, dynamic> scorecards,
  ) {
    final items = _languageItems(scorecards);
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _sourceLabel('Stored unseen-benchmark report · ${benchmark['timestamp'] ?? 'date not reported'}'),
        const SizedBox(height: 12),
        _metricGrid([
          _Metric('Evaluated queries', _number(benchmark['total_queries'])),
          _Metric('Execution accuracy', _percent(metrics['execution_accuracy_pct'])),
          _Metric('Schema grounding', _percent(metrics['grounding_accuracy_pct'])),
          _Metric('Average latency', _latency(metrics['avg_latency_ms'])),
        ]),
        const SizedBox(height: 20),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Execution accuracy by language', style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 18),
                if (items.isEmpty)
                  const Text('No language scorecards were returned.')
                else
                  SizedBox(height: 230, child: _languageChart(items)),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
        const Text(
          'These are repository evaluation results, not live query telemetry.',
          style: TextStyle(fontSize: 12),
        ),
      ],
    );
  }

  Widget _benchmarkView(
    Map<String, dynamic> data,
    Map<String, dynamic> benchmark,
    Map<String, dynamic> metrics,
  ) {
    final queries = (data['benchmark_queries'] as List? ?? const [])
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
    final search = TextEditingController();
    return _BenchmarkList(
      queryCount: benchmark['total_queries'],
      metrics: metrics,
      queries: queries,
      searchController: search,
    );
  }

  Widget _languageView(Map<String, dynamic> scorecards) {
    final items = _languageItems(scorecards);
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _sourceLabel('Per-language metrics from the checked-in evaluation report.'),
        const SizedBox(height: 12),
        if (items.isEmpty)
          const _EmptyCard(message: 'No language scorecards were returned.')
        else
          Card(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columns: const [
                  DataColumn(label: Text('Language')),
                  DataColumn(label: Text('Queries')),
                  DataColumn(label: Text('Execution')),
                  DataColumn(label: Text('Grounding')),
                  DataColumn(label: Text('Latency')),
                ],
                rows: items.map((item) {
                  final metrics = item.value;
                  return DataRow(cells: [
                    DataCell(Text(_languageName(item.key))),
                    DataCell(Text(_number(metrics['total_queries']))),
                    DataCell(Text(_percent(metrics['execution_accuracy_pct']))),
                    DataCell(Text(_percent(metrics['grounding_accuracy_pct']))),
                    DataCell(Text(_latency(metrics['avg_latency_ms']))),
                  ]);
                }).toList(),
              ),
            ),
          ),
      ],
    );
  }

  Widget _modelsView(Map<String, dynamic> models) {
    final entries = models.entries
        .where((entry) => entry.value is Map)
        .map((entry) => MapEntry(entry.key, _map(entry.value)))
        .toList();
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _sourceLabel('Recorded model baseline matrix. Metrics are shown as published.'),
        const SizedBox(height: 12),
        if (entries.isEmpty)
          const _EmptyCard(message: 'No model comparison data is available.')
        else ...[
          for (final entry in entries)
            Card(
              child: ExpansionTile(
                title: Text('${entry.value['model_name'] ?? entry.key}'),
                subtitle: Text(
                  '${entry.value['provider'] ?? 'Provider not reported'} · '
                  '${entry.value['parameter_size'] ?? 'Size not reported'}',
                ),
                childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                children: [
                  _detail('Execution accuracy', _percent(_map(entry.value['execution_accuracy_pct'])['overall'])),
                  _detail('Indic average accuracy', _percent(entry.value['indic_avg_ex_pct'])),
                  _detail('Schema F1', _percent(_percentageSchemaF1(entry.value['schema_f1']))),
                  _detail('Average latency', _latency(entry.value['avg_latency_ms'])),
                  _detail('Indic-English gap', _percent(entry.value['indic_to_english_gap_delta_pct'])),
                ],
              ),
            ),
        ],
      ],
    );
  }

  Widget _failuresView(Map<String, dynamic> failures) {
    final traces = (failures['traces'] as List? ?? const [])
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _sourceLabel('Audited failure traces from the repository failure audit.'),
        const SizedBox(height: 12),
        _metricGrid([
          _Metric('Audited failures', _number(failures['total_audited_failures'])),
          _Metric('Trace records', traces.length.toString()),
        ]),
        const SizedBox(height: 12),
        if (traces.isEmpty)
          const _EmptyCard(message: 'No failure traces were returned.')
        else
          for (final trace in traces)
            Card(
              child: ExpansionTile(
                title: Text(
                  '${trace['original_question'] ?? 'Question not recorded'}',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                subtitle: Text(
                  '${trace['primary_category'] ?? 'Uncategorized'} · '
                  '${trace['language_detected'] ?? 'language unknown'}',
                ),
                childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                children: [
                  _detail('Selected table', '${trace['selected_table'] ?? 'Not reported'}'),
                  _detail('Audit finding', '${trace['exact_failure_reason'] ?? 'Not reported'}'),
                  _detail('Generated SQL', '${trace['generated_sql'] ?? 'Not reported'}'),
                ],
              ),
            ),
      ],
    );
  }

  Widget _metricGrid(List<_Metric> metrics) {
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      childAspectRatio: 1.55,
      crossAxisSpacing: 10,
      mainAxisSpacing: 10,
      children: [
        for (final metric in metrics)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(metric.label, style: Theme.of(context).textTheme.labelMedium),
                  const SizedBox(height: 6),
                  Text(metric.value, style: Theme.of(context).textTheme.titleLarge),
                ],
              ),
            ),
          ),
      ],
    );
  }

  Widget _languageChart(List<MapEntry<String, Map<String, dynamic>>> items) {
    final accent = Theme.of(context).colorScheme.primary;
    return BarChart(
      BarChartData(
        maxY: 100,
        minY: 0,
        gridData: const FlGridData(show: true, drawVerticalLine: false),
        borderData: FlBorderData(show: false),
        barGroups: [
          for (var index = 0; index < items.length; index++)
            BarChartGroupData(
              x: index,
              barRods: [
                BarChartRodData(
                  toY: _double(items[index].value['execution_accuracy_pct']),
                  width: 18,
                  color: accent,
                  borderRadius: BorderRadius.circular(4),
                ),
              ],
            ),
        ],
        titlesData: FlTitlesData(
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: true, reservedSize: 38),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 32,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index < 0 || index >= items.length) return const SizedBox.shrink();
                return SideTitleWidget(
                  meta: meta,
                  child: Text(
                    _languageShort(items[index].key),
                    style: const TextStyle(fontSize: 10),
                  ),
                );
              },
            ),
          ),
        ),
      ),
    );
  }

  List<MapEntry<String, Map<String, dynamic>>> _languageItems(Map<String, dynamic> source) =>
      source.entries
          .where((entry) => entry.value is Map)
          .map((entry) => MapEntry(entry.key, _map(entry.value)))
          .toList();

  Widget _sourceLabel(String text) => Text(
        text,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
      );

  Widget _detail(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Align(
          alignment: Alignment.centerLeft,
          child: SelectableText('$label: $value'),
        ),
      );

  static Map<String, dynamic> _map(Object? value) =>
      value is Map ? Map<String, dynamic>.from(value) : <String, dynamic>{};

  static double _double(Object? value) =>
      value is num ? value.toDouble() : double.tryParse('$value') ?? 0;

  static String _number(Object? value) =>
      value is num ? value.toStringAsFixed(value is int ? 0 : 1) : 'Not reported';

  static String _percent(Object? value) =>
      value is num ? '${value.toStringAsFixed(1)}%' : 'Not reported';

  static String _latency(Object? value) =>
      value is num ? '${value.toStringAsFixed(1)} ms' : 'Not reported';

  static Object? _percentageSchemaF1(Object? value) {
    if (value is num && value <= 1) return value * 100;
    return value;
  }

  static String _languageName(String code) => const {
        'en': 'English',
        'hi': 'Hindi',
        'hi-en': 'Hinglish',
        'mr': 'Marathi',
        'bn': 'Bengali',
        'ta': 'Tamil',
        'te': 'Telugu',
      }[code] ??
      code;

  static String _languageShort(String code) => _languageName(code).substring(0, 2);
}

class _BenchmarkList extends StatefulWidget {
  const _BenchmarkList({
    required this.queryCount,
    required this.metrics,
    required this.queries,
    required this.searchController,
  });

  final Object? queryCount;
  final Map<String, dynamic> metrics;
  final List<Map<String, dynamic>> queries;
  final TextEditingController searchController;

  @override
  State<_BenchmarkList> createState() => _BenchmarkListState();
}

class _BenchmarkListState extends State<_BenchmarkList> {
  String _search = '';

  @override
  void dispose() {
    widget.searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final filtered = widget.queries.where((query) {
      final text = '${query['query_id'] ?? ''} ${query['query'] ?? ''} ${query['target_table'] ?? ''}';
      return text.toLowerCase().contains(_search.toLowerCase());
    }).toList();
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Stored benchmark · ${widget.queryCount ?? 'query count unavailable'} questions'),
        const SizedBox(height: 10),
        _MetricCard(label: 'Execution accuracy', value: _formatMetric(widget.metrics['execution_accuracy_pct'])),
        _MetricCard(label: 'Grounding accuracy', value: _formatMetric(widget.metrics['grounding_accuracy_pct'])),
        _MetricCard(label: 'Table routing', value: _formatMetric(widget.metrics['table_routing_accuracy_pct'])),
        const SizedBox(height: 8),
        TextField(
          controller: widget.searchController,
          decoration: const InputDecoration(
            prefixIcon: Icon(Icons.search),
            hintText: 'Search benchmark questions',
            border: OutlineInputBorder(),
          ),
          onChanged: (value) => setState(() => _search = value),
        ),
        const SizedBox(height: 6),
        Text('Showing ${filtered.length} of ${widget.queries.length} stored benchmark questions.'),
        for (final query in filtered)
          Card(
            child: ExpansionTile(
              title: Text('${query['query'] ?? 'Question not provided'}'),
              subtitle: Text(
                '${query['language'] ?? 'language unknown'} · '
                '${query['domain'] ?? 'domain unknown'} · '
                '${query['target_table'] ?? 'table unknown'}',
              ),
              childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              children: [
                _detailText('Query ID', query['query_id']),
                _detailText('Difficulty', query['difficulty']),
                _detailText('Gold SQL (reference)', query['gold_sql']),
              ],
            ),
          ),
      ],
    );
  }

  static String _formatMetric(Object? value) =>
      value is num ? '${value.toStringAsFixed(1)}%' : 'Not reported';

  static Widget _detailText(String label, Object? value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Align(
          alignment: Alignment.centerLeft,
          child: SelectableText('$label: ${value ?? 'Not reported'}'),
        ),
      );
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          title: Text(label),
          trailing: Text(value, style: Theme.of(context).textTheme.titleMedium),
        ),
      );
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Center(child: Text(message, textAlign: TextAlign.center)),
        ),
      );
}

class _Metric {
  const _Metric(this.label, this.value);

  final String label;
  final String value;
}
