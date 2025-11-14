import os
import sys
from pathlib import Path
from unittest import mock

# Import directly from constants.py to avoid __init__.py which needs aiohttp
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "crank" / "security"))
from constants import get_default_cert_dir  # noqa: E402, I001  # type: ignore[import-not-found]


def test_cert_dir_env_override() -> None:
    """CERT_DIR environment variable takes precedence."""
    with mock.patch.dict(os.environ, {"CERT_DIR": "/custom/path"}, clear=True):
        assert get_default_cert_dir() == Path("/custom/path")


def test_cert_dir_container_fallback(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Inside containers we still point to /etc/certs even if not writable."""
    def fake_exists(path: str) -> bool:
        if path == "/.dockerenv":
            return True
        return False

    monkeypatch.delenv("CERT_DIR", raising=False)
    monkeypatch.setenv("KUBERNETES_SERVICE_HOST", "1")
    with mock.patch("os.path.exists", side_effect=fake_exists), mock.patch(
        "os.access", return_value=False
    ):
        assert get_default_cert_dir() == Path("/etc/certs")


def test_cert_dir_local_development(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Falls back to ~/.crank/certs when no container markers are present."""
    home = tmp_path
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CERT_DIR", raising=False)
    monkeypatch.delenv("KUBERNETES_SERVICE_HOST", raising=False)

    with mock.patch("os.path.exists", return_value=False), mock.patch("os.access", return_value=False):
        assert get_default_cert_dir() == home / ".crank" / "certs"
