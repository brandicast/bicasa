import cv2
import numpy

import math
from deepface import DeepFace

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

    def findFaces(self, mat: numpy.ndarray):
        representations = None
        try:
            representations = DeepFace.represent(
                mat, detector_backend=self.backends[self.backend_index])
        except:
            logger.debug("Deepface represent found error ! ")
            representations = list()

        logger.debug(str(len(representations)) +
                     " face(s) found ! ")

        face_coordinates = list()

        if len(representations) > 0:
            faces_array = []
            for representation in representations:

                face_area = representation["facial_area"]
                logger.debug(face_area)
                face_coordinates.append(face_area)

                face_thumbnail = self.getNormalizedFaceImage(
                    mat, face_area)
                single_face = {}
                single_face["representation"] = representation
                single_face["thumbnail"] = face_thumbnail
                faces_array.append(single_face)

        return face_coordinates

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
