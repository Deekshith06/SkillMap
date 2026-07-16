"""Bounded bulk upload and analysis state."""

from __future__ import annotations

import asyncio
import csv
import io

import reflex as rx
from reflex_base.components.props import PropsBase

from skillmap.config.settings import get_settings
from skillmap.core.exceptions import UserFacingError
from skillmap.state.app_state import AppState


class BulkResultItem(PropsBase):
    index: int = 0
    filename: str = ""
    cluster_id: int = -1
    cluster_name: str = ""
    confidence: float = 0.0
    top_skills: list[str] = []
    match_score: float | None = None
    scoring_mode: str = ""
    evidence: list[str] = []
    error: str = ""


class BulkState(AppState):
    _bulk_documents: dict[str, str] = {}
    _bulk_order: list[tuple[str, str]] = []
    _batch_size_bytes: int = 0

    bulk_files: list[dict] = []
    bulk_results: list[BulkResultItem] = []
    bulk_processing: bool = False
    cancel_requested: bool = False
    processed_count: int = 0
    bulk_error: str = ""
    jd_text: str = ""
    jd_filename: str = ""
    jd_mode: str = "text"
    filter_cluster: str = ""
    filter_min_conf: int = 0
    sort_field: str = "index"
    sort_dir: str = "asc"
    page: int = 1
    per_page: int = 25

    def set_jd_text(self, value: str) -> None:
        self.jd_text = value

    def set_jd_mode(self, mode: str) -> None:
        self.jd_mode = mode

    def clear_jd_file(self) -> None:
        self.jd_filename = ""
        self.jd_text = ""

    def cancel_processing(self) -> None:
        self.cancel_requested = True

    def set_filter_cluster(self, value: str) -> None:
        self.filter_cluster = value
        self.page = 1

    def set_filter_min_conf(self, value: str) -> None:
        try:
            self.filter_min_conf = int(value)
        except ValueError:
            self.filter_min_conf = 0
        self.page = 1

    def toggle_sort(self, field: str) -> None:
        if self.sort_field == field:
            self.sort_dir = "desc" if self.sort_dir == "asc" else "asc"
        else:
            self.sort_field = field
            self.sort_dir = "asc"

    def prev_page(self) -> None:
        if self.page > 1:
            self.page -= 1

    def next_page(self) -> None:
        if self.page < self.total_pages:
            self.page += 1

    def clear_all(self) -> None:
        self._bulk_documents = {}
        self._bulk_order = []
        self._batch_size_bytes = 0
        self.bulk_files = []
        self.bulk_results = []
        self.processed_count = 0
        self.bulk_error = ""
        self.jd_text = ""
        self.jd_filename = ""
        self.page = 1
        self.filter_cluster = ""
        self.filter_min_conf = 0
        self.cancel_requested = False

    @rx.var
    def success_results(self) -> list[BulkResultItem]:
        return [result for result in self.bulk_results if not result.error]

    @rx.var
    def filtered_results(self) -> list[BulkResultItem]:
        data = list(self.success_results)
        if self.filter_cluster:
            data = [item for item in data if item.cluster_name == self.filter_cluster]
        if self.filter_min_conf > 0:
            data = [item for item in data if item.confidence >= self.filter_min_conf / 100]
        reverse = self.sort_dir == "desc"
        if self.sort_field == "confidence":
            data.sort(key=lambda item: item.confidence, reverse=reverse)
        elif self.sort_field == "cluster":
            data.sort(key=lambda item: item.cluster_name, reverse=reverse)
        elif self.sort_field == "match_score":
            data.sort(
                key=lambda item: item.match_score if item.match_score is not None else -1,
                reverse=reverse,
            )
        else:
            data.sort(key=lambda item: item.index, reverse=reverse)
        return data

    @rx.var
    def page_results(self) -> list[BulkResultItem]:
        start = (self.page - 1) * self.per_page
        return self.filtered_results[start : start + self.per_page]

    @rx.var
    def total_pages(self) -> int:
        return max(1, -(-len(self.filtered_results) // self.per_page))

    @rx.var
    def progress_pct(self) -> int:
        total = len(self._bulk_order)
        return round(self.processed_count / total * 100) if total else 0

    @rx.var
    def cluster_names(self) -> list[str]:
        return sorted({item.cluster_name for item in self.success_results if item.cluster_name})

    async def handle_bulk_upload(self, files: list[rx.UploadFile]) -> None:
        if not files or self.bulk_processing:
            return
        settings = get_settings()
        self.bulk_error = ""
        duplicate_count = 0
        remaining = max(0, 50 - len(self._bulk_order))
        for upload in files[:remaining]:
            from skillmap.adapters.document_parser import sanitize_filename
            from skillmap.services.resume_service import parse_upload

            fallback_name = sanitize_filename(upload.filename or "upload")
            try:
                document = await parse_upload(upload)
                if document.sha256 in self._bulk_documents:
                    duplicate_count += 1
                    continue
                if self._batch_size_bytes + document.size_bytes > settings.max_batch_bytes:
                    raise UserFacingError(
                        "The batch exceeds the configured total upload limit.",
                        category="batch_size_limit",
                    )
                self._bulk_documents[document.sha256] = document.text
                self._bulk_order.append((document.sha256, document.filename))
                self._batch_size_bytes += document.size_bytes
                self.bulk_files.append(
                    {"name": document.filename, "status": "pending", "error": ""}
                )
            except Exception as exc:
                message = (
                    exc.public_message
                    if isinstance(exc, UserFacingError)
                    else UserFacingError(
                        "A document could not be queued.", category="bulk_upload_failure"
                    ).public_message
                )
                self.bulk_files.append({"name": fallback_name, "status": "error", "error": message})
        if len(files) > remaining:
            self.bulk_error = "Only the first 50 valid, unique files can be queued."
        elif duplicate_count:
            self.bulk_error = f"Skipped {duplicate_count} duplicate file(s)."

    async def handle_jd_upload(self, files: list[rx.UploadFile]) -> None:
        if not files or self.bulk_processing:
            return
        self.bulk_processing = True
        try:
            from skillmap.services.resume_service import parse_upload

            document = await parse_upload(files[0])
            self.jd_text = document.text
            self.jd_filename = document.filename
        except Exception as exc:
            self.bulk_error = (
                exc.public_message
                if isinstance(exc, UserFacingError)
                else UserFacingError(
                    "Job description upload failed.", category="bulk_jd_upload_failure"
                ).public_message
            )
        finally:
            self.bulk_processing = False

    @rx.event(background=True)  # type: ignore[operator]
    async def process_all(self) -> None:
        async with self:
            if self.bulk_processing or not self._bulk_order:
                return
            self.bulk_processing = True
            self.cancel_requested = False
            self.bulk_error = ""
            self.processed_count = 0
            items = [
                (digest, filename, self._bulk_documents[digest])
                for digest, filename in self._bulk_order
            ]
            job_text = self.jd_text

        results: list[BulkResultItem] = []
        from skillmap.services.analysis_service import analyze_resume, match_job

        for index, (_, filename, text) in enumerate(items):
            async with self:
                if self.cancel_requested:
                    break
            try:
                prediction = await asyncio.to_thread(analyze_resume, text)
                match = None
                if job_text.strip():
                    match = await asyncio.to_thread(match_job, text, job_text)
                results.append(
                    BulkResultItem(
                        index=index,
                        filename=filename,
                        cluster_id=prediction.cluster_id,
                        cluster_name=prediction.cluster_name,
                        confidence=prediction.confidence,
                        top_skills=prediction.top_skills,
                        match_score=match.score if match else None,
                        scoring_mode=(match.scoring_mode if match else prediction.scoring_mode),
                        evidence=(match.evidence if match else prediction.evidence),
                    )
                )
            except Exception as exc:
                results.append(
                    BulkResultItem(
                        index=index,
                        filename=filename,
                        error=(
                            exc.public_message
                            if isinstance(exc, UserFacingError)
                            else UserFacingError(
                                "Analysis failed for this file.",
                                category="bulk_analysis_failure",
                            ).public_message
                        ),
                    )
                )
            async with self:
                self.processed_count = index + 1

        async with self:
            self.bulk_results = results
            self.bulk_processing = False

    def export_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Index",
                "Filename",
                "Domain",
                "Evidence Strength%",
                "Job Match%",
                "Scoring Mode",
                "Top Skills",
            ]
        )
        for result in self.filtered_results:
            writer.writerow(
                [
                    result.index,
                    result.filename,
                    result.cluster_name,
                    f"{result.confidence * 100:.1f}",
                    "" if result.match_score is None else f"{result.match_score:.1f}",
                    result.scoring_mode,
                    " | ".join(result.top_skills),
                ]
            )
        return output.getvalue()

    def download_csv(self):
        return rx.download(data=self.export_csv().encode(), filename="skillmap-bulk.csv")
