import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from PyQt5.Qsci import * 


import sys
from pathlib import Path



class MainWindow(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        # add before init
        self.side_bar_clr = "#282c34"

        self.init_ui()

        self.current_file = None

    def init_ui(self):
        self.setWindowTitle("PYQT EDITOR")
        self.resize(1300, 900)

        self.setStyleSheet(open("./src/css/style.qss", "r").read())

        # alternative Consolas font
        self.window_font = QFont("Fire Code") # font needs to be installed in your computer if its not use something else
        self.window_font.setPointSize(12)
        self.setFont(self.window_font)


        self.set_up_menu()
        self.set_up_body()
        self.statusBar().showMessage("heelo")

        

        self.show()


    def set_up_menu(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("File")
        
        new_file = file_menu.addAction("New")
        new_file.setShortcut("Ctrl+N")
        new_file.triggered.connect(self.new_file)

        open_file = file_menu.addAction("Open File")
        open_file.setShortcut("Ctrl+O")
        open_file.triggered.connect(self.open_file)

        open_folder = file_menu.addAction("Open File")
        open_folder.setShortcut("Ctrl+K")
        open_folder.triggered.connect(self.open_folder)


        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        
        copy_action = edit_menu.addAction("Copy")
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)
        # you can add more

    
    def new_file(self):
        ...
    
    def open_file(self):
        ...

    def open_folder(self):
        ...

    def copy(self):
        ...
    
    def get_editor(self) -> QsciScintilla:
        
        #instance
        editor = QsciScintilla()
        # encoding
        editor.setUtf8(True)
        # Font
        editor.setFont(self.window_font)

        # brace matching
        editor.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # indentation
        editor.setIndentationGuides(True)
        editor.setTabWidth(4)
        editor.setIndentationsUseTabs(False)
        editor.setAutoIndent(True)


        # autocomplete
        # TODO: add autocomplete next video

        # caret
        # TODO: ADD caret settings next video

        # EOL
        editor.setEolMode(QsciScintilla.EolWindows)
        editor.setEolVisibility(False)


        # lexer 
        # TODO: add lexer next video
        editor.setLexer(None)


        return editor


    def is_binary(self, path):
        '''
        Check if file is binary
        '''
        with open(path, 'rb') as f:
            return b'\0' in f.read(1024)


    def set_new_tab(self, path: Path, is_new_file=False):
        if not path.is_file():
            return
        if not is_new_file and self.is_binary(path):
            self.statusBar().showMessage("Cannot Open Binary File", 2000)
            return

        
        # check if file already open
        if not is_new_file:
            for i in range(self.tab_view.count()):
                if self.tab_view.tabText(i) == path.name:
                    self.tab_view.setCurrentIndex(i)
                    self.current_file = path
                    return

        # create new tab
        editor = self.get_editor()

        self.tab_view.addTab(editor, path.name)
        if not is_new_file:
            editor.setText(path.read_text())
        self.setWindowTitle(path.name)
        self.current_file = path
        self.tab_view.setCurrentIndex(self.tab_view.count() - 1)
        self.statusBar().showMessage(f"Opened {path.name}", 2000)



    def set_up_body(self):

        # Body        
        body_frame = QFrame()
        body_frame.setFrameShape(QFrame.NoFrame)
        body_frame.setFrameShadow(QFrame.Plain)
        body_frame.setLineWidth(0)
        body_frame.setMidLineWidth(0)
        body_frame.setContentsMargins(0, 0, 0, 0)
        body_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body_frame.setLayout(body)

        # side_bar
        self.side_bar = QFrame()
        self.side_bar.setFrameShape(QFrame.StyledPanel)
        self.side_bar.setFrameShadow(QFrame.Plain)
        self.side_bar.setStyleSheet(f'''
            background-color: {self.side_bar_clr};
        ''')   
        side_bar_layout = QHBoxLayout()
        side_bar_layout.setContentsMargins(5, 10, 5, 0)
        side_bar_layout.setSpacing(0)
        side_bar_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)

        # setup labels
        folder_label = QLabel()
        folder_label.setPixmap(QPixmap("./src/icons/folder-icon-blue.svg").scaled(QSize(25, 25)))
        folder_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        folder_label.setFont(self.window_font)
        folder_label.mousePressEvent = self.show_hide_tab
        side_bar_layout.addWidget(folder_label)
        self.side_bar.setLayout(side_bar_layout)

        body.addWidget(self.side_bar)

        # split view
        self.hsplit = QSplitter(Qt.Horizontal)

        # frame and layout to hold tree view (file manager)
        self.tree_frame = QFrame()
        self.tree_frame.setLineWidth(1)
        self.tree_frame.setMaximumWidth(400)
        self.tree_frame.setMinimumWidth(200)
        self.tree_frame.setBaseSize(100, 0)
        self.tree_frame.setContentsMargins(0, 0, 0, 0)
        tree_frame_layout = QVBoxLayout()
        tree_frame_layout.setContentsMargins(0, 0, 0, 0)
        tree_frame_layout.setSpacing(0)
        self.tree_frame.setStyleSheet('''
            QFrame {
                background-color: #21252b;
                border-radius: 5px;
                border: none;
                padding: 5px;
                color: #D3D3D3;
            }
            QFrame:hover {
                color: white;
            }
        ''')

        # Create file system model to show in tree view
        self.model = QFileSystemModel()
        self.model.setRootPath(os.getcwd())
        # File system filters
        self.model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files)

        # Tree View 
        self.tree_view = QTreeView()
        self.tree_view.setFont(QFont("FiraCode", 13))
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(os.getcwd()))
        self.tree_view.setSelectionMode(QTreeView.SingleSelection)
        self.tree_view.setSelectionBehavior(QTreeView.SelectRows)
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)
        # add custom context menu
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.tree_view_context_menu)
        # handling click
        self.tree_view.clicked.connect(self.tree_view_clicked)
        self.tree_view.setIndentation(10)
        self.tree_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
         # Hide header and hide other columns except for name
        self.tree_view.setHeaderHidden(True) # hiding header
        self.tree_view.setColumnHidden(1, True)
        self.tree_view.setColumnHidden(2, True)
        self.tree_view.setColumnHidden(3, True)

        # setup layout
        tree_frame_layout.addWidget(self.tree_view)
        self.tree_frame.setLayout(tree_frame_layout)


        # Tab Widget to add editor to
        self.tab_view = QTabWidget()
        self.tab_view.setContentsMargins(0, 0, 0, 0)
        self.tab_view.setTabsClosable(True)
        self.tab_view.setMovable(True)
        self.tab_view.setDocumentMode(True)
        # self.tab_view.tabsClos

        # add tree view and tab view
        self.hsplit.addWidget(self.tree_frame)
        self.hsplit.addWidget(self.tab_view)


        body.addWidget(self.hsplit)
        body_frame.setLayout(body)


        self.setCentralWidget(body_frame)

    def show_hide_tab(self):
        ...


    def tree_view_context_menu(self, pos):
        ...


    def tree_view_clicked(self, index: QModelIndex):
        path = self.model.filePath(index)
        p = Path(path)
        self.set_new_tab(p)
       



if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    sys.exit(app.exec())















