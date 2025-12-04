from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QColorDialog, QLabel, QLineEdit
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Signal

from helper_functions import load_config, save_config


class ColorSettingsDialog(QDialog):
    colors_changed = Signal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Layout colors")
        self.setFixedSize(200,300)# width, height

        self.config = load_config() # loads config.json
        # read col_name, col_url, col_tags from config
        self.colors = self.config["colors"]

        layout = QVBoxLayout(self)

        self.col_name = QLineEdit()
        self.col_name.setText(self.colors.get("col_name", ""))
        self.col_url = QLineEdit()
        self.col_url.setText(self.colors.get("col_url", ""))
        self.col_tags = QLineEdit()
        self.col_tags.setText(self.colors.get("col_tags", ""))

        layout.addWidget(QLabel("Name"))
        layout.addWidget(self.col_name)
        layout.addWidget(QLabel("URL"))
        layout.addWidget(self.col_url)
        layout.addWidget(QLabel("Tags"))
        layout.addWidget(self.col_tags)

        self.btn_save = QPushButton("Save")
        layout.addWidget(self.btn_save)

        self.btn_save.clicked.connect(self.on_save)

    def on_save(self) -> None:
        """Save config and close dialog."""
        # Get values from the textEdit field
        self.colors["col_name"] = self.col_name.text()
        self.colors["col_url"] = self.col_url.text()
        self.colors["col_tags"] = self.col_tags.text()

        # write the newly entered color settings to config file
        # and overwrite older or default color schemes permanently
        self.config["colors"] = self.colors
        save_config(self.config)
        self.colors_changed.emit(self.colors)
        self.accept()
