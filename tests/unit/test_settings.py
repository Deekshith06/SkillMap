from __future__ import annotations

import pytest
from pydantic import ValidationError

from skillmap.config.settings import Settings


def test_environment_configuration_parses_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKILLMAP_MODE", "lite")
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "https://skillmap.vercel.app, http://localhost:3000/",
    )
    monkeypatch.setenv("MAX_RESUME_SIZE_MB", "2")

    settings = Settings.from_env()

    assert settings.mode == "lite"
    assert settings.max_resume_bytes == 2 * 1024 * 1024
    assert settings.cors_allowed_origins == (
        "https://skillmap.vercel.app",
        "http://localhost:3000",
    )


@pytest.mark.parametrize(
    "origin",
    ["*", "javascript:alert(1)", "https://example.com/path"],
)
def test_rejects_unsafe_cors_origins(origin: str) -> None:
    with pytest.raises(ValidationError):
        Settings(cors_allowed_origins=(origin,))


def test_rejects_unknown_application_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKILLMAP_MODE", "automatic")

    with pytest.raises(ValidationError):
        Settings.from_env()
