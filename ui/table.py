import subprocess
from urllib.parse import unquote, quote
from unicodedata import normalize as uni_normalize

from PySide6.QtWidgets import (QTableWidget, QTableWidgetItem, QAbstractItemView,
        QHeaderView, QLabel)
from PySide6.QtCore import Qt, QItemSelectionModel

from helper_functions import load_config


class Table():
    def __init__(self, mydict, extended_search_line_url, extended_search_line_name) -> None:
        super().__init__()
        self.table = QTableWidget()
        self.mydict = mydict
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.extended_search_line_url = extended_search_line_url
        self.extended_search_line_name = extended_search_line_name

        config = load_config()
        self.colors: dict[str, str] = config.get("colors", {})

        # define colors 
        self.col_name = self.colors.get("col_name")
        self.col_url  = self.colors.get("col_url")
        self.col_tags = self.colors.get("col_tags")

        # create set from all tags from the dict 
        all_tags = set()
        for value in self.mydict.values():
            for tag in value["tags"].split(","):
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)
        # set of all existing tags to all bookmarks 
        self.all_tags_full = set(all_tags)
        # set of all available tags (filtered)
        self.set_of_tags = set(all_tags)

        # CREATE TABLE with the Bookmarks
        table  = self.table 
        table.setRowCount(len(mydict.keys()))
        header_labels = ["Bookmarks", "URL", "Tags", "Name"]
        table.setColumnCount(len(header_labels))
        table.setHorizontalHeaderLabels(header_labels)

        # Hide all columns except the first one
        table.setColumnHidden(1, True)
        table.setColumnHidden(2, True)
        table.setColumnHidden(3, True)

        table.verticalHeader().hide() # hide row numbers

        # Create a set of all available tags (no pre-filtering)
        all_tags = set()
        for value in self.mydict.values():
            # split the comma-separated tags by comma
            for tag in value["tags"].split(","):
                tag = tag.strip()
                if tag:
                    # add the tags to the set 
                    all_tags.add(tag)

        self.fill_table(mydict)

    def fill_table(self, mydict):
        table = self.table
        # name of bookmark, data containing url and tags
        # example of how the mydict dict looks like:
        # {name : {"url": "...", "tags": "tag1,tag2"} }
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

            # instead of columns, use label in HTML-format to display 
            label = QLabel()
            label.setText(display_text)
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setWordWrap(True)
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            label.setMinimumHeight(100)

            # show the Name/URL/Tags Combo as one label per bookmark entry
            table.setCellWidget(row, 0, label)

            # hide the columns containing url/tags_str/name for each 
            # bookmark entry in the table
            # these infos are still needed for live filtering the table elements
            table.setItem(row, 1, QTableWidgetItem(url))
            table.setItem(row, 2, QTableWidgetItem(tags_str))
            table.setItem(row, 3, QTableWidgetItem(name))

        # adjust row's height according to the needed space for each entry (with Name,URL,Tags)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # stretch row 0 as it is the only row visible
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        # forces height calculation after filling the table 
        table.resizeRowsToContents()

    def get_all_tags(self) -> list[str]:
        """desc: returns sorted list of tags"""
        return sorted(self.set_of_tags)

    def filter_table(self, filter_text: str, used_tags=None):
        """Filter: hide/show rows of table using a simple text filter.
        filter_text: str -> comma separated tags
        """
        table = self.table
        table.setUpdatesEnabled(False)
        filter_text = (filter_text or "").strip().lower()

        # create empty set if no tags are used as filters yet
        used_tags = used_tags or set()
        
        # create filter_tags list (deleting spaces and empty strings)
        filter_tags = [
            tag.strip()
            for tag in filter_text.split(",")
            if tag.strip()
        ]

        # URL SUBSTRING in extended_search_line_url
        url_substring = ""
        # if the user pasted a URL into the extended_search_line_url TextEdit field ...
        if self.extended_search_line_url is not None:
            # strip the URL string and make it lowercase
            url_substring = (self.extended_search_line_url.text() or "").strip().lower()
        # normalize the String: e.g. "%C3%B6" becomes German "ö" 
        url_substring_dec = uni_normalize("NFC", unquote(url_substring))
        # normalize the unicode variant into NFC-Form -> 
        # e.g. "ö" and "o"+ Combining Umlaut are treated the same 
        url_substring_enc = quote(url_substring_dec, safe=":/?#[]@!$&'()*+,;=%")
        
        # NAME SUBSTRING in extended_search_line_name
        name_substring = ""
        # if the user pasted a Name substring to extended_search_line_name ...
        if self.extended_search_line_name is not None:
            name_substring = (self.extended_search_line_name.text() or "").strip().lower()

        visible_tags = set()

        try: 
            for row in range(table.rowCount()):
                item = table.item(row, 2)  # column: tags

                # -- TAGS --
                # make tags lowercase
                tags = item.text().lower() if item else ""
                # reformat the comma-separated tags and create list with these
                row_tags = [
                    tag.strip()
                    for tag in tags.split(",")
                    if tag.strip()
                ]

                # True only if EVERY filter tag exists in the row's tags
                tag_match:bool = all(ftag in row_tags for ftag in filter_tags)

                # -- URL --
                url_item = table.item(row, 1)
                # lowercase and normalize url
                url_text = url_item.text().lower() if url_item else ""
                url_text_dec = uni_normalize("NFC", unquote(url_text))

                # url_match if url_substring empty
                if not url_substring:
                    url_match = True
                else:
                    # url match if any url_text variant in any url_substring variant
                    url_match = (
                        # TODO: minimize variants
                        url_substring in url_text
                        or url_substring_dec in url_text
                        or url_substring in url_text_dec
                        or url_substring_dec in url_text_dec
                        or url_substring_enc in url_text
                    )

                # -- NAME --
                name_item = table.item(row, 3)
                name_text = name_item.text().lower() if name_item else ""
                # name_match if name_substring empty or substring of name_text 
                # -> allows only one single consecutive substring of name_text
                name_match: bool = (not name_substring) or (name_substring in name_text)

                # MATCH if ALL SUBCATEGORIES (tags, url, name) are True (empty possible)
                match: bool = tag_match and url_match and name_match
                table.setRowHidden(row, not match)

                if not match: # if a row is no match 
                    # get the model-index of the row (for col 0)
                    index = table.model().index(row, 0)
                    # deselect the rows that have no match
                    table.selectionModel().select(
                        index, # selection
                        # SelectionFlag: deselect
                        QItemSelectionModel.SelectionFlag.Deselect |
                        # the entire row for the given index
                        QItemSelectionModel.SelectionFlag.Rows
                    )

                if match:
                    # add the row_tags to the set of visible_tags
                    visible_tags.update(row_tags)

        finally:
            # re-render the table
            table.setUpdatesEnabled(True)
        # available tags, i.e. tags-set of visible table rows 
        # minus set of tags selected via dropdown
        self.set_of_tags = visible_tags - used_tags
                
    def open_selected_bookmark_urls(self):
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

        # Apple Script:
        # - open each selected bookmark entry 
        # - ensure Safari window is the frontmost window
        script = f'''set theURLs to {{{url_list}}}

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

        delay 0.1

        tell application "System Events"
            tell process "Safari"
                set frontmost to true 
                perform action "AXRaise" of window 1
            end tell
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
        """Clears the existing table and reloads its content"""
        self.mydict = mydict

        table = self.table
        table.clearContents()
        table.setRowCount(len(mydict.keys()))

        self.fill_table(mydict)
