import pathlib
from pathlib import Path

# Base directory of the project (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent

# Paths resolved relative to the project so they work regardless of CWD
TAGS_JSON = BASE_DIR / "tags.json"
BOOKMARKS_PLIST = Path("~/Library/Safari/Bookmarks.plist").expanduser()
