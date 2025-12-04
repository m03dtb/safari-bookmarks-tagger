# Standard library
import sys
from pathlib import Path

# Third-party 
from PySide6.QtGui import QKeySequence, QShortcut, QIcon
from PySide6.QtCore import Qt, QTimer, QSize, QItemSelectionModel, QEvent
from PySide6.QtWidgets import (
    QApplication, QBoxLayout, QWidget, QMainWindow, QPushButton,
    QHBoxLayout, QVBoxLayout, QLineEdit, QLabel, QListWidget, QSystemTrayIcon,
    QMessageBox
)
# Local application modules
from helper_functions import *
from ui.colors import ColorSettingsDialog
from ui.table import Table
from ui.tags_window import TagsWindow 
from ui.line_edit import LineEdit
from services.bookmark_status import BookmarkStatus, LightIcons
from services.bookmark_watcher import BookmarkWatcher
from services.settings import *


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        screen = QApplication.primaryScreen().geometry()
        _, height = screen.width(), screen.height()
        icon_dir = Path(__file__).resolve().parent / "icons"
        self.icon_colors = QIcon(str(icon_dir / "color_icon.svg"))
        self.icon_tags = QIcon(str(icon_dir / "tag_icon.svg"))
        self.icon_reload = QIcon(str(icon_dir / "reload_icon.svg"))
        self.icon_reload_green = QIcon(str(icon_dir / "reload_icon_green.svg"))
        self.icon_clear = QIcon(str(icon_dir / "clear_icon.svg"))

        self.setGeometry(0, 0, 400, height)
        self.setWindowTitle("BookmarksTagger")

        self._plist_missing_warned = False
        if not BOOKMARKS_PLIST.exists():
            self.warn_no_bookmarks_plist()
            self.mydict = {}
        else:
            self.mydict = build_table_dict()

        self.bookmark_watcher = BookmarkWatcher(str(BOOKMARKS_PLIST))
        self.bookmark_watcher.bookmark_added.connect(self.on_new_bookmark)

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
        self.button.setToolTip("Add/Delete tags of selected bookmarks> select by holding Cmd and tipping on entries")

        self.button_lights = QPushButton()

        # lights + bookmark status
        self.icons = LightIcons()
        self.bookmark_status = BookmarkStatus(self)
        # cycle through off -> window -> menubar
        self.lights_mode = "menubar"

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
        # enable menubar mode on launch
        self.apply_lights_mode()
            
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

        self.table = Table(self.mydict, self.extended_search_line_url, self.extended_search_line_name)
        self.table.table.installEventFilter(self)

        self.help_message_table = QLabel("Open selected Bookmark(s) with Ctrl+X")
        self.help_message_table.hide()

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
        self.shortcut_button.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_button.activated.connect(self.on_tags_button_clicked)

        self.line_delete_button.clicked.connect(self.on_line_delete_button_clicked)
        self.shortcut_line_delete_button = QShortcut(QKeySequence("Meta+C"), self)
        self.shortcut_line_delete_button.activated.connect(self.on_line_delete_button_clicked)

        self.line_shortcut = QShortcut(QKeySequence("Meta+S"), self)
        self.line_shortcut.activated.connect(self.go_to_search_bar)

        self.open_selected_bookmark_urls = self.table.open_selected_bookmark_urls
        self.shortcut_open_selected_bookmark_urls = QShortcut(QKeySequence("Meta+X"), self)
        self.shortcut_open_selected_bookmark_urls.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_open_selected_bookmark_urls.activated.connect(self.open_selected_bookmark_urls)

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
        self.upper_layout_help_message = QHBoxLayout()
        middle_layout = QHBoxLayout()
        bottom_layout = QVBoxLayout()
        main_layout = QVBoxLayout()

        upper_layout.addLayout(button_layout)
        upper_layout2.addLayout(self.button_layout2)
        self.upper_layout_help_message.addWidget(self.help_message_table)
        middle_layout.addWidget(self.table.table)
        bottom_layout.addLayout(self.line_layout)
        bottom_layout.addWidget(self.dropdown)
        bottom_layout.addWidget(self.extended_search_line_url)
        bottom_layout.addWidget(self.extended_search_line_name)

        main_layout.addLayout(upper_layout)
        main_layout.addLayout(upper_layout2)
        main_layout.addLayout(self.upper_layout_help_message)
        main_layout.addLayout(middle_layout)
        main_layout.addLayout(bottom_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def on_tags_button_clicked(self):
        """
        Toggle visibility of tags_window. 
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
        """Clear  SearchBar, URL and Name Search filters.
        Reloads the tags and fills table and dropdown menu."""
        self.line.clear()
        self.extended_search_line_name.clear()
        self.extended_search_line_url.clear()
        # force refresh 
        self.table.filter_table("", set())
        self.dropdown.clear()
        for tag in self.table.get_all_tags():
            self.dropdown.addItem(tag)

    def go_to_search_bar(self):
        """
        - Toggle focus between search bar and first table cell.
        - Also show help_message showing hotkey for opening URLs of 
          selected bookmarks in table."""
        if self.line.hasFocus():
            table_widget = self.table.table
            if table_widget.rowCount() and table_widget.columnCount():
                table_widget.setCurrentCell(0, 0)
            table_widget.setFocus()
            self.help_message_table.show()
        else:
            self.line.setFocus()
            self.help_message_table.hide()

    def on_button_details_clicked(self):
        """Toggle visibility of extended_search_lines for name/url substrings."""
        if self.extended_search_line_url.isVisible():
            self.extended_search_line_url.hide()
            self.extended_search_line_name.hide()
            self.extended_search_button.setText("▶Details")
        else:
            self.extended_search_line_url.show()
            self.extended_search_line_name.show()
            self.extended_search_button.setText("▼Details")

    def open_selected_bookmarks(self):
        """Open selected bookmarks in new tabs of the frontmost safari window."""
        self.open_selected_bookmark_urls()

   
    def on_button_load_safari_bookmarks_updated(self):
        """get data from bookmarks plist and save them as dict"""
        btn = self.button_update_safari_bookmarks
        if not BOOKMARKS_PLIST.exists():
            self.warn_no_bookmarks_plist()
            return
        self.mydict = build_table_dict()
        # fill existing table with the new data 
        self.table.reload(self.mydict)
        # refresh lights so the indicator reacts to the new bookmark set
        if self.lights_mode != "off":
            self.bookmark_status.check_frontmost_url_changed(force=True)
        # short visual feedback on reload button
        old_style = btn.styleSheet()
        btn.setIcon(self.icon_reload_green) # now-time 
        QTimer.singleShot(250, lambda: btn.setIcon(self.icon_reload)) # now-time + t1 
        QTimer.singleShot(550, lambda: btn.setIcon(self.icon_reload_green)) # now-time +t2 
        QTimer.singleShot(1050, lambda: btn.setIcon(self.icon_reload)) # now-time +t3 

    def resizeEvent(self, event):
        """Contains and calls all resize functions"""
        self.auto_resize(event)
        super().resizeEvent(event)

    def auto_resize(self, event):
        """Reorder elements vertically if small width"""
        if self.width() < 300:
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

        self.apply_lights_mode()

    def apply_lights_mode(self):
        """Apply current lights_mode value and update UI/tray."""
        if self.lights_mode == "off":
            self.bookmark_status.stop()
            self.button_lights.setIcon(self.icons.lights_off)
            self.tray_icon.hide()
            return

        # lights on: start monitoring and perform immediate check
        self.bookmark_status.start()
        # immediately reflect the last known state in both button and tray
        self.update_light_icon(self.bookmark_status.last_url_state)

        self.bookmark_status.check_frontmost_url_changed(force=True)
        if self.lights_mode == "window":
            self.button_lights.setToolTip("Lights: window mode (click for menubar)")
        else:
            # menubar mode -> show tray icon and keep button as toggle indicator
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
            if st == "error":
                return self.icons.lights_off
            return self.icons.lights_red

        icon = icon_for(status)
        tooltip_status = {
            None: "no Safari window",
            "full": "exact bookmark found",
            "domain": "domain bookmarked",
            "none": "no bookmark",
            "error": "could not read Safari URL",
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

    def warn_no_bookmarks_plist(self):
        """Show a one-time notice when Safari has no bookmarks file yet."""
        if self._plist_missing_warned:
            return
        self._plist_missing_warned = True
        QMessageBox.information(
            self,
            "No Bookmarks plist found",
            "No Bookmarks plist found. Open Safari once so macOS creates the file, then reload.",
        )

    def select_bookmark_by_url(self, url: str) -> bool:
        """Select the row that matches the given URL, if present."""
        table = self.table.table
        model = table.model()
        table.clearSelection()
        for row in range(table.rowCount()):
            item = table.item(row, 1)  # hidden URL column
            if item and item.text() == url:
                table.setRowHidden(row, False)
                idx = model.index(row, 0)
                table.selectionModel().select(
                    idx,
                    QItemSelectionModel.SelectionFlag.ClearAndSelect
                    | QItemSelectionModel.SelectionFlag.Rows,
                )
                table.scrollTo(idx)
                return True
        return False

    def on_new_bookmark(self, item_dict):
        """Focus the new bookmark added to Safari Bookmarks in the Table."""
        url = item_dict.get("URLString")
        if not url:
            return

        # refresh table so the new bookmark is visible/selectable
        self.on_button_load_safari_bookmarks_updated()

        # select the new bookmark row (if present) and open the tag window
        self.select_bookmark_by_url(url)

        if not hasattr(self, "tags_window"):
            self.tags_window = TagsWindow(self.table.table, self.height())

        self.tags_window.populate_tag_checkboxes()
        self.tags_window.show()
        self.tags_window.raise_()
        self.tags_window.activateWindow()
        self.tags_window.tags_input_field.setFocus()

    def eventFilter(self, obj, event):
        """Show a small hint for hotkeys to open url(s)
        when the table gains focus."""
        if obj is self.table.table:
            if event.type() == QEvent.Type.FocusIn:
                self.help_message_table.show()
            elif event.type() == QEvent.Type.FocusOut:
                self.help_message_table.hide()
        return super().eventFilter(obj, event)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
