#hallo
import pathlib
import sys
import json
import re
import plistlib
from pathlib import Path
import subprocess

from dataclasses import dataclass 
from PySide6.QtGui import QKeySequence, QShortcut
from rapidfuzz import fuzz
from PySide6.QtCore import QSize, Qt, QAbstractTableModel, QTimer, QItemSelectionModel
from PySide6.QtWidgets import (
    QApplication, QBoxLayout, QLayout, QMessageBox, QWidget, QMainWindow, QPushButton,
    QHBoxLayout, QVBoxLayout, QLineEdit, QLabel,
    QTableView, QTableWidget, QListWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QCheckBox
)

# CONSTANT VARIABLES 
TAGS_JSON = Path("~/tags.json").expanduser()
BOOKMARKS_PLIST = Path("~/Library/Safari/Bookmarks.plist").expanduser()

@dataclass
class SafariBookmarks:
    name: str
    url: str

def load_safari_bookmarks(plist_path: str | Path) -> list[SafariBookmarks]:
    plist_path = Path(plist_path)
    with plist_path.open("rb") as f:
        root = plistlib.load(f)

    bookmarks: list[SafariBookmarks] = []

    def walk(node: dict):
        # filders/containers 
        for child in node.get("Children",[]):
            if child.get("WebBookmarkType") == "WebBookmarkTypeLeaf" and "URLString" in child:
                title = (
                    child.get("URIDictionary", {}).get("title") or child.get("Title") or ""
                )
                url=child["URLString"]
                bookmarks.append(SafariBookmarks(name=title, url=url))

            # RECURSIVELY call function walk()
            if "Children" in child:
                walk(child)

    # function call 
    walk(root)
    return bookmarks

def load_tags() -> dict[str, list[str]]:
    if not TAGS_JSON.exists():
        return {}
    with TAGS_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    bm_tags = {}
    for url, tags in data.items():
        bm_tags[url] = tags if isinstance(tags, list) else str(tags).split(",")

    return bm_tags

def save_tags(tag_map: dict[str, list[str]]) -> None: 
    with TAGS_JSON.open("w", encoding="utf-8") as f:
        json.dump(tag_map, f, ensure_ascii=False, indent=2)

def build_table_dict() -> dict[str, dict[str, str]]:
    bookmarks = load_safari_bookmarks(BOOKMARKS_PLIST)
    tag_map = load_tags()

    table_dict: dict[str, dict[str, str]] = {}
    for bm in bookmarks:
        tags = tag_map.get(bm.url, [])
        tags_str = ",".join(tags)
        table_dict[bm.name] = {
            "url": bm.url,
            "tags": tags_str,
        }
    
    return table_dict


