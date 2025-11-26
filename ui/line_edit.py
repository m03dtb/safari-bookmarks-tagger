import re

from rapidfuzz import fuzz

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
     QLineEdit
)


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

        # if user presses downkey 
        elif event.key() == Qt.Key_Up:
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
                row -=1 
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
