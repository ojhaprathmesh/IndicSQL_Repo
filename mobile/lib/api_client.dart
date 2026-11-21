import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'models.dart';

class IndicSqlApi {
  IndicSqlApi({required String baseUrl, http.Client? client})
      : _baseUrl = _normalizeBaseUrl(baseUrl),
        _client = client ?? http.Client();

  String _baseUrl;
  final http.Client _client;

  String get baseUrl => _baseUrl;

  set baseUrl(String value) => _baseUrl = _normalizeBaseUrl(value);

  static String _normalizeBaseUrl(String value) =>
      value.trim().replaceAll(RegExp(r'/+$'), '');

  Uri _uri(String path) => Uri.parse('$_baseUrl$path');

  Future<dynamic> _request(
    String path, {
    String method = 'GET',
    Map<String, dynamic>? body,
  }) async {
    final uri = _uri(path);
    try {
      final response = switch (method) {
        'POST' => await _client
            .post(
              uri,
              headers: const {'Content-Type': 'application/json'},
              body: jsonEncode(body),
            )
            .timeout(const Duration(seconds: 45)),
        _ => await _client.get(uri).timeout(const Duration(seconds: 20)),
      };

      dynamic decoded;
      try {
        decoded = jsonDecode(utf8.decode(response.bodyBytes));
      } on FormatException {
        throw ApiException(
          'Backend returned an unreadable response (${response.statusCode}).',
          statusCode: response.statusCode,
        );
      }

      if (response.statusCode < 200 || response.statusCode >= 300) {
        final detail = decoded is Map ? decoded['detail'] : null;
        throw ApiException(
          detail is String ? detail : 'Backend request failed (${response.statusCode}).',
          statusCode: response.statusCode,
        );
      }
      return decoded;
    } on ApiException {
      rethrow;
    } on TimeoutException {
      throw const ApiException('The backend request timed out.');
    } on http.ClientException {
      throw ApiException('Could not connect to the IndicSQL backend at $_baseUrl.');
    }
  }

  Future<bool> checkHealth() async {
    final body = await _request('/health');
    return body is Map && body['status'] == 'ok';
  }

  Future<Map<String, dynamic>> fetchSchemas() async {
    final body = await _request('/schemas');
    if (body is! Map<String, dynamic>) {
      throw const ApiException('The schema endpoint returned an unexpected response.');
    }
    return body;
  }

  Future<Map<String, dynamic>> fetchAnalytics() async {
    final body = await _request('/analytics');
    if (body is! Map<String, dynamic>) {
      throw const ApiException('The analytics endpoint returned an unexpected response.');
    }
    return body;
  }

  Future<QueryReply> ask(
    String question, {
    required String conversationId,
    String language = 'auto',
  }) async {
    final body = await _request(
      '/query',
      method: 'POST',
      body: {
        'query': question,
        'session_id': conversationId,
        if (language != 'auto') 'language': language,
      },
    );
    if (body is! Map<String, dynamic>) {
      throw const ApiException('The query endpoint returned an unexpected response.');
    }
    return QueryReply(body);
  }

  Future<Map<String, dynamic>> inspectSql(String sql) async {
    final body = await _request('/sql/inspect', method: 'POST', body: {'sql': sql});
    if (body is! Map<String, dynamic>) {
      throw const ApiException('The SQL inspection endpoint returned an unexpected response.');
    }
    return body;
  }

  Future<List<dynamic>> listConversations() async {
    final body = await _request('/conversations');
    if (body is! List) {
      throw const ApiException('Expected list of conversations from server.');
    }
    return body;
  }

  Future<Map<String, dynamic>> getConversation(String conversationId) async {
    final body = await _request('/conversations/$conversationId');
    if (body is! Map<String, dynamic>) {
      throw const ApiException('Expected conversation details from server.');
    }
    return body;
  }

  Future<void> deleteConversation(String conversationId) async {
    await _request('/conversations/$conversationId', method: 'DELETE');
  }

  void close() => _client.close();
}
