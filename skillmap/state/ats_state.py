"""ats_state.py — ATS editor state + score history."""
from __future__ import annotations
import reflex as rx
from reflex_base.components.props import PropsBase

from skillmap.state.app_state import AppState


class ATSSuggestion(PropsBase):
    priority: str = "nice"
    title: str = ""
    detail: str = ""


class ATSState(AppState):
    resume_text: str = ""
    jd_text: str = ""
    jd_mode: str = "text"
    jd_filename: str = ""
    ats_result: dict = {}
    ats_loading: bool = False
    ats_error: str = ""
    ats_filename: str = ""

    def set_resume_text(self, t: str):
        self.resume_text = t

    def set_jd_text(self, t: str):
        self.jd_text = t

    def reset_ats(self):
        self.resume_text = ""
        self.jd_text = ""
        self.jd_filename = ""
        self.ats_result = {}
        self.ats_error = ""
        self.ats_filename = ""

    def set_jd_mode(self, mode: str):
        self.jd_mode = mode

    def clear_resume_file(self):
        self.ats_filename = ""
        self.resume_text = ""

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

    async def handle_ats_upload(self, files: list[rx.UploadFile]):
        if not files:
            return
        self.ats_loading = True
        self.ats_error = ""
        try:
            f = files[0]
            data = await f.read()
            filename = f.filename or "resume.txt"
            from skillmap.ml.extractors import extract_and_clean
            text = extract_and_clean(data, filename)
            self.resume_text = text
            self.ats_filename = filename
        except Exception as e:
            self.ats_error = str(e)
        finally:
            self.ats_loading = False
        
        if self.resume_text.strip():
            yield ATSState.score_resume()
            import asyncio
            await asyncio.sleep(0.1)

    async def handle_jd_upload(self, files: list[rx.UploadFile]):
        if not files:
            return
        self.ats_loading = True
        self.ats_error = ""
        try:
            f = files[0]
            data = await f.read()
            filename = f.filename or "jd.txt"
            from skillmap.ml.extractors import extract_and_clean
            text = extract_and_clean(data, filename)
            self.jd_text = text
            self.jd_filename = filename
        except Exception as e:
            self.ats_error = f"JD Error: {str(e)}"
        finally:
            self.ats_loading = False

    @rx.event(background=True)
    async def score_resume(self):
        if not self.resume_text.strip():
            return
        async with self:
            self.ats_loading = True
            self.ats_error = ""
        try:
            from skillmap.ml.skills import extract_skill_names
            from skillmap.ml.extractors import clean_text
            from skillmap.ml.ats_scorer import score_resume as _score
            spacy_skills = extract_skill_names(self.resume_text, max_skills=30)
            result = _score(
                text=self.resume_text,
                job_description=self.jd_text,
                spacy_skills=spacy_skills,
            )
            async with self:
                self.ats_result = result
                self.add_to_history({
                    "score": result.get("total", 0),
                    "name": self.ats_filename or "Resume",
                    "type": "ATS",
                })
        except Exception as e:
            async with self:
                self.ats_error = str(e)
        finally:
            async with self:
                self.ats_loading = False
