import sys

import threading


# QTreeWidget, QFrame

from PySide6.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem, QListWidgetItem, QListView, QScrollArea, QSizePolicy
from PySide6.QtCore import QFile, QSize, QThread, Signal, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPixmap, QImageReader, QIcon, QResizeEvent, QImage

from ui.components import ResizeLabel, ImageDisplayWidget

from config_reader import *
from handle_treewidget import *
from handle_listwidget import *

import logging
# import logging.config

logger = logging.getLogger(__name__)


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
        root_node.setExpanded(True)
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

            # if found duplicated index, show that tab instead of adding a new tab
            if duplicated_index > 0:
                self.main_window.tabWidget.setCurrentIndex(duplicated_index)
            else:

                pic = ImageDisplayWidget()

                reader = QImageReader(item.statusTip())
                reader.setAutoTransform(True)
                image = reader.read()  # QImage
                pic.setImage(image)
                # pic.setMargin(10)

                '''
                
                scrollarea = QScrollArea()
                print(scrollarea.size())
                print(pic.size())
                print(self.main_window.tabWidget.size())
                scrollarea.setWidget(pic)
                scrollarea.setMinimumSize(self.main_window.tabWidget.size())
                scrollarea.resize(self.main_window.tabWidget.size())
                scrollarea.setSizePolicy(
                    QSizePolicy.Expanding, QSizePolicy.Expanding)
                '''

                index = self.main_window.tabWidget.addTab(
                    pic, item.text())
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


'''
    def resizeEvent(self, event: QResizeEvent):
        logger.debug(event)
        logger.debug(self.main_window.listWidget.size())
        return super().resizeEvent(event)

'''