class TagsWindow(QWidget):
    def __init__(self, table, height) -> None:
        super().__init__()
        self.setWindowTitle("Add / Delete Tags")

        self.setGeometry(0, 0, 300,(height/2))
       
        self.status_label_1 = QLabel("INFO: Adds tags to your selected bookmarks")
        self.status_label_2 = QLabel("Exit with <Ctrl> T")
        self.table = table
        self.tags_input_field = QLineEdit()
        self.add_button = QPushButton("Add Tag [Enter]")
        self.add_button.clicked.connect(self.add_tags)
        
        self.tags_input_field.returnPressed.connect(self.add_tags)
        self.delete_button = QPushButton("[D]elete selected Tag(s)")
        self.delete_button.clicked.connect(self.delete_tags)
        self.shortcut_delete_button = QShortcut(QKeySequence("Meta+D"), self)
        self.shortcut_delete_button.activated.connect(self.delete_tags)

        self.tag_checkboxes: list[QCheckBox] = []
        self.checkboxes_layout = QVBoxLayout()
        self.checkboxes_layout.setContentsMargins(0, 0, 0, 0)
        self.checkboxes_layout.setSpacing(0)
   
        self.reverse_selected_button = QPushButton("[i]nvert_Sel")
        self.reverse_selected_button.clicked.connect(self.reverse_selected_checkboxes)
        self.reverse_selected_shortcut = QShortcut(QKeySequence("Meta+I"), self)
        self.reverse_selected_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.reverse_selected_shortcut.activated.connect(self.reverse_selected_checkboxes)

        self.select_delete_label = QLabel("Select tags to del: ")

        self.selection_layout = QHBoxLayout()
        self.selection_layout.addWidget(self.select_delete_label)
        self.selection_layout.addWidget(self.reverse_selected_button)

        # indexes = table.selectionModel().selectedRows()
        # print("Anzahl selektierter Zeilen:", len(indexes))
        # for idx in sorted(indexes):
        #     print(f"ROW: {idx}")

        layout = QVBoxLayout()
        layout.addWidget(self.tags_input_field)
        layout.addWidget(self.add_button)
        layout.addLayout(self.selection_layout)
        layout.addLayout(self.checkboxes_layout)
        layout.addWidget(self.delete_button)
        layout.addStretch()
        layout.addWidget(self.status_label_1)
        layout.addWidget(self.status_label_2)
        self.setLayout(layout)

        self.populate_tag_checkboxes()


    def populate_tag_checkboxes(self):
        for cb in self.tag_checkboxes:
            cb.setParent(None)
        self.tag_checkboxes.clear()

        tag_map = load_tags()
        indexes = self.table.selectionModel().selectedRows()
        tags_set: set[str] = set()
        for idx in indexes:
            row = idx.row()
            if self.table.isRowHidden(row):
                continue
            url_item = self.table.item(row, 1)
            if url_item is None:
                continue
            url = url_item.text()
            existing = tag_map.get(url, [])
            for t in existing:
                t = t.strip()
                if t:
                    tags_set.add(t)

        for tag in sorted(tags_set, key=str.lower):
            cb = QCheckBox(tag)
            self.checkboxes_layout.addWidget(cb)
            self.tag_checkboxes.append(cb)


    def add_tags(self):
        # 1) Tags aus dem Eingabefeld holen (kommagetrennt)
        raw_text = self.tags_input_field.text().strip()
        if not raw_text:
            return
        new_tags = [t.strip() for t in raw_text.split(",") if t.strip()]
        if not new_tags:
            return

        # 2) bestehende Tags aus JSON laden
        tag_map = load_tags()  # dict[url] -> list[str]

        # 3) alle selektierten Zeilen durchgehen
        indexes = self.table.selectionModel().selectedRows()
        if len(indexes) == 0:
            QMessageBox.information(self,"Info", "Select one or more entries you want to add tags to")
        else:

            for idx in indexes:
                row = idx.row()
                # get url from hidden column 1 
                url_item = self.table.item(row,1) # column 1 == urls 
                if url_item is None:
                    continue
                url = url_item.text()

                # tags existing before for URL 
                existing = tag_map.get(url, [])
                # convert tags to lowercase 
                existing_lower = [tag.lower() for tag in existing]

                for t in new_tags:
                    if t.lower() not in existing_lower:
                        existing.append(t)
                        existing_lower.append(t.lower())

                # update map
                tag_map[url] = existing

            # Tabelle und Labels mit den aktualisierten Tags synchronisieren
            self._apply_tag_map_to_selection(tag_map, indexes)

            save_tags(tag_map)
            self.tags_input_field.clear()
            self.populate_tag_checkboxes()
            self.status_label_1.setText("Tag(s) saved")
            QTimer.singleShot(1000, self.status_label_1.clear)

    def reverse_selected_checkboxes(self) -> None:
        for checkbox in self.tag_checkboxes:
            checkbox.setChecked(not checkbox.isChecked())

    def delete_tags(self):
        tag_map = load_tags()
        indexes = self.table.selectionModel().selectedRows()
        if len(indexes) == 0:
            QMessageBox.information(self, "Info", "Select one or more entries you want to delete tags from")
            return

        tags_to_delete = [cb.text().strip().lower() for cb in self.tag_checkboxes if cb.isChecked()]
        if not tags_to_delete:
            return

        for idx in indexes:
            row = idx.row()
            if self.table.isRowHidden(row):
                continue
            url_item = self.table.item(row, 1)
            if url_item is None:
                continue

            url = url_item.text()
            existing = tag_map.get(url, [])
            # alle Tags entfernen, die im Delete-Input stehen (case-insensitive)
            remaining = [t for t in existing if t.lower() not in tags_to_delete]

            if remaining:
                tag_map[url] = remaining
            else:
                tag_map.pop(url, None)

        # Tabelle und Labels mit den aktualisierten Tags synchronisieren
        self._apply_tag_map_to_selection(tag_map, indexes)

        save_tags(tag_map)
        self.tags_input_field.clear()
        self.populate_tag_checkboxes()
        self.status_label_1.setText("Tag(s) deleted")
        QTimer.singleShot(1000, self.status_label_1.clear)

    def _apply_tag_map_to_selection(self, tag_map, indexes):
        """Gemeinsamer Code zum Aktualisieren der Tabelle und Labels
        für alle selektierten Zeilen basierend auf dem übergebenen tag_map.
        """
        for idx in indexes:
            row = idx.row()
            url_item = self.table.item(row, 1)
            if url_item is None:
                continue

            url = url_item.text()
            existing = tag_map.get(url, [])
            tags_str = ",".join(existing)

            # update table (col 2 = tags)
            tags_item = self.table.item(row, 2)
            if tags_item is not None:
                tags_item.setText(tags_str)
            else:
                self.table.setItem(row, 2, QTableWidgetItem(tags_str))

            # replace label in row 0 with new tags 
            label = self.table.cellWidget(row, 0)
            if label is not None:
                old_html = label.text()
                name_part = old_html.split("<br>", 1)[0]

                new_html = (
                    "<html><body>"
                    f"{name_part}<br>"
                    f'<span style="color:#00ccff;">{url}</span><br>'
                    f'<span style="color:#008000;">{tags_str}</span>'
                    "</body></html>"
                )
                label.setText(new_html)

        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.resizeRowsToContents()



