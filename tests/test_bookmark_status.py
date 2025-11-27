from dataclasses import dataclass

import pytest
from PySide6.QtCore import QCoreApplication

from services.bookmark_status import BookmarkStatus


@pytest.fixture(scope="session", autouse=True)
def qt_app():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


@dataclass
class FakeResult:
    returncode: int
    stdout: str = ""


def test_applescript_error_emits_error(monkeypatch):
    bs = BookmarkStatus()
    emitted = []
    bs.bookmark_checked.connect(emitted.append)

    monkeypatch.setattr(
        "services.bookmark_status.subprocess.run",
        lambda *args, **kwargs: FakeResult(returncode=1, stdout=""),
    )

    bs.check_frontmost_url_changed()
    assert emitted[-1] == "error"


def test_no_window_emits_none(monkeypatch):
    bs = BookmarkStatus()
    emitted = []
    bs.bookmark_checked.connect(emitted.append)

    monkeypatch.setattr(
        "services.bookmark_status.subprocess.run",
        lambda *args, **kwargs: FakeResult(returncode=0, stdout="NO_WINDOW\n"),
    )

    bs.check_frontmost_url_changed()
    assert emitted[-1] is None
