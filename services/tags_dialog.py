from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton
)


class TagsDialog(QDialog):
    """Dialog for user input for newly added bookmarks"""

    def __init__(self, bookmark_dict, parent = None) -> None:
        super().__init__(parent)

        self.bookmark = bookmark_dict 
        self.setWindowTitle("Add Tags")

        # ------------------- 
        # Layout 
        # ------------------- 
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Info Text 
        title = self.bookmark.get("URIDictionary", {}).get("title", "Neues Lesezeichen")
        layout.addWidget(QLabel(f"Bookmark: <b>{title}</b>"))

        # Tag entry 
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Comma separated Tags")
        layout.addWidget(self.input_line)

        # Buttons (Cancel / OK)
        buttons =  QHBoxLayout()
        layout.addLayout(buttons)

        cancel_button = QPushButton("Abort")
        ok_button = QPushButton("OK")

        buttons.addWidget(cancel_button)
        buttons.addWidget(ok_button)

        cancel_button.clicked.connect(self.reject)
        ok_button.clicked.connect(self.accept)
        
        # focus on line edit 

    def get_tags(self):
        """Return list of tags entered by the user.
        Strips whitespaces and ignores empty entries 
        """
        
        raw = self.input_line.text()
        parts = [tag.strip() for tag in raw.split(",")]
        return [part for part in parts if part]

