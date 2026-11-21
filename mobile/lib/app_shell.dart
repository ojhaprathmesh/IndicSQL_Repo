import 'package:material_ui/material_ui.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api_client.dart';
import 'conversation_store.dart';
import 'models.dart';
import 'screens/analytics_screen.dart';
import 'screens/chat_screen.dart';
import 'screens/conversation_history_screen.dart';
import 'screens/schema_screen.dart';
import 'screens/sql_workspace_screen.dart';

enum _Module {
  chat,
  history,
  sql,
  sources,
  analytics,
  benchmark,
  language,
  models,
  failures,
  pipeline,
  settings,
  documentation,
}

class IndicSqlHome extends StatefulWidget {
  const IndicSqlHome({
    super.key,
    required this.api,
    required this.store,
    required this.preferences,
  });

  final IndicSqlApi api;
  final ConversationStore store;
  final SharedPreferences preferences;

  @override
  State<IndicSqlHome> createState() => _IndicSqlHomeState();
}

class _IndicSqlHomeState extends State<IndicSqlHome> {
  _Module _module = _Module.chat;
  Conversation? _conversation;
  List<StoredMessage> _messages = [];
  String _sqlDraft = '';
  String? _backendError;
  bool _isSending = false;
  bool _backendConnected = false;

  @override
  void initState() {
    super.initState();
    _checkBackend();
  }

