"""Optional semantic mode; never imported by lite production startup."""

from __future__ import annotations

from sklearn.metrics.pairwise import cosine_similarity

from skillmap.config.settings import get_settings
from skillmap.core.exceptions import FullModeUnavailableError
from skillmap.domain.models import MatchResult, PredictionResult
from skillmap.domain.scoring import score_match
from skillmap.ml_runtime.lite_engine import LiteEngine


class FullEngine(LiteEngine):
    def __init__(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise FullModeUnavailableError() from exc
        model_path = get_settings().full_model_path.resolve()
        if not model_path.is_dir():
            raise FullModeUnavailableError()
        super().__init__()
        self._semantic_model = SentenceTransformer(
            str(model_path),
            local_files_only=True,
        )

    def analyze(self, text: str) -> PredictionResult:
        result = super().analyze(text)
        return result.model_copy(update={"scoring_mode": "semantic+taxonomy"})

    def match(self, resume_text: str, job_text: str) -> MatchResult:
        embeddings = self._semantic_model.encode(
            [resume_text, job_text],
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        semantic = max(
            0.0,
            min(1.0, float(cosine_similarity(embeddings[:1], embeddings[1:])[0][0])),
        )
        resume_domain = super().analyze(resume_text).cluster_name
        job_domain = super().analyze(job_text).cluster_name
        role_alignment = None
        if "Insufficient evidence" not in {resume_domain, job_domain}:
            role_alignment = 1.0 if resume_domain == job_domain else 0.0
        return score_match(
            resume_text,
            job_text,
            all_skills=self._all_skills,
            vectorizer=self.assets.vectorizer,
            model_version=self.assets.manifest.model_version,
            taxonomy_version=self.assets.manifest.taxonomy_version,
            semantic_similarity=semantic,
            role_alignment=role_alignment,
        )
