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
        self.imageToPixmap()

    # Return image as QImage
    def Image(self):
        return self.image

    def getImageSize(self) -> QSize:
        if self.image != None:
            return self.image.size()

    def imageToPixmap(self, size=None):
        if size == None:
            size = self.size()
        pixmap = QPixmap.fromImage(self.image)
        scaled = pixmap.scaled(size, Qt.KeepAspectRatio)
        self.setPixmap(scaled)

    def resizePixmap(self, size):
        logger.debug(f"Resizing Pixmap to {size}")
        logger.debug(
            f"Label size is: {self.size()}, origin pixmap size is: {self.pixmap().size()}, resizing pixmap to: {size}" + " and is called by " + inspect.stack()[1].function)
        self.imageToPixmap(size)

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
        self.faces = None
        self.detected = False
        self.enable_face_detect = False
        self.t = None
        self.path = None

    # [Override] Load Image as OpenCV Mat

    def setImagePath(self, image_path):
        try:
            self.path = image_path
            self.image = cv2_loadimage(image_path, cv2.IMREAD_COLOR)
            self.imageToPixmap()

        except Exception as e:
            logger.error(e)

    # [Override to Mat]
    def getImageSize(self) -> QSize:
        return QSize(self.image.shape[1], self.image.shape[0])

    # [Override]
    def imageToPixmap(self, size=None):
        try:
            mat = self.image.copy()
            if self.enable_face_detect:
                mat = self.drawFaces()
            if size == None:
                size = self.size()
            qimage = self.__Mat_To_QImage__(mat)
            pixmap = QPixmap.fromImage(qimage)
            scaled = pixmap.scaled(size, Qt.KeepAspectRatio)
            self.setPixmap(scaled)
        except Exception as e:
            logger.debug(e)

    '''
    # [Override] Need to check if the image is not initialized
    def reset(self):
        pixmap = self.imageToPixmap()
        scaled = pixmap.scaled(self.size(), Qt.KeepAspectRatio)
        self.setPixmap(scaled)
    '''

    def enableFaceDetect(self, enable: bool):
        logger.debug(f"{enable} and {self.detected}")
        self.enable_face_detect = enable
        if self.enable_face_detect and not self.detected:
            logger.debug("Detecting Face.....")
            self.findFaces()
            self.detected = True
        else:
            self.imageToPixmap()

    # * Using mat to initialize QImage, the parameter is mat data, mat width, mat height, "steps" and format
    #   without "steps", when converting QImage to Pixmap using Pixmap.fromImage, it crashes without error on certain JPEG files.
    #   steps, according to Googled, is width * 3.   Need to check further for what it stands for.  Works for now
    def __Mat_To_QImage__(self, mat):
        try:
            qimage = QImage(mat, mat.shape[1],
                            mat.shape[0], 3 * mat.shape[1], QImage.Format_BGR888)
        except Exception as e:
            logger.debug(e)
        return qimage

    def findFaces(self):
        if self.faces is None:
            self.t = FaceFinder(self.path, self.image)
            self.t
            self.t.resultReady.connect(self.collectFaceCoordinates)
            self.t.start()

    def drawFaces(self):
        if self.faces is not None and len(self.faces) > 0:
            mat = self.image.copy()
            for face in self.faces:
                face_area = face.coordinates
                mat = cv2.rectangle(mat, (face_area['x'], face_area['y']), (
                    face_area['x']+face_area['w'], face_area['y']+face_area['h']), (255, 0, 255), 3)
            return mat
        else:
            return self.image

    def collectFaceCoordinates(self, faces):
        self.faces = faces
        self.imageToPixmap()


class FaceFinder(QThread):
    signal = Signal(list, name='resultReady')

    # was only mat, but then need the image path as id in database
    def __init__(self, image_path, mat):
        self.mat = mat
        self.path = image_path
        super().__init__()

    def run(self):
        ai = AI()
        faces = ai.findFaces(self.path, self.mat)
        if len(faces) > 0:
            self.signal.emit(faces)
