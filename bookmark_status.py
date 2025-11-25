import subprocess
import textwrap
import plistlib
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtCore import QObject, QTimer, Signal


class LightIcons:
    def __init__(self) -> None:
        #lights 
        self.lights_off = QIcon("./icons/lights_off.svg")
        self.lights_on = QIcon("./icons/lights_on.svg")
        self.lights_green = QIcon("./icons/lights_green.svg")
        self.lights_yellow = QIcon("./icons/lights_yellow.svg")
        self.lights_red = QIcon("./icons/lights_red.svg")

class BookmarkStatus(QObject):
    """Periodically check if Safari's frontmost URL has changed"""
    # True = bookmarked, False = not bookmarked, None = no Safari window
    bookmark_checked = Signal(object)

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self.last_url_checked: str | None = None 
        self.last_url_state_bool: bool | None = None # True = bookmarked, False = not 

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_frontmost_url_changed)
        self.poll_interval_ms = 2000  # 2 s

    def start(self):
        """Begin periodic checks."""
        if not self.timer.isActive():
            self.timer.start(self.poll_interval_ms)

    def stop(self):
        """Stop periodic checks."""
        if self.timer.isActive():
            self.timer.stop()

    def check_frontmost_url_changed(self, force: bool = False):
        script_url = textwrap.dedent("""
        tell application "Safari" 
            if not (exists front window) then 
                return "NO_WINDOW"
            end if 
            set theURL to URL of current tab of front window
            return theURL
        end tell
        """)

        result = subprocess.run(
            ["/usr/bin/osascript", "-e", script_url],
            capture_output=True,
            text=True,
        )

        # if AppleScript failed, fall back to "no window" handling
        if result.returncode != 0:
            self.last_url_checked = None
            self.last_url_state_bool = False
            self.bookmark_checked.emit(False)
            return

        current_url = result.stdout.strip()

        if current_url == "NO_WINDOW" or current_url == "":
            # no window > no repeated bookmark check necessary 
            self.last_url_checked = None 
            self.last_url_state_bool = None
            self.bookmark_checked.emit(None)
            return

        # if URL has not changed -> nothing to do; last icon still valid
        if (
            self.last_url_checked == current_url
            and self.last_url_state_bool is not None
            and not force
        ):
            return 

        # if URL HAS CHANGED -> call check_bookmark_existence
        self.last_url_checked = current_url
        self.check_bookmark_existence(current_url)

    def check_bookmark_existence(self, url: str) -> None:
        """Check if given URL is stored in Safari bookmarks plist."""
        plist_path = Path.home() / "Library" / "Safari" / "Bookmarks.plist"

        # normalize to match both with/without trailing slash
        candidates = {url}
        if url.endswith("/"):
            candidates.add(url.rstrip("/"))
        else:
            candidates.add(url + "/")

        url_exists = False
        try:
            with plist_path.open("rb") as fp:
                data = plistlib.load(fp)

            stack = [data]
            while stack:
                node = stack.pop()
                if isinstance(node, dict):
                    stack.extend(node.values())
                elif isinstance(node, list):
                    stack.extend(node)
                elif isinstance(node, str):
                    if node in candidates:
                        url_exists = True
                        break
        except Exception:
            url_exists = False

        # cache state 
        self.last_url_state_bool = url_exists

        # NOTIFY MainWindow so it can update the icon 
        self.bookmark_checked.emit(url_exists)
