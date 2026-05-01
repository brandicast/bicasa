class FaceData:
    id = None
    # photo_path = None
    photo_id = None

    coordinates = None  # as json string with coordinates
    embedding = None   # as embedding as list()
    thumbnail = None   # binary


'''
    "fullpath"	TEXT NOT NULL UNIQUE,
	"filename"	TEXT NOT NULL,
	"size"	INTEGER NOT NULL,
	"last_access_time"	INTEGER NOT NULL,
	"exif"	TEXT,

'''


class PhotoData:
    photo_id = None
    fullpath = None
    filename = None
    size = None
    last_access_Time = None
    exif = None

    binary = None  # mat

    faces = None
