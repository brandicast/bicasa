import sys
import os
import threading
from pathlib import Path

# QTreeWidget, QFrame

from PySide6.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem, QListWidgetItem, QListView
from PySide6.QtCore import QFile, QSize, QObject, QThread, Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPixmap, QImageReader, QIcon


from config_setup import *
import logging
import logging.config

logger = logging.getLogger(__name__)


def collectTreeNodes(path, parent):
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_dir():
                node = QTreeWidgetItem(parent)
                node.setText(0, entry.name)
                parent.addChild(node)
                collectTreeNodes(entry.path, node)


# iterate thru all parent of the tree item to get the full path
def getFullPath(item):
    x = item
    path_str = item.text(0)

    while x.parent():
        x = x.parent()
        path_str = str(Path(x.text(0)).joinpath(
            path_str))  # May be optimized a bit?
    return path_str

# handle tree item click event


class CollectListWidgetItem_Thread(QThread):
    # define Signal to pass the loaded QICon and filename out to QApp level
    signal = Signal(QIcon, str, name='resultReady')

    def __init__(self, item):
        self.item = item
        self.stop_flag = False
        super().__init__()
        logger.debug('Init CollectListWidgetItem')

    def setStopFlag(self, stop):
        self.stop_flag = stop

    def run(self):
        logger.debug('run CollectListWidgetItem')
        path = Path(getFullPath(self.item))

        for filename in path.iterdir():
            if not self.stop_flag:
                try:
                    reader = QImageReader(str(filename))
                    reader.setAutoTransform(True)
                    image = reader.read()  # QImage
                    pixmap = QPixmap.fromImage(image)
                    '''
                    # Was setting QIcon size in UI level.  
                    # However, could check if scaled is needed to ease memory
                    thumbnail_size = int(config["gui"]["thumbnail_size"])
                    pixmap.scaled(thumbnail_size, thumbnail_size, Qt.KeepAspectRatio)
                    '''
                    self.signal.emit(QIcon(pixmap), filename.name)
                except:
                    logger.error('Reading ' + filename.name + ' with error !')


class Window (QMainWindow):
    def __init__(self, parent=None):
        logger.info("Init MainWindow")
        super().__init__(parent)
        ui_file = QFile(config["gui"]["design"])
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.main_window = loader.load(ui_file)
        self.setCentralWidget(self.main_window)
        root = config["app"]["root"]
        # root = '.'

        # TreeWidget init below
        root_node = QTreeWidgetItem(self.main_window.treeWidget)
        root_node.setText(0, root)
        collectTreeNodes(root, root_node)
        self.main_window.treeWidget.setColumnCount(1)
        self.main_window.treeWidget.insertTopLevelItem(0, root_node)

        # tab_1 > listWidget init
        self.main_window.listWidget.setViewMode(QListView.IconMode)
        self.main_window.listWidget.setIconSize(QSize(150, 150))
        self.main_window.listWidget.setResizeMode(QListView.Adjust)

        # main_window.listWidget.setUniformItemSizes(True)

        # event connect
        self.main_window.treeWidget.itemClicked.connect(
            self.onTreeItemClicked)   # regiter tree item click event

    def addListWidgetItem(self, icon, text):
        self.main_window.listWidget.addItem(QListWidgetItem(icon, text))

    def onTreeItemClicked(self, item, col):
        logger.debug('onTreeItemClicked')
        self.main_window.listWidget.clear()
        workerthread = CollectListWidgetItem_Thread(item)

        workerthread.resultReady.connect(win.addListWidgetItem)
        # self.workerThread.started.connect(collect_item_task.run)
        workerthread.start()


app = QApplication(sys.argv)
win = Window()
win.show()
sys.exit(app.exec())
