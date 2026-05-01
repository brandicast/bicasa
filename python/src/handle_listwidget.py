from pathlib import Path
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QPixmap, QImageReader, QIcon
from ui.media_item_delegate import THUMBNAIL_SIZE as _THUMB_SIZE

import logging
# import logging.config

logger = logging.getLogger(__name__)


# handle tree item click event


class CollectListWidgetItem_Thread(QThread):
    # define Signal to pass the loaded QICon and filename out to QApp level
    # The signal respectively contains :
    #               1)  A loaded QIcon represent the picture
    #               2)  path
    #               3)  whether this thread is about to stop or not    -> to prevent the thread was stopped but still add item into listwidget
    #               4)  name of the slot
    signal = Signal(QIcon, Path, bool, name='resultReady')

    def __init__(self, item):
        self.item = item
        self.stop_flag = False
        super().__init__()
        logger.debug('Init CollectListWidgetItem')

    def setStopFlag(self, stop):
        self.stop_flag = stop

    def run(self):
        logger.debug('run CollectListWidgetItem')
        path = Path(getFullPath(self.item))

        # Sort the entries
        sorted_entries = sorted(path.iterdir(), key=lambda e: e.name)

        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.wmv'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}

        for entry in sorted_entries:
            if entry.is_file() and not self.stop_flag:
                ext = entry.suffix.lower()
                try:
                    pixmap = None
                    if ext in image_extensions:
                        from PySide6.QtCore import QByteArray, QBuffer
                        with open(entry, 'rb') as f:
                            data = f.read()
                        byte_array = QByteArray(data)
                        buffer = QBuffer(byte_array)
                        buffer.open(QBuffer.ReadOnly)
                        
                        reader = QImageReader(buffer)
                        reader.setAutoTransform(True)
                        image = reader.read()
                        if not image.isNull():
                            pixmap = QPixmap.fromImage(image)
                            
                    elif ext in video_extensions:
                        import cv2
                        import numpy as np
                        from PySide6.QtGui import QImage
                        cap = cv2.VideoCapture(str(entry))
                        # Read 10th frame to avoid black screen at start
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 10)
                        ret, frame = cap.read()
                        if not ret:
                            # Fallback to first frame
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            ret, frame = cap.read()
                        cap.release()
                        
                        if ret:
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            h, w, ch = frame.shape
                            bytes_per_line = ch * w
                            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                            pixmap = QPixmap.fromImage(qimg)

                    if pixmap is not None and not pixmap.isNull():
                        # Downscale thumbnail to the exact size the delegate expects
                        try:
                            from config_reader import config
                            thumbnail_size = int(config["gui"]["thumbnail_size"])
                        except Exception:
                            thumbnail_size = _THUMB_SIZE

                        pixmap = pixmap.scaled(
                            thumbnail_size, thumbnail_size,
                            Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                        self.signal.emit(QIcon(pixmap), entry, self.stop_flag)

                except Exception as e:
                    logger.error(f'Reading {entry.name} with error: {e}')
            elif self.stop_flag:
                break

# iterate thru all parent of the tree item to get the full path


def getFullPath(item):
    x = item
    path_str = item.text(0)

    while x.parent():
        x = x.parent()
        path_str = str(Path(x.text(0)).joinpath(
            path_str))  # May be optimized a bit?
    return path_str
