import sys 
from PySide6.QtGui import QKeySequence, QShortcut, QIcon
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtWidgets import (
    QApplication, QBoxLayout, QWidget, QMainWindow, QPushButton,
    QHBoxLayout, QVBoxLayout, QLineEdit, QLabel, QListWidget
)
from PySide6.QtSvgWidgets import QSvgWidget

from line_edit import LineEdit
from table import *
from tags_window import *
from constants import *
from colors import *

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        screen = QApplication.primaryScreen().geometry()
        _, height = screen.width(), screen.height()
        icon_colors = QIcon("./icons/color_icon.svg")

        self.setGeometry(0, 0, 700, height)
        self.setWindowTitle("BookmarksTagger")

        self.mydict = build_table_dict()

        self.button_update_safari_bookmarks = QPushButton("🔄[r]eload BMs")
        self.color_button = QPushButton()
        self.color_button.setIcon(icon_colors)
        self.color_button.setIconSize(QSize(32,32))
        self.color_button.setFlat(True)
        self.color_button.setStyleSheet("background: none; border: 0;")
        
        self.color_button.clicked.connect(self.open_color_settings)
        self.update_safari_bookmarks = load_safari_bookmarks
        self.button_update_safari_bookmarks.clicked.connect(self.on_button_load_safari_bookmarks_updated)
        self.shortcut_button_update_safari_bookmarks = QShortcut(QKeySequence("Meta+R"), self)
        self.shortcut_button_update_safari_bookmarks.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_button_update_safari_bookmarks.activated.connect(self.on_button_load_safari_bookmarks_updated)

        self.button = QPushButton("[t]ags: add/del")
        self.dropdown = QListWidget()
        self.dropdown.hide()
        

        self.line_delete_button = QPushButton("[c]lear")
        self.extended_search_button = QPushButton("▶ Details")
        self.extended_search_button.clicked.connect(self.on_button_details_clicked)
        self.extended_search_line = QLineEdit()
        self.extended_search_line.setPlaceholderText("substring of urls")
        self.extended_search_line.hide()

        self.extended_search_line_name = QLineEdit()
        self.extended_search_line_name.setPlaceholderText("substring of name")
        self.extended_search_line_name.hide()
        # self.set_of_tags = None 

        self.table = Table(self.mydict, self.extended_search_line, self.extended_search_line_name)

        self.line = LineEdit(self.table, self.dropdown)
        self.line.setPlaceholderText("[s]")
        self.extended_search_line.textChanged.connect(
            lambda _: self.table.filter_table(self.line.text())
        )
        self.extended_search_line_name.textChanged.connect(
            lambda _: self.table.filter_table(self.line.text())
        )

        self.info = QLabel("Hotkeys: use ctrl+[key]")
        self.button.clicked.connect(self.on_tags_button_clicked)
        self.shortcut_button = QShortcut(QKeySequence("Meta+T"), self)
        # make shortcut globally accessible 
        self.shortcut_button.setContext(Qt.ShortcutContext.ApplicationShortcut)  # <── das fehlt
        self.shortcut_button.activated.connect(self.on_tags_button_clicked)

        self.line_delete_button.clicked.connect(self.on_line_delete_button_clicked)
        self.shortcut_line_delete_button = QShortcut(QKeySequence("Meta+C"), self)
        self.shortcut_line_delete_button.activated.connect(self.on_line_delete_button_clicked)

        self.line_shortcut = QShortcut(QKeySequence("Meta+S"), self)
        self.line_shortcut.activated.connect(self.go_to_search_bar)

        self.open_selected_boomarks_urls = self.table.open_selected_boomarks_urls
        self.shortcut_open_selecte_bookmarks_url = QShortcut(QKeySequence("Meta+X"), self)
        self.shortcut_open_selecte_bookmarks_url.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_open_selecte_bookmarks_url.activated.connect(self.open_selected_boomarks_urls)

        self.line_layout = QHBoxLayout()
        self.line_layout.addWidget(self.line)
        self.line_layout.addWidget(self.line_delete_button)
        self.line_layout.addWidget(self.extended_search_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.info)

        self.button_layout2 = QHBoxLayout()
        self.button_layout2.addWidget(self.button)
        self.button_layout2.addWidget(self.button_update_safari_bookmarks)
        self.button_layout2.addWidget(self.color_button)


        # LAYOUT 
        upper_layout = QHBoxLayout()
        upper_layout2= QHBoxLayout()
        middle_layout = QHBoxLayout()
        bottom_layout = QVBoxLayout()
        main_layout = QVBoxLayout()

        upper_layout.addLayout(button_layout)
        upper_layout2.addLayout(self.button_layout2)
        middle_layout.addWidget(self.table.table)
        bottom_layout.addLayout(self.line_layout)
        bottom_layout.addWidget(self.dropdown)
        bottom_layout.addWidget(self.extended_search_line)
        bottom_layout.addWidget(self.extended_search_line_name)

        main_layout.addLayout(upper_layout)
        main_layout.addLayout(upper_layout2)
        main_layout.addLayout(middle_layout)
        main_layout.addLayout(bottom_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def on_tags_button_clicked(self):
        """
        window: tags_window
        """
        if not hasattr(self, "tags_window"):
            self.tags_window = TagsWindow(self.table.table, self.height())

        if self.tags_window.isVisible():
            self.tags_window.close()
        else:
            self.tags_window.populate_tag_checkboxes()
            self.tags_window.show()
            self.tags_window.raise_()
            self.tags_window.activateWindow()

    def on_line_delete_button_clicked(self):
        self.line.clear()

    def go_to_search_bar(self):
        # Toggle focus between search bar and first table cell
        if self.line.hasFocus():
            table_widget = self.table.table
            if table_widget.rowCount() and table_widget.columnCount():
                table_widget.setCurrentCell(0, 0)
            table_widget.setFocus()
        else:
            self.line.setFocus()

    def on_button_details_clicked(self):
        if self.extended_search_line.isVisible():
            self.extended_search_line.hide()
            self.extended_search_line_name.hide()
            self.extended_search_button.setText("▶Details")
        else:
            self.extended_search_line.show()
            self.extended_search_line_name.show()
            self.extended_search_button.setText("▼Details")

    def open_selected_bookmarks(self):
        self.open_selected_boomarks_urls()

   
    def on_button_load_safari_bookmarks_updated(self):
        """get data from bookmarks plist and save them as dict"""
        btn = self.button_update_safari_bookmarks
        self.mydict = build_table_dict()
        # fill existing table with the new data 
        self.table.reload(self.mydict)
        # short visual feedback on reload button
        old_style = btn.styleSheet()
        btn.setStyleSheet("background-color: #c5fbc5;")
        QTimer.singleShot(300, lambda: btn.setStyleSheet(old_style))

    # RESIZE EVENTS 
    def resizeEvent(self, event):
        """Contains and calls all resize functions"""
        self.auto_resize(event)
        super().resizeEvent(event)

    def auto_resize(self, event):
        """Reorder elements vertically if small width"""
        if self.width() < 400:
            self.button_layout2.setDirection(QBoxLayout.TopToBottom)
            self.line_layout.setDirection(QBoxLayout.TopToBottom)
        else:
            self.button_layout2.setDirection(QBoxLayout.LeftToRight)
            self.line_layout.setDirection(QBoxLayout.LeftToRight)
        
    def open_color_settings(self):
        dlg = ColorSettingsDialog(self)
        dlg.colors_changed.connect(self.on_colors_changed)
        dlg.exec()

    def on_colors_changed(self, colors: dict):
        """Refresh table colors after the dialog saves."""
        self.table.update_colors(colors)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
