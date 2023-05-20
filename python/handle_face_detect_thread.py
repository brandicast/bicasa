from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QPixmap, QImageReader, QIcon


import logging
logger = logging.getLogger(__name__)


# handle tree item click event


class FaceDetect_Thread(QThread):

    def __init__(self, tabwidget):
        self.stop_flag = False
        self.isDetect = True
        self.tabWidget = tabwidget

        logger.debug('Init FaceDetect_Thread')

        super().__init__()

    def setStopFlag(self, stop):
        self.stop_flag = stop

    def setDectect(self, detect: bool):
        self.isDetect = bool

    def run(self):
        logger.debug('run FaceDetect_Thread')
        for i in range(1, self.tabWidget.count()):
            if not self.stop_flag:
                logger.debug(self.tabWidget.tabToolTip(i))
                logger.debug(self.tabWidget.widget(i) == None)
                if self.tabWidget.widget(i) != None:  # PannableScrollArea
                    label = self.tabWidget.widget(
                        i).widget()   # Zoommable_Image_Label  / Zoomable_Mat_Label
                    if self.isDetect:
                        label.findFaces()
                    else:
                        label.reset()

            else:
                break