  Future<void> _checkBackend() async {
    try {
      final healthy = await widget.api.checkHealth();
      if (mounted) {
        setState(() {
          _backendConnected = healthy;
          _backendError = healthy
              ? null
              : 'The API health endpoint returned an unexpected status.';
        });
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          _backendConnected = false;
          _backendError = '$error';
        });
      }
    }
  }

  Future<QueryReply?> _send(String question, String language) async {
    if (_isSending) return null;
    var conversation = _conversation;
    try {
      conversation ??= await widget.store.createConversation();
      await widget.store.addMessage(
        conversationId: conversation.id,
        role: 'user',
        content: question,
      );
      if (!mounted) return null;
      setState(() {
        _conversation = conversation;
        _isSending = true;
      });
      await _reloadMessages(conversation.id);

      try {
        final reply = await widget.api.ask(
          question,
          conversationId: conversation.id,
          language: language,
        );
        await widget.store.addMessage(
          conversationId: conversation.id,
          role: 'assistant',
          content: reply.answer.isEmpty
              ? 'The backend returned no verbalized answer.'
              : reply.answer,
          payload: reply.json,
        );
        if (mounted) setState(() => _backendConnected = true);
        await _reloadMessages(conversation.id);
        return reply;
      } catch (error) {
        await widget.store.addMessage(
          conversationId: conversation.id,
          role: 'assistant',
          content: '$error',
          isError: true,
        );
        if (mounted) {
          setState(() {
            _backendConnected = false;
            _backendError = '$error';
          });
        }
        await _reloadMessages(conversation.id);
        return null;
      }
    } catch (error) {
      _showMessage('Could not save this conversation: $error');
      return null;
    } finally {
      if (mounted) setState(() => _isSending = false);
    }
  }

  Future<void> _reloadMessages(String conversationId) async {
    final messages = await widget.store.loadMessages(conversationId);
    if (mounted) setState(() => _messages = messages);
  }

  Future<void> _openConversation(Conversation conversation) async {
    try {
      final messages = await widget.store.loadMessages(conversation.id);
      if (!mounted) return;
      setState(() {
        _conversation = conversation;
        _messages = messages;
        _module = _Module.chat;
      });
    } catch (error) {
      _showMessage('Could not open this conversation: $error');
    }
  }

  void _newConversation() {
    setState(() {
      _conversation = null;
      _messages = [];
      _module = _Module.chat;
    });
  }

  void _openSql(String sql) {
    setState(() {
      _sqlDraft = sql;
      _module = _Module.sql;
    });
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  String get _title => switch (_module) {
    _Module.chat => 'Ask Data',
    _Module.history => 'Conversations',
    _Module.sql => 'SQL Workspace',
    _Module.sources => 'Data Sources',
    _Module.analytics => 'Analytics Dashboard',
    _Module.benchmark => 'Benchmarks & Evaluation',
    _Module.language => 'Language Analytics',
    _Module.models => 'Model Comparison',
    _Module.failures => 'Failure Analysis',
    _Module.pipeline => 'Query Pipeline',
    _Module.settings => 'Settings',
    _Module.documentation => 'Documentation',
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 66,
        titleSpacing: 16,
        title: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.secondaryContainer,
                borderRadius: BorderRadius.circular(13),
              ),
              child: Icon(
                Icons.query_stats_rounded,
                color: Theme.of(context).colorScheme.secondary,
                size: 21,
              ),
            ),
            const SizedBox(width: 11),
            Expanded(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleSmall
                        ?.copyWith(fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 3),
                  Row(
                    children: [
                      Container(
                        width: 7,
                        height: 7,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: _backendConnected
                              ? Theme.of(context).colorScheme.secondary
                              : _backendError == null
                              ? const Color(0xffc28a2c)
                              : Theme.of(context).colorScheme.error,
                        ),
                      ),
                      const SizedBox(width: 6),
                      Flexible(
                        child: Text(
                          _backendConnected
                              ? 'Backend connected'
                              : _backendError == null
                              ? 'Checking backend…'
                              : 'Backend unavailable',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context).textTheme.labelSmall
                              ?.copyWith(
                                color: _backendConnected
                                    ? Theme.of(context).colorScheme.secondary
                                    : Theme.of(context)
                                          .colorScheme
                                          .onSurfaceVariant,
                              ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          if (_module == _Module.chat)
            IconButton(
              tooltip: 'New conversation',
              onPressed: _newConversation,
              icon: const Icon(Icons.add_comment_outlined),
            ),
          if (!_backendConnected)
            IconButton(
              tooltip: 'Retry backend connection',
              onPressed: _checkBackend,
              icon: const Icon(Icons.sync),
            ),
        ],
      ),
      drawer: _navigationDrawer(context),
      body: _body(),
    );
  }

  Widget _navigationDrawer(BuildContext context) {
    final modules = _Module.values;
    return NavigationDrawer(
      selectedIndex: modules.indexOf(_module),
      onDestinationSelected: (index) {
        setState(() => _module = modules[index]);
        Navigator.pop(context);
      },
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
          child: Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(20),
              gradient: const LinearGradient(
                colors: [Color(0xff174762), Color(0xff23827d)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  backgroundColor: Color(0x33ffffff),
                  child: Text(
                    'IS',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                SizedBox(height: 14),
                Text(
                  'IndicSQL Studio',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                SizedBox(height: 3),
                Text(
                  'Insight from data, in your language',
                  style: TextStyle(color: Color(0xffd9eeee), fontSize: 12),
                ),
              ],
            ),
          ),
        ),
        const Padding(
          padding: EdgeInsets.fromLTRB(28, 8, 20, 6),
          child: Text(
            'WORKSPACE',
            style: TextStyle(
              color: Color(0xff6b7f90),
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.1,
            ),
          ),
        ),
        const NavigationDrawerDestination(
          icon: Icon(Icons.chat_bubble_outline),
          selectedIcon: Icon(Icons.chat_bubble),
          label: Text('Ask Data'),
        ),
        const NavigationDrawerDestination(
          icon: Icon(Icons.history),
          label: Text('Conversations'),
        ),
        const NavigationDrawerDestination(
          icon: Icon(Icons.code),
          label: Text('SQL Workspace'),
        ),
        const Divider(indent: 28, endIndent: 28, height: 24),
        const Padding(
          padding: EdgeInsets.fromLTRB(28, 0, 20, 6),
          child: Text(
            'INSIGHTS',
            style: TextStyle(
              color: Color(0xff6b7f90),
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.1,
            ),
          ),
        ),
        const NavigationDrawerDestination(
          icon: Icon(Icons.storage_outlined),
          label: Text('Data Sources'),
        ),
        const NavigationDrawerDestination(
          icon: Icon(Icons.analytics_outlined),
          label: Text('Analytics Dashboard'),
        ),
        const NavigationDrawerDestination(
          icon: Icon(Icons.fact_check_outlined),
          label: Text('Benchmarks / Evaluation'),
        ),
        const NavigationDrawerDestination(
          icon: Icon(Icons.language),
          label: Text('Language Analytics'),
        ),
        const NavigationDrawerDestination(
          icon: Icon(Icons.compare_arrows),
          label: Text('Model Comparison'),
        ),
        const NavigationDrawerDestination(
          icon: Icon(Icons.bug_report_outlined),
          label: Text('Failure Analysis'),
        ),
        const NavigationDrawerDestination(
          icon: Icon(Icons.account_tree_outlined),
          label: Text('Query Pipeline'),
        ),
        const Divider(indent: 28, endIndent: 28, height: 24),
        const NavigationDrawerDestination(
          icon: Icon(Icons.settings_outlined),
          label: Text('Settings'),
        ),
        const NavigationDrawerDestination(
          icon: Icon(Icons.menu_book_outlined),
          label: Text('Documentation'),
        ),
      ],
    );
  }

  Widget _body() => switch (_module) {
    _Module.chat => ChatScreen(
      key: ValueKey(_conversation?.id ?? 'new'),
      messages: _messages,
      isSending: _isSending,
      onSend: _send,
      onOpenSql: _openSql,
      backendConnected: _backendConnected,
    ),
    _Module.history => ConversationHistoryScreen(
      store: widget.store,
      onOpen: _openConversation,
    ),
    _Module.sql => SqlWorkspaceScreen(
      key: ValueKey(_sqlDraft),
      api: widget.api,
      initialSql: _sqlDraft,
      backendConnected: _backendConnected,
    ),
    _Module.sources => SchemaScreen(api: widget.api),
    _Module.analytics => AnalyticsScreen(api: widget.api, section: 'overview'),
    _Module.benchmark => AnalyticsScreen(api: widget.api, section: 'benchmark'),
    _Module.language => AnalyticsScreen(api: widget.api, section: 'language'),
    _Module.models => AnalyticsScreen(api: widget.api, section: 'models'),
    _Module.failures => AnalyticsScreen(api: widget.api, section: 'failures'),
    _Module.pipeline => _PipelineScreen(
      messages: _messages,
      onOpenChat: _newConversation,
    ),
    _Module.settings => _SettingsScreen(
      api: widget.api,
      preferences: widget.preferences,
      onBackendStatusChanged: (connected, error) {
        if (!mounted) return;
        setState(() {
          _backendConnected = connected;
          _backendError = error;
        });
      },
    ),
    _Module.documentation => const _DocumentationScreen(),
  };
}

