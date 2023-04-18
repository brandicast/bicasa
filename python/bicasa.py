import setup
import logging

from gui_thread_safe import *

logger = logging.getLogger(__name__)
logger.info("Launching bicasa")

app = QApplication(sys.argv)

'''
screen = app.primaryScreen()
print(screen.availableSize())
print(screen.availableGeometry())
# print(screen.physicalSize())
print(screen.virtualSize())
'''

win = Window()
win.showMaximized()
win.show()
sys.exit(app.exec())
