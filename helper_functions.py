import plistlib
import pathlib
from pathlib import Path
import json
from dataclasses import dataclass

from services.settings import TAGS_JSON, BOOKMARKS_PLIST

CONFIG_PATH = Path(__file__).with_name("config.json")

DEFAULT_CONFIG = {
    "colors": {
        "col_name": "#cfffed",
        "col_url": "#00ccff", 
        "col_tags": "#008000",
    }
}


@dataclass
class SafariBookmarks:
    name: str
    url: str

def load_safari_bookmarks(plist_path: str | Path) -> list[SafariBookmarks]:
    plist_path = Path(plist_path)
    if not plist_path.exists():
        # No Safari bookmarks yet (or Safari never opened) -> return empty set instead of crashing
        return []

    try:
        with plist_path.open("rb") as f:
            root = plistlib.load(f)
    except Exception:
        # Corrupt or unreadable plist: fail softly
        return []

    bookmarks: list[SafariBookmarks] = []

    def walk(node: dict):
        # filders/containers 
        for child in node.get("Children",[]):
            if child.get("WebBookmarkType") == "WebBookmarkTypeLeaf" and "URLString" in child:
                title = (
                    child.get("URIDictionary", {}).get("title") or child.get("Title") or ""
                )
                url=child["URLString"]
                bookmarks.append(SafariBookmarks(name=title, url=url))

            # RECURSIVELY call function walk()
            if "Children" in child:
                walk(child)

    # function call 
    walk(root)
    return bookmarks

def load_tags() -> dict[str, list[str]]:
    if not TAGS_JSON.exists():
        return {}
    with TAGS_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    bm_tags = {}
    for url, tags in data.items():
        bm_tags[url] = tags if isinstance(tags, list) else str(tags).split(",")

    return bm_tags

def save_tags(tag_map: dict[str, list[str]]) -> None: 
    with TAGS_JSON.open("w", encoding="utf-8") as f:
        json.dump(tag_map, f, ensure_ascii=False, indent=2)

def build_table_dict() -> dict[str, dict[str, str]]:
    bookmarks = load_safari_bookmarks(BOOKMARKS_PLIST)
    tag_map = load_tags()

    table_dict: dict[str, dict[str, str]] = {}
    name_counter: dict[str, int] = {}
    for bm in bookmarks:
        tags = tag_map.get(bm.url, [])
        tags_str = ",".join(tags)
        base_name = bm.name or bm.url
        count = name_counter.get(base_name, 0) + 1
        name_counter[base_name] = count
        unique_name = base_name if count == 1 else f"{base_name} ({count})"

        table_dict[unique_name] = {
            "url": bm.url,
            "tags": tags_str,
        }
    
    return table_dict


def load_config() -> dict:
    """Load config file or return defaults if missing/invalid."""
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with CONFIG_PATH.open("r", encoding="utf8") as f:
            data = json.load(f)
    except Exception:
        # If file is broken, fall back to defaults
        return DEFAULT_CONFIG.copy()

    # Basic safety: ensure top-level keys exist
    cfg = DEFAULT_CONFIG.copy()
    cfg["colors"].update(data.get("colors", {}))
    return cfg


def save_config(config: dict) -> None:
    """Save config to JSON file."""
    with CONFIG_PATH.open("w", encoding="utf8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