class _PipelineScreen extends StatelessWidget {
  const _PipelineScreen({required this.messages, required this.onOpenChat});

  final List<StoredMessage> messages;
  final VoidCallback onOpenChat;

  @override
  Widget build(BuildContext context) {
    final traced = messages
        .where(
          (message) =>
              message.role == 'assistant' &&
              message.payload?['audit_trace'] is List,
        )
        .toList();
    if (traced.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.account_tree_outlined, size: 40),
              const SizedBox(height: 12),
              const Text(
                'Run a question to inspect its real agent audit trace.',
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: onOpenChat,
                icon: const Icon(Icons.chat),
                label: const Text('Start a new chat'),
              ),
            ],
          ),
        ),
      );
    }
    return ListView(
      padding: const EdgeInsets.all(12),
      children: [
        for (final message in traced)
          Card(
            child: ExpansionTile(
              title: Text(message.payload?['raw_query'] as String? ?? 'Query'),
              subtitle: Text(
                'Query ID: ${message.payload?['query_id'] ?? 'not reported'}',
              ),
              children: [
                for (final step
                    in (message.payload?['audit_trace'] as List)
                        .whereType<Map>())
                  ListTile(
                    leading: const Icon(Icons.check_circle_outline),
                    title: Text('${step['agent'] ?? 'Agent'}'),
                    subtitle: Text(
                      '${step['action'] ?? 'Action'} · ${step['status'] ?? 'status not reported'}',
                    ),
                  ),
              ],
            ),
          ),
      ],
    );
  }
}

class _SettingsScreen extends StatefulWidget {
  const _SettingsScreen({
    required this.api,
    required this.preferences,
    required this.onBackendStatusChanged,
  });

