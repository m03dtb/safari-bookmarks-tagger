# BookmarksTagger

Desktop app (PySide6) for searching, tagging, and opening Safari bookmarks on macOS.

## Platform
- macOS only (uses Safari bookmarks and AppleScript) 

## Prerequisites
- macOS with Safari (reads `~/Library/Safari/Bookmarks.plist`; macOS creates it after Safari is opened once)
- Python 3.10+ (tested with 3.11.9, 3.12.6, 3.13.8)

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

## Tests
Run the small pytest suite for helper logic and the Safari status wrapper:
```bash
pip install pytest
python -m pytest
```

## Usage 
### Hotkeys (Cmd/Meta)
- Cmd+R: reload Safari bookmarks
- Cmd+T: open/close tag window
- Cmd+S: focus search bar; Enter applies first suggested tag
- Cmd+C: clear tag search (not URL/name filters)
- Cmd+X: open selected bookmarks in new Safari tabs
- Cmd+I: invert tag selection (in tag window)
- Cmd+D: delete selected tags (in tag window)
- Cmd+Click: multi-select bookmark rows

### Buttons
- Lights: Off / GUI / GUI + menu bar icon; checks every 2s if frontmost Safari tab is bookmarked (green exact, yellow
domain, red none).
- Color: set display colors for Name/URL/Tags.
- Details: show URL/Name substring filters next to tag search.
