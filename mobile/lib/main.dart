import 'dart:io' show Platform;

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:material_ui/material_ui.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api_client.dart';
import 'app_shell.dart';
import 'conversation_store.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final preferences = await SharedPreferences.getInstance();
  final defaultApiUrl = (!kIsWeb && Platform.isAndroid)
      ? 'http://10.0.2.2:8000'
      : 'http://127.0.0.1:8000';
  final api = IndicSqlApi(
    baseUrl: preferences.getString('api_base_url') ?? defaultApiUrl,
  );
  final store = ConversationStore();
  await store.initialize();
  runApp(IndicSqlApp(api: api, store: store, preferences: preferences));
}

class IndicSqlApp extends StatelessWidget {
  const IndicSqlApp({
    super.key,
    required this.api,
    required this.store,
    required this.preferences,
  });

  final IndicSqlApi api;
  final ConversationStore store;
  final SharedPreferences preferences;

  @override
  Widget build(BuildContext context) {
    const ink = Color(0xff183247);
    const primary = Color(0xff1d5876);
    const secondary = Color(0xff167a73);
    const canvas = Color(0xfff3f7fa);
    const outline = Color(0xffd8e2e9);
    final scheme =
        ColorScheme.fromSeed(
          seedColor: primary,
          brightness: Brightness.light,
        ).copyWith(
          primary: primary,
          onPrimary: Colors.white,
          secondary: secondary,
          onSecondary: Colors.white,
          surface: Colors.white,
          onSurface: ink,
          outline: outline,
        );
    final roundedBorder = OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: const BorderSide(color: outline),
    );

    return MaterialApp(
      title: 'IndicSQL Studio',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.light,
      theme: ThemeData(
        colorScheme: scheme,
        scaffoldBackgroundColor: canvas,
        useMaterial3: true,
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: ink,
          surfaceTintColor: Colors.transparent,
          elevation: 0,
          scrolledUnderElevation: 0,
          centerTitle: false,
        ),
        cardTheme: CardThemeData(
          color: Colors.white,
          elevation: 0,
          margin: EdgeInsets.zero,
          clipBehavior: Clip.antiAlias,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 14,
          ),
          border: roundedBorder,
          enabledBorder: roundedBorder,
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: const BorderSide(color: primary, width: 1.5),
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            backgroundColor: primary,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 13),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(13),
            ),
          ),
        ),
        navigationDrawerTheme: NavigationDrawerThemeData(
          backgroundColor: Colors.white,
          indicatorColor: const Color(0xffe6f1f5),
          indicatorShape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          tileHeight: 52,
        ),
        chipTheme: ChipThemeData(
          backgroundColor: const Color(0xffedf5f5),
          side: BorderSide.none,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          labelStyle: const TextStyle(color: ink, fontWeight: FontWeight.w600),
        ),
        dividerColor: const Color(0xffe8edf1),
        textTheme: ThemeData.light().textTheme.apply(
          bodyColor: ink,
          displayColor: ink,
        ),
      ),
      home: IndicSqlHome(api: api, store: store, preferences: preferences),
    );
  }
}
