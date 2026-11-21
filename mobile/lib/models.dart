import 'dart:convert';

class Conversation {
  const Conversation({
    required this.id,
    required this.title,
    required this.createdAt,
    required this.updatedAt,
  });

  final String id;
  final String title;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory Conversation.fromMap(Map<String, Object?> row) => Conversation(
        id: row['id']! as String,
        title: row['title']! as String,
        createdAt: DateTime.parse(row['created_at']! as String),
        updatedAt: DateTime.parse(row['updated_at']! as String),
      );
}

class StoredMessage {
  const StoredMessage({
    this.id,
    required this.conversationId,
    required this.role,
    required this.content,
    required this.createdAt,
    this.payload,
    this.isError = false,
  });

  final int? id;
  final String conversationId;
  final String role;
  final String content;
  final DateTime createdAt;
  final Map<String, dynamic>? payload;
  final bool isError;

  factory StoredMessage.fromMap(Map<String, Object?> row) {
    final payloadJson = row['payload_json'] as String?;
    final decoded = payloadJson == null
        ? null
        : jsonDecode(payloadJson) as Map<String, dynamic>;
    return StoredMessage(
      id: row['id'] as int?,
      conversationId: row['conversation_id']! as String,
      role: row['role']! as String,
      content: row['content']! as String,
      createdAt: DateTime.parse(row['created_at']! as String),
      payload: decoded,
      isError: (row['is_error']! as int) == 1,
    );
  }
}

class QueryReply {
  const QueryReply(this.json);

  final Map<String, dynamic> json;

  String get queryId => json['query_id'] as String? ?? '';
  String get language => json['detected_language'] as String? ?? 'unknown';
  String get script => json['detected_script'] as String? ?? 'unknown';
  String get generatedSql => json['generated_sql'] as String? ?? '';
  String get answer => json['verbalized_response'] as String? ?? '';
  String get modelTier => json['model_tier'] as String? ?? 'trained_pro';
  Map<String, dynamic>? get executionResult {
    final result = json['execution_result'];
    return result is Map<String, dynamic> ? result : null;
  }

  List<Map<String, dynamic>> get auditTrace {
    final trace = json['audit_trace'];
    if (trace is! List) return const [];
    return trace.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
  }
}

class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}
