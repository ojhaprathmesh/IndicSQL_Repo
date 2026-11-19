import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:indicsql_studio/api_client.dart';
import 'package:indicsql_studio/models.dart';

void main() {
  test('ask sends the backend query contract and selected language', () async {
    late http.Request capturedRequest;
    final api = IndicSqlApi(
      baseUrl: 'http://localhost:8000/',
      client: MockClient((request) async {
        capturedRequest = request;
        return http.Response(
          jsonEncode({
            'query_id': 'q-1',
            'detected_language': 'hi',
            'generated_sql': 'SELECT 1',
            'verbalized_response': 'एक परिणाम',
          }),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }),
    );

    final reply = await api.ask(
      'कुल कितने रिकॉर्ड हैं?',
      conversationId: 'conversation-1',
      language: 'hi',
    );

    expect(capturedRequest.url.path, '/query');
    expect(capturedRequest.method, 'POST');
    expect(jsonDecode(capturedRequest.body), {
      'query': 'कुल कितने रिकॉर्ड हैं?',
      'session_id': 'conversation-1',
      'language': 'hi',
    });
    expect(reply.generatedSql, 'SELECT 1');
    expect(reply.answer, 'एक परिणाम');
  });

  test('ask reports backend validation errors', () async {
    final api = IndicSqlApi(
      baseUrl: 'http://localhost:8000',
      client: MockClient((_) async => http.Response(
            jsonEncode({'detail': 'Unsupported language.'}),
            422,
            headers: {'content-type': 'application/json'},
          )),
    );

    await expectLater(
      api.ask('question', conversationId: 'conversation-1', language: 'xx'),
      throwsA(
        isA<ApiException>()
            .having((error) => error.statusCode, 'statusCode', 422)
            .having((error) => error.message, 'message', 'Unsupported language.'),
      ),
    );
  });
}
