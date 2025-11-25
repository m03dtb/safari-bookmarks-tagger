from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QColorDialog, QLabel, QLineEdit
)
from PySide6.QtGui import QColor


from helper_functions import load_config, save_config


class ColorSettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Choose layout colors")

        self.config = load_config()
        self.colors = self.config["colors"]

        layout = QVBoxLayout(self)

        self.label_preview = QLabel("Colors")
        layout.addWidget(self.label_preview)


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
        # Werte aus den Eingabefeldern holen
        self.colors["col_name"] = self.col_name.text()
        self.colors["col_url"] = self.col_url.text()
        self.colors["col_tags"] = self.col_tags.text()

        # zurück in config schreiben und speichern
        self.config["colors"] = self.colors
        save_config(self.config)
        self.accept()
