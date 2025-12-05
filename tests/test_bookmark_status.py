from dataclasses import dataclass

import pytest
from PySide6.QtCore import QCoreApplication

from services.bookmark_status import BookmarkStatus, base_domain


@pytest.fixture(scope="session", autouse=True)
def qt_app():
    """Instantiate a QCoreApplication each time test is run."""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


@dataclass
class FakeResult:
    returncode: int
    stdout: str = ""


def test_applescript_error_emits_error(monkeypatch):
    """
    Assert that apple script error is correctly caught.
    """
    bs = BookmarkStatus()
    emitted = []
    bs.bookmark_checked.connect(emitted.append)

    # monkeypatch guarantees that subprocess.run() in services.bookmark_status
    # will always return a returncode=1 (error)
    monkeypatch.setattr(
        "services.bookmark_status.subprocess.run",
        lambda *args, **kwargs: FakeResult(returncode=1, stdout=""),
    )

    # calling check_frontmost_url_changed(), it is expected that last emittet Signal 
    # is "error", i.e. error is caught and asserted
    bs.check_frontmost_url_changed()
    assert emitted[-1] == "error"


def test_no_window_emits_none(monkeypatch):
    """Make sure check_frontmost_url_changed correctly catches the case 
    where no Safari window is open."""
    bs = BookmarkStatus()
    emitted = []
    bs.bookmark_checked.connect(emitted.append)

    monkeypatch.setattr(
        "services.bookmark_status.subprocess.run",
        lambda *args, **kwargs: FakeResult(returncode=0, stdout="NO_WINDOW\n"),
    )

    bs.check_frontmost_url_changed()
    assert emitted[-1] is None


def test_base_domain_ignores_common_inserts():
    """Checks if services/bookmark_status.py correctly handles 
    ignoring common second-level ccTLD inserts under country TLDs.
    """
    assert base_domain("foo.co.uk") == "foo.uk"
    assert base_domain("bar.com.au") == "bar.au"
    assert base_domain("example.com") == "example.com"
    assert base_domain("192.168.0.1") == "192.168.0.1"


def test_force_recheck_runs_even_if_url_same(monkeypatch):
    bs = BookmarkStatus()
    emitted = []
    bs.bookmark_checked.connect(emitted.append)

    # first run sets last_url_checked/state
    def fake_run(*_args, **_kwargs):
        return FakeResult(returncode=0, stdout="https://example.com\n")

    called = {"checks": 0}

    def fake_check(url):
        called["checks"] += 1
        bs.last_url_state = "none"
        bs.bookmark_checked.emit("none")

    monkeypatch.setattr("services.bookmark_status.subprocess.run", fake_run)
    monkeypatch.setattr(bs, "check_bookmark_existence", fake_check)

    bs.check_frontmost_url_changed()
    assert called["checks"] == 1

    # Without force, same URL would short-circuit; force=True must re-run
    bs.check_frontmost_url_changed(force=True)
    assert called["checks"] == 2
