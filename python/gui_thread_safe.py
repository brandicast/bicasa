import sys

import threading


# QTreeWidget, QFrame

from PySide6.QtWidgets import QMainWindow, QTreeWidgetItem, QListWidgetItem, QListView, QApplication, QVBoxLayout, QWidget, QSizePolicy
from PySide6.QtCore import QFile, QSize
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QImageReader, QResizeEvent

from ui.pannable_scrollarea import PannableScrollArea
from ui.zoomable_image_label import Zoomable_Image_Label, Zoomable_Mat_Label

from config_reader import *
from handle_treewidget import *
from handle_listwidget import *
from handle_face_detect_thread import FaceDetect_Thread

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
        tree = CollectTreeNodes()
        tree.collect(root, root_node)
        self.main_window.treeWidget.setColumnCount(1)
        self.main_window.treeWidget.insertTopLevelItem(0, root_node)
        # event connect
        self.main_window.treeWidget.itemClicked.connect(
            self.onTreeItemClicked)   # regiter tree item click event

        # tab_1 > listWidget init
        self.main_window.listWidget.setViewMode(QListView.IconMode)
        self.main_window.listWidget.setIconSize(QSize(150, 150))
        self.main_window.listWidget.setResizeMode(QListView.Adjust)
        self.main_window.listWidget.setSpacing(3)
        # when item in list widget is clicked
        self.main_window.listWidget.itemDoubleClicked.connect(
            self.listWigetItemDoubleClicked)
        # declare a list to hold the reference of threads...
        self.listWidget_running_thread = []
        self.face_detect_enable_theadpool = []
        self.face_detect_disable_theadpool = []  # [TO BE IMPLEMENT LATER]

        # when tab is close
        self.main_window.tabWidget.tabCloseRequested.connect(self.onCloseTab)
        self.main_window.tabWidget.currentChanged.connect(self.onTabChanged)

        # Menu Actions
        self.main_window.actionExit.triggered.connect(QApplication.quit)

        self.main_window.menuInstant_Detect.aboutToHide.connect(
            self.hideAllMenu)

        self.main_window.actionFaceEnable.triggered.connect(
            self.toggleInstanceFaceDetection)
        self.main_window.actionFaceDisable.triggered.connect(
            self.toggleInstanceFaceDetection)

    def addListWidgetItem(self, icon, path, isStopped):
        if not isStopped:
            list_widget_item = QListWidgetItem(icon, path.name)
            list_widget_item.setStatusTip(str(path))
            self.main_window.listWidget.addItem(list_widget_item)

    def onCloseTab(self, index):
        if index != 0:
            self.main_window.tabWidget.removeTab(index)

    def onTabChanged(self, index):
        logger.debug(f"Tab change to index :{index}")
        if index > 0:
            self.main_window.tabWidget.widget(index).widget().enableFaceDetect(
                self.main_window.actionFaceEnable.isChecked())

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

                scrollarea = PannableScrollArea()
                scrollarea.resize(self.main_window.listWidget.size())
                logger.debug("Before")
                pic = Zoomable_Mat_Label()
                # pic.setSizeHint(self.main_window.listWidget.size())
                pic.resize(scrollarea.size())
                pic.setImagePath(item.statusTip())
                logger.debug("After")
                # scrollarea = PannableScrollArea()
                scrollarea.setWidget(pic)
                scrollarea.setWidgetResizable(False)

                pic.mousePressEvent = scrollarea.mouse_press
                pic.mouseMoveEvent = scrollarea.mouse_move
                pic.mouseReleaseEvent = scrollarea.mouse_release

                pic.enableFaceDetect(
                    self.main_window.actionFaceEnable.isChecked())

                logger.debug(self.main_window.tabWidget.size())
                logger.debug(self.main_window.listWidget.size())
                logger.debug(pic.size())
                logger.debug(scrollarea.size())

                index = self.main_window.tabWidget.addTab(
                    scrollarea, item.text())
                # Trying to use statusTip as id of the tab.   To avoid the same picture is opened twice
                self.main_window.tabWidget.setTabToolTip(
                    index, item.statusTip())

                self.main_window.tabWidget.setCurrentIndex(index)

    def onTreeItemClicked(self, item, col):
        logger.debug('onTreeItemClicked')

        # If there was any thread running, stop them....
        for thread in self.listWidget_running_thread:
            thread.setStopFlag(True)

        item.setExpanded(True)

        # clear listWidget item
        self.main_window.listWidget.clear()

        self.main_window.tabWidget.setTabText(0, getFullPath(item))
        self.main_window.tabWidget.setCurrentIndex(0)

        workerthread = CollectListWidgetItem_Thread(item)
        self.listWidget_running_thread.append(workerthread)

        # below is where to receive the signal from the thread
        workerthread.resultReady.connect(self.addListWidgetItem)
        # self.workerThread.started.connect(collect_item_task.run)
        workerthread.start()

    def toggleInstanceFaceDetection(self):

        if self.sender() == self.main_window.actionFaceEnable:
            self.main_window.actionFaceDisable.toggle()
        else:
            self.main_window.actionFaceEnable.toggle()

        self.main_window.tabWidget.currentWidget().widget().enableFaceDetect(
            self.main_window.actionFaceEnable.isChecked())

        self.main_window.menuA_I.show()
        self.main_window.menuFace_Detection.show()
        self.main_window.menuInstant_Detect.show()

    def hideAllMenu(self):
        self.main_window.menuA_I.hide()
        self.main_window.menuFace_Detection.hide()
        # self.main_window.menuInstant_Detect.show()

    '''
    def handleFaceDetection(self):
        logger.debug(
            "Hi ! " + str(self.main_window.actionFaceEnable.isChecked()))

    '''
