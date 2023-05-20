import inspect
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtGui import Qt, QPixmap, QImageReader, QImage
from PySide6.QtCore import QSize, QObject, Signal, QThread

import cv2
from utils.opencv_util import cv2_loadimage
from utils.ai import AI


import logging
logger = logging.getLogger(__name__)


class Zoomable_Image_Label(QLabel):

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(1, 1)
        self.image = None
        self.size_hint = None

    # Load Image as QImage
    def setImagePath(self, image_path):
        reader = QImageReader(image_path)
        reader.setAutoTransform(True)
        self.image = reader.read()  # QImage
        pixmap = self.imageToPixmap()
        scaled = pixmap.scaled(self.size(), Qt.KeepAspectRatio)
        self.setPixmap(scaled)

    # Reset pixmap to origin image
    def reset(self):
        if self.image != None:
            pixmap = self.imageToPixmap()
            scaled = pixmap.scaled(self.size(), Qt.KeepAspectRatio)
            self.setPixmap(scaled)

    # Return image as QImage
    def Image(self):
        return self.image

    def getImageSize(self) -> QSize:
        if self.image != None:
            return self.image.size()

    def imageToPixmap(self):
        return QPixmap.fromImage(self.image)

    '''
    # Need the following 2 functions because when initialized, need this for initial size
    def setSizeHint(self, sizeHint):
        self.size_hint = sizeHint
        self.resizeLabel(sizeHint)
    '''

    def resizePixmap(self, size):
        logger.debug(f"Resizing Pixmap to {size}")

        logger.debug(
            f"Label size is: {self.size()}, origin pixmap size is: {self.pixmap().size()}, resizing pixmap to: {size}" + " and is called by " + inspect.stack()[1].function)
        pixmap = self.imageToPixmap()
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
        origin_size = self.getImageSize()
        if event.angleDelta().y() > 0:
            logger.debug("Zoom In")
            if self.pixmap().size().width() < origin_size.width() and self.pixmap().size().height() < origin_size.height():
                newSize = QSize(self.pixmap().size().width() + 100,
                                self.pixmap().size().height() + 100)
        else:
            logger.debug("Zoom Out")
            if self.pixmap().size().width() > 300 and self.pixmap().size().height() > 300:
                newSize = QSize(self.pixmap().size().width() - 100,
                                self.pixmap().size().height() - 100)

        # this is to change the label size, so that the container (scollarea) knows it grows bigger and thereforce display scrollbar
        if newSize != None:
            self.resizePixmap(newSize)
            self.resizeLabel(newSize)


class Zoomable_Mat_Label(Zoomable_Image_Label):

    def __init__(self):
        super().__init__()
        self.face_coordiates = None
        self.detected = False
        self.t = None

    # [Override] Load Image as OpenCV Mat

    def setImagePath(self, image_path):
        try:
            logger.debug("A")
            self.image = cv2_loadimage(image_path, cv2.IMREAD_COLOR)
            logger.debug("B")
            self.updateMatToPixmap(self.image)
            logger.debug("C")
        except Exception as e:
            logger.error(e)

    # [Override]
    def getImageSize(self) -> QSize:
        return QSize(self.image.shape[1], self.image.shape[0])

    # [Override]
    def imageToPixmap(self):
        qimage = self.__Mat_To_QImage__(self.image)
        return QPixmap.fromImage(qimage)

    # [Override] Need to check if the image is not initialized
    def reset(self):
        pixmap = self.imageToPixmap()
        scaled = pixmap.scaled(self.size(), Qt.KeepAspectRatio)
        self.setPixmap(scaled)

    def enableFaceDetect(self, enable: bool):
        logger.debug(f"{enable} and {self.detected}")
        if enable and not self.detected:
            logger.debug("Detecting Face.....")
            self.findFaces()
            self.detected = True
        elif not enable and self.detected:
            logger.debug("Reset Detecting Face.....")
            self.reset()
            self.detected = False

    # This is when Mat is temperary being changed and want to keep the origin mat
    # May change to graphic item instead

    def updateMatToPixmap(self, mat):
        try:
            qimage = self.__Mat_To_QImage__(mat)
            logger.debug("W")
            pixmap = QPixmap.fromImage(qimage)
            logger.debug("F")
            scaled = pixmap.scaled(self.size(), Qt.KeepAspectRatio)
            self.setPixmap(scaled)
            logger.debug("G")
        except Exception as e:
            logger.debug(e)

    def __Mat_To_QImage__(self, mat):
        try:
            logger.debug(f"D :  {mat.shape} ")
            qimage = QImage(mat, mat.shape[1],
                            mat.shape[0], QImage.Format_BGR888)
            logger.debug(f"E : {type(qimage)}")
        except Exception as e:
            logger.debug(e)
        return qimage

    def findFaces(self):
        if self.face_coordiates is None:
            self.t = FaceFinder(self.image)
            self.t.resultReady.connect(self.drawFaces)
            self.t.start()
        else:
            self.drawFaces(self.face_coordiates)

    def drawFaces(self, face_coordinates):
        if len(face_coordinates) > 0:
            self.face_coordiates = face_coordinates
            mat = self.image.copy()
            for face_area in face_coordinates:
                mat = cv2.rectangle(mat, (face_area['x'], face_area['y']), (
                    face_area['x']+face_area['w'], face_area['y']+face_area['h']), (255, 0, 255), 3)
            self.updateMatToPixmap(mat)


class FaceFinder(QThread):
    signal = Signal(list, name='resultReady')

    def __init__(self, mat):
        self.mat = mat
        super().__init__()

    def run(self):
        ai = AI()
        face_coordiates = ai.findFaces(self.mat)
        if len(face_coordiates) > 0:
            self.signal.emit(face_coordiates)
