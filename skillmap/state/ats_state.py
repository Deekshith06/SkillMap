"""ats_state.py — ATS editor state + score history."""

from __future__ import annotations

import asyncio

import reflex as rx
from reflex_base.components.props import PropsBase

from skillmap.core.exceptions import UserFacingError
from skillmap.state.app_state import AppState


class ATSSuggestion(PropsBase):
    priority: str = "nice"
    title: str = ""
    detail: str = ""


class ATSState(AppState):
    _resume_text: str = ""
    jd_text: str = ""
    jd_mode: str = "text"
    jd_filename: str = ""
    ats_result: dict = {}
    ats_loading: bool = False
    ats_error: str = ""
    ats_filename: str = ""

    def set_jd_text(self, t: str):
        self.jd_text = t

    def reset_ats(self):
        self._resume_text = ""
        self.jd_text = ""
        self.jd_filename = ""
        self.ats_result = {}
        self.ats_error = ""
        self.ats_filename = ""

    def set_jd_mode(self, mode: str):
        self.jd_mode = mode

    def clear_resume_file(self):
        self.ats_filename = ""
        self._resume_text = ""

    def clear_jd_file(self):
        self.jd_filename = ""
        self.jd_text = ""

    @rx.var
    def has_ats_result(self) -> bool:
        return bool(self.ats_result)

    @rx.var
    def ats_total_score(self) -> int:
        return self.ats_result.get("total", 0)

    @rx.var
    def ats_categories(self) -> dict:
        return self.ats_result.get("categories", {})

    @rx.var
    def detected_domain(self) -> str:
        domains = self.ats_result.get("domains", [])
        return domains[0].get("domain", "General") if domains else "General"

    @rx.var
    def detected_sub_domain(self) -> str:
        domains = self.ats_result.get("domains", [])
        return domains[0].get("sub_domain", "") if domains else ""

    @rx.var
    def ats_suggestions(self) -> list[ATSSuggestion]:
        raw = self.ats_result.get("suggestions", [])
        return [
            ATSSuggestion(
                priority=s.get("priority", "nice"),
                title=s.get("title", ""),
                detail=s.get("detail", ""),
            )
            for s in raw
        ]

    @rx.var
    def ats_matched_kw(self) -> list[str]:
        kw = self.ats_result.get("keywords", {})
        return kw.get("matched", [])[:15] if kw else []

    @rx.var
    def ats_missing_kw(self) -> list[str]:
        kw = self.ats_result.get("keywords", {})
        return kw.get("missing", [])[:15] if kw else []

    @rx.var
    def ats_score_grade(self) -> str:
        score = self.ats_result.get("total", 0)
        if score >= 80:
            return "Excellent — Very likely to pass ATS"
        if score >= 60:
            return "Good — Some improvements needed"
        return "Needs work — Major gaps found"

    @rx.var
    def ats_scoring_mode(self) -> str:
        return self.ats_result.get("scoring_mode", "")

    @rx.var
    def ats_model_version(self) -> str:
        return self.ats_result.get("model_version", "")

    # Per-category sub-scores
    @rx.var
    def cat_keywords(self) -> int:
        cats = self.ats_result.get("categories", {})
        return cats.get("keywords", {}).get("score", 0) if cats else 0

    @rx.var
    def cat_keywords_pct(self) -> int:
        cats = self.ats_result.get("categories", {})
        return cats.get("keywords", {}).get("matchPct", 0) if cats else 0

    @rx.var
    def cat_formatting(self) -> int:
        cats = self.ats_result.get("categories", {})
        return cats.get("formatting", {}).get("score", 0) if cats else 0

    @rx.var
    def cat_formatting_pct(self) -> int:
        cats = self.ats_result.get("categories", {})
        score = cats.get("formatting", {}).get("score", 0) if cats else 0
        return round((score / 20.0) * 100) if score else 0

    @rx.var
    def cat_contact(self) -> int:
        cats = self.ats_result.get("categories", {})
        return cats.get("contact", {}).get("score", 0) if cats else 0

    @rx.var
    def cat_structure(self) -> int:
        cats = self.ats_result.get("categories", {})
        return cats.get("structure", {}).get("score", 0) if cats else 0

    @rx.var
    def cat_achievements(self) -> int:
        cats = self.ats_result.get("categories", {})
        return cats.get("achievements", {}).get("score", 0) if cats else 0

    @rx.var
    def cat_action_verbs(self) -> int:
        cats = self.ats_result.get("categories", {})
        return cats.get("actionVerbs", {}).get("score", 0) if cats else 0

    @rx.var
    def cat_length(self) -> int:
        cats = self.ats_result.get("categories", {})
        return cats.get("length", {}).get("score", 0) if cats else 0

    async def handle_ats_upload(self, files: list[rx.UploadFile]) -> None:
        if not files or self.ats_loading:
            return
        self.ats_loading = True
        self.ats_error = ""
        try:
            from skillmap.services.resume_service import parse_upload

            document = await parse_upload(files[0])
            self._resume_text = document.text
            self.ats_filename = document.filename
        except Exception as exc:
            self.ats_error = (
                exc.public_message
                if isinstance(exc, UserFacingError)
                else UserFacingError(
                    "Resume upload failed.", category="ats_upload_failure"
                ).public_message
            )
        finally:
            self.ats_loading = False

    async def handle_jd_upload(self, files: list[rx.UploadFile]):
        if not files or self.ats_loading:
            return
        self.ats_loading = True
        self.ats_error = ""
        try:
            from skillmap.services.resume_service import parse_upload

            document = await parse_upload(files[0])
            self.jd_text = document.text
            self.jd_filename = document.filename
        except Exception as exc:
            self.ats_error = (
                exc.public_message
                if isinstance(exc, UserFacingError)
                else UserFacingError(
                    "Job description upload failed.", category="ats_jd_upload_failure"
                ).public_message
            )
        finally:
            self.ats_loading = False

    @rx.event(background=True)  # type: ignore[operator]
    async def score_resume(self):
        async with self:
            if self.ats_loading or not self._resume_text.strip():
                return
            self.ats_loading = True
            self.ats_error = ""
            resume_text = self._resume_text
            job_description = self.jd_text
            filename = self.ats_filename
        try:

            def run_score() -> dict:
                from skillmap.adapters.artifact_repository import load_runtime_assets
                from skillmap.ml.ats_scorer import score_resume as compute_ats_score
                from skillmap.ml.skills import extract_skill_names

                assets = load_runtime_assets()
                result = compute_ats_score(
                    text=resume_text,
                    job_description=job_description,
                    spacy_skills=extract_skill_names(resume_text, max_skills=30),
                )
                result.update(
                    {
                        "scoring_mode": "document-quality+taxonomy",
                        "model_version": assets.manifest.model_version,
                        "taxonomy_version": assets.manifest.taxonomy_version,
                    }
                )
                return result

            result = await asyncio.to_thread(run_score)
            async with self:
                self.ats_result = result
                self.add_to_history(
                    {
                        "score": result.get("total", 0),
                        "name": filename or "Resume",
                        "type": "ATS",
                    }
                )
        except Exception as exc:
            async with self:
                self.ats_error = (
                    exc.public_message
                    if isinstance(exc, UserFacingError)
                    else UserFacingError(
                        "ATS scoring failed.", category="ats_scoring_failure"
                    ).public_message
                )
        finally:
            async with self:
                self.ats_loading = False