class Table():
    def __init__(self, mydict, extended_search_line, extended_search_line_name) -> None:
        super().__init__()
        self.table = QTableWidget()
        self.mydict = mydict
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.extended_search_line = extended_search_line
        self.extended_search_line_name = extended_search_line_name

        # define colors 
        self.col_name = "#cfffed"
        self.col_url = "#00ccff"
        self.col_tags = "#008000"
        # self.col_folders = "#888888"
    

        # Grundmenge aller EINZELNEN Tags aus dem Dict aufbauen
        all_tags = set()
        for value in self.mydict.values():
            for tag in value["tags"].split(","):
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)
        # unveränderliche Basis-Menge und aktuell verfügbare Tags
        self.all_tags_full = set(all_tags)
        self.set_of_tags = set(all_tags)

        # CREATE TABLE with the columns "name" and "tags"
        table  = self.table 
        table.setRowCount(len(mydict.keys()))
        header_labels = ["Bookmarks", "URL", "Tags", "Name"]
        table.setColumnCount(len(header_labels))
        table.setHorizontalHeaderLabels(header_labels)

        table.setColumnHidden(1, True)
        table.setColumnHidden(2, True)
        table.setColumnHidden(3, True)

        table.verticalHeader().hide() # hide row numbers

        all_tags = set()
        for value in self.mydict.values():
            for tag in value["tags"].split(","):
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)

        for row, (name, data) in enumerate(mydict.items()):
            url = data["url"]
            tags_str = data["tags"]

            display_text = (
                "<html><body>"
                f'<span style="font-weight:bold; color:{self.col_name};">{name}</span><br>'
                f'<span style="color:{self.col_url};">{url}</span><br>'
                f'<span style="color:{self.col_tags};">{tags_str}</span>'
                "</body></html>"
            )

            label = QLabel()
            label.setText(display_text)
            label.setTextFormat(Qt.TextFormat.RichText)   # wichtig für HTML
            label.setWordWrap(True)
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

            # HTML in Spalte 0 anzeigen
            table.setCellWidget(row, 0, label)

            table.setItem(row, 1, QTableWidgetItem(url))
            table.setItem(row, 2, QTableWidgetItem(tags_str))
            table.setItem(row, 3, QTableWidgetItem(name))

        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.resizeRowsToContents()


    # other functions
    def get_all_tags(self) -> list[str]:
        """desc: returns sorted list of tags"""
        return sorted(self.set_of_tags)

    def filter_table(self, filter_text: str, used_tags=None):
        """Zeilen der Tabelle anhand eines einfachen Textfilters ein-/ausblenden.
            filter_text: str -> comma separated tags
        """
        table = self.table
        table.setUpdatesEnabled(False)
        filter_text = (filter_text or "").strip().lower()
        used_tags = used_tags or set()
        
        # create filter_tags list (deleting spaces and empty strings)
        filter_tags = [
            tag.strip()
            for tag in filter_text.split(",")
            if tag.strip()
        ]

        url_substring = ""
        if self.extended_search_line is not None:
            url_substring = (self.extended_search_line.text() or "").strip().lower()
        
        name_substring = ""
        if self.extended_search_line_name is not None:
            name_substring = (self.extended_search_line_name.text() or "").strip().lower()

        visible_tags = set()

        try: 
            for row in range(table.rowCount()):
                item = table.item(row, 2)  # Spalte 1 = Tags-Spalte
                tags = item.text().lower() if item else ""
                row_tags = [
                    tag.strip()
                    for tag in tags.split(",")
                    if tag.strip()
                ]
                tag_match = all(ftag in row_tags for ftag in filter_tags)

                url_item = table.item(row, 1)
                url_text = url_item.text().lower() if url_item else ""
                url_match = (not url_substring) or (url_substring in url_text)


                name_item = table.item(row, 3)
                name_text = name_item.text().lower() if name_item else ""
                name_match = (not name_substring) or (name_substring in name_text)

                match = tag_match and url_match and name_match
                table.setRowHidden(row, not match)

                if not match:
                    # Deselect rows that got hidden so stale selections do not bleed into tag actions
                    index = table.model().index(row, 0)
                    table.selectionModel().select(
                        index, QItemSelectionModel.SelectionFlag.Deselect | QItemSelectionModel.SelectionFlag.Rows
                    )

                if match:
                    visible_tags.update(row_tags)

        finally:
            table.setUpdatesEnabled(True)
        # available tags, i.e. tags of visible table rows minus those selected via dropdown
        self.set_of_tags = visible_tags - used_tags
                
    def open_selected_boomarks_urls(self):
        """desc: opens each selected entry in a separate new Safari tab"""
        indexes = self.table.selectionModel().selectedRows()

        list_of_urls_to_open = []
        # iterate over the selected bookmark entries 
        for bookmark in indexes:
            # extract each selected bookmark's url 
            row = bookmark.row()
            bookmark_url = self.table.item(row,1)
            if bookmark_url is None:
                continue
            url = bookmark_url.text()
        
            # save extracted urls in a list
            list_of_urls_to_open.append(url)

        # create comma-separated string of list of urls to open
        url_list = ",".join(f'"{u}"' for u in list_of_urls_to_open)

        # Apple Script to open each selected bookmark entry 
        # in a separate new tab
        script = f'''
        set theURLs to {{{url_list}}}

        tell application "Safari"
            if not (exists document 1) then
                make new document
            end if
            tell window 1
                    repeat with u in theURLs
                        make new tab with properties {{URL:u}}
                    end repeat
            end tell
            activate
        end tell
        '''

        subprocess.run(["osascript", "-e", script])

    def reload(self, mydict):
        self.mydict = mydict
        table = self.table
        table.clearContents()
        table.setRowCount(len(mydict.keys()))

        for row, (name, data) in enumerate(mydict.items()):
            url = data["url"]
            tags_str = data["tags"]

            display_text = (
                "<html><body>"
                f'<span style="font-weight:bold; color:{self.col_name};">{name}</span><br>'
                f'<span style="color:{self.col_url};">{url}</span><br>'
                f'<span style="color:{self.col_tags};">{tags_str}</span>'
                "</body></html>"
            )

            label = QLabel()
            label.setText(display_text)
            label.setTextFormat(Qt.TextFormat.RichText)   # wichtig für HTML
            label.setWordWrap(True)
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

            # HTML in Spalte 0 anzeigen
            table.setCellWidget(row, 0, label)

            table.setItem(row, 1, QTableWidgetItem(url))
            table.setItem(row, 2, QTableWidgetItem(tags_str))
            table.setItem(row, 3, QTableWidgetItem(name))

        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.resizeRowsToContents()


