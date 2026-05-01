import sqlite3
from config_reader import *
from pathlib import Path
import json

from utils.data_objects import FaceData, PhotoData

import traceback
import threading

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

        self.database_filename = str(BASE_DIR / config['app']['database'])
        logger.debug(self.database_filename)
        self.lock = threading.Lock()

        p = Path(self.database_filename)
        # Always try to run the init script to ensure all tables (including new ones) exist
        script = None
        try:
            database_init_script = str(BASE_DIR / config['app']['database_init_script'])
            with open(database_init_script, 'r') as f:
                script = f.read()

            p.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("database init script not found or error. " + str(e))

        if script is not None:
            try:
                conn = sqlite3.connect(self.database_filename)
                cur = conn.cursor()
                cur.executescript(script)
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(
                    "Error ensuring database tables exist: " + self.database_filename)
                logger.error(str(e))
        
        # Initialize the persistent connection
        self.conn = sqlite3.connect(self.database_filename, check_same_thread=False)
        # Enable WAL mode for better concurrency performance
        self.conn.execute('PRAGMA journal_mode=WAL;')

    def addPhotoMetadata(self, metadata: PhotoData) -> PhotoData:
        with self.lock:
            cur = self.conn.cursor()
            cur.execute('insert into photos (fullpath, filename, size, last_access_time, exif) values (?,?,?,?,?)',
                        (metadata.fullpath, metadata.filename, metadata.size, metadata.last_access_Time, metadata.exif))
            metadata.photo_id = cur.lastrowid
    
            self.conn.commit()
        return metadata

    def getPhotoMetadata(self, path) -> PhotoData:
        cur = self.conn.cursor()
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
        return metadata

    def getFaces(self, photo_id):
        cur = self.conn.cursor()
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
        result = None
        if len(faces) > 0:
            result = faces

        return result

    def addFaces(self, faces: list[FaceData]):
        if PhotoData is not None:
            try:
                with self.lock:
                    cur = self.conn.cursor()
    
                    if faces is not None and len(faces) > 0:
                        vals = []
                        for one_face in faces:
    
                            tmp = (one_face.photo_id, json.dumps(one_face.coordinates),
                                   json.dumps(one_face.embedding),  sqlite3.Binary(one_face.thumbnail))
    
                            vals.append(tmp)
    
                    cur.executemany(
                        'insert into faces (photo_id, facial_area, embedding,thumbnail ) values (?,?,?,?)', vals)
    
                    self.conn.commit()
            except Exception as e:
                logger.error(str(e))
                traceback.print_exc()

    def insertFaces(self, metadata: PhotoData):
        if PhotoData is not None:
            try:
                with self.lock:
                    cur = self.conn.cursor()
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
    
                    self.conn.commit()
            except Exception as e:
                logger.error(str(e))
                traceback.print_exc()

    def addFolder(self, parent_path, name, full_path):
        try:
            with self.lock:
                cur = self.conn.cursor()
                cur.execute('insert or ignore into folders (parent_path, name, full_path) values (?,?,?)',
                            (parent_path, name, full_path))
                self.conn.commit()
        except Exception as e:
            logger.error(f"Error adding folder to cache: {e}")

    def getFolders(self, parent_path):
        try:
            cur = self.conn.cursor()
            cur.execute('select name, full_path from folders where parent_path = ? order by name', (parent_path,))
            return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting folders from cache: {e}")
            return []

    def hasFolderCache(self, root_path):
        try:
            cur = self.conn.cursor()
            # Check if there are any folders where the parent_path starts with or is the root_path
            # Or simpler: check if there's at least one entry with root_path as parent_path
            cur.execute('select count(*) from folders where parent_path = ?', (root_path,))
            return cur.fetchone()[0] > 0
        except Exception as e:
            logger.error(f"Error checking folder cache: {e}")
            return False

    def clearFolderCache(self, root_path):
        try:
            with self.lock:
                cur = self.conn.cursor()
                # Delete all folders that are children of root_path recursively?
                # Actually, if we just want to clear the whole cache for a fresh scan:
                # cur.execute('delete from folders') 
                # But to be more specific to root_path:
                cur.execute('delete from folders where full_path like ? or parent_path = ?', (f"{root_path}%", root_path))
                self.conn.commit()
        except Exception as e:
            logger.error(f"Error clearing folder cache: {e}")
