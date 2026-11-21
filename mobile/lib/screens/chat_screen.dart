import 'dart:async';

import 'package:flutter_tts/flutter_tts.dart';
import 'package:material_ui/material_ui.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:flutter/services.dart';
import 'package:re_editor/re_editor.dart';

import '../models.dart';
import '../widgets/result_table.dart';
import '../widgets/sql_editor.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({
    super.key,
    required this.messages,
    required this.isSending,
    required this.onSend,
    required this.onOpenSql,
    this.backendConnected = true,
  });

  final List<StoredMessage> messages;
  final bool isSending;
  final Future<QueryReply?> Function(
    String question,
    String language, {
    String modelTier,
  }) onSend;
  final ValueChanged<String> onOpenSql;
  final bool backendConnected;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _questionController = TextEditingController();
  final _scrollController = ScrollController();
  final SpeechToText _speech = SpeechToText();
  final FlutterTts _tts = FlutterTts();
  String _language = 'auto';
  String _modelTier = 'trained_pro';
  bool _speechInitialized = false;
  bool _isInitializingSpeech = false;
  bool _isListening = false;
  bool _isSpeaking = false;
  bool _voiceDraft = false;
  String? _voiceError;
  String? _systemLocaleId;
  List<LocaleName> _speechLocales = [];

  static const _examples = [
    'What is the total number of farmer beneficiaries under PM-KISAN in Andhra Pradesh?',
    'ఆంధ్రప్రదేశ్‌లో పీఎం-కిసాన్ పథకం ద్వారా ఎంతమంది రైతులకు లబ్ధి చేకూరింది?',
    'पंजाब में गेहूं का कुल उत्पादन कितने टन हुआ?',
    'பஞ்சாபில் கோதுமையின் மொத்த உற்பத்தி எத்தனை டன்?',
  ];

  @override
  void didUpdateWidget(covariant ChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.messages.length != oldWidget.messages.length ||
        widget.isSending != oldWidget.isSending) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(
            _scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 220),
            curve: Curves.easeOut,
          );
        }
      });
    }
  }

  @override
  void dispose() {
    if (_speechInitialized) unawaited(_speech.cancel());
    unawaited(_tts.stop());
    _questionController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _submit([String? value]) async {
    final question = (value ?? _questionController.text).trim();
    if (question.isEmpty || widget.isSending) return;
    final speakResponse = value == null && _voiceDraft;
    _voiceDraft = false;
    _questionController.clear();
    final reply = await widget.onSend(
      question,
      _language,
      modelTier: _modelTier,
    );
    if (mounted && speakResponse && reply != null) {
      await _speakResponse(reply.answer, reply.language);
    }
  }

  Future<void> _toggleListening() async {
    if (_isInitializingSpeech) return;
    if (_isListening || _speech.isListening) {
      await _speech.stop();
      if (mounted) setState(() => _isListening = false);
      return;
    }

    setState(() {
      _isInitializingSpeech = true;
      _voiceError = null;
    });
    try {
      if (!_speechInitialized) {
        _speechInitialized = await _speech.initialize(
          onError: (error) {
            if (!mounted) return;
            setState(() {
              _isListening = false;
              _voiceError = _speechErrorMessage(error.errorMsg);
            });
          },
          onStatus: (status) {
            if (!mounted) return;
            setState(() {
              _isListening = status == SpeechToText.listeningStatus;
            });
          },
        );
        if (!_speechInitialized) {
          throw StateError(
            'Speech recognition is unavailable. Check microphone permission and your phone’s speech service.',
          );
        }
        _speechLocales = await _speech.locales();
        _systemLocaleId = (await _speech.systemLocale())?.localeId;
      }
      if (!mounted) return;

      final localeId = _speechLocaleFor(_language);
      if (_language != 'auto' && localeId == null) {
        throw StateError(
          'Your phone’s speech service does not list a ${_languageName(_language)} locale.',
        );
      }
      _questionController.clear();
      _voiceDraft = false;
      setState(() => _isListening = true);
      await _speech.listen(
        onResult: (result) {
          if (!mounted) return;
          final transcript = result.recognizedWords;
          _questionController.value = TextEditingValue(
            text: transcript,
            selection: TextSelection.collapsed(offset: transcript.length),
          );
          setState(() {
            _voiceDraft = transcript.trim().isNotEmpty;
            if (result.finalResult) _isListening = false;
          });
        },
        listenOptions: SpeechListenOptions(
          localeId: localeId,
          cancelOnError: true,
          partialResults: true,
          listenMode: ListenMode.dictation,
          listenFor: const Duration(minutes: 1),
          pauseFor: const Duration(seconds: 4),
          contextualPhrases: const [
            'IndicSQL',
            'NDAP',
            'PM-Kisan',
            'DuckDB',
            'beneficiaries',
          ],
        ),
      );
    } catch (error) {
      _voiceDraft = false;
      if (mounted) {
        setState(() {
          _isListening = false;
          _voiceError = 'Could not start speech recognition: $error';
        });
      }
    } finally {
      if (mounted) setState(() => _isInitializingSpeech = false);
    }
  }

  String? _speechLocaleFor(String language) {
    if (language == 'auto') return _systemLocaleId;
    final languageCode = language == 'hi-en' ? 'hi' : language;
    for (final locale in _speechLocales) {
      final normalized = locale.localeId.replaceAll('_', '-').toLowerCase();
      if (normalized == languageCode ||
          normalized.startsWith('$languageCode-')) {
        return locale.localeId;
      }
    }
    return null;
  }

  String? _ttsLocaleFor(String language) => switch (language.toLowerCase()) {
    'en' => 'en-IN',
    'hi' => 'hi-IN',
    'hi-en' => 'hi-IN',
    'mr' => 'mr-IN',
    'bn' => 'bn-IN',
    'ta' => 'ta-IN',
    'te' => 'te-IN',
    _ => null,
  };

  String _languageName(String code) => switch (code) {
    'en' => 'English',
    'hi' => 'Hindi',
    'hi-en' => 'Hinglish',
    'mr' => 'Marathi',
    'bn' => 'Bengali',
    'ta' => 'Tamil',
    'te' => 'Telugu',
    _ => code,
  };

  String _speechErrorMessage(String error) {
    if (error.toLowerCase().contains('permission')) {
      return 'Microphone access was denied. Allow it in your phone’s app settings.';
    }
    return 'Speech recognition failed: $error';
  }

  Future<void> _speakResponse(String text, String detectedLanguage) async {
    if (!mounted) return;
    if (_isSpeaking) {
      await _tts.stop();
      if (mounted) setState(() => _isSpeaking = false);
      return;
    }
    final preferredLocale = _ttsLocaleFor(detectedLanguage);
    if (preferredLocale == null) {
      setState(() {
        _voiceError = 'IndicSQL could not identify the answer language, so a matching voice could not be selected.';
      });
      return;
    }

    setState(() {
      _isSpeaking = true;
      _voiceError = null;
    });
    try {
      await _speech.stop();
      await _tts.stop();
      final rawLanguages = await _tts.getLanguages;
      var selectedLocale = preferredLocale;
      if (rawLanguages is List && rawLanguages.isNotEmpty) {
        final available = rawLanguages
            .map((locale) => '$locale'.replaceAll('_', '-').toLowerCase())
            .toList();
        final languagePrefix = preferredLocale.split('-').first.toLowerCase();
        final match = available.where(
          (locale) =>
              locale == preferredLocale.toLowerCase() ||
              locale.startsWith('$languagePrefix-'),
        );
        if (match.isEmpty) {
          throw StateError(
            'Install a ${_languageName(detectedLanguage)} voice in your phone’s Text-to-speech settings.',
          );
        }
        selectedLocale = match.first;
      }
      await _tts.setLanguage(selectedLocale);
      await _tts.setSpeechRate(0.47);
      await _tts.setVolume(1);
      await _tts.awaitSpeakCompletion(true);
      await _tts.speak(text);
    } catch (error) {
      if (mounted) {
        setState(() => _voiceError = 'Voice playback failed: $error');
      }
    } finally {
      if (mounted) setState(() => _isSpeaking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      children: [
        if (!widget.backendConnected)
          Container(
            width: double.infinity,
            color: const Color(0xfffff4e5),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                const Icon(Icons.cloud_off, size: 18, color: Color(0xffb76e00)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'IndicSQL backend is offline. Query interactions are paused; saved conversation history is fully available.',
                    style: TextStyle(
                      color: Colors.amber.shade900,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
        Expanded(
          child: widget.messages.isEmpty
              ? _emptyState(theme)
              : ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.fromLTRB(16, 20, 16, 16),
                  itemCount:
                      widget.messages.length + (widget.isSending ? 1 : 0),
                  itemBuilder: (context, index) {
                    if (index >= widget.messages.length) {
                      return const _ThinkingIndicator();
                    }
                    return _MessageCard(
                      message: widget.messages[index],
                      onOpenSql: widget.onOpenSql,
                      onSpeak: _speakResponse,
                      isSpeaking: _isSpeaking,
                    );
                  },
                ),
        ),
        _composer(theme),
      ],
    );
  }

  Widget _emptyState(ThemeData theme) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
      children: [
        Container(
          padding: const EdgeInsets.all(22),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(22),
            gradient: const LinearGradient(
              colors: [Color(0xff174762), Color(0xff23827d)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                height: 48,
                width: 48,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(15),
                ),
                child: const Icon(
                  Icons.auto_awesome,
                  color: Colors.white,
                  size: 26,
                ),
              ),
              const SizedBox(height: 20),
              const Text(
                'YOUR DATA, YOUR LANGUAGE',
                style: TextStyle(
                  color: Color(0xffd9eeee),
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 7),
              const Text(
                'Ask a question.\nFind the insight.',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 27,
                  height: 1.15,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                'Type or speak naturally. IndicSQL turns your question into real, verified SQL.',
                style: TextStyle(
                  color: Color(0xffe6f2f2),
                  fontSize: 14,
                  height: 1.45,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 22),
        Row(
          children: [
            Text('Try an example', style: theme.textTheme.titleMedium),
            const Spacer(),
            const Icon(
              Icons.touch_app_outlined,
              size: 18,
              color: Color(0xff718398),
            ),
          ],
        ),
        const SizedBox(height: 10),
        for (final example in _examples)
          Card(
            margin: const EdgeInsets.only(bottom: 8),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(15),
              side: const BorderSide(color: Color(0xffe2eaf0)),
            ),
            child: ListTile(
              leading: const CircleAvatar(
                radius: 18,
                backgroundColor: Color(0xffedf5f5),
                child: Icon(
                  Icons.arrow_outward,
                  size: 17,
                  color: Color(0xff167a73),
                ),
              ),
              title: Text(
                example,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              onTap: widget.isSending || !widget.backendConnected ? null : () => _submit(example),
              trailing: Icon(
                Icons.chevron_right,
                size: 20,
                color: !widget.backendConnected ? theme.disabledColor : null,
              ),
            ),
          ),
      ],
    );
  }

  Widget _composer(ThemeData theme) {
    return SafeArea(
      top: false,
      child: Material(
        elevation: 8,
        color: theme.colorScheme.surface,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  const Icon(
                    Icons.translate,
                    size: 19,
                    color: Color(0xff537082),
                  ),
                  const SizedBox(width: 9),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _language,
                      isExpanded: true,
                      decoration: const InputDecoration(
                        labelText: 'Language',
                        isDense: true,
                        contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      ),
                      items: const [
                        DropdownMenuItem(
                          value: 'auto',
                          child: Text('Auto-detect'),
                        ),
                        DropdownMenuItem(value: 'en', child: Text('English')),
                        DropdownMenuItem(value: 'hi', child: Text('Hindi')),
                        DropdownMenuItem(
                          value: 'hi-en',
                          child: Text('Hinglish'),
                        ),
                        DropdownMenuItem(value: 'mr', child: Text('Marathi')),
                        DropdownMenuItem(value: 'bn', child: Text('Bengali')),
                        DropdownMenuItem(value: 'ta', child: Text('Tamil')),
                        DropdownMenuItem(value: 'te', child: Text('Telugu')),
                      ],
                      onChanged: widget.isSending
                          ? null
                          : (value) =>
                                setState(() => _language = value ?? 'auto'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  SegmentedButton<String>(
                    segments: const [
                      ButtonSegment(
                        value: 'trained_pro',
                        label: Text('Pro 🎯', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                        tooltip: 'Accurate Dual-LoRA Tier',
                      ),
                      ButtonSegment(
                        value: 'turbo_fast',
                        label: Text('Turbo ⚡', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                        tooltip: 'Sub-Second Edge Tier',
                      ),
                    ],
                    selected: {_modelTier},
                    onSelectionChanged: widget.isSending
                        ? null
                        : (set) => setState(() => _modelTier = set.first),
                    showSelectedIcon: false,
                    style: SegmentedButton.styleFrom(
                      visualDensity: VisualDensity.compact,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 9),
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Expanded(
                    child: TextField(
                      controller: _questionController,
                      enabled: widget.backendConnected && !widget.isSending,
                      minLines: 1,
                      maxLines: 5,
                      textInputAction: TextInputAction.newline,
                      decoration: InputDecoration(
                        hintText: !widget.backendConnected
                            ? 'Backend offline — live questions disabled'
                            : 'Ask or dictate a question…',
                        alignLabelWithHint: true,
                      ),
                      onSubmitted: (_) => _submit(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filledTonal(
                    tooltip: !widget.backendConnected
                        ? 'Backend offline'
                        : (_isListening ? 'Stop voice input' : 'Dictate a question'),
                    onPressed: widget.isSending || _isInitializingSpeech || !widget.backendConnected
                        ? null
                        : _toggleListening,
                    style: IconButton.styleFrom(
                      backgroundColor: _isListening
                          ? const Color(0xffffe8e5)
                          : const Color(0xffe7f2f2),
                      foregroundColor: _isListening
                          ? const Color(0xffb42318)
                          : const Color(0xff167a73),
                    ),
                    icon: _isInitializingSpeech
                        ? const SizedBox(
                            width: 19,
                            height: 19,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : Icon(
                            _isListening
                                ? Icons.stop_rounded
                                : Icons.mic_none_rounded,
                          ),
                  ),
                  const SizedBox(width: 4),
                  IconButton.filled(
                    tooltip: !widget.backendConnected ? 'Backend offline' : 'Send question',
                    onPressed: widget.isSending || !widget.backendConnected ? null : () => _submit(),
                    icon: widget.isSending
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.arrow_upward),
                  ),
                ],
              ),
              if (_isListening || _voiceError != null) ...[
                const SizedBox(height: 9),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 9,
                  ),
                  decoration: BoxDecoration(
                    color: _voiceError != null
                        ? theme.colorScheme.errorContainer
                        : const Color(0xffeaf4f5),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        _voiceError != null
                            ? Icons.info_outline
                            : Icons.graphic_eq,
                        size: 18,
                        color: _voiceError != null
                            ? theme.colorScheme.error
                            : theme.colorScheme.secondary,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _voiceError ?? 'Listening… review the transcript, then send it for language detection.',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: _voiceError != null
                                ? theme.colorScheme.error
                                : theme.colorScheme.onSurface,
                          ),
                        ),
                      ),
                      if (_voiceError != null)
                        IconButton(
                          tooltip: 'Dismiss message',
                          visualDensity: VisualDensity.compact,
                          onPressed: () => setState(() => _voiceError = null),
                          icon: const Icon(Icons.close, size: 17),
                        ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 6),
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Your phone transcribes speech. IndicSQL detects the transcript language and speaks voice prompts back in that language.',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MessageCard extends StatelessWidget {
  const _MessageCard({
    required this.message,
    required this.onOpenSql,
    required this.onSpeak,
    required this.isSpeaking,
  });

  final StoredMessage message;
  final ValueChanged<String> onOpenSql;
  final Future<void> Function(String text, String language) onSpeak;
  final bool isSpeaking;

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    final theme = Theme.of(context);
    final payload = message.payload;
    final sql = payload?['generated_sql'] as String? ?? '';
    final result = payload?['execution_result'];
    final trace = payload?['audit_trace'];

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.sizeOf(context).width * (isUser ? .88 : .96),
        ),
        child: Card(
          color: message.isError
              ? theme.colorScheme.errorContainer
              : isUser
              ? theme.colorScheme.primaryContainer
              : theme.colorScheme.surface,
          margin: const EdgeInsets.only(bottom: 14),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      isUser ? Icons.person_outline : Icons.auto_awesome,
                      size: 16,
                      color: isUser
                          ? theme.colorScheme.primary
                          : const Color(0xff6138ca),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      isUser
                          ? 'You'
                          : message.isError
                          ? 'Backend error'
                          : 'IndicSQL',
                      style: theme.textTheme.labelLarge,
                    ),
                    const Spacer(),
                    Text(
                      MaterialLocalizations.of(context).formatTimeOfDay(
                        TimeOfDay.fromDateTime(message.createdAt.toLocal()),
                      ),
                      style: theme.textTheme.labelSmall,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                SelectableText(message.content),
                if (!isUser && !message.isError && payload != null) ...[
                  if (payload['detected_language'] case final String language)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Wrap(
                        spacing: 6,
                        runSpacing: 4,
                        children: [
                          Chip(
                            label: Text(
                              'Language: ${language.toUpperCase()}${payload['detected_script'] != null ? ' (${payload['detected_script']})' : ''}',
                            ),
                            visualDensity: VisualDensity.compact,
                          ),
                          if (payload['model_tier'] case final String tier)
                            Chip(
                              label: Text(
                                tier == 'turbo_fast' ? 'Turbo ⚡' : 'Pro 🎯',
                              ),
                              visualDensity: VisualDensity.compact,
                            ),
                        ],
                      ),
                    ),
                  if (sql.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Text(
                          'Generated SQL',
                          style: theme.textTheme.titleSmall,
                        ),
                        const Spacer(),
                        IconButton(
                          tooltip: 'Copy SQL',
                          visualDensity: VisualDensity.compact,
                          onPressed: () => _copy(context, sql, 'SQL copied'),
                          icon: const Icon(Icons.copy, size: 18),
                        ),
                        TextButton.icon(
                          onPressed: () => onOpenSql(sql),
                          icon: const Icon(Icons.edit_note, size: 18),
                          label: const Text('Edit & run'),
                        ),
                      ],
                    ),
                    _SqlSnippet(sql: sql),
                  ],
                  if (result is Map<String, dynamic>) ...[
                    const SizedBox(height: 12),
                    ResultTable(result: result),
                  ],
                  if (trace is List && trace.isNotEmpty)
                    ExpansionTile(
                      tilePadding: EdgeInsets.zero,
                      title: const Text('Pipeline trace'),
                      children: [
                        for (final rawStep in trace.whereType<Map>())
                          ListTile(
                            dense: true,
                            leading: const Icon(
                              Icons.check_circle_outline,
                              size: 18,
                            ),
                            title: Text(
                              '${rawStep['agent'] ?? 'Agent'} · ${rawStep['action'] ?? 'Step'}',
                            ),
                            subtitle: Text(
                              [
                                if (rawStep['matched_table'] != null)
                                  '${rawStep['matched_table']}',
                                if (rawStep['error'] != null)
                                  '${rawStep['error']}',
                              ].join(' · '),
                            ),
                          ),
                      ],
                    ),
                  Align(
                    alignment: Alignment.centerRight,
                    child: Wrap(
                      spacing: 2,
                      children: [
                        TextButton.icon(
                          onPressed: () => onSpeak(
                            message.content,
                            '${payload['detected_language'] ?? 'unknown'}',
                          ),
                          icon: Icon(
                            isSpeaking
                                ? Icons.stop_circle_outlined
                                : Icons.volume_up_outlined,
                            size: 17,
                          ),
                          label: Text(isSpeaking ? 'Stop' : 'Listen'),
                        ),
                        TextButton.icon(
                          onPressed: () =>
                              _copy(context, message.content, 'Answer copied'),
                          icon: const Icon(Icons.copy, size: 16),
                          label: const Text('Copy answer'),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _copy(BuildContext context, String value, String message) {
    Clipboard.setData(ClipboardData(text: value)).then((_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(message)));
      }
    });
  }
}

class _SqlSnippet extends StatefulWidget {
  const _SqlSnippet({required this.sql});

  final String sql;

  @override
  State<_SqlSnippet> createState() => _SqlSnippetState();
}

class _SqlSnippetState extends State<_SqlSnippet> {
  late final CodeLineEditingController _controller =
      CodeLineEditingController.fromText(widget.sql);

  @override
  void didUpdateWidget(covariant _SqlSnippet oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.sql != widget.sql) {
      _controller.text = widget.sql;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final lineCount = widget.sql.trim().split('\n').length;
    final snippetHeight = (lineCount * 22.0 + 32.0).clamp(72.0, 160.0);
    return SqlEditor(
      controller: _controller,
      readOnly: true,
      height: snippetHeight,
    );
  }
}

class _ThinkingIndicator extends StatelessWidget {
  const _ThinkingIndicator();

  @override
  Widget build(BuildContext context) => const Padding(
    padding: EdgeInsets.all(12),
    child: Row(
      children: [
        SizedBox(
          width: 18,
          height: 18,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
        SizedBox(width: 10),
        Text('Sending to IndicSQL backend…'),
      ],
    ),
  );
}
