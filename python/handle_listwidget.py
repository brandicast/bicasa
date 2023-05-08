from pathlib import Path
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QPixmap, QImageReader, QIcon

import logging
# import logging.config

logger = logging.getLogger(__name__)


# iterate thru all parent of the tree item to get the full path


def getFullPath(item):
    x = item
    path_str = item.text(0)

    while x.parent():
        x = x.parent()
        path_str = str(Path(x.text(0)).joinpath(
            path_str))  # May be optimized a bit?
    return path_str

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

        for entry in path.iterdir():
            if entry.is_file() and not self.stop_flag:
                try:
                    # [NOTE] Executing QImageReader.setAllocationLimit(0) disables the 128MB limitation,
                    reader = QImageReader(str(entry))
                    reader.setAutoTransform(True)
                    image = reader.read()  # QImage
                    if image != None:
                        pixmap = QPixmap.fromImage(image)
                        self.signal.emit(
                            QIcon(pixmap), entry, self.stop_flag)
                    '''
                    # Was setting QIcon size in UI level.  
                    # However, could check if scaled is needed to ease memory
                    thumbnail_size = int(config["gui"]["thumbnail_size"])
                    pixmap.scaled(thumbnail_size, thumbnail_size, Qt.KeepAspectRatio)
                    '''

                except:
                    logger.error('Reading ' + entry.name + ' with error !')
            else:
                break
