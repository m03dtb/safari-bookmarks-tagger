import plistlib
import pathlib
from pathlib import Path
import json
from dataclasses import dataclass

from constants import TAGS_JSON, BOOKMARKS_PLIST

@dataclass
class SafariBookmarks:
    name: str
    url: str

def load_safari_bookmarks(plist_path: str | Path) -> list[SafariBookmarks]:
    plist_path = Path(plist_path)
    with plist_path.open("rb") as f:
        root = plistlib.load(f)

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
    for bm in bookmarks:
        tags = tag_map.get(bm.url, [])
        tags_str = ",".join(tags)
        table_dict[bm.name] = {
            "url": bm.url,
            "tags": tags_str,
        }
    
    return table_dict