class LineEdit(QLineEdit):
    def __init__(self, table_obj, dropdown, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_obj = table_obj
        self.dropdown = dropdown

        # KEY PRESSING ELEMENTS 
        self.textChanged.connect(self.on_text_changed)
        # if pressed Enter in SearchBar
        self.returnPressed.connect(self.on_return_pressed)
        # Enter/Doppelklick im Dropdown löst die gleiche Logik aus
        self.dropdown.itemActivated.connect(self.on_dropdown_item_activated)

    def on_dropdown_item_activated(self, item):
        """Called when pressed 'return' in the dropdown menu"""
        self.on_return_pressed()

    def focusInEvent(self, event):
        """Unfold dropdown menu if focused and fill it with all tags"""
        super().focusInEvent(event)
        all_tags = self.table_obj.get_all_tags()
        self.dropdown.clear()
        self.dropdown.show()
        for tag in all_tags:
            self.dropdown.addItem(tag)

    def focusOutEvent(self, event):
        """Hide dropdown menu if not focused"""
        super().focusOutEvent(event)
        self.dropdown.hide()

    def on_text_changed(self, text: str):
        text = text or ""
        # split string in SearchBar and create list of comma-sep strings
        parts = [p.strip() for p in text.split(",") if p.strip()]

        # fertige Tags und Stub bestimmen
        if text.endswith(","):
            # letzter Tag abgeschlossen, kein Stub
            selected_tags = set(parts)
            user_input = ""
        else:
            if parts:
                selected_tags = set(parts[:-1])   # fertige Tags
                user_input = parts[-1]           # Stub
            else:
                selected_tags = set()
                user_input = ""

        used_tags = selected_tags

        filter_text = ",".join(selected_tags)

        self.table_obj.filter_table(filter_text, used_tags)

        # Dropdown aus verfügbaren Tags
        all_tags = list(self.table_obj.get_all_tags())
        self.dropdown.clear()

        if not user_input:
            # kein Stub -> alle verfügbaren Tags zeigen
            for tag in all_tags:
                self.dropdown.addItem(tag)
            return

        # mit Stub fuzzy filtern
        scored = []
        for tag in all_tags:
            score = fuzz.ratio(str(tag), user_input)
            scored.append((score, tag))
        scored.sort(reverse=True)

        for score, tag in scored:
            if score >= 30:
                self.dropdown.addItem(tag)

    def on_return_pressed(self):
        """Take tag from dropdown and put it into SearchBar as a string"""
        item = self.dropdown.currentItem()
        if item is None and self.dropdown.count() > 0:
            item = self.dropdown.item(0)

        if item is None:
            return

        tag = item.text().strip()
        text = self.text()

        # Text in "Teil vor letztem Komma" und "Stub danach" aufteilen
        before, sep, _ = text.rpartition(",")

        if sep:
            # If tags already existing, e.g. "tag1,myt"
            # -> Prefix ist alles vor dem Stub + Komma
            prefix = before.strip()
            if prefix:
                prefix = prefix + ","
        else:
            # set no comma "myt"
            # -> kein Prefix, nur den ausgewählten Tag setzen
            prefix = ""

        # Stub ("myt") not put into SearchBar, but is replaced by 'tag'
        new_text = prefix + tag + ","

        # Text setzen -> löst on_text_changed aus,
        # das set_of_tags anhand des neuen Inhalts aktualisiert
        self.setText(new_text)
        self.setCursorPosition(len(self.text()))

    def keyPressEvent(self, event):
        # if user presses downkey 
        if event.key() == Qt.Key_Down:
            # ON KEY_DOWN:
            # count lines in dropdown
            count = self.dropdown.count()
            # if no entries in dropdown > do not open dropdown
            if count == 0:
                return 

            # row = currently selected row
            row = self.dropdown.currentRow()
            if row  < 0: # if no row selected 
                row = 0 # start at first row 
            # if focus not yet on last element 
            elif row < count -1: 
                # on keypress down: go to next row 
                row +=1 
            else: 
                row = 0 # if focus on last row: go to first row (wrap-around)    
            # focus on first element in dropdown menu 
            self.dropdown.setCurrentRow(row)

        # elif event.key() == Qt.Key_Backspace:
        elif event.key() == Qt.Key_Backspace and event.modifiers() & Qt.MetaModifier:

            old_text = self.text()
            new_text = re.sub(r'[^,]+,?$', '', old_text)
            self.setText(new_text)

            return 

        super().keyPressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        screen = QApplication.primaryScreen().geometry()
        _, height = screen.width(), screen.height()
        self.setGeometry(0, 0, 700, height)
        self.setWindowTitle("BookmarksTagger_RELEASE")

        self.mydict = build_table_dict()

        self.button_update_safari_bookmarks = QPushButton("🔄[r]eload bookmarks")
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
        QTimer.singleShot(100, lambda: btn.setStyleSheet(old_style))

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
        

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
