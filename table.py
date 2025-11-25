import subprocess

from PySide6.QtWidgets import (QTableWidget, QTableWidgetItem, QAbstractItemView, 
        QHeaderView, QLabel)
from PySide6.QtCore import QSize, Qt, QAbstractTableModel, QItemSelectionModel

from helper_functions import load_config
import colors 

class Table():
    def __init__(self, mydict, extended_search_line, extended_search_line_name) -> None:
        super().__init__()
        self.table = QTableWidget()
        self.mydict = mydict
        self.colors = colors
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.extended_search_line = extended_search_line
        self.extended_search_line_name = extended_search_line_name

        config = load_config()
        self.colors = config.get("colors", {})

        # define colors 
        self.col_name = self.colors.get("col_name")
        self.col_url  = self.colors.get("col_url")
        self.col_tags = self.colors.get("col_tags")

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

    def update_colors(self, colors: dict) -> None:
        """Update displayed colors and repaint rows."""
        if not colors:
            return
        self.colors = colors
        self.col_name = colors.get("col_name", self.col_name)
        self.col_url = colors.get("col_url", self.col_url)
        self.col_tags = colors.get("col_tags", self.col_tags)
        self.reload(self.mydict)

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

