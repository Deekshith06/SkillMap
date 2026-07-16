"""Small operational API mounted into the Reflex backend."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from skillmap.adapters.artifact_repository import load_runtime_assets, runtime_ready
from skillmap.config.settings import get_settings

backend_api = FastAPI(
    title="SkillMap operational API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@backend_api.get("/health", include_in_schema=False)
async def health() -> JSONResponse:
    ready = runtime_ready()
    payload: dict[str, object] = {
        "status": "ready" if ready else "not_ready",
        "mode": get_settings().mode,
    }
    if ready:
        manifest = load_runtime_assets().manifest
        payload.update(
            {
                "model_version": manifest.model_version,
                "taxonomy_version": manifest.taxonomy_version,
            }
        )
    return JSONResponse(payload, status_code=200 if ready else 503)
