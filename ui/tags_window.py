
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QWidget, QLabel, QCheckBox, QLineEdit, QVBoxLayout,  QHBoxLayout, QPushButton,
    QTableWidgetItem, QHeaderView, QMessageBox
)

from helper_functions import * 

class TagsWindow(QWidget):
    def __init__(self, table, height) -> None:
        super().__init__()
        self.setWindowTitle("Add / Delete Tags")

        self.setGeometry(0, 0, 300,(height/2))
        # cache colors from config so we can reuse them when updating labels
        self.colors = load_config().get("colors", {})
       
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
        self.checkboxes_layout.setSpacing(7)
   
        self.reverse_selected_button = QPushButton("[i]nvert_Sel")
        self.reverse_selected_button.clicked.connect(self.reverse_selected_checkboxes)
        self.reverse_selected_shortcut = QShortcut(QKeySequence("Meta+I"), self)
        self.reverse_selected_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.reverse_selected_shortcut.activated.connect(self.reverse_selected_checkboxes)

        self.select_delete_label = QLabel("Select tags to del: ")

        self.selection_layout = QHBoxLayout()
        self.selection_layout.addWidget(self.select_delete_label)
        self.selection_layout.addWidget(self.reverse_selected_button)

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
        # 1) get comma-separated tags from search bar entry field 
        raw_text = self.tags_input_field.text().strip()
        if not raw_text:
            return
        new_tags = [t.strip() for t in raw_text.split(",") if t.strip()]
        if not new_tags:
            return

        # 2) load existings tags from JSON 
        tag_map = load_tags()  # dict[url] -> list[str]

        # 3) iterate over seleceted rows
        indexes = self.table.selectionModel().selectedRows()
        if len(indexes) == 0:
            QMessageBox.information(self,"Info", "Select one or more entries you want to add tags to")
        else:

            for idx in indexes:
                row = idx.row()
                if self.table.isRowHidden(row):
                    # skip filtered-out entries so we only tag what's visible/selected
                    continue
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

            # sync table and labels with the updated tags
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
            # delete all tags in the delete-input (case case-insensitive)
            remaining = [t for t in existing if t.lower() not in tags_to_delete]

            if remaining:
                tag_map[url] = remaining
            else:
                tag_map.pop(url, None)

        # sync table and labels with the updated tags
        self._apply_tag_map_to_selection(tag_map, indexes)

        save_tags(tag_map)
        self.tags_input_field.clear()
        self.populate_tag_checkboxes()
        self.status_label_1.setText("Tag(s) deleted")
        QTimer.singleShot(2000, self.status_label_1.clear)

    def _apply_tag_map_to_selection(self, tag_map, indexes):
        """
        Update Table and Labels for all selected rows based on the passed tag_map. 
        """
        # refresh colors in case they were changed in the color dialog
        self.colors = load_config().get("colors", self.colors)
        col_url = self.colors.get("col_url", "#00ccff")
        col_tags = self.colors.get("col_tags", "#008000")

        for idx in indexes:
            row = idx.row()
            if self.table.isRowHidden(row):
                continue
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
                    f'<span style="color:{col_url};">{url}</span><br>'
                    f'<span style="color:{col_tags};">{tags_str}</span>'
                    "</body></html>"
                )
                label.setText(new_html)

        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.resizeRowsToContents()
