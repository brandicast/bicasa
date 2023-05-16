
import inspect
from PySide6.QtWidgets import QScrollArea, QSizePolicy, QAbstractScrollArea
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class PannableScrollArea  (QScrollArea):

    def __init__(self):
        super().__init__()
        self.x = 0
        self.y = 0
        self.setAlignment(Qt.AlignCenter)

    def mouse_press(self, event):
        global x, y
        logger.debug(event)
        logger.debug("h: " + str(self.horizontalScrollBar().value()) + " (max: " + str(self.horizontalScrollBar().maximum()) +
                     ")" + " v:" + str(self.verticalScrollBar().value()) + " (max: " + str(self.verticalScrollBar().maximum()) + ")")
        x = event.globalPosition().x()
        y = event.globalPosition().y()
        # close hand works better on windows.   doesn't see much diff on Linux
        QApplication.setOverrideCursor(Qt.ClosedHandCursor)

    def mouse_release(self, event):
        logger.debug(event)
        QApplication.restoreOverrideCursor()

    def mouse_move(self, event):
        # QApplication.changeOverrideCursor(Qt.ClosedHandCursor)
        global x, y
        x_diff = x - event.globalPosition().x()  # - x
        y_diff = y - event.globalPosition().y()  # - y

        x_max = self.horizontalScrollBar().maximum()
        y_max = self.verticalScrollBar().maximum()

        x_now = self.horizontalScrollBar().value()
        y_now = self.verticalScrollBar().value()

        logger.debug(f"origin: ({x},{y}),  moveto: (({event.globalPosition().x()},{event.globalPosition().y()})),  mouse diff : ({x_diff}, {y_diff}),     scrollbar current value : ({x_now}, {y_now})  ,  scrollbar max value : ({x_max},{y_max})")

        if (x_max > 0):         # if the bar shows
            if (x_diff > 0 and x_now < x_max) or (x_diff < 0 and x_now > 0):
                self.horizontalScrollBar().setValue(x_now + x_diff)
                logger.debug("h setValue : " + str(x_now + x_diff))
                x = event.globalPosition().x()

        if (y_max > 0):         # if the bar shows
            if (y_diff > 0 and y_now < y_max) or (y_diff < 0 and y_now > 0):

                self.verticalScrollBar().setValue(y_now + y_diff)
                logger.debug("v setValue : " + str(y_now + y_diff))
                y = event.globalPosition().y()
