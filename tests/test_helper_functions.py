import plistlib
from pathlib import Path

import pytest

import helper_functions as hf


def make_plist(tmp_path: Path, entries: list[tuple[str, str]]) -> Path:
    """Create a minimal Safari-like plist with given (title, url) entries."""
    children = []
    for title, url in entries:
        children.append(
            {
                "WebBookmarkType": "WebBookmarkTypeLeaf",
                "URLString": url,
                "URIDictionary": {"title": title},
            }
        )
    plist_root = {"Children": [{"Children": children}]}
    plist_path = tmp_path / "Bookmarks.plist"
    with plist_path.open("wb") as f:
        plistlib.dump(plist_root, f)
    return plist_path


def test_load_safari_bookmarks_missing(tmp_path):
    plist_path = tmp_path / "missing.plist"
    bookmarks = hf.load_safari_bookmarks(plist_path)
    assert bookmarks == []


def test_load_safari_bookmarks_corrupt(tmp_path):
    plist_path = tmp_path / "corrupt.plist"
    plist_path.write_bytes(b"not a plist")
    bookmarks = hf.load_safari_bookmarks(plist_path)
    assert bookmarks == []


def test_build_table_dict_disambiguates_names(tmp_path, monkeypatch):
    plist_path = make_plist(
        tmp_path,
        [
            ("Example", "https://example.com"),
            ("Example", "https://example.org"),
        ],
    )
    tags_json = tmp_path / "tags.json"
    tags_json.write_text("{}", encoding="utf-8")

    # Redirect paths used by helper_functions
    monkeypatch.setattr(hf, "BOOKMARKS_PLIST", plist_path)
    monkeypatch.setattr(hf, "TAGS_JSON", tags_json)

    table = hf.build_table_dict()
    assert "Example" in table
    assert "Example (2)" in table
    assert table["Example"]["url"] == "https://example.com"
    assert table["Example (2)"]["url"] == "https://example.org"
