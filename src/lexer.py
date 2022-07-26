import builtins
import keyword
import re
import types

from PyQt5.Qsci import QsciLexerCustom, QsciScintilla
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class PyCustomLexer(QsciLexerCustom):

    def __init__(self, parent):
        super(PyCustomLexer, self).__init__(parent)

        self.color1 = "#abb2bf"
        self.color2 = "#282c34"
        
        # Default Settings
        self.setDefaultColor(QColor(self.color1))
        self.setDefaultPaper(QColor(self.color2))
        self.setDefaultFont(QFont("Consolas", 14))

        # Keywords
        self.KEYWORD_LIST = keyword.kwlist

        
        self.builtin_functions_names = [name for name, obj in vars(builtins).items()
                                if isinstance(obj, types.BuiltinFunctionType)]


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

        # styles
        self.setColor(QColor(self.color1), self.DEFAULT)
        self.setColor(QColor("#c678dd"), self.KEYWORD)
        self.setColor(QColor("#56b6c2"), self.TYPES)   
        self.setColor(QColor("#98c379"), self.STRING)
        self.setColor(QColor("#c678dd"), self.KEYARGS)  
        self.setColor(QColor("#c678dd"), self.BRACKETS) 
        self.setColor(QColor("#777777"), self.COMMENTS)  
        self.setColor(QColor("#d19a5e"), self.CONSTANTS)
        self.setColor(QColor("#61afd1"), self.FUNCTIONS)  
        self.setColor(QColor("#C68F55"), self.CLASSES)  
        self.setColor(QColor("#61afd1"), self.FUNCTION_DEF)  


        # paper color
        self.setPaper(QColor(self.color2), self.DEFAULT)
        self.setPaper(QColor(self.color2), self.KEYWORD)
        self.setPaper(QColor(self.color2), self.TYPES)
        self.setPaper(QColor(self.color2), self.STRING)
        self.setPaper(QColor(self.color2), self.KEYARGS)
        self.setPaper(QColor(self.color2), self.BRACKETS)
        self.setPaper(QColor(self.color2), self.COMMENTS)
        self.setPaper(QColor(self.color2), self.CONSTANTS)
        self.setPaper(QColor(self.color2), self.FUNCTIONS)
        self.setPaper(QColor(self.color2), self.CLASSES)
        self.setPaper(QColor(self.color2), self.FUNCTION_DEF)

        # font
        self.setFont(QFont("Consolas", 14, weight=QFont.Bold), self.DEFAULT)
        self.setFont(QFont("Consolas", 14, weight=QFont.Bold), self.KEYWORD)
        self.setFont(QFont("Consolas", 14, weight=QFont.Bold), self.CLASSES)
        self.setFont(QFont("Consolas", 14, weight=QFont.Bold), self.FUNCTION_DEF)


    
    def language(self) -> str:
        return "PYCustomLexer"

    
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
        else:
            return ""

    def get_tokens(self, text) -> list[str, int]:
        # 3. Tokenize the text 
        # ---------------------
        p = re.compile(r"[*]\/|\/[*]|\s+|\w+|\W")

        # 'token_list' is a list of tuples: (token_name, token_len), ex: '(class, 5)' 
        return [ (token, len(bytearray(token, "utf-8"))) for token in p.findall(text)]


    def styleText(self, start: int, end: int) -> None:
        
        self.startStyling(start)
        editor: QsciScintilla = self.parent()

        text = editor.text()[start:end]
        token_list = self.get_tokens(text)


        string_flag = False

        if start > 0:
            previous_style_nr = editor.SendScintilla(editor.SCI_GETSTYLEAT, start - 1)
            if previous_style_nr == self.STRING:
                string_flag = False

        def next_tok(skip: int=None):
            if len(token_list) > 0:
                if skip is not None and skip != 0:
                    for _ in range(skip-1):
                        if len(token_list) > 0:
                            token_list.pop(0)
                return token_list.pop(0)
            else:
                return None
        
        def peek_tok(n=0):
            try:
                return token_list[n]
            except IndexError:
                return ['']

        def skip_sapce_peek(skip=None):
            i = 0
            tok = (' ')
            if skip is not None:
                i = skip
            while tok[0].isspace():
                tok = peek_tok(i)
                i += 1
            return tok, i

        while True:
            curr_token = next_tok()
            if curr_token is None:
                break
            tok: str = curr_token[0]
            tok_len: int = curr_token[1]

            if string_flag:
                self.setStyling(tok_len, self.STRING)
                if tok == '"' or tok == "'":
                    string_flag = False
                continue

            if tok == "class":
                name, ni = skip_sapce_peek()
                brac_or_colon, _ = skip_sapce_peek(ni)
                if name[0].isidentifier() and brac_or_colon[0] in (":", "("):
                    self.setStyling(tok_len, self.KEYWORD)
                    _ = next_tok(ni)
                    self.setStyling(name[1]+1, self.CLASSES)
                    continue
                else:
                    self.setStyling(tok_len, self.KEYWORD)
                    continue
            elif tok == "def":
                name, ni = skip_sapce_peek()
                if name[0].isidentifier():
                    self.setStyling(tok_len, self.KEYWORD)
                    _ = next_tok(ni)
                    self.setStyling(name[1]+1, self.FUNCTION_DEF)
                    continue
                else:
                    self.setStyling(tok_len, self.KEYWORD)
                    continue
            elif tok in self.KEYWORD_LIST:
                self.setStyling(tok_len, self.KEYWORD)
            elif tok.isnumeric() or tok == 'self':
                self.setStyling(tok_len, self.CONSTANTS)
            elif tok in ["(", ")", "{", "}", "[", "]"]:
                self.setStyling(tok_len, self.BRACKETS)
            elif tok == '"' or tok == "'":
                self.setStyling(tok_len, self.STRING)
                string_flag = True
            elif tok in self.builtin_functions_names or tok in ['+', '-', '*', '/', '%', '=', '<', '>']:
                self.setStyling(tok_len, self.TYPES)
            else:
                self.setStyling(tok_len, self.DEFAULT)