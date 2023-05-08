from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import QSize
from PySide6.QtGui import Qt
import PySide6
import logging
from typing import Union

from PySide6.QtGui import QPixmap
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QLabel

logger = logging.getLogger(__name__)


class ResizeLabel (QLabel):

    def __init__(self) -> None:
        super().__init__()
        self.dirty = False
        # self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        # self.setScaledContents(True)

    def setPixmap(self, arg__1: Union[PySide6.QtGui.QPixmap, PySide6.QtGui.QImage, str]):
        if not self.dirty:
            self.origin_pixmap = arg__1.copy()
            self.dirty = True
            logger.debug("Keep the origin pixmap")
        super().setPixmap(arg__1)

    def resizeEvent(self, event: PySide6.QtGui.QResizeEvent):
        # logger.info(str(event) + " and self size is :" + str(self.size()))

        # set the pixmal size a bit smaller than current label size
        # if NOT, it causes rescursion.  (May because the pixmap is bigger than the container and then trigger another resize event)
        size = QSize(event.size().width() - self.margin() - self.lineWidth() - 10,
                     event.size().height() - self.margin() - self.lineWidth() - 10)

        # logger.info("pximap size is : " + str(size))

        pix = self.origin_pixmap.scaled(
            size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.setPixmap(pix)
        super().resizeEvent(event)


'''
The following are reference from StackOverflow
'''


class ImageDisplayWidget(QLabel):
    def __init__(self, max_enlargement=2.0):
        super().__init__()
        self.max_enlargement = max_enlargement
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(1, 1)
        self.__image = None

    def setImage(self, image):
        self.__image = image
        self.resize(self.sizeHint())
        self.update()

    def sizeHint(self):
        if self.__image:
            return self.__image.size()  # * self.max_enlargement
        else:
            return QSize(1, 1)

    def resizeEvent(self, event):

        if self.__image:
            pixmap = QPixmap.fromImage(self.__image)
            logger.info(str(event) + " and self size is :" + str(self.size()))
            scaled = pixmap.scaled(event.size(), Qt.KeepAspectRatio)
            self.setPixmap(scaled)
        super().resizeEvent(event)

    def wheelEvent(self, event):
        newSize = None
        if event.angleDelta().y() > 0:
            logger.debug("Zoom In")
            if self.pixmap().size().width() < self.sizeHint().width() and self.pixmap().size().height() < self.sizeHint().height():
                newSize = QSize(self.pixmap().size().width() + 100,
                                self.pixmap().size().height() + 100)
        else:
            logger.debug("Zoom Out")
            if self.pixmap().size().width() > 300 and self.pixmap().size().height() > 300:
                newSize = QSize(self.pixmap().size().width() - 100,
                                self.pixmap().size().height() - 100)
        if newSize != None:
            pixmap = QPixmap.fromImage(self.__image)
            scaled = pixmap.scaled(newSize, Qt.KeepAspectRatio)
            self.setPixmap(scaled)

        # return super().wheelEvent(event)
