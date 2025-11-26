import os
import subprocess
import textwrap
import plistlib
from pathlib import Path
from urllib.parse import urlparse, unquote, quote
from unicodedata import normalize as uni_normalize

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

        # if AppleScript failed, fall back to "no window" handling
        if result.returncode != 0:
            self.last_url_checked = None
            self.last_url_state = "none"
            self.bookmark_checked.emit("none")
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

        def normalize_variants(u: str) -> set[str]:
            """Return decoded/raw variants, with/without query, to tolerate encoding noise."""
            variants: set[str] = set()
            if not u:
                return variants

            parsed = urlparse(u if "://" in u else "https://" + u)
            host = parsed.netloc.lower()
            if host.startswith("www."):
                host = host[4:]
            scheme = parsed.scheme or "https"
            fragment = ""  # ignore fragments for matching

            # decoded variant (handles % encodings + Unicode NFC)
            path_dec = uni_normalize("NFC", unquote(parsed.path)).rstrip("/")
            query_dec = uni_normalize("NFC", unquote(parsed.query))
            query_dec_str = f"?{query_dec}" if query_dec else ""
            variants.add(f"{scheme}://{host}{path_dec}{query_dec_str}{fragment}")
            variants.add(f"{scheme}://{host}{path_dec}")
            # re-encoded variant to cover input with umlauts vs stored percent-encoding
            path_dec_enc = quote(path_dec, safe="/")
            query_dec_enc = quote(query_dec, safe="=&?")
            query_dec_enc_str = f"?{query_dec_enc}" if query_dec_enc else ""
            variants.add(f"{scheme}://{host}{path_dec_enc}{query_dec_enc_str}{fragment}")
            variants.add(f"{scheme}://{host}{path_dec_enc}")

            # raw variant (in case stored value stays percent-encoded)
            path_raw = uni_normalize("NFC", parsed.path).rstrip("/")
            query_raw = uni_normalize("NFC", parsed.query)
            query_raw_str = f"?{query_raw}" if query_raw else ""
            variants.add(f"{scheme}://{host}{path_raw}{query_raw_str}{fragment}")
            variants.add(f"{scheme}://{host}{path_raw}")
            return variants

        def host_only(u: str) -> str:
            parsed = urlparse(u if "://" in u else "https://" + u)
            host = parsed.netloc.lower()
            if host.startswith("www."):
                host = host[4:]
            return host

        def base_domain(host: str) -> str:
            parts = host.split(".")
            if len(parts) >= 2:
                return ".".join(parts[-2:])
            return host

        target_host = host_only(url)
        target_base = base_domain(target_host)
        target_variants = normalize_variants(url)
        debug = bool(os.getenv("BOOKMARK_DEBUG"))

        full_match = False
        domain_match = False
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
                    continue
                else:
                    continue

                if isinstance(node, dict) and "URLString" in node:
                    candidate_url = node.get("URLString", "")
                    cand_variants = normalize_variants(candidate_url)
                    if target_variants & cand_variants:
                        full_match = True
                        break
                    if not full_match and target_base:
                        cand_host = host_only(candidate_url)
                        if base_domain(cand_host) == target_base:
                            domain_match = True
                    if debug:
                        print(
                            "[bookmark debug] no match yet",
                            {"current": url, "candidate": candidate_url, "cand_variants": list(cand_variants)},
                        )
        except Exception:
            full_match = False
            domain_match = False

        # cache state 
        if full_match:
            self.last_url_state = "full"
        elif domain_match:
            self.last_url_state = "domain"
        else:
            self.last_url_state = "none"

        if debug:
            print(
                "[bookmark debug] result",
                {"target_variants": list(target_variants), "full_match": full_match, "domain_match": domain_match},
            )

        # NOTIFY MainWindow so it can update the icon 
        self.bookmark_checked.emit(self.last_url_state)
