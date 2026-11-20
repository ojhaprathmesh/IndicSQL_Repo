import 'package:material_ui/material_ui.dart';

import '../conversation_store.dart';
import '../models.dart';

class ConversationHistoryScreen extends StatefulWidget {
  const ConversationHistoryScreen({
    super.key,
    required this.store,
    required this.onOpen,
  });

  final ConversationStore store;
  final ValueChanged<Conversation> onOpen;

  @override
  State<ConversationHistoryScreen> createState() =>
      _ConversationHistoryScreenState();
}

class _ConversationHistoryScreenState extends State<ConversationHistoryScreen> {
  final _searchController = TextEditingController();
  late Future<List<Conversation>> _conversations;

  @override
  void initState() {
    super.initState();
    _conversations = widget.store.listConversations();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _reload() {
    setState(() {
      _conversations = widget.store.listConversations(search: _searchController.text);
    });
  }

  Future<void> _rename(Conversation conversation) async {
    final controller = TextEditingController(text: conversation.title);
    final title = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Rename conversation'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(labelText: 'Conversation name'),
          onSubmitted: (value) => Navigator.pop(context, value),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () => Navigator.pop(context, controller.text),
            child: const Text('Save'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (title == null || !mounted) return;
    try {
      await widget.store.renameConversation(conversation.id, title);
      _reload();
    } catch (error) {
      _showError('$error');
    }
  }

  Future<void> _delete(Conversation conversation) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete conversation?'),
        content: Text('“${conversation.title}” and its local messages will be deleted from this device.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton.tonal(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await widget.store.deleteConversation(conversation.id);
      _reload();
    } catch (error) {
      _showError('$error');
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: TextField(
            controller: _searchController,
            decoration: InputDecoration(
              hintText: 'Search saved conversations',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: IconButton(
                tooltip: 'Clear search',
                onPressed: () {
                  _searchController.clear();
                  _reload();
                },
                icon: const Icon(Icons.clear),
              ),
              border: const OutlineInputBorder(),
            ),
            onChanged: (_) => _reload(),
          ),
        ),
        Expanded(
          child: FutureBuilder<List<Conversation>>(
            future: _conversations,
            builder: (context, snapshot) {
              if (snapshot.hasError) {
                return _HistoryMessage(
                  text: 'Could not load saved conversations: ${snapshot.error}',
                  onRetry: _reload,
                );
              }
              if (!snapshot.hasData) {
                return const Center(child: CircularProgressIndicator());
              }
              final items = snapshot.data!;
              if (items.isEmpty) {
                return Center(
                  child: Text(
                    _searchController.text.isEmpty
                        ? 'Your saved conversations will appear here.'
                        : 'No conversations match this search.',
                  ),
                );
              }
              return ListView.separated(
                padding: const EdgeInsets.fromLTRB(12, 0, 12, 20),
                itemCount: items.length,
                separatorBuilder: (_, _) => const SizedBox(height: 4),
                itemBuilder: (context, index) {
                  final conversation = items[index];
                  return Card(
                    child: ListTile(
                      leading: const CircleAvatar(child: Icon(Icons.forum_outlined)),
                      title: Text(conversation.title, maxLines: 2, overflow: TextOverflow.ellipsis),
                      subtitle: Text(
                        'Updated ${MaterialLocalizations.of(context).formatShortDate(conversation.updatedAt.toLocal())}',
                      ),
                      onTap: () => widget.onOpen(conversation),
                      trailing: PopupMenuButton<String>(
                        tooltip: 'Conversation actions',
                        onSelected: (action) {
                          if (action == 'rename') _rename(conversation);
                          if (action == 'delete') _delete(conversation);
                        },
                        itemBuilder: (_) => const [
                          PopupMenuItem(value: 'rename', child: Text('Rename')),
                          PopupMenuItem(value: 'delete', child: Text('Delete')),
                        ],
                      ),
                    ),
                  );
                },
              );
            },
          ),
        ),
      ],
    );
  }
}

class _HistoryMessage extends StatelessWidget {
  const _HistoryMessage({required this.text, required this.onRetry});

  final String text;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(text, textAlign: TextAlign.center),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
}
