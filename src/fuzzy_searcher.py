from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QListWidgetItem

import os
from pathlib import Path
import re



class SearchItem(QListWidgetItem):
    def __init__(self, name, full_path, lineno, end, line):
        self.name = name
        self.full_path = full_path
        self.lineno = lineno
        self.end = end
        self.line = line
        self.formatted = f'{self.name}:{self.lineno}:{self.end} - {self.line} ...'
        super().__init__(self.formatted)


    def __str__(self):
        return self.formatted

    def __repr__(self):
        return self.formatted


class SearchWorker(QThread):
    finished = pyqtSignal(list)

    def __init__(self):
        super(SearchWorker, self).__init__(None)
        self.items = []
        self.search_path: str = None
        self.search_text: str = None
        self.search_project: bool = None

    def is_binary(self, path):
            '''
            Check if file is binary
            '''
            with open(path, 'rb') as f:
                return b'\0' in f.read(1024)

    def walkdir(self, path, exclude_dirs: list, exclude_files: list):
        for root, dirs, files, in os.walk(path, topdown=True):
            # filtering
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            files[:] = [f for f in files if Path(f).suffix not in exclude_files]
            yield root, dirs, files

    def search(self):
        debug = False
        self.items = []
        # you can add more
        exclude_dirs = set([".git", ".svn", ".hg", ".bzr", ".idea", "__pycache__", "venv"])
        if self.search_project:
            exclude_dirs.remove("venv")
        exclude_files = set([".svg", ".png", ".exe", ".pyc", ".qm"])

        for root, _, files in self.walkdir(self.search_path, exclude_dirs, exclude_files):
            # total search limit
            if len(self.items) > 5_000:
                break
            for file_ in files:
                full_path = os.path.join(root, file_)
                if self.is_binary(full_path):
                    break        

                try: 
                    with open(full_path, 'r', encoding='utf8') as f:
                        try:
                            reg = re.compile(self.search_text, re.IGNORECASE)
                            for i, line in enumerate(f):
                                if m := reg.search(line):
                                    fd = SearchItem(
                                        file_,
                                        full_path,
                                        i,
                                        m.end(),
                                        line[m.start():].strip()[:50], # limiting to 50 chars
                                    )
                                    self.items.append(fd)
                        except re.error as e:
                            if debug: print(e)
                except UnicodeDecodeError as e:
                    if debug: print(e)
                    continue

        self.finished.emit(self.items)

    def run(self):
        self.search()

    def update(self, pattern, path, search_project):
        self.search_text = pattern
        self.search_path = path
        self.search_project = search_project
        self.start()
