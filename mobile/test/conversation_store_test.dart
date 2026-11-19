import 'package:flutter_test/flutter_test.dart';
import 'package:indicsql_studio/conversation_store.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  test('persists conversation titles, message payloads, and errors', () async {
    final store = ConversationStore(databasePath: inMemoryDatabasePath);
    await store.initialize();
    try {
      final conversation = await store.createConversation();
      await store.addMessage(
        conversationId: conversation.id,
        role: 'user',
        content: 'Show total farmers',
      );
      await store.addMessage(
        conversationId: conversation.id,
        role: 'assistant',
        content: 'There are 12.',
        payload: {'generated_sql': 'SELECT 12'},
      );
      await store.addMessage(
        conversationId: conversation.id,
        role: 'assistant',
        content: 'Backend unavailable',
        isError: true,
      );

      final messages = await store.loadMessages(conversation.id);
      final conversations = await store.listConversations();

      expect(conversations.single.title, 'Show total farmers');
      expect(messages, hasLength(3));
      expect(messages[1].payload?['generated_sql'], 'SELECT 12');
      expect(messages[2].isError, isTrue);
    } finally {
      await store.close();
    }
  });
}
