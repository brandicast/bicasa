import sqlite3
from config_reader import *
from pathlib import Path
import json

from utils.data_objects import FaceData, PhotoData

import traceback

import logging
logger = logging.getLogger(__name__)


class DB ():

    # Try to implement DB as Singleton
    # Because want to init the database just once
    _instance = None
    database_filename = None

    def get_instance():
        if DB._instance is None:
            DB()
        return DB._instance

    def __init__(self):
        if DB._instance is not None:
            raise Exception(
                'PersistentDB is designed as Singleton.  Use get_instance(path) to initialize')
        else:
            DB._instance = self

        self.database_filename = config['app']['database']
        logger.debug(self.database_filename)

        p = Path(self.database_filename)
        if not p.exists():

            script = None
            try:
                database_init_script = config['app']['database_init_script']
                f = open(database_init_script, 'r')
                script = f.read()

                # create the db folder if not exists
                # Path(self.database_filename).mkdir(parents=True, exist_ok=True)
                p = Path(self.database_filename)
                p.parent.mkdir(parents=True, exist_ok=True)

                logger.debug(p.parent.exists())
            except Exception as e:
                logger.error("database init script not found. " + str(e))

            if script is not None:
                try:
                    conn = sqlite3.connect(self.database_filename)
                    cur = conn.cursor()
                    cur.executescript(script)
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(
                        "database file doesn't exist and can not be created : " + self.database_filename)
                    logger.error(str(e))

    def addPhotoMetadata(self, metadata: PhotoData) -> PhotoData:
        conn = sqlite3.connect(self.database_filename)
        cur = conn.cursor()
        cur.execute('insert into photos (fullpath, filename, size, last_access_time, exif) values (?,?,?,?,?)',
                    (metadata.fullpath, metadata.filename, metadata.size, metadata.last_access_Time, metadata.exif))
        metadata.photo_id = cur.lastrowid

        conn.commit()
        conn.close()
        return metadata

    def getPhotoMetadata(self, path) -> PhotoData:
        conn = sqlite3.connect(self.database_filename)
        cur = conn.cursor()
        cur.execute('select * from photos where fullpath = ?', (path,))
        row = cur.fetchone()
        metadata = None
        if row is not None:
            metadata = PhotoData()
            metadata.photo_id = row[0]
            metadata.fullpath = row[1]
            metadata.filename = row[2]
            metadata.size = row[3]
            metadata.last_access_Time = row[4]
            metadata.exif = row[5]
        conn.close()
        return metadata

    def getFaces(self, photo_id):
        conn = sqlite3.connect(self.database_filename)
        cur = conn.cursor()
        cur.execute('select * from faces where photo_id = ?', (photo_id,))
        rows = cur.fetchall()
        faces = []
        for row in rows:
            face = FaceData()

            face.id = row[0]
            # face.photo_path = row[1]
            face.photo_id = row[1]
            face.coordinates = json.loads(row[2])
            face.embedding = row[3]
            face.thumbnail = row[4]

            logger.debug(face)
            logger.debug(type(face.embedding))
            faces.append(face)

        conn.close()
        result = None
        if len(faces) > 0:
            result = faces

        return result

    def addFaces(self, faces: list[FaceData]):
        if PhotoData is not None:
            try:
                conn = sqlite3.connect(self.database_filename)
                cur = conn.cursor()

                if faces is not None and len(faces) > 0:
                    vals = []
                    for one_face in faces:

                        tmp = (one_face.photo_id, json.dumps(one_face.coordinates),
                               json.dumps(one_face.embedding),  sqlite3.Binary(one_face.thumbnail))

                        vals.append(tmp)

                cur.executemany(
                    'insert into faces (photo_id, facial_area, embedding,thumbnail ) values (?,?,?,?)', vals)

                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(str(e))
                traceback.print_exc()

    def insertFaces(self, metadata: PhotoData):
        if PhotoData is not None:
            try:
                conn = sqlite3.connect(self.database_filename)
                cur = conn.cursor()
                cur.execute('insert into photos (fullpath, filename, size, last_access_time, exif) values (?,?,?,?,?)',
                            (metadata.fullpath, metadata.filename, metadata.size, metadata.last_access_Time, metadata.exif))

                if metadata.faces is not None and len(metadata.faces) > 0:
                    photo_id = cur.lastrowid
                    vals = []
                    for one_face in metadata.faces:

                        tmp = (photo_id, json.dumps(one_face.coordinates),
                               json.dumps(one_face.embedding),  sqlite3.Binary(one_face.thumbnail))

                        vals.append(tmp)

                cur.executemany(
                    'insert into faces (photo_id, facial_area, embedding,thumbnail ) values (?,?,?,?)', vals)

                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(str(e))
                traceback.print_exc()
