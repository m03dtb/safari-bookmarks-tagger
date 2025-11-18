import sys
from PySide6.QtGui import QKeySequence, QShortcut
from rapidfuzz import fuzz
from PySide6.QtCore import QSize, Qt, QAbstractTableModel
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QPushButton,
    QHBoxLayout, QVBoxLayout, QLineEdit,
    QTableView, QTableWidget, QListWidget, QTableWidgetItem
)


class Table():
    def __init__(self, mydict, line) -> None:
        super().__init__()
        self.table = QTableWidget()
        self.mydict = mydict
        # Grundmenge aller EINZELNEN Tags aus dem Dict aufbauen
        all_tags = set()
        for value in self.mydict.values():
            for tag in value.split(","):
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)
        # unveränderliche Basis-Menge und aktuell verfügbare Tags
        self.all_tags_full = set(all_tags)
        self.set_of_tags = set(all_tags)

        # CREATE TABLE with the columns "name" and "tags"
        table  = self.table 
        table.setRowCount(len(mydict.keys()))
        header_labels = ["Name", "Tags"]
        table.setColumnCount(len(header_labels))
        table.setHorizontalHeaderLabels(header_labels)

        for row, (key, value) in enumerate(mydict.items()):
            # Name in Column 0
            table.setItem(row, 0, QTableWidgetItem(key))
            # Tags in Column 1
            table.setItem(row, 1, QTableWidgetItem(value))


    def get_all_tags(self):
        # immer aktuelle verfügbare Tags zurückgeben
        return sorted(self.set_of_tags)

    def filter_table(self, filter_text: str, used_tags=None):
        """Zeilen der Tabelle anhand eines einfachen Textfilters ein-/ausblenden.
            filter_text: str -> comma separated tags
        """
        table = self.table
        filter_text = (filter_text or "").strip().lower()
        used_tags = used_tags or set()
        
        # create filter_tags list (deleting spaces and empty strings)
        filter_tags = [
            tag.strip()
            for tag in filter_text.split(",")
            if tag.strip()
        ]

        visible_tags = set()

        for row in range(table.rowCount()):
            item = table.item(row, 1)  # Spalte 1 = Tags-Spalte
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
        # read all tags already chosen from QLineEdit SearchBar
        parts = [part.strip() for part in text.split(",") if part.strip()]
        used_tags = set(parts)

        # still available tags = all_tags_full minus used_tags
        # self.table_obj.set_of_tags = self.table_obj.all_tags_full - used_tags


        # use only the part AFTER the last comma in SearchBar
        _ , sep, after = text.rpartition(",")
        if sep:
            # Wenn schon Tags vor dem Komma stehen, nur den Stub danach suchen
            user_input = after.strip()
        else:
            # Kein Komma -> kompletter Text ist der Stub
            user_input = text.strip()

        # Tabelle filtern:
        # - wenn noch ein Stub eingegeben wird: nach dem Stub filtern
        # - sonst (kein Stub, aber schon Tags gewählt): nach dem letzten Tag filtern
        if user_input:
            filter_text = user_input
        elif parts:
            filter_text = parts[-1]
        else:
            filter_text = ""

        self.table_obj.filter_table(filter_text, used_tags)

        all_tags = list(self.table_obj.get_all_tags())
        self.dropdown.clear()

        if len(user_input) < 1:
            # Kein Stub -> alle Tags anzeigen
            for tag in all_tags:
                self.dropdown.addItem(tag)
            return

        scored = []
        # aktuellen Score für jeden Tag berechnen
        for tag in all_tags:
            score = fuzz.ratio(str(tag), user_input)
            scored.append((score, tag))
        # beste Treffer zuerst anzeigen
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

            return 

        super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.line = None 
        self.mydict = self.return_input_list()
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


    def return_input_list(self):
        mylist= ["el_num1", "el_num2", "el_num3","el_albert","el_chrissy",
                "el_number", "el_num2b", "el_numb2", "el_num4a", "el_num4b",
                "el_nmb41", "el_num41"]

        mytags =  ["num1", "num2", "num3,num41,num4","num1","num2",
                   "number", "num2b", "numb2", "anum2", "num4b",
                   "nmb41", "num41,num2"]

        dict_list_tags = {}
        for elem, tag in zip(mylist, mytags) :
            dict_list_tags[elem] = tag

        return dict_list_tags


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
