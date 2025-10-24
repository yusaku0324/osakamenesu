import os
import sys
import types
from pathlib import Path

import pytest

APP_ROOT = Path(__file__).resolve().parents[2]
os.chdir(APP_ROOT.parents[2])
sys.path.insert(0, str(APP_ROOT))


dummy_settings_module = types.ModuleType("app.settings")


class _DummySettings:
    def __init__(self) -> None:
        self.database_url = "postgresql+asyncpg://app:app@localhost:5432/osaka_menesu"
        self.api_origin = "http://localhost:3000"
        self.media_storage_backend = "local"
        self.media_local_directory = "test-media"
        self.media_url_prefix = "/media"
        self.media_cdn_base_url = None

    @property
    def media_root(self) -> Path:
        return Path.cwd() / self.media_local_directory


dummy_settings_module.settings = _DummySettings()
dummy_settings_module.Settings = _DummySettings  # type: ignore[attr-defined]
sys.modules.setdefault("app.settings", dummy_settings_module)

from app.storage import LocalMediaStorage  # type: ignore  # noqa: E402


@pytest.mark.asyncio
async def test_local_storage_returns_relative_url(tmp_path: Path) -> None:
    storage = LocalMediaStorage(
        root=tmp_path,
        url_prefix="/media",
        cdn_base_url=None,
    )
    result = await storage.save(folder="profiles", filename="photo.png", content=b"data", content_type="image/png")

    assert result.url == "/media/profiles/photo.png"
    assert result.key == "profiles/photo.png"
    assert result.path is not None and result.path.exists()


@pytest.mark.asyncio
async def test_local_storage_prefers_cdn_base(tmp_path: Path) -> None:
    storage = LocalMediaStorage(
        root=tmp_path,
        url_prefix="/media",
        cdn_base_url="https://cdn.example.com/assets",
    )
    result = await storage.save(folder="profiles", filename="photo.png", content=b"data", content_type="image/png")

    assert result.url == "https://cdn.example.com/assets/profiles/photo.png"
