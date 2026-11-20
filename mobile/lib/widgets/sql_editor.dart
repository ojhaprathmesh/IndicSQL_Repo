import 'package:material_ui/material_ui.dart';
import 'package:re_editor/re_editor.dart';
import 'package:re_highlight/languages/sql.dart';
import 'package:re_highlight/styles/atom-one-dark.dart';

class SqlEditor extends StatelessWidget {
  const SqlEditor({
    super.key,
    required this.controller,
    this.readOnly = false,
    this.height = 220,
  });

  final CodeLineEditingController controller;
  final bool readOnly;
  final double height;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      decoration: BoxDecoration(
        color: const Color(0xff282c34),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xff414854)),
      ),
      clipBehavior: Clip.antiAlias,
      child: CodeEditor(
        controller: controller,
        readOnly: readOnly,
        wordWrap: false,
        padding: const EdgeInsets.all(14),
        style: CodeEditorStyle(
          codeTheme: CodeHighlightTheme(
            languages: {'sql': CodeHighlightThemeMode(mode: langSql)},
            theme: atomOneDarkTheme,
          ),
        ),
      ),
    );
  }
}
