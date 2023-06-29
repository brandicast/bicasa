

from PySide6.QtCore import QSize, Signal, QThread
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import Qt, QPixmap, QImage

import cv2
from utils.opencv_util import cv2_loadimage
from utils.ai import AI
from utils.data_objects import PhotoData
from database import DB

from pathlib import Path
import exifread
import json

import inspect
import traceback

import logging
logger = logging.getLogger(__name__)


class Photo_Label (QLabel):
    def __init__(self):
        super().__init__()

        self.enable_face_detect = False
        self.worker_thread = None

        self.photo_data = None

        self.setAlignment(Qt.AlignCenter)

    def setImagePath(self, image_path):
        try:
            self.photo_data = self.getPhotoMetadata(image_path)
            self.photo_data.binary = cv2_loadimage(
                image_path, cv2.IMREAD_COLOR)
            self.imageToPixmap()
        except Exception as e:
            logger.error(e)

    def getPhotoMetadata(self, image_path):
        db = DB.get_instance()
        metadata = db.getPhotoMetadata(image_path)
        if metadata is None:
            image_path_object = Path(image_path)
            if image_path_object.exists():
                metadata = PhotoData()
                metadata.fullpath = image_path
                metadata.filename = image_path_object.name
                metadata.size = image_path_object.stat().st_size
                metadata.last_access_Time = image_path_object.stat().st_mtime

                with open(image_path, 'rb') as file_object:
                    try:
                        tags = exifread.process_file(
                            file_object, details=False)
                        metadata.exif = json.dumps(tags, default=str)
                    except:
                        logger.error(
                            "Parsing Image for EXIF encounter error : " + image_path)
                logger.debug(
                    "Loading Photo Metadata from physical : " + image_path)

                # add into database and get photo_id
                metadata = db.addPhotoMetadata(metadata)
        else:
            logger.debug("Loading Photo Metadata from DB : " + image_path)

        logger.debug("faces is None ? " + str(metadata.faces is None))
        return metadata

    def imageToPixmap(self, size=None):
        try:
            mat = self.photo_data.binary.copy()
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

   # [Override to Mat]
    def getImageSize(self) -> QSize:
        return QSize(self.photo_data.binary.shape[1], self.photo_data.binary.shape[0])

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

    def enableFaceDetect(self, enable: bool):
        logger.debug(f"Enable Face Detection : {enable}")
        self.enable_face_detect = enable
        if self.enable_face_detect and self.photo_data.faces is None:
            logger.debug("Detecting Face.....")
            self.findFaces()
        else:
            self.imageToPixmap()

    def findFaces(self):
        self.t = FaceFinder(self.photo_data)
        self.t.resultReady.connect(self.collectFaceCoordinates)
        self.t.start()

    def drawFaces(self):
        if self.photo_data.faces is not None and len(self.photo_data.faces) > 0:
            mat = self.photo_data.binary.copy()
            for face in self.photo_data.faces:
                face_area = face.coordinates
                mat = cv2.rectangle(mat, (face_area['x'], face_area['y']), (
                    face_area['x']+face_area['w'], face_area['y']+face_area['h']), (255, 0, 255), 3)
            return mat
        else:
            return self.photo_data.binary

    def collectFaceCoordinates(self, faces):
        self.faces = faces
        self.imageToPixmap()


class FaceFinder(QThread):
    signal = Signal(list, name='resultReady')

    # was only mat, but then need the image path as id in database
    def __init__(self, photo_data):
        super().__init__()
        self.photo_data = photo_data

    def run(self):
        ai = AI()
        faces = ai.findFaces(self.photo_data)
        logger.debug(str(self.photo_data.faces is None))
        logger.debug(id(self.photo_data))
        if len(faces) > 0:
            self.signal.emit(faces)
