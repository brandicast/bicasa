
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QStatusBar
from PySide6.QtGui import QMovie

from config_reader import *

import logging
logger = logging.getLogger(__name__)


class StatusWidget (QWidget):

    def __init__(self, statusbar: QStatusBar) -> None:
        super().__init__()
        self.info_label = QLabel("info")
        self.msg_label = QLabel("msg")
        self.loading_label = QLabel()
        loading_icon = config['app']['loading_gif']
        logger.debug("Loading_icon : " + loading_icon)

        self.loading_label.setFixedSize(30, 20)
        # loadingBar.setStyleSheet("border: 1px solid black;")
        self.loading_label.setScaledContents(True)
        self.movie = QMovie('ui/loading.gif')

        '''
        layout = QHBoxLayout()
        layout.addWidget(self.info_label)
        layout.addWidget(self.msg_label)
        layout.addWidget(self.loading_label)
        self.setLayout(layout)
        '''
        statusbar.addPermanentWidget(self.info_label)
        statusbar.addPermanentWidget(self.msg_label)
        statusbar.addPermanentWidget(self.loading_label)

    def setInfoText(self, text):
        self.info_label.setText(text)

    def clearInfoText(self):
        self.info_label.clear()

    def setMsgText(self, text):
        self.msg_label.setText(text)

    def clearInfoText(self):
        self.msg_label.clear()

    def startLoadingAnimation(self):
        self.loading_label.setMovie(self.movie)
        self.movie.start()

    def stopLoadingAnimation(self):
        self.movie.stop()
        self.loading_label.clear()
