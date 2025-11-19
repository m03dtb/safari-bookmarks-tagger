import pathlib
import sys
import json
import re
import plistlib
from pathlib import Path

from dataclasses import dataclass 
from PySide6.QtGui import QKeySequence, QShortcut
from rapidfuzz import fuzz
from PySide6.QtCore import QSize, Qt, QAbstractTableModel
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QPushButton,
    QHBoxLayout, QVBoxLayout, QLineEdit, QLabel,
    QTableView, QTableWidget, QListWidget, QTableWidgetItem,
    QHeaderView,
)

# CONSTANT VARIABLES 
TAGS_JSON = Path("tags.json")
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

class Table():
    def __init__(self, mydict, line) -> None:
        super().__init__()
        self.table = QTableWidget()
        self.mydict = mydict

        # define colors 
        self.col_name = "#cfffed"
        self.col_url = "#0000ff"
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
        header_labels = ["Name", "URL", "Tags"]
        table.setColumnCount(len(header_labels))
        table.setHorizontalHeaderLabels(header_labels)

        table.setColumnHidden(1, True)
        table.setColumnHidden(2, True)

        table.verticalHeader().hide() # hide row numbers

        all_tags = set()
        for value in self.mydict.values():
            for tag in value["tags"].split(","):
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)


        for row, (name, data) in enumerate(mydict.items()):
            url = data["url"]
            # TODO: wieder auf data["tags"] zurücksetzen 
            tags_str = "TAG"# data["tags"]

            display_text = (
                "<html><body>"
                f'<span style="font-weight:bold; color:{self.col_name};">{name}</span><br>'
                f'<span style="color:{self.col_url};">{url}</span><br>'
                f'<span style="color:{self.col_tags};">{tags_str}</span>'
                "</body></html>"
            )

            label = QLabel()
            label.setText(display_text)
            label.setTextFormat(Qt.RichText)   # wichtig für HTML
            label.setWordWrap(True)

            # HTML in Spalte 0 anzeigen
            table.setCellWidget(row, 0, label)

            table.setItem(row, 1, QTableWidgetItem(url))
            table.setItem(row, 2, QTableWidgetItem(tags_str))

            # table.resizeRowToContents()

        table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        table.verticalHeader().setDefaultSectionSize(60)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        # table.resizeRowToContents()

    def get_all_tags(self):
        # immer aktuelle verfügbare Tags zurückgeben
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
                match = all(ftag in row_tags for ftag in filter_tags)
                table.setRowHidden(row, not match)

                if match:
                    visible_tags.update(row_tags)

        finally:
            table.setUpdatesEnabled(True)
        # available tags, i.e. tags of visible table rows minus those selected via dropdown
        self.set_of_tags = visible_tags - used_tags
                

class LineEdit(QLineEdit):
    def __init__(self, table_obj, dropdown, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_obj = table_obj
        self.dropdown = dropdown

        # KEY PRESSING ELEMENTS 
        self.textChanged.connect(self.on_text_changed)
        # Enter im LineEdit
        self.returnPressed.connect(self.on_return_pressed)
        # Enter/Doppelklick im Dropdown löst die gleiche Logik aus
        self.dropdown.itemActivated.connect(self.on_dropdown_item_activated)

    def on_dropdown_item_activated(self, item):
        """Called when pressed 'return' in the dropdown menu"""
        # Nutzt dieselbe Logik wie Enter im LineEdit
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
        # Alle Teile (inkl. Stub)
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

        # Tabellenfilter: alle fertigen Tags + ggf. Stub -> UND
        filter_tags = list(selected_tags)
        if user_input:
            filter_tags.append(user_input)
        filter_text = ",".join(filter_tags)

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
            if score >= 50:
                self.dropdown.addItem(tag)



    def on_return_pressed(self):
        """Tag aus der aktuellen Dropdown-Auswahl in die Zeile übernehmen."""
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
            # if no row selected 
            if row  < 0:
                # start at first row 
                row = 0
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
        _, height =  screen.width(), screen.height()
        self.setGeometry(0, 0, 700,height)


        self.line = None 
        # self.mydict = self.return_input_list()
        self.mydict = build_table_dict()
        self.setWindowTitle("MyApp")
        self.table = Table(self.mydict, self.line)
        self.button = QPushButton("Pressme")
        self.dropdown = QListWidget()
        self.dropdown.hide()
        self.line = LineEdit(self.table, self.dropdown)
        # self.set_of_tags = None 

        # LAYOUT 
        upper_layout = QHBoxLayout()
        middle_layout = QHBoxLayout()

        bottom_layout = QVBoxLayout()

        main_layout = QVBoxLayout()

        upper_layout.addWidget(self.button)
        middle_layout.addWidget(self.table.table)
        bottom_layout.addWidget(self.line)
        bottom_layout.addWidget(self.dropdown)

        main_layout.addLayout(upper_layout)
        main_layout.addLayout(middle_layout)
        main_layout.addLayout(bottom_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)



def main():
    # plist_path = pathlib.Path("~/Library/Safari/Bookmarks.plist").expanduser()
    # print(plist_path)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
