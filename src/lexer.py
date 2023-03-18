import re
import keyword
import builtins
import types
import json

from PyQt5.Qsci import QsciLexerCustom, QsciScintilla
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


# config type
DefaultConfig = dict[str, str, tuple[str, int]]

class NeutronLexer(QsciLexerCustom):
    """Base Custo Lexer class for all language"""

    def __init__(self, language_name, editor, theme=None, defaults: DefaultConfig = None):
        super(NeutronLexer, self).__init__(editor)

        self.editor = editor
        self.language_name = language_name
        self.theme_json = None
        if theme is None:
            self.theme = "./theme.json"
        else:
            self.theme = theme

        self.token_list: list[str, str] = []

        self.keywords_list = []
        self.builtin_names = []

        if defaults is None:
            defaults: DefaultConfig = {}
            defaults["color"] = "#abb2bf"
            defaults["paper"] = "#282c34"
            defaults["font"] = ("Consolas", 14)


        # Default text settings
        self.setDefaultColor(QColor(defaults["color"]))
        self.setDefaultPaper(QColor(defaults["paper"]))
        self.setDefaultFont(QFont(defaults["font"][0], defaults["font"][1]))

        self._init_theme_vars()
        self._init_theme()

    def setKeywords(self, keywords: list[str]):
        """Set List of strings that considered keywords for this language."""
        self.keywords_list =keywords

    def setBuiltinNames(self, buitin_names: list[str]):
        """Set list of builtin names"""
        self.builtin_names = buitin_names

    def _init_theme_vars(self):
        # color per style

        self.DEFAULT = 0
        self.KEYWORD = 1
        self.TYPES = 2
        self.STRING = 3
        self.KEYARGS = 4
        self.BRACKETS = 5
        self.COMMENTS = 6
        self.CONSTANTS = 7
        self.FUNCTIONS = 8
        self.CLASSES = 9
        self.FUNCTION_DEF = 10

        self.default_names = [
            "default",
            "keyword",
            "types",
            "string",
            "keyargs",
            "brackets",
            "comments",
            "constants",
            "functions",
            "classes",
            "function_def"
        ]

        self.font_weights = {
            "thin": QFont.Thin,
            "extralight": QFont.ExtraLight,
            "light": QFont.Light,
            "normal": QFont.Normal,
            "medium": QFont.Medium,
            "demibold": QFont.DemiBold,
            "bold": QFont.Bold,
            "extrabold": QFont.ExtraBold,
            "black": QFont.Black,
        }

    def _init_theme(self):
        with open(self.theme, "r") as f:
            self.theme_json = json.load(f)

        colors = self.theme_json["theme"]["syntax"]

        for clr in colors:
            name: str = list(clr.keys())[0]

            if name not in self.default_names:
                print(f"Theme error: {name} is not a valid style name")
                continue
            
            for k, v in clr[name].items():
                if k == "color":
                    self.setColor(QColor(v), getattr(self, name.upper()))
                elif k == "paper-color":
                    self.setPaper(QColor(v), getattr(self, name.upper()))
                elif k == "font":
                    try:
                        self.setFont(
                            QFont(
                                v.get("family", "Consolas"), 
                                v.get("font-size", 14),
                                self.font_weights.get(v.get("font-weight", QFont.Normal)),
                                v.get("italic", False)
                            ),
                            getattr(self, name.upper())
                        )    
                    except AttributeError as e:
                        print(f"theme error: {e}")
            

    def language(self) -> str:
        return self.language_name

    def description(self, style: int) -> str:
        if style == self.DEFAULT:
            return "DEFAULT"
        elif style == self.KEYWORD:
            return "KEYWORD"
        elif style == self.TYPES:
            return "TYPES"
        elif style == self.STRING:
            return "STRING"
        elif style == self.KEYARGS:
            return "KEYARGS"
        elif style == self.BRACKETS:
            return "BRACKETS"
        elif style == self.COMMENTS:
            return "COMMENTS"
        elif style == self.CONSTANTS:
            return "CONSTANTS"
        elif style == self.FUNCTIONS:
            return "FUNCTIONS"
        elif style == self.CLASSES:
            return "CLASSES"
        elif style == self.FUNCTION_DEF:
            return "FUNCTION_DEF"

        return ""

    def generate_token(self, text):
        # 3. Tokenize the text 
        # ---------------------
        p = re.compile(r"[*]\/|\/[*]|\s+|\w+|\W")

        # 'token_list' is a list of tuples: (token_name, token_len), ex: '(class, 5)' 
        self.token_list =  [ (token, len(bytearray(token, "utf-8"))) for token in p.findall(text)]

    def next_tok(self, skip: int = None):
        if len(self.token_list) > 0:
            if skip is not None and skip != 0:
                for _ in range(skip-1):
                    if len(self.token_list) > 0:
                        self.token_list.pop(0)
            return self.token_list.pop(0)
        else:
            return None

    def peek_tok(self, n=0):
        try:
            return self.token_list[n]
        except IndexError:
            return ['']

    def skip_spaces_peek(self, skip=None):
        """find he next non-space token but using peek without consuming it"""
        i = 0
        tok = " "
        if skip is not None:
            i = skip
        while tok[0].isspace():
            tok = self.peek_tok(i)
            i += 1
        return tok, i

    
