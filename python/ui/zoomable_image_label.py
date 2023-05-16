import inspect
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QSize
from PySide6.QtGui import Qt


import logging
logger = logging.getLogger(__name__)


class Zoomable_Image_Label(QLabel):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(1, 1)
        self.__image = None
        self.size_hint = None
        self.container = None

    def setImage(self, image):
        self.__image = image

        pixmap = QPixmap.fromImage(self.__image)
        scaled = pixmap.scaled(self.size(), Qt.KeepAspectRatio)
        self.setPixmap(scaled)

    # Need the following 2 functions because when initialized, need this for initial size
    def setSizeHint(self, sizeHint):
        self.size_hint = sizeHint
        self.resizeLabel(sizeHint)

    def sizeHint(self):
        return self.size_hint

    def resizePixmap(self, size):
        logger.debug(f"Resizing Pixmap to {size}")
        if self.__image:
            logger.debug(
                f"Label size is: {self.size()}, origin pixmap size is: {self.pixmap().size()}, resizing pixmap to: {size}" + " and is called by " + inspect.stack()[1].function)
            pixmap = QPixmap.fromImage(self.__image)
            scaled = pixmap.scaled(size, Qt.KeepAspectRatio)
            self.setPixmap(scaled)

    def resizeLabel(self, size):
        logger.debug(f"Resizing Label to {size}")
        self.resize(size)

    '''
    # If expect the picture could resize according to the top level window/widget, need the following
    def resizeEvent(self, event):
        self.resizePixmap(event.size())
    '''

    def wheelEvent(self, event):
        newSize = None
        if event.angleDelta().y() > 0:
            logger.debug("Zoom In")
            if self.pixmap().size().width() < self.__image.size().width() and self.pixmap().size().height() < self.__image.size().height():
                newSize = QSize(self.pixmap().size().width() + 100,
                                self.pixmap().size().height() + 100)
        else:
            logger.debug("Zoom Out")
            if self.pixmap().size().width() > 300 and self.pixmap().size().height() > 300:
                newSize = QSize(self.pixmap().size().width() - 100,
                                self.pixmap().size().height() - 100)
        '''
        if newSize != None:
            pixmap = QPixmap.fromImage(self.__image)
            scaled = pixmap.scaled(newSize, Qt.KeepAspectRatio)
            self.setPixmap(scaled)
            logger.info(" Label Size is : " + str(self.size()) +
                        " Pixmap Size is :" + str(newSize))
        '''
        # this is to change the label size, so that the container (scollarea) knows it grows bigger and thereforce display scrollbar
        if newSize != None:
            self.resizePixmap(newSize)
            self.resizeLabel(newSize)
