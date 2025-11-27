# BookmarksTagger

Desktop app (PySide6) for searching, tagging, and opening Safari bookmarks on macOS.

## Prerequisites
- macOS with Safari (reads `~/Library/Safari/Bookmarks.plist`; macOS creates it after Safari is opened once)
- Python 3.10+ (tested with 3.10/3.11)

## Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python main.py
```

## Notes
- Icons and `tags.json` resolve relative to the project path, so starting from any CWD works.
- If `Bookmarks.plist` is missing, the app shows a notice; open Safari once, then reload.
- Hotkeys use the Meta/Cmd key (e.g., Cmd+S for search, Cmd+R to reload).
