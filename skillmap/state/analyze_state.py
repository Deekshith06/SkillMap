"""analyze_state.py — Single resume upload + cluster prediction."""
from __future__ import annotations
import reflex as rx

from skillmap.state.app_state import AppState


class AnalyzeState(AppState):
    resume_text: str = ""
    resume_filename: str = ""
    jd_text: str = ""
    jd_filename: str = ""
    step: str = "upload"   # upload | embedding | result
    result: dict = {}
    match_result: dict = {}
    analyze_error: str = ""
    analyzing: bool = False
    input_mode: str = "file"   # file | text
    jd_mode: str = "text"

    def set_resume_text(self, text: str):
        self.resume_text = text

    def set_jd_text(self, text: str):
        self.jd_text = text

    def set_input_mode(self, mode: str):
        self.input_mode = mode

    def set_jd_mode(self, mode: str):
        self.jd_mode = mode

    # ── Computed vars for safe Var access ────────────────────────

    @rx.var
    def result_cluster_name(self) -> str:
        domains = self.result.get("domains", [])
        if domains and "sub_domain" in domains[0]:
            return domains[0]["sub_domain"]
        return self.result.get("cluster_name", "")

    @rx.var
    def result_confidence_pct(self) -> str:
        conf = self.result.get("confidence", 0)
        return f"{round(conf * 100)}%"

    @rx.var
    def result_top_skills(self) -> list[str]:
        return self.result.get("top_skills", [])[:12]

    @rx.var
    def result_domain(self) -> str:
        domains = self.result.get("domains", [])
        if domains:
            return domains[0].get("domain", "")
        return ""

    @rx.var
    def result_has_match(self) -> bool:
        return bool(self.match_result)

    @rx.var
    def match_score_str(self) -> str:
        ms = self.match_result.get("match_score", 0)
        return f"{ms}%"

    @rx.var
    def matched_keywords(self) -> list[str]:
        return self.match_result.get("matched_keywords", [])[:8]

    @rx.var
    def missing_keywords(self) -> list[str]:
        return self.match_result.get("missing_keywords", [])[:8]

    @rx.var
    def has_result(self) -> bool:
        return bool(self.result)

    @rx.var
    def result_similar_resumes(self) -> list[dict]:
        return self.result.get("similar_resumes", [])[:5]

    @rx.var
    def radar_data(self) -> list[dict]:
        skills = self.result.get("top_skills", [])[:8]
        return [{"domain": skill, "confidence": 95 - (i * 4)} for i, skill in enumerate(skills)]

    def reset_analyze(self):
        self.resume_text = ""
        self.resume_filename = ""
        self.jd_text = ""
        self.jd_filename = ""
        self.step = "upload"
        self.result = {}
        self.match_result = {}
        self.analyze_error = ""

    def clear_resume_file(self):
        self.resume_filename = ""
        self.resume_text = ""

    def clear_jd_file(self):
        self.jd_filename = ""
        self.jd_text = ""

    async def handle_upload(self, files: list[rx.UploadFile]):
        if not files:
            return
        self.analyzing = True
        self.analyze_error = ""
        self.step = "embedding"
        try:
            f = files[0]
            data = await f.read()
            filename = f.filename or "upload.txt"
            from skillmap.ml.extractors import extract_and_clean, validate_upload
            err = validate_upload(data, filename, f.content_type or "text/plain")
            if err:
                self.analyze_error = err
                self.step = "upload"
                self.analyzing = False
                return
            text = extract_and_clean(data, filename)
            self.resume_text = text
            self.resume_filename = filename
        except Exception as e:
            self.analyze_error = str(e)
            self.step = "upload"
        finally:
            self.analyzing = False
        
        if self.resume_text.strip():
            return AnalyzeState.predict_cluster()

    async def handle_jd_upload(self, files: list[rx.UploadFile]):
        if not files:
            return
        self.analyzing = True
        self.analyze_error = ""
        try:
            f = files[0]
            data = await f.read()
            filename = f.filename or "jd.txt"
            from skillmap.ml.extractors import extract_and_clean
            text = extract_and_clean(data, filename)
            self.jd_text = text
            self.jd_filename = filename
        except Exception as e:
            self.analyze_error = f"JD Error: {str(e)}"
        finally:
            self.analyzing = False

    @rx.event(background=True)
    async def predict_cluster(self):
        if not self.resume_text.strip():
            return
        async with self:
            self.analyzing = True
            self.analyze_error = ""
            self.step = "embedding"
        try:
            from skillmap.ml.predictor import embed_and_predict, cluster_lookup
            cid, conf, skills, similar, domains = embed_and_predict(self.resume_text)
            cluster = cluster_lookup.get(cid, {"name": "Unknown", "id": cid})
            result = {
                "cluster_id": cid,
                "cluster_name": cluster["name"],
                "confidence": round(conf, 4),
                "top_skills": skills,
                "similar_resumes": similar,
                "domains": domains,
            }
            entry = {
                "score": round(conf * 100),
                "name": self.resume_filename or "Pasted Resume",
                "type": "Analyze",
            }
            # Match if JD provided
            match_result = {}
            if self.jd_text.strip():
                from skillmap.ml.matcher import (
                    embed_text, compute_match_score,
                    extract_jd_keywords, compute_skill_gap
                )
                sm = None
                try:
                    from skillmap.ml.predictor import get_sentence_model
                    sm = get_sentence_model()
                except Exception:
                    pass
                if sm:
                    r_emb = embed_text(sm, self.resume_text)
                    j_emb = embed_text(sm, self.jd_text)
                    ms    = compute_match_score(r_emb, j_emb)
                else:
                    ms = 50.0
                jd_kw   = extract_jd_keywords(self.jd_text)
                gaps    = compute_skill_gap(self.resume_text, jd_kw)
                from skillmap.ml.matcher import compute_keyword_overlap
                overlap = compute_keyword_overlap(self.resume_text, jd_kw)
                match_result = {
                    "match_score": ms,
                    "skill_gaps": gaps,
                    "matched_keywords": overlap["matched"],
                    "missing_keywords": overlap["missing"],
                }
                entry["score"] = round(ms)
                entry["type"]  = "Match"

            async with self:
                self.result       = result
                self.match_result = match_result
                self.step         = "result"
                self.add_to_history(entry)
        except Exception as e:
            async with self:
                self.analyze_error = str(e)
                self.step = "upload"
        finally:
            async with self:
                self.analyzing = False
