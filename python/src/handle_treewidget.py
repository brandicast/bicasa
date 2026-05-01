from PySide6.QtCore import QThread, Signal
import os
import logging
from database import DB

logger = logging.getLogger(__name__)


class CollectTreeNodes_Thread(QThread):
    dir_found = Signal(object, object, object)  # parent_path, dir_name, full_path
    finished_scan = Signal()

    def __init__(self, root_path):
        super().__init__()
        self.root_path = root_path
        self.stop_flag = False
        self.db = DB.get_instance()

    def run(self):
        if self.db.hasFolderCache(self.root_path):
            logger.info(f"Loading directory tree from cache for {self.root_path}")
            self.load_from_cache(self.root_path)
        else:
            logger.info(f"Scanning directory tree for {self.root_path}")
            self.collect(self.root_path)
        self.finished_scan.emit()

    def load_from_cache(self, parent_path):
        if self.stop_flag:
            return
        folders = self.db.getFolders(parent_path)
        for name, full_path in folders:
            self.dir_found.emit(parent_path, name, full_path)
            self.load_from_cache(full_path)

    def collect(self, path):
        if self.stop_flag:
            return
        try:
            with os.scandir(path) as entries:
                sorted_entries = sorted(entries, key=lambda e: e.name)
                for entry in sorted_entries:
                    if entry.is_dir():
                        self.db.addFolder(path, entry.name, entry.path)
                        self.dir_found.emit(path, entry.name, entry.path)
                        self.collect(entry.path)
        except Exception as e:
            logger.debug(f"Error scanning {path}: {e}")
