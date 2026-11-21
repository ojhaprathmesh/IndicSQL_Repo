import 'package:material_ui/material_ui.dart';
import 'package:re_editor/re_editor.dart';
import 'package:re_highlight/languages/sql.dart';

/// Clean, high-contrast light theme for SQL syntax highlighting.
const Map<String, TextStyle> sqlLightTheme = {
  'root': TextStyle(
    color: Color(0xff0f172a), // Slate 900: deep crisp text for columns, tables, and identifiers
    backgroundColor: Colors.transparent,
  ),
  'keyword': TextStyle(
    color: Color(0xff0284c7), // Sky 600: vibrant blue for SELECT, FROM, WHERE, AS, GROUP BY, LIMIT
    fontWeight: FontWeight.bold,
  ),
  'built_in': TextStyle(
    color: Color(0xff7c3aed), // Violet 600: distinct purple for SUM, COUNT, AVG, MIN, MAX
    fontWeight: FontWeight.w600,
  ),
  'type': TextStyle(
    color: Color(0xff0891b2), // Cyan 600: data types
    fontWeight: FontWeight.w600,
  ),
  'literal': TextStyle(
    color: Color(0xffc2410c), // Orange 700: TRUE, FALSE, NULL
    fontWeight: FontWeight.w600,
  ),
  'number': TextStyle(
    color: Color(0xffb45309), // Amber 700: numeric literals
    fontWeight: FontWeight.w500,
  ),
  'string': TextStyle(
    color: Color(0xff15803d), // Green 700: string literals
  ),
  'comment': TextStyle(
    color: Color(0xff64748b), // Slate 500: muted comments
    fontStyle: FontStyle.italic,
  ),
  'operator': TextStyle(
    color: Color(0xff334155), // Slate 700
    fontWeight: FontWeight.bold,
  ),
  'punctuation': TextStyle(
    color: Color(0xff475569), // Slate 600: commas, parentheses
  ),
  'title': TextStyle(
    color: Color(0xff4338ca), // Indigo 700
  ),
  'variable': TextStyle(
    color: Color(0xff0f172a), // Slate 900
  ),
};

class SqlEditor extends StatelessWidget {
  const SqlEditor({
    super.key,
    required this.controller,
    this.readOnly = false,
    this.height = 220,
    this.wordWrap = false,
  });

  final CodeLineEditingController controller;
  final bool readOnly;
  final double height;
  final bool wordWrap;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      decoration: BoxDecoration(
        color: const Color(0xfff8fafc), // Slate 50: clean light background
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xffcbd5e1), width: 1.2), // Slate 300
      ),
      clipBehavior: Clip.antiAlias,
      child: CodeEditor(
        controller: controller,
        readOnly: readOnly,
        wordWrap: wordWrap,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        style: CodeEditorStyle(
          fontSize: 13.0,
          fontFamily: 'monospace',
          textColor: const Color(0xff0f172a), // Ensures columns, tables, aliases are pitch crisp
          backgroundColor: Colors.transparent,
          cursorColor: const Color(0xff1d5876),
          selectionColor: const Color(0x331d5876),
          codeTheme: CodeHighlightTheme(
            languages: {'sql': CodeHighlightThemeMode(mode: langSql)},
            theme: sqlLightTheme,
          ),
        ),
      ),
    );
  }
}
