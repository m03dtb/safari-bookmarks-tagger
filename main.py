import sys 
from PySide6.QtGui import QKeySequence, QShortcut, QIcon
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtWidgets import (
    QApplication, QBoxLayout, QWidget, QMainWindow, QPushButton,
    QHBoxLayout, QVBoxLayout, QLineEdit, QLabel, QListWidget, QSystemTrayIcon
)
from PySide6.QtSvgWidgets import QSvgWidget

from ui.line_edit import LineEdit
from ui.table import *
from ui.tags_window import *
from services.settings import *
from ui.colors import *
from services.bookmark_status import BookmarkStatus, LightIcons

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        screen = QApplication.primaryScreen().geometry()
        _, height = screen.width(), screen.height()
        self.icon_colors = QIcon("./icons/color_icon.svg")
        self.icon_tags = QIcon("./icons/tag_icon.svg")
        self.icon_reload = QIcon("./icons/reload_icon.svg")
        self.icon_reload_green = QIcon("./icons/reload_icon_green.svg")
        self.icon_clear = QIcon("./icons/clear_icon.svg")


        self.setGeometry(0, 0, 700, height)
        self.setWindowTitle("BookmarksTagger")

        self.mydict = build_table_dict()

        self.button_update_safari_bookmarks = QPushButton()
        self.button_update_safari_bookmarks.setIcon(self.icon_reload)
        self.button_update_safari_bookmarks.setIconSize(QSize(32,32))
        self.button_update_safari_bookmarks.setFlat(True)
        self.button_update_safari_bookmarks.setStyleSheet("background: none; border: 0;")
        self.button_update_safari_bookmarks.setToolTip("[r]eload safari bookmarks")

        self.color_button = QPushButton()
        self.color_button.setIcon(self.icon_colors)
        self.color_button.setIconSize(QSize(32,32))
        self.color_button.setFlat(True)
        self.color_button.setStyleSheet("background: none; border: 0;")
        
        self.color_button.clicked.connect(self.open_color_settings)
        self.update_safari_bookmarks = load_safari_bookmarks
        self.button_update_safari_bookmarks.clicked.connect(self.on_button_load_safari_bookmarks_updated)
        self.shortcut_button_update_safari_bookmarks = QShortcut(QKeySequence("Meta+R"), self)
        self.shortcut_button_update_safari_bookmarks.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_button_update_safari_bookmarks.activated.connect(self.on_button_load_safari_bookmarks_updated)

        self.button = QPushButton()
        self.button.setIcon(self.icon_tags)
        self.button.setIconSize(QSize(32,32))
        self.button.setFlat(True)
        self.button.setStyleSheet("background: none; border: 0;")
        self.button.setToolTip("Add/Delete all selected tags > select by holding Cmd and tipping on entries")

        self.button_lights = QPushButton()

        # lights + bookmark status
        self.icons = LightIcons()
        self.bookmark_status = BookmarkStatus(self)
        # cycle through off -> window -> menubar
        self.lights_mode = "off"

        # button_lights setup
        self.button_lights.setIcon(self.icons.lights_off)
        self.button_lights.setIconSize(QSize(32,32))
        self.button_lights.setFlat(True)
        self.button_lights.setStyleSheet("background: none; border:0;")
        # connect button click -> manual check trigger
        self.button_lights.clicked.connect(self.on_button_lights_clicked)
        # connect bookmark status -> icon update
        self.bookmark_status.bookmark_checked.connect(self.update_light_icon)
        # NSStatusBar/QSystemTrayIcon indicator (menu bar)
        self.tray_icon = QSystemTrayIcon(self.icons.lights_off, self)
        self.tray_icon.setToolTip("Safari bookmark status")
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
            
        self.dropdown = QListWidget()
        self.dropdown.hide()
        

        self.line_delete_button = QPushButton()
        self.line_delete_button.setIcon(self.icon_clear)
        self.line_delete_button.setIconSize(QSize(32,32))
        self.line_delete_button.setFlat(True)
        self.line_delete_button.setStyleSheet("background: none; border: 0;")
        self.line_delete_button.setToolTip("[c]lear Tags Search")

        self.extended_search_button = QPushButton("▶ Details")
        self.extended_search_button.clicked.connect(self.on_button_details_clicked)
        self.extended_search_line_url = QLineEdit()
        self.extended_search_line_url.setPlaceholderText("substring of urls")
        self.extended_search_line_url.hide()

        self.extended_search_line_name = QLineEdit()
        self.extended_search_line_name.setPlaceholderText("substring of name")
        self.extended_search_line_name.hide()
        # self.set_of_tags = None 

        self.table = Table(self.mydict, self.extended_search_line_url, self.extended_search_line_name)

        self.line = LineEdit(self.table, self.dropdown)
        self.line.setPlaceholderText("[s]")
        self.extended_search_line_url.textChanged.connect(
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
        self.button_layout2.addWidget(self.button_lights)


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
        bottom_layout.addWidget(self.extended_search_line_url)
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
        if self.extended_search_line_url.isVisible():
            self.extended_search_line_url.hide()
            self.extended_search_line_name.hide()
            self.extended_search_button.setText("▶Details")
        else:
            self.extended_search_line_url.show()
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
        btn.setIcon(self.icon_reload_green) # now-time 
        QTimer.singleShot(250, lambda: btn.setIcon(self.icon_reload)) # now-time + t1 
        QTimer.singleShot(550, lambda: btn.setIcon(self.icon_reload_green)) # now-time +t2 
        QTimer.singleShot(1050, lambda: btn.setIcon(self.icon_reload)) # now-time +t3 

    # RESIZE EVENTS 
    def resizeEvent(self, event):
        """Contains and calls all resize functions"""
        self.auto_resize(event)
        super().resizeEvent(event)

    def auto_resize(self, event):
        """Reorder elements vertically if small width"""
        if self.width() < 400:
            self.line_layout.setDirection(QBoxLayout.TopToBottom)
        else:
            self.line_layout.setDirection(QBoxLayout.LeftToRight)
        
    def open_color_settings(self):
        dlg = ColorSettingsDialog(self)
        dlg.colors_changed.connect(self.on_colors_changed)
        dlg.exec()

    def on_colors_changed(self, colors: dict):
        """Refresh table colors after the dialog saves."""
        self.table.update_colors(colors)

    def on_button_lights_clicked(self):
        # cycle: off -> window -> menubar -> off
        mode_order = {"off": "window", "window": "menubar", "menubar": "off"}
        self.lights_mode = mode_order.get(self.lights_mode, "off")

        if self.lights_mode == "off":
            self.bookmark_status.stop()
            self.button_lights.setIcon(self.icons.lights_off)
            self.tray_icon.hide()
            return

        # lights on: start monitoring and perform immediate check
        self.bookmark_status.start()
        self.bookmark_status.check_frontmost_url_changed(force=True)
        if self.lights_mode == "window":
            self.tray_icon.hide()
            # show last-known status directly in the button
            self.button_lights.setIcon(self.icons.lights_on)
            self.button_lights.setToolTip("Lights: window mode (click for menubar)")
        else:
            # menubar-only mode -> show tray icon and keep button as toggle indicator
            self.tray_icon.show()
            self.button_lights.setIcon(self.icons.lights_on)
            self.button_lights.setToolTip("Lights: menubar only (click to turn off)")

    def update_light_icon(self, status: str | None) -> None:
        """Update the lights icon depending on bookmark existence."""
        if self.lights_mode == "off":
            return

        def icon_for(st: str | None):
            if st is None:
                return self.icons.lights_off
            if st == "full":
                return self.icons.lights_green
            if st == "domain":
                return self.icons.lights_yellow
            return self.icons.lights_red

        icon = icon_for(status)
        tooltip_status = {
            None: "no Safari window",
            "full": "exact bookmark found",
            "domain": "domain bookmarked",
            "none": "no bookmark",
        }.get(status, "no bookmark")

        # always update the button while active so the GUI reflects state
        self.button_lights.setIcon(icon)

        if self.lights_mode == "window":
            self.tray_icon.hide()
        elif self.lights_mode == "menubar":
            self.tray_icon.setIcon(icon)
            self.tray_icon.setToolTip(f"Safari bookmark status: {tooltip_status}")
            self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        """Toggle window visibility when clicking the menubar icon."""
        if reason not in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            return
        if self.isMinimized() or not self.isVisible():
            self.showNormal()
            self.raise_()
            self.activateWindow()
        else:
            self.showMinimized()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
