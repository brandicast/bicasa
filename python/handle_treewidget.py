from PySide6.QtWidgets import QTreeWidgetItem
import os
import logging

logger = logging.getLogger(__name__)


class CollectTreeNodes ():

    def collect(self, path, parent):
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_dir():
                    node = QTreeWidgetItem(parent)
                    node.setText(0, entry.name)
                    # logger.info("Adding {entry.name} to Tree node")
                    parent.addChild(node)
                    self.collect(entry.path, node)
