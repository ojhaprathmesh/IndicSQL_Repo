import 'dart:convert';
import 'dart:math';

import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import 'models.dart';

class ConversationStore {
  ConversationStore({this.databasePath});

  final String? databasePath;
  Database? _database;

  Future<void> initialize() async {
    final path = databasePath ?? p.join(await getDatabasesPath(), 'indicsql_studio.db');
    _database = await openDatabase(
      path,
      version: 1,
      onConfigure: (db) => db.execute('PRAGMA foreign_keys = ON'),
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
          )
        ''');
        await db.execute('''
          CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            payload_json TEXT,
            is_error INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
          )
        ''');
        await db.execute(
          'CREATE INDEX messages_conversation_order ON messages(conversation_id, id)',
        );
      },
    );
  }

  Database get _db {
    final database = _database;
    if (database == null) {
      throw StateError('ConversationStore.initialize() must be called first.');
    }
    return database;
  }

  String _newId() =>
      '${DateTime.now().microsecondsSinceEpoch}-${Random.secure().nextInt(1 << 32)}';

  Future<Conversation> createConversation({String title = 'New conversation'}) async {
    final now = DateTime.now().toUtc();
    final id = _newId();
    await _db.insert('conversations', {
      'id': id,
      'title': title,
      'created_at': now.toIso8601String(),
      'updated_at': now.toIso8601String(),
    });
    return Conversation(id: id, title: title, createdAt: now, updatedAt: now);
  }

  Future<List<Conversation>> listConversations({String search = ''}) async {
    final term = search.trim();
    final rows = await _db.query(
      'conversations',
      where: term.isEmpty ? null : 'title LIKE ?',
      whereArgs: term.isEmpty ? null : ['%$term%'],
      orderBy: 'updated_at DESC',
    );
    return rows.map(Conversation.fromMap).toList();
  }

  Future<List<StoredMessage>> loadMessages(String conversationId) async {
    final rows = await _db.query(
      'messages',
      where: 'conversation_id = ?',
      whereArgs: [conversationId],
      orderBy: 'id ASC',
    );
    return rows.map(StoredMessage.fromMap).toList();
  }

  Future<void> addMessage({
    required String conversationId,
    required String role,
    required String content,
    Map<String, dynamic>? payload,
    bool isError = false,
  }) async {
    final now = DateTime.now().toUtc().toIso8601String();
    await _db.transaction((transaction) async {
      final existingMessages = Sqflite.firstIntValue(
        await transaction.rawQuery(
          'SELECT COUNT(*) FROM messages WHERE conversation_id = ?',
          [conversationId],
        ),
      );
      await transaction.insert('messages', {
        'conversation_id': conversationId,
        'role': role,
        'content': content,
        'created_at': now,
        'payload_json': payload == null ? null : jsonEncode(payload),
        'is_error': isError ? 1 : 0,
      });
      if (existingMessages == 0 && role == 'user') {
        final title = content.replaceAll(RegExp(r'\s+'), ' ').trim();
        await transaction.update(
          'conversations',
          {'title': title.length > 72 ? '${title.substring(0, 69)}...' : title, 'updated_at': now},
          where: 'id = ?',
          whereArgs: [conversationId],
        );
      } else {
        await transaction.update(
          'conversations',
          {'updated_at': now},
          where: 'id = ?',
          whereArgs: [conversationId],
        );
      }
    });
  }

  Future<void> renameConversation(String id, String title) async {
    final normalized = title.trim();
    if (normalized.isEmpty) throw ArgumentError.value(title, 'title', 'Cannot be empty.');
    await _db.update(
      'conversations',
      {'title': normalized, 'updated_at': DateTime.now().toUtc().toIso8601String()},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> deleteConversation(String id) async {
    await _db.delete('conversations', where: 'id = ?', whereArgs: [id]);
  }

  Future<void> close() async {
    await _database?.close();
    _database = null;
  }
}
