import cv2
import numpy as np
import math

"""
For loading images with unicode path/filename
"""


def cv2_loadimage(filePath, mode=cv2.IMREAD_UNCHANGED):
    img = cv2.imdecode(np.fromfile(filePath, dtype=np.uint8), mode)
    return img


"""
Get Face Thumbail out of photo and normalized to smaller size
"""


def getThumbnailFace(img, coordinates):
    thumbnail_size = 90

    # crop the face from the original image
    face_img = img[coordinates['y']:coordinates['y']+coordinates['h'],
                   coordinates['x']:coordinates['x']+coordinates['w']]

    # Fit the face into the size of 256*256
    scale = max(math.ceil(coordinates['h']/thumbnail_size),
                math.ceil(coordinates['w']/thumbnail_size))

    # resize function is dst (w * h)
    # double slash to get the math.floor result
    normalized_face_img = cv2.resize(
        face_img, (coordinates['w']//scale, coordinates['h']//scale), interpolation=cv2.INTER_AREA)

    return normalized_face_img
