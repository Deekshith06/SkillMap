"""Runtime engine protocol and mode selection."""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from skillmap.config.settings import get_settings
from skillmap.domain.models import MatchResult, PredictionResult


class RuntimeEngine(Protocol):
    def analyze(self, text: str) -> PredictionResult: ...

    def match(self, resume_text: str, job_text: str) -> MatchResult: ...


@lru_cache(maxsize=1)
def get_engine() -> RuntimeEngine:
    if get_settings().mode == "full":
        from skillmap.ml_runtime.full_engine import FullEngine

        return FullEngine()
    from skillmap.ml_runtime.lite_engine import LiteEngine

    return LiteEngine()
