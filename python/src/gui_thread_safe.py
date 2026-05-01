
from PySide6.QtWidgets import QMainWindow, QTreeWidgetItem, QListWidgetItem, QListView, QApplication, QLabel, QVBoxLayout, QWidget, QSizePolicy
from PySide6.QtCore import QFile, QSize
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QMovie

from ui.pannable_scrollarea import PannableScrollArea
from ui.zoomable_image_label import Zoomable_Image_Label, Zoomable_Mat_Label
from ui.photo_label import Photo_Label
from ui.status_widget import StatusWidget
from ui.media_item_delegate import MediaItemDelegate, THUMBNAIL_SIZE

from config_reader import *
from handle_treewidget import *
from handle_listwidget import *
# from handle_face_detect_thread import FaceDetect_Thread

import logging
# import logging.config

logger = logging.getLogger(__name__)


class Window (QMainWindow):
    def __init__(self, parent=None):
        logger.info("Init MainWindow")
        super().__init__(parent)
        self.setObjectName("MainWindow")
        from pathlib import Path
        design_path = str(Path(__file__).parent / config["gui"]["design"])
        ui_file = QFile(design_path)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.main_window = loader.load(ui_file)
        self.setCentralWidget(self.main_window)
        root = config["app"]["root"]
        # root = '.'

        # status bar
        self.statusWidget = StatusWidget(self.main_window.statusbar)

        # TreeWidget init below
        root_node = QTreeWidgetItem(self.main_window.treeWidget)
        root_node.setText(0, root)
        root_node.setExpanded(True)
        self.main_window.treeWidget.setColumnCount(1)
        self.main_window.treeWidget.insertTopLevelItem(0, root_node)
        
        self.tree_nodes_map = {root: root_node}
        self.tree_thread = CollectTreeNodes_Thread(root)
        from PySide6.QtCore import Qt, Slot
        self.tree_thread.dir_found.connect(self.on_tree_dir_found, Qt.QueuedConnection)
        self.tree_thread.finished_scan.connect(self.on_tree_finished, Qt.QueuedConnection)
        self.statusWidget.startLoadingAnimation()
        self.tree_thread.start()
        # event connect
        self.main_window.treeWidget.itemClicked.connect(
            self.onTreeItemClicked)   # regiter tree item click event

        # tab_1 > listWidget init
        self.main_window.listWidget.setViewMode(QListView.IconMode)
        self.main_window.listWidget.setIconSize(QSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE))
        self.main_window.listWidget.setResizeMode(QListView.Adjust)
        self.main_window.listWidget.setSpacing(6)   # inter-cell gap; padding is inside delegate
        self.main_window.listWidget.setUniformItemSizes(True)
        self.main_window.listWidget.setItemDelegate(MediaItemDelegate(self.main_window.listWidget))
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
        self.main_window.actionFaceEnable.triggered.connect(
            self.toggleInstanceFaceDetection)
        self.main_window.actionFaceDisable.triggered.connect(
            self.toggleInstanceFaceDetection)

        self.main_window.actionConfiguration.triggered.connect(
            self.onConfigurationTriggered)

    from PySide6.QtCore import Slot
    @Slot(object, object, object)
    def on_tree_dir_found(self, parent_path, dir_name, full_path):
        parent_node = self.tree_nodes_map.get(parent_path)
        if parent_node:
            node = QTreeWidgetItem(parent_node)
            node.setText(0, dir_name)
            self.tree_nodes_map[full_path] = node

    def on_tree_finished(self):
        self.statusWidget.stopLoadingAnimation()
        self.tree_nodes_map.clear()
        
    def onConfigurationTriggered(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Configuration", "Configuration editor is not yet implemented.\nPlease edit conf/config.ini manually for now.")

    def addListWidgetItem(self, icon, path, isStopped):
        if not isStopped:
            list_widget_item = QListWidgetItem(icon, path.name)
            list_widget_item.setStatusTip(str(path))
            self.main_window.listWidget.addItem(list_widget_item)

    def onCloseTab(self, index):
        if index != 0:
            current_widget = self.main_window.tabWidget.widget(index)
            if hasattr(current_widget, 'stop'):
                current_widget.stop()
            self.main_window.tabWidget.removeTab(index)

    def onTabChanged(self, index):
        logger.debug(f"Tab change to index :{index}")
        if index > 0:
            current_widget = self.main_window.tabWidget.widget(index)
            if isinstance(current_widget, PannableScrollArea):
                current_widget.widget().enableFaceDetect(
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
                file_path = item.statusTip()
                from pathlib import Path
                ext = Path(file_path).suffix.lower()
                video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.wmv'}
                
                if ext in video_extensions:
                    from ui.video_player_widget import VideoPlayerWidget
                    player = VideoPlayerWidget()
                    player.load_video(file_path)
                    widget_to_add = player
                else:
                    scrollarea = PannableScrollArea()
                    scrollarea.resize(self.main_window.listWidget.size())
                    logger.debug("Before")
                    pic = Photo_Label()
                    pic.start_animation.connect(
                        self.statusWidget.startLoadingAnimation)
                    pic.stop_animation.connect(
                        self.statusWidget.stopLoadingAnimation)

                    # pic = Zoomable_Image_Label()
                    # pic.setSizeHint(self.main_window.listWidget.size())
                    pic.resize(scrollarea.size())
                    pic.setImagePath(file_path)
                    logger.debug("After")
                    # scrollarea = PannableScrollArea()
                    scrollarea.setWidget(pic)
                    scrollarea.setWidgetResizable(False)

                    pic.mousePressEvent = scrollarea.mouse_press
                    pic.mouseMoveEvent = scrollarea.mouse_move
                    pic.mouseReleaseEvent = scrollarea.mouse_release

                    pic.enableFaceDetect(
                        self.main_window.actionFaceEnable.isChecked())
                    widget_to_add = scrollarea

                logger.debug(self.main_window.tabWidget.size())
                logger.debug(self.main_window.listWidget.size())

                index = self.main_window.tabWidget.addTab(
                    widget_to_add, item.text())
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
        # Clean up thread reference after it finishes to prevent memory leak
        workerthread.finished.connect(lambda t=workerthread: self.listWidget_running_thread.remove(t) if t in self.listWidget_running_thread else None)
        
        # self.workerThread.started.connect(collect_item_task.run)
        workerthread.start()

    def toggleInstanceFaceDetection(self):

        if self.sender() == self.main_window.actionFaceEnable:
            self.main_window.actionFaceDisable.toggle()
        else:
            self.main_window.actionFaceEnable.toggle()

        if type(self.main_window.tabWidget.currentWidget()) is PannableScrollArea:
            self.main_window.tabWidget.currentWidget().widget().enableFaceDetect(
                self.main_window.actionFaceEnable.isChecked())

    def keyPressEvent(self, event):
        from PySide6.QtCore import Qt
        if self.main_window.tabWidget.currentIndex() > 0:
            if event.key() == Qt.Key_Left:
                self.switchImage(-1)
            elif event.key() == Qt.Key_Right:
                self.switchImage(1)
        super().keyPressEvent(event)

    def switchImage(self, direction):
        current_path = self.main_window.tabWidget.tabToolTip(self.main_window.tabWidget.currentIndex())
        list_count = self.main_window.listWidget.count()
        if list_count == 0:
            return
            
        for i in range(list_count):
            item = self.main_window.listWidget.item(i)
            if item.statusTip() == current_path:
                next_index = (i + direction) % list_count
                next_item = self.main_window.listWidget.item(next_index)
                
                # Close current tab to act as a switch
                current_tab_idx = self.main_window.tabWidget.currentIndex()
                self.main_window.tabWidget.removeTab(current_tab_idx)
                
                # Open next item
                self.listWigetItemDoubleClicked(next_item)
                break

    def closeEvent(self, event):
        logger.info("Closing application, stopping threads...")
        if hasattr(self, 'tree_thread') and self.tree_thread.isRunning():
            self.tree_thread.stop_flag = True
            self.tree_thread.wait()
            
        for thread in self.listWidget_running_thread:
            thread.setStopFlag(True)
            thread.wait()
            
        super().closeEvent(event)
