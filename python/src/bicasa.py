import sys
import os
from pathlib import Path

def _detect_platform():
    """
    Returns a dict describing the runtime environment.
    Used to apply platform-specific workarounds.
    """
    info = {
        "is_wsl": False,
        "is_windows": sys.platform == "win32",
        "is_linux": sys.platform.startswith("linux"),
    }
    if info["is_linux"]:
        try:
            version = Path("/proc/version").read_text().lower()
            info["is_wsl"] = "microsoft" in version
        except Exception:
            pass
    return info

PLATFORM = _detect_platform()

if PLATFORM["is_wsl"]:
    # WSL2: No real GPU, no audio daemon. Force software rendering for UI stability.
    # Video playback via QMediaPlayer is NOT supported in this environment.
    os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"
    os.environ["GALLIUM_DRIVER"] = "llvmpipe"
    os.environ["QT_XCB_GL_INTEGRATION"] = "none"
    os.environ["BICASA_VIDEO_SUPPORT"] = "0"
else:
    # Native Linux / Windows: full hardware support, QMediaPlayer works normally.
    os.environ["BICASA_VIDEO_SUPPORT"] = "1"

from init import *
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QFont
from gui_thread_safe import *
from pathlib import Path

logger = logging.getLogger(__name__)
logger.info("Launching bicasa")

app = QApplication(sys.argv)

# Load Chinese font to fix missing glyphs (square blocks) on Linux
font_path = Path(__file__).parent / "ui" / "fonts" / "NotoSansTC-Regular.otf"
if font_path.exists():
    font_id = QFontDatabase.addApplicationFont(str(font_path))
    if font_id != -1:
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if font_families:
            app_font = app.font()
            app_font.setFamilies([font_families[0], app_font.family()])
            app.setFont(app_font)
            logger.info(f"Loaded application font: {font_families[0]}")

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
