import 'dart:convert';
import 'dart:math';

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import 'models.dart';

class ConversationStore {
  ConversationStore({this.databasePath});

  final String? databasePath;
  Database? _database;

  // In-memory fallback for web platforms where sqflite is unavailable
  final List<Map<String, dynamic>> _webConversations = [];
  final List<Map<String, dynamic>> _webMessages = [];
  int _webMsgIdSeq = 1;

  Future<void> initialize() async {
    if (kIsWeb) return;
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
    if (kIsWeb) {
      _webConversations.add({
        'id': id,
        'title': title,
        'created_at': now.toIso8601String(),
        'updated_at': now.toIso8601String(),
      });
      return Conversation(id: id, title: title, createdAt: now, updatedAt: now);
    }
    await _db.insert('conversations', {
      'id': id,
      'title': title,
      'created_at': now.toIso8601String(),
      'updated_at': now.toIso8601String(),
    });
    return Conversation(id: id, title: title, createdAt: now, updatedAt: now);
  }

  Future<List<Conversation>> listConversations({String search = ''}) async {
    final term = search.trim().toLowerCase();
    if (kIsWeb) {
      final filtered = _webConversations.where((c) {
        if (term.isEmpty) return true;
        final title = (c['title'] as String? ?? '').toLowerCase();
        return title.contains(term);
      }).toList();
      filtered.sort((a, b) => (b['updated_at'] as String).compareTo(a['updated_at'] as String));
      return filtered.map(Conversation.fromMap).toList();
    }
    final rows = await _db.query(
      'conversations',
      where: term.isEmpty ? null : 'title LIKE ?',
      whereArgs: term.isEmpty ? null : ['%$term%'],
      orderBy: 'updated_at DESC',
    );
    return rows.map(Conversation.fromMap).toList();
  }

  Future<List<StoredMessage>> loadMessages(String conversationId) async {
    if (kIsWeb) {
      final filtered = _webMessages.where((m) => m['conversation_id'] == conversationId).toList();
      filtered.sort((a, b) => (a['id'] as int).compareTo(b['id'] as int));
      return filtered.map(StoredMessage.fromMap).toList();
    }
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
    if (kIsWeb) {
      final existingCount = _webMessages.where((m) => m['conversation_id'] == conversationId).length;
      _webMessages.add({
        'id': _webMsgIdSeq++,
        'conversation_id': conversationId,
        'role': role,
        'content': content,
        'created_at': now,
        'payload_json': payload == null ? null : jsonEncode(payload),
        'is_error': isError ? 1 : 0,
      });
      final convIndex = _webConversations.indexWhere((c) => c['id'] == conversationId);
      if (convIndex != -1) {
        if (existingCount == 0 && role == 'user') {
          final title = content.replaceAll(RegExp(r'\s+'), ' ').trim();
          _webConversations[convIndex]['title'] = title.length > 72 ? '${title.substring(0, 69)}...' : title;
        }
        _webConversations[convIndex]['updated_at'] = now;
      }
      return;
    }
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
    if (kIsWeb) {
      final index = _webConversations.indexWhere((c) => c['id'] == id);
      if (index != -1) {
        _webConversations[index]['title'] = normalized;
        _webConversations[index]['updated_at'] = DateTime.now().toUtc().toIso8601String();
      }
      return;
    }
    await _db.update(
      'conversations',
      {'title': normalized, 'updated_at': DateTime.now().toUtc().toIso8601String()},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> deleteConversation(String id) async {
    if (kIsWeb) {
      _webConversations.removeWhere((c) => c['id'] == id);
      _webMessages.removeWhere((m) => m['conversation_id'] == id);
      return;
    }
    await _db.delete('conversations', where: 'id = ?', whereArgs: [id]);
  }

  Future<void> close() async {
    if (kIsWeb) {
      _webConversations.clear();
      _webMessages.clear();
      return;
    }
    await _database?.close();
    _database = null;
  }
}
