import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QTreeWidgetItem, QTreeWidget, QFrame
from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader

from config_setup import *
import logging
import logging.config

logger = logging.getLogger(__name__)


def collectTreeNodes(path, parent):
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_dir():
                node = QTreeWidgetItem(parent)
                node.setText(0, entry.name)
                parent.addChild(node)
                collectTreeNodes(entry.path, node)


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


def onTreeItemClicked(item, col):
    path = Path(getFullPath(item))
    for f in path.iterdir():
        print(f)


logger.info("GUI launching.....")
app = QApplication(sys.argv)

ui_file = QFile(config["gui"]["design"])
ui_file.open(QFile.ReadOnly)

loader = QUiLoader()
main_window = loader.load(ui_file)

root = config["app"]["root"]
#root = '.'
root_node = QTreeWidgetItem(main_window.treeWidget)
root_node.setText(0, root)
collectTreeNodes(root, root_node)
main_window.treeWidget.setColumnCount(1)
main_window.treeWidget.insertTopLevelItem(0, root_node)

main_window.treeWidget.itemClicked.connect(
    onTreeItemClicked)   # regiter tree item click event

main_window.show()
sys.exit(app.exec())
