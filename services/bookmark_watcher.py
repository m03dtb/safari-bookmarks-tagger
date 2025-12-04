import os
import pathlib

from PySide6.QtCore import QObject, QFileSystemWatcher, QTimer, Signal

from services.settings import BOOKMARKS_PLIST
import helper_functions

class BookmarkWatcher(QObject):
    bookmark_added = Signal(dict)

    def __init__(self, plist_path: str, parent=None):
        super().__init__(parent)

        self.plist_path = BOOKMARKS_PLIST
        self.watcher = QFileSystemWatcher([plist_path])

        # load initializing state of safari bookmarks
        self.old_data = helper_functions.load_safari_bookmarks(plist_path)
        
        # react to changes in plist 
        self.watcher.fileChanged.connect(self.on_changed)

    def on_changed(self, plist_path):
        """Function called when Safari's bookmarks.plist has changed"""

        new_data = helper_functions.load_safari_bookmarks(plist_path)

        # search for the new bookmark 
        added_bookmark = self.detect_new_bookmark(self.old_data, new_data)

        # update old data 
        self.old_data = new_data

        if added_bookmark:
            self.bookmark_added.emit(added_bookmark)

    def detect_new_bookmark(self, old, new):
        """Compares old and new bookmarks plist and examines newly added bookmark"""

        # helper_functions returns SafariBookmarks objects; compare by url
        old_urls = {item.url for item in old}
        new_urls = {item.url for item in new}

        added = new_urls - old_urls

        if not added:
            return None 

        # return the complete dict instead of just the URL 
        new_url = next(iter(added))
        for item in new:
            if item.url == new_url:
                # Emit a dict to match expected dialog structure
                return {"URLString": item.url, "URIDictionary": {"title": item.name}}

        return None
