import cv2
import numpy

import math
from deepface import DeepFace

from utils.data_objects import FaceData, PhotoData
from database import DB

import logging
logger = logging.getLogger(__name__)


class AI():

    def __init__(self):
        self.backends = [
            'opencv',
            'ssd',
            'dlib',
            'mtcnn',
            'retinaface',
            'mediapipe'
        ]
        self.backend_index = 4

    def findFaces(self, photo_data: PhotoData):

        db = DB.get_instance()

        # return None if the photo hasn't been checked
        # return empty list if photo has been checked and no faces found
        faces = db.getFaces(photo_data.photo_id)

        if faces is None:
            try:
                representations = DeepFace.represent(
                    photo_data.binary, detector_backend=self.backends[self.backend_index])
            except:
                logger.debug("Deepface represent found error ! ")
                representations = list()

            logger.debug(str(len(representations)) +
                         " face(s) found ! ")

            faces = []

            if len(representations) > 0:

                for representation in representations:
                    one_face = FaceData()

                    one_face.photo_id = photo_data.photo_id

                    one_face.photo_path = photo_data.fullpath

                    one_face.coordinates = representation["facial_area"]
                    logger.debug(one_face.coordinates)

                    one_face.thumbnail = self.getNormalizedFaceImage(
                        photo_data.binary, one_face.coordinates)

                    one_face.embedding = representation["embedding"]

                    faces.append(one_face)

                # Add faces into database
                 # db.insertFaces(photo_data)
                db.addFaces(faces)

        photo_data.faces = faces

        return faces

    def getNormalizedFaceImage(self, mat, coordinates):
        thumbnail_size = 90

        # crop the face from the original image
        face_img = mat[coordinates['y']:coordinates['y']+coordinates['h'],
                       coordinates['x']:coordinates['x']+coordinates['w']]

        # Fit the face into the size of 256*256
        scale = max(math.ceil(coordinates['h']/thumbnail_size),
                    math.ceil(coordinates['w']/thumbnail_size))

        # resize function is dst (w * h)
        # double slash to get the math.floor result
        normalized_face_img = cv2.resize(
            face_img, (coordinates['w']//scale, coordinates['h']//scale), interpolation=cv2.INTER_AREA)

        return normalized_face_img