  final IndicSqlApi api;
  final SharedPreferences preferences;
  final void Function(bool connected, String? error) onBackendStatusChanged;

  @override
  State<_SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<_SettingsScreen> {
  late final TextEditingController _urlController = TextEditingController(
    text: widget.api.baseUrl,
  );
  bool _checking = false;
  String? _error;
  String? _status;

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _saveAndCheck() async {
    final uri = Uri.tryParse(_urlController.text.trim());
    if (uri == null ||
        !{'http', 'https'}.contains(uri.scheme) ||
        uri.host.isEmpty) {
      setState(
        () => _error = 'Enter a valid http:// or https:// API base URL.',
      );
      return;
    }
    setState(() {
      _checking = true;
      _error = null;
      _status = null;
    });
    try {
      widget.api.baseUrl = uri.toString().replaceAll(RegExp(r'/+$'), '');
      await widget.preferences.setString('api_base_url', widget.api.baseUrl);
      final connected = await widget.api.checkHealth();
      if (!connected) {
        throw const ApiException(
          'The backend health check did not return status=ok.',
        );
      }
      if (mounted) {
        setState(() => _status = 'Connected to ${widget.api.baseUrl}');
        widget.onBackendStatusChanged(true, null);
      }
    } catch (error) {
      if (mounted) {
        setState(() => _error = '$error');
        widget.onBackendStatusChanged(false, '$error');
      }
    } finally {
      if (mounted) setState(() => _checking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Connection', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        TextField(
          controller: _urlController,
          keyboardType: TextInputType.url,
          decoration: const InputDecoration(
            labelText: 'FastAPI base URL',
            hintText: 'http://10.0.2.2:8000',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 10),
        Align(
          alignment: Alignment.centerLeft,
          child: FilledButton.icon(
            onPressed: _checking ? null : _saveAndCheck,
            icon: _checking
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.link),
            label: Text(_checking ? 'Checking…' : 'Save and check connection'),
          ),
        ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              _error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ),
        if (_status != null)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              _status!,
              style: TextStyle(color: Colors.green.shade800),
            ),
          ),
        const SizedBox(height: 18),
        const Card(
          child: Padding(
            padding: EdgeInsets.all(14),
            child: Text(
              'Android emulator: http://10.0.2.2:8000. USB-connected phone: http://127.0.0.1:8000 '
              'after running adb reverse tcp:8000 tcp:8000. For Wi-Fi, use the computer’s LAN IP. '
              'Use HTTPS for non-local deployments.',
            ),
          ),
        ),
        const Divider(height: 30),
        Text('Local data', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 6),
        const Text(
          'Conversations are stored in this app’s private SQLite database. They are not uploaded or synchronized. '
          'Questions are sent to the configured backend when submitted.',
        ),
      ],
    );
  }
}

class _DocumentationScreen extends StatelessWidget {
  const _DocumentationScreen();

  @override
  Widget build(BuildContext context) {
    const languages =
        'English, Hindi, Hinglish, Marathi, Bengali, Tamil, and Telugu.';
    return ListView(
      padding: const EdgeInsets.all(16),
      children: const [
        Card(
          child: ListTile(
            title: Text('What IndicSQL does'),
            subtitle: Text(
              'The backend uses language detection, cross-lingual schema linking, SQL synthesis, '
              'read-only validation, DuckDB execution, and response verbalization.',
            ),
          ),
        ),
        Card(
          child: ListTile(
            title: Text('Supported languages'),
            subtitle: Text(languages),
          ),
        ),
        Card(
          child: ListTile(
            title: Text('Data and execution'),
            subtitle: Text(
              'The app uses the live schema catalog and the backend’s registered Parquet datasets. '
              'Queries are processed by the existing FastAPI service; SQL execution is bounded and read-only.',
            ),
          ),
        ),
        Card(
          child: ListTile(
            title: Text('Known limitations'),
            subtitle: Text(
              'Conversation history is local to this device. The backend detects language automatically unless '
              'a supported override is selected. Voice input uses the phone’s speech-recognition service; '
              'voice answers require a matching system TTS voice. Benchmark dashboards show stored evaluation artifacts.',
            ),
          ),
        ),
      ],
    );
  }
}
