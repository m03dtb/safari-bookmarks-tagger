import os
import subprocess
import textwrap
import plistlib
from pathlib import Path
from urllib.parse import urlparse, unquote, quote
from unicodedata import normalize as uni_normalize

from PySide6.QtGui import QIcon
from PySide6.QtCore import QObject, QTimer, Signal


ICON_DIR = Path(__file__).resolve().parent.parent / "icons"


class LightIcons:
    def __init__(self) -> None:
        # lights
        self.lights_off = QIcon(str(ICON_DIR / "lights_off.svg"))
        self.lights_on = QIcon(str(ICON_DIR / "lights_on.svg"))
        self.lights_green = QIcon(str(ICON_DIR / "lights_green.svg"))
        self.lights_yellow = QIcon(str(ICON_DIR / "lights_yellow.svg"))
        self.lights_red = QIcon(str(ICON_DIR / "lights_red.svg"))


class BookmarkStatus(QObject):
    """Periodically check if Safari's frontmost URL has changed"""
    # emits: "full" | "domain" | "none" | None (no Safari window)
    bookmark_checked = Signal(object)

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self.last_url_checked: str | None = None 
        self.last_url_state: str | None = None # "full" | "domain" | "none"

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

        # if AppleScript failed, mark as error instead of "no bookmark"
        if result.returncode != 0:
            self.last_url_checked = None
            self.last_url_state = "error"
            self.bookmark_checked.emit("error")
            return

        current_url = result.stdout.strip()

        if current_url == "NO_WINDOW" or current_url == "":
            # no window > no repeated bookmark check necessary 
            self.last_url_checked = None 
            self.last_url_state = None
            self.bookmark_checked.emit(None)
            return

        # if URL has not changed -> nothing to do; last icon still valid
        if (
            self.last_url_checked == current_url
            and self.last_url_state is not None
            and not force
        ):
            return 

        # if URL HAS CHANGED -> call check_bookmark_existence
        self.last_url_checked = current_url
        self.check_bookmark_existence(current_url)

    def check_bookmark_existence(self, url: str) -> None:
        """Check if given URL is stored in Safari bookmarks plist."""
        plist_path = Path.home() / "Library" / "Safari" / "Bookmarks.plist"

        def host_only(u: str) -> str:
            parsed = urlparse(u if "://" in u else "https://" + u)
            host = parsed.netloc.lower()
            if "@" in host:
                host = host.split("@", 1)[-1]
            if ":" in host:
                host = host.split(":", 1)[0]
            if host.startswith("www."):
                host = host[4:]
            return host

        def base_domain(host: str) -> str:
            parts = host.split(".")
            if len(parts) >= 2:
                return ".".join(parts[-2:])
            return host

        def normalize_parts(u: str) -> tuple[str, str, str, str]:
            """Return (host, base, path, query) with decoding and NFC."""
            parsed = urlparse(u if "://" in u else "https://" + u)
            host = host_only(u)
            base = base_domain(host)
            path = uni_normalize("NFC", unquote(parsed.path)).rstrip("/")
            query = uni_normalize("NFC", unquote(parsed.query))
            return host, base, path, query

        target_host = host_only(url)
        target_base = base_domain(target_host)
        _, _, target_path, target_query = normalize_parts(url)

        # collect all bookmark URL variants and base domains
        bookmark_bases: set[str] = set()
        bookmark_hosts: set[str] = set()
        full_match = False
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
                else:
                    continue

                if isinstance(node, dict) and "URLString" in node:
                    candidate_url = node.get("URLString", "")
                    cand_host, cand_base, cand_path, cand_query = normalize_parts(candidate_url)
                    if cand_host:
                        bookmark_hosts.add(cand_host)
                    if cand_base:
                        bookmark_bases.add(cand_base)
                    # full-match detection: same host and same path+query
                    if (
                        cand_host
                        and cand_host == target_host
                        and cand_path == target_path
                        and cand_query == target_query
                    ):
                        full_match = True
                        break
        except Exception:
            bookmark_bases = set()
            bookmark_hosts = set()
            full_match = False

        domain_match = bool(
            (target_host and target_host in bookmark_hosts)
            or (target_base and target_base in bookmark_bases)
        )

        # cache state: prefer full over domain
        if full_match:
            self.last_url_state = "full"
        elif domain_match:
            self.last_url_state = "domain"
        else:
            self.last_url_state = "none"

        # NOTIFY MainWindow so it can update the icon 
        self.bookmark_checked.emit(self.last_url_state)