class PyCustomLexer(NeutronLexer):
    """Custom lexer for python"""

    def __init__(self, editor):
        super(PyCustomLexer, self).__init__("Python", editor)

        self.setKeywords(keyword.kwlist)
        self.setBuiltinNames([
            name
            for name, obj in vars(builtins).items()
            if isinstance(obj, types.BuiltinFunctionType)
        ])

    def styleText(self, start: int, end: int) -> None:
        # 1. Start styling procedure
        self.startStyling(start)

        # 2. Slice out part from the text
        text = self.editor.text()[start:end]

        # 3. Tokenize the text
        self.generate_token(text)

        # Flags
        string_flag = False
        comment_flag = False

        if start > 0:
            prev_style = self.editor.SendScintilla(self.editor.SCI_GETSTYLEAT, start -1)
            if prev_style == self.COMMENTS:
                comment_flag = False

        while True:
            curr_token = self.next_tok()

            if curr_token is None:
                break

            tok: str = curr_token[0]
            tok_len: int = curr_token[1]

            if comment_flag:
                self.setStyling(tok_len, self.COMMENTS)
                if tok.startswith("\n"):
                    comment_flag = False
                continue


            if string_flag:
                self.setStyling(tok_len, self.STRING)
                if tok == '"' or tok == "'":
                    string_flag = False
                continue

            if tok == "class":
                name, ni = self.skip_spaces_peek()
                brac_or_colon, _ = self.skip_spaces_peek(ni)
                if name[0].isidentifier() and brac_or_colon[0] in (":", "("):
                    self.setStyling(tok_len, self.KEYWORD)
                    _ = self.next_tok(ni)
                    self.setStyling(name[1]+1, self.CLASSES)
                    continue
                else:
                    self.setStyling(tok_len, self.KEYWORD)
                    continue
            elif tok == "def":
                name, ni = self.skip_spaces_peek()
                if name[0].isidentifier():
                    self.setStyling(tok_len, self.KEYWORD)
                    _ = self.next_tok(ni)
                    self.setStyling(name[1]+1, self.FUNCTION_DEF)
                    continue
                else:
                    self.setStyling(tok_len, self.KEYWORD)
                    continue
            elif tok in self.keywords_list:
                self.setStyling(tok_len, self.KEYWORD)
            elif tok.strip() == "." and self.peek_tok()[0].isidentifier():
                self.setStyling(tok_len, self.DEFAULT)
                curr_token = self.next_tok()
                tok: str = curr_token[0]
                tok_len: int = curr_token[1]
                if self.peek_tok()[0] == "(":
                    self.setStyling(tok_len, self.FUNCTIONS)
                else:
                    self.setStyling(tok_len, self.DEFAULT)
                continue
            elif tok.isnumeric() or tok == 'self':
                self.setStyling(tok_len, self.CONSTANTS)
            elif tok in ["(", ")", "{", "}", "[", "]"]:
                self.setStyling(tok_len, self.BRACKETS)
            elif tok == '"' or tok == "'":
                self.setStyling(tok_len, self.STRING)
                string_flag = True
            elif tok == "#":
                self.setStyling(tok_len, self.COMMENTS)
                comment_flag = True
            elif tok in self.builtin_names or tok in ['+', '-', '*', '/', '%', '=', '<', '>']:
                self.setStyling(tok_len, self.TYPES)
            else:
                self.setStyling(tok_len, self.DEFAULT)