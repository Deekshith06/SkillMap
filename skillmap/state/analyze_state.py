"""Single-resume workflow state backed by typed runtime services."""

from __future__ import annotations

import asyncio

import reflex as rx

from skillmap.core.exceptions import UserFacingError
from skillmap.state.app_state import AppState


def _safe_message(exc: Exception, fallback: str) -> str:
    if isinstance(exc, UserFacingError):
        return exc.public_message
    return UserFacingError(fallback, category="unexpected_state_error").public_message


class AnalyzeState(AppState):
    _resume_text: str = ""
    resume_filename: str = ""
    jd_text: str = ""
    jd_filename: str = ""
    step: str = "upload"
    result: dict = {}
    match_result: dict = {}
    analyze_error: str = ""
    analyzing: bool = False
    cancel_requested: bool = False
    input_mode: str = "file"
    jd_mode: str = "text"

    def set_jd_text(self, text: str) -> None:
        self.jd_text = text

    def set_input_mode(self, mode: str) -> None:
        self.input_mode = mode

    def set_jd_mode(self, mode: str) -> None:
        self.jd_mode = mode

    def cancel_analysis(self) -> None:
        self.cancel_requested = True

    @rx.var
    def result_cluster_name(self) -> str:
        return self.result.get("cluster_name", "")

    @rx.var
    def result_confidence_pct(self) -> str:
        return f"{round(self.result.get('confidence', 0) * 100)}%"

    @rx.var
    def result_top_skills(self) -> list[str]:
        return self.result.get("top_skills", [])[:12]

    @rx.var
    def result_domain(self) -> str:
        domains = self.result.get("domains", [])
        return domains[0].get("domain", "") if domains else ""

    @rx.var
    def result_has_match(self) -> bool:
        return bool(self.match_result)

    @rx.var
    def match_score_str(self) -> str:
        score = self.match_result.get("score")
        return f"{score}%" if score is not None else "Insufficient evidence for a reliable score"

    @rx.var
    def matched_keywords(self) -> list[str]:
        return self.match_result.get("matched_skills", [])[:8]

    @rx.var
    def missing_keywords(self) -> list[str]:
        return self.match_result.get("missing_skills", [])[:8]

    @rx.var
    def match_evidence(self) -> list[str]:
        return self.match_result.get("evidence", [])

    @rx.var
    def scoring_mode(self) -> str:
        return self.match_result.get("scoring_mode", self.result.get("scoring_mode", ""))

    @rx.var
    def model_version(self) -> str:
        return self.result.get("model_version", "")

    @rx.var
    def result_evidence(self) -> list[str]:
        return self.result.get("evidence", [])

    @rx.var
    def has_result(self) -> bool:
        return bool(self.result)

    @rx.var
    def result_similar_resumes(self) -> list[dict]:
        return self.result.get("similar_profiles", [])[:5]

    @rx.var
    def result_seniority(self) -> str:
        return self.result.get("seniority", "Not enough evidence")

    @rx.var
    def result_behavioral(self) -> list[str]:
        return self.result.get("behavioral_signals", [])

    @rx.var
    def result_adjacent(self) -> list[str]:
        return self.result.get("adjacent_roles", [])

    @rx.var
    def result_trajectory(self) -> list[str]:
        return self.result.get("adjacent_roles", [])

    @rx.var
    def radar_data(self) -> list[dict]:
        return [
            {
                "domain": domain.get("domain", ""),
                "confidence": domain.get("confidence", 0),
            }
            for domain in self.result.get("domains", [])[:8]
        ]

    def reset_analyze(self) -> None:
        self._resume_text = ""
        self.resume_filename = ""
        self.jd_text = ""
        self.jd_filename = ""
        self.step = "upload"
        self.result = {}
        self.match_result = {}
        self.analyze_error = ""
        self.cancel_requested = False

    def clear_resume_file(self) -> None:
        self.resume_filename = ""
        self._resume_text = ""

    def clear_jd_file(self) -> None:
        self.jd_filename = ""
        self.jd_text = ""

    async def handle_upload(self, files: list[rx.UploadFile]) -> None:
        if not files or self.analyzing:
            return
        self.analyzing = True
        self.analyze_error = ""
        self.step = "embedding"
        try:
            from skillmap.services.resume_service import parse_upload

            document = await parse_upload(files[0])
            self._resume_text = document.text
            self.resume_filename = document.filename
            self.step = "upload"
        except Exception as exc:
            self.analyze_error = _safe_message(exc, "Resume upload failed.")
            self.step = "upload"
        finally:
            self.analyzing = False

    async def handle_jd_upload(self, files: list[rx.UploadFile]):
        if not files or self.analyzing:
            return
        self.analyzing = True
        self.analyze_error = ""
        try:
            from skillmap.services.resume_service import parse_upload

            document = await parse_upload(files[0])
            self.jd_text = document.text
            self.jd_filename = document.filename
        except Exception as exc:
            self.analyze_error = _safe_message(exc, "Job description upload failed.")
        finally:
            self.analyzing = False

    @rx.event(background=True)  # type: ignore[operator]
    async def predict_cluster(self) -> None:
        async with self:
            if self.analyzing or not self._resume_text.strip():
                return
            self.analyzing = True
            self.cancel_requested = False
            self.analyze_error = ""
            self.step = "embedding"
            resume_text = self._resume_text
            jd_text = self.jd_text
            filename = self.resume_filename
        try:
            from skillmap.services.analysis_service import analyze_resume, match_job

            prediction = await asyncio.to_thread(analyze_resume, resume_text)
            match = None
            if jd_text.strip():
                match = await asyncio.to_thread(match_job, resume_text, jd_text)
            async with self:
                if self.cancel_requested:
                    self.step = "upload"
                    return
                self.result = prediction.model_dump(mode="json")
                self.match_result = match.model_dump(mode="json") if match else {}
                self.step = "result"
                self.add_to_history(
                    {
                        "score": (
                            round(match.score)
                            if match and match.score is not None
                            else None
                            if match
                            else round(prediction.confidence * 100)
                        ),
                        "name": filename or "Resume",
                        "type": "Match" if match else "Analyze",
                    }
                )
        except Exception as exc:
            async with self:
                self.analyze_error = _safe_message(exc, "Analysis failed.")
                self.step = "upload"
        finally:
            async with self:
                self.analyzing = False
