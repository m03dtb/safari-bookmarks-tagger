# Standard library
import re

# Third-party 
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
        # Enter in dropdown causes the same logic
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

        # determine the tags selected in SearchBar vs. the stub
        if text.endswith(","):
            # last tag selected; no stub
            selected_tags = set(parts)
            user_input = ""
        else:
            if parts: 
                selected_tags = set(parts[:-1]) # "full" filtering tags
                user_input = parts[-1] # stub
            else:
                selected_tags = set()
                user_input = ""

        used_tags = selected_tags
        filter_text = ",".join(selected_tags)

        self.table_obj.filter_table(filter_text, used_tags)

        # dropdown with all available tags 
        all_tags = list(self.table_obj.get_all_tags())
        self.dropdown.clear()

        if not user_input:
            # no stub > show all tags available
            for tag in all_tags:
                self.dropdown.addItem(tag)
            return

        # fuzzy filter available tags based on the stub
        scored = []
        for tag in all_tags:
            score = fuzz.ratio(str(tag), user_input)
            scored.append((score, tag))
        scored.sort(reverse=True)

        # tags with threshold score += 30 become visible in dropdown menu
        for score, tag in scored:
            if score >= 30:
                self.dropdown.addItem(tag)

    def on_return_pressed(self):
        """Take tag from dropdown and put it into SearchBar as a string"""
        # currently preselected dropdown tag
        item = self.dropdown.currentItem()
        # if no focus on a tag in the dropdown
        # -> select the topmost tag on Return
        if item is None and self.dropdown.count() > 0:
            item = self.dropdown.item(0)

        if item is None:
            return

        tag = item.text().strip()
        text = self.text()

        # split text into "part before last comma" and "stub after comma"
        before, sep, _ = text.rpartition(",")

        if sep:
            # If tags already existing, e.g. "tag1,myt"
            # -> prefix is what stands before "stub plus comma"
            prefix = before.strip()
            if prefix:
                prefix = prefix + ","
        else:
            # set no comma "myt"
            # -> no prefix: set the selected tag only
            prefix = ""

        # Stub ("myt") not put into SearchBar, but is replaced by 'tag'
        new_text = prefix + tag + ","

        # put text -> calls: on_text_changed
        # which updates set_of_tags with its new content
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

        elif event.key() == Qt.Key_Up:
            # ON KEY_UP:
            # count lines in dropdown
            count = self.dropdown.count()
            # if no entries in dropdown > do not open dropdown
            if count == 0:
                return 

            # row = currently selected row
            row = self.dropdown.currentRow()
            if row < 0:
                # no selection yet -> jump to last entry
                row = count - 1
            elif row > 0:
                # move one up
                row -= 1
            else:
                # already at first entry -> wrap to last
                row = count - 1
            # focus on first element in dropdown menu 
            self.dropdown.setCurrentRow(row)

        # if Cmd + Backspace 
        elif event.key() == Qt.Key_Backspace and event.modifiers() & Qt.MetaModifier:

            old_text = self.text()
            #  e.g. "tag1,tag2,tag3," or "tag1,tag2,tag3" -> "tag1,tag2,"
            new_text = re.sub(r'[^,]+,?$', '', old_text)
            self.setText(new_text)

            return 

        super().keyPressEvent(event)
