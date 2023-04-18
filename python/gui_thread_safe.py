import sys
import os
import threading
from pathlib import Path

# QTreeWidget, QFrame

from PySide6.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem, QListWidgetItem, QListView, QLabel
from PySide6.QtCore import QFile, QSize, QThread, Signal, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPixmap, QImageReader, QIcon, QScreen


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
    # The signal respectively contains :
    #               1)  A loaded QIcon represent the picture
    #               2)  path
    #               3)  whether this thread is about to stop or not    -> to prevent the thread was stopped but still add item into listwidget
    #               4)  name of the slot
    signal = Signal(QIcon, Path, bool, name='resultReady')

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

        for entry in path.iterdir():
            if entry.is_file() and not self.stop_flag:
                try:
                    # [NOTE] Executing QImageReader.setAllocationLimit(0) disables the 128MB limitation,
                    reader = QImageReader(str(entry))
                    reader.setAutoTransform(True)
                    image = reader.read()  # QImage
                    if image != None:
                        pixmap = QPixmap.fromImage(image)
                        self.signal.emit(
                            QIcon(pixmap), entry, self.stop_flag)
                    '''
                    # Was setting QIcon size in UI level.  
                    # However, could check if scaled is needed to ease memory
                    thumbnail_size = int(config["gui"]["thumbnail_size"])
                    pixmap.scaled(thumbnail_size, thumbnail_size, Qt.KeepAspectRatio)
                    '''

                except:
                    logger.error('Reading ' + entry.name + ' with error !')
            else:
                break


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

        # when item in list widget is clicked
        self.main_window.listWidget.itemDoubleClicked.connect(
            self.listWigetItemDoubleClicked)

        # when tab is close
        self.main_window.tabWidget.tabCloseRequested.connect(self.onCloseTab)

        # declare a list to hold the reference of threads...
        self.running_thread = []

    def addListWidgetItem(self, icon, path, isStopped):
        if not isStopped:
            list_widget_item = QListWidgetItem(icon, path.name)
            list_widget_item.setStatusTip(str(path))
            self.main_window.listWidget.addItem(list_widget_item)

    def onCloseTab(self, index):
        if index != 0:
            self.main_window.tabWidget.removeTab(index)

    def listWigetItemDoubleClicked(self, item):
        logger.debug("listWidgetItem Doubleclicked")

        if self.main_window.tabWidget.count() > 0:
            # Here are checking if there's duplicated "path" already opened by borrowing listWidgetItem.statusTip()/tabWidget.tabToolTip()
            # Which is the full path of the picture
            duplicated_index = 0

            for i in range(1, self.main_window.tabWidget.count()):
                if self.main_window.tabWidget.tabToolTip(i) == item.statusTip():
                    duplicated_index = i
                    break

            if duplicated_index > 0:
                self.main_window.tabWidget.setCurrentIndex(duplicated_index)
            else:
                pic = QLabel()
                pic.setPixmap(item.icon().pixmap(
                    self.main_window.listWidget.size(), QIcon.Normal))

                pic.setAlignment(Qt.AlignCenter)

                index = self.main_window.tabWidget.addTab(pic, item.text())
                # Trying to use statusTip as id of the tab.   To avoid the same picture is opened twice
                self.main_window.tabWidget.setTabToolTip(
                    index, item.statusTip())

                self.main_window.tabWidget.setCurrentIndex(index)

    def onTreeItemClicked(self, item, col):
        logger.debug('onTreeItemClicked')

        # If there was any thread running, stop them....
        for thread in self.running_thread:
            thread.setStopFlag(True)

        item.setExpanded(True)

        # clear listWidget item
        self.main_window.listWidget.clear()

        self.main_window.tabWidget.setTabText(0, getFullPath(item))
        self.main_window.tabWidget.setCurrentIndex(0)

        workerthread = CollectListWidgetItem_Thread(item)
        self.running_thread.append(workerthread)

        # below is where to receive the signal from the thread
        workerthread.resultReady.connect(self.addListWidgetItem)
        # self.workerThread.started.connect(collect_item_task.run)
        workerthread.start()
