from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from PyQt5.Qsci import * 


import keyword
import pkgutil
from pathlib import Path
from lexer import PyCustomLexer
from autcompleter import AutoCompleter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import MainWindow

import resources

class Editor(QsciScintilla):
    
    def __init__(self, main_window, parent=None, path: Path = None, is_python_file=True):
        super(Editor, self).__init__(parent)

        self.main_window: MainWindow = main_window
        self._current_file_changed = False
        self.first_launch = True

        self.path = path
        self.full_path = self.path.absolute()
        self.is_python_file = is_python_file
        
        # EDITOR
        self.cursorPositionChanged.connect(self._cusorPositionChanged)        
        self.textChanged.connect(self._textChanged)

        # encoding
        self.setUtf8(True)
        # Font
        self.window_font = QFont("Fire Code") # font needs to be installed in your computer if its not use something else
        self.window_font.setPointSize(12)
        self.setFont(self.window_font)

        # brace matching
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # indentation
        self.setIndentationGuides(True)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.setAutoIndent(True)

        # autocomplete
        self.setAutoCompletionSource(QsciScintilla.AcsAll)
        self.setAutoCompletionThreshold(1) 
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionUseSingle(QsciScintilla.AcusNever)


        # caret
        self.setCaretForegroundColor(QColor("#dedcdc"))
        self.setCaretLineVisible(True)
        self.setCaretWidth(2)
        self.setCaretLineBackgroundColor(QColor("#2c313c"))
        

        # EOL
        self.setEolMode(QsciScintilla.EolWindows)
        self.setEolVisibility(False)


        if self.is_python_file:       
            # lexer for syntax highlighting
            self.pylexer = PyCustomLexer(self) 
            self.pylexer.setDefaultFont(self.window_font)

            self.__api = QsciAPIs(self.pylexer)

            self.auto_completer = AutoCompleter(self.full_path, self.__api)
            self.auto_completer.finished.connect(self.loaded_autocomplete) # you can use this callback to do something 

            self.setLexer(self.pylexer)
        else:
            self.setPaper(QColor("#282c34"))
            self.setColor(QColor("#abb2bf"))


        # line numbers
        self.setMarginType(0, QsciScintilla.NumberMargin)
        self.setMarginWidth(0, "000")
        self.setMarginsForegroundColor(QColor("#ff888888"))
        self.setMarginsBackgroundColor(QColor("#282c34"))
        self.setMarginsFont(self.window_font)

        # key press
        # self.keyPressEvent = self.handle_editor_press

    @property
    def current_file_changed(self):
        return self._current_file_changed
    
    @current_file_changed.setter
    def current_file_changed(self, value: bool):
        curr_index = self.main_window.tab_view.currentIndex()
        if value:
            self.main_window.tab_view.setTabText(curr_index, "*"+self.path.name)
            self.main_window.setWindowTitle(f"*{self.path.name} - {self.main_window.app_name}")
        else:
            if self.main_window.tab_view.tabText(curr_index).startswith("*"):
                self.main_window.tab_view.setTabText(
                    curr_index,
                    self.main_window.tab_view.tabText(curr_index)[1:]
                )
                self.main_window.setWindowTitle(self.main_window.windowTitle()[1:])

        self._current_file_changed = value

    def toggle_comment(self, text: str):
        lines = text.split('\n')
        toggled_lines = []
        for line in lines:
            if line.startswith('#'):
                toggled_lines.append(line[1:].lstrip())
            else:
                toggled_lines.append("# " + line)
        
        return '\n'.join(toggled_lines)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_Space:
            if self.is_python_file:
                pos = self.getCursorPosition()
                self.auto_completer.get_completions(pos[0]+1, pos[1], self.text())
                self.autoCompleteFromAPIs()
                return

        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_X: # CUT SHORTCUT
            if not self.hasSelectedText():
                line, index = self.getCursorPosition()
                self.setSelection(line, 0, line, self.lineLength(line))
                self.cut()
                return
            
        if e.modifiers() == Qt.ControlModifier and e.text() == "/": # COMMENT SHORTCUT
            if self.hasSelectedText():
                start, srow, end, erow = self.getSelection()
                self.setSelection(start, 0, end, self.lineLength(end)-1)
                self.replaceSelectedText(self.toggle_comment(self.selectedText()))
                self.setSelection(start, srow, end, erow)
            else:
                line, _ = self.getCursorPosition()
                self.setSelection(line, 0, line, self.lineLength(line)-1)
                self.replaceSelectedText(self.toggle_comment(self.selectedText()))
                self.setSelection(-1, -1, -1, -1) # reset selection
            return

        return super().keyPressEvent(e)
    
    def _cusorPositionChanged(self, line: int, index: int) -> None:
        if self.is_python_file:
            self.auto_completer.get_completions(line+1, index, self.text())

    def loaded_autocomplete(self):
        pass

    def _textChanged(self):
        if not self.current_file_changed and not self.first_launch:
            self.current_file_changed = True
            
        if self.first_launch:
            self.first_launch = False