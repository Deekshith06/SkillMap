"""bulk_state.py — Bulk upload + batch processing state."""
from __future__ import annotations
import csv
import io
import reflex as rx
from reflex_base.components.props import PropsBase

from skillmap.state.app_state import AppState


class BulkResultItem(PropsBase):
    index: int = 0
    filename: str = ""
    cluster_id: int = 0
    cluster_name: str = ""
    confidence: float = 0.0
    top_skills: list[str] = []
    match_score: float = 0.0
    error: str = ""



class BulkState(AppState):
    bulk_files: list[dict] = []   # {name, status, text, result, error}
    bulk_results: list[BulkResultItem] = []
    bulk_processing: bool = False
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

    def set_jd_text(self, t: str):
        self.jd_text = t

    def set_jd_mode(self, mode: str):
        self.jd_mode = mode

    def clear_jd_file(self):
        self.jd_filename = ""
        self.jd_text = ""

    def set_filter_cluster(self, v: str):
        self.filter_cluster = v
        self.page = 1

    def set_filter_min_conf(self, v: str):
        try:
            self.filter_min_conf = int(v)
        except Exception:
            self.filter_min_conf = 0
        self.page = 1

    def toggle_sort(self, field: str):
        if self.sort_field == field:
            self.sort_dir = "desc" if self.sort_dir == "asc" else "asc"
        else:
            self.sort_field = field
            self.sort_dir = "asc"

    def prev_page(self):
        if self.page > 1:
            self.page -= 1

    def next_page(self):
        self.page += 1

    def clear_all(self):
        self.bulk_files = []
        self.bulk_results = []
        self.processed_count = 0
        self.bulk_error = ""
        self.jd_text = ""
        self.jd_filename = ""
        self.page = 1
        self.filter_cluster = ""
        self.filter_min_conf = 0

    @rx.var
    def success_results(self) -> list[BulkResultItem]:
        return [r for r in self.bulk_results if not r.error]

    @rx.var
    def filtered_results(self) -> list[BulkResultItem]:
        data = list(self.success_results)
        if self.filter_cluster:
            data = [r for r in data if r.cluster_name == self.filter_cluster]
        if self.filter_min_conf > 0:
            data = [r for r in data if r.confidence >= self.filter_min_conf / 100]
        rev = self.sort_dir == "desc"
        if self.sort_field == "confidence":
            data.sort(key=lambda r: r.confidence, reverse=rev)
        elif self.sort_field == "cluster":
            data.sort(key=lambda r: r.cluster_name, reverse=rev)
        elif self.sort_field == "match_score":
            data.sort(key=lambda r: r.match_score, reverse=rev)
        else:
            data.sort(key=lambda r: r.index, reverse=rev)
        return data

    @rx.var
    def page_results(self) -> list[BulkResultItem]:
        start = (self.page - 1) * self.per_page
        return self.filtered_results[start: start + self.per_page]

    @rx.var
    def total_pages(self) -> int:
        return max(1, -(-len(self.filtered_results) // self.per_page))

    @rx.var
    def progress_pct(self) -> int:
        if not self.bulk_files:
            return 0
        return round((self.processed_count / len(self.bulk_files)) * 100)

    @rx.var
    def cluster_names(self) -> list[str]:
        seen: set[str] = set()
        out = []
        for r in self.success_results:
            n = r.cluster_name
            if n and n not in seen:
                seen.add(n); out.append(n)
        return sorted(out)

    async def handle_bulk_upload(self, files: list[rx.UploadFile]):
        if not files:
            return
        new_entries = []
        for f in files[:50]:
            data = await f.read()
            filename = f.filename or "upload.txt"
            try:
                from skillmap.ml.extractors import extract_and_clean
                text = extract_and_clean(data, filename)
                new_entries.append({"name": filename, "status": "pending", "text": text, "result": {}, "error": ""})
            except Exception as e:
                new_entries.append({"name": filename, "status": "error", "text": "", "result": {}, "error": str(e)})
        self.bulk_files = (self.bulk_files + new_entries)[:50]

    async def handle_jd_upload(self, files: list[rx.UploadFile]):
        if not files:
            return
        self.bulk_processing = True
        try:
            f = files[0]
            data = await f.read()
            filename = f.filename or "jd.txt"
            from skillmap.ml.extractors import extract_and_clean
            text = extract_and_clean(data, filename)
            self.jd_text = text
            self.jd_filename = filename
        except Exception as e:
            self.bulk_error = f"JD Error: {str(e)}"
        finally:
            self.bulk_processing = False

    @rx.event(background=True)
    async def process_all(self):
        if not self.bulk_files:
            return
        async with self:
            self.bulk_processing = True
            self.bulk_error = ""
            self.processed_count = 0

        results = []
        jd_active = len(self.jd_text.strip()) > 10

        for i, f in enumerate(self.bulk_files):
            try:
                from skillmap.ml.predictor import embed_and_predict, cluster_lookup
                cid, conf, skills, _, domains, _ = embed_and_predict(f["text"])
                cname = cluster_lookup.get(cid, {}).get("name", "Unknown")

                match_score = None
                if jd_active:
                    try:
                        from skillmap.ml.matcher import embed_text, compute_match_score
                        from skillmap.ml.predictor import get_sentence_model
                        sm = get_sentence_model()
                        if sm:
                            r_emb = embed_text(sm, f["text"])
                            j_emb = embed_text(sm, self.jd_text)
                            match_score = compute_match_score(r_emb, j_emb)
                    except Exception:
                        pass

                results.append(BulkResultItem(
                    index=i, filename=f["name"],
                    cluster_id=cid, cluster_name=cname,
                    confidence=round(conf, 4),
                    top_skills=skills,
                    match_score=match_score or 0.0,
                ))
            except Exception as e:
                results.append(BulkResultItem(
                    index=i, filename=f["name"], error=str(e),
                ))

            async with self:
                self.processed_count = i + 1

        async with self:
            self.bulk_results   = results
            self.bulk_processing = False

    def export_csv(self) -> str:
        """Return CSV string of filtered results."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Index", "Filename", "Cluster ID", "Cluster Name", "Confidence%", "Top Skills"])
        for r in self.filtered_results:
            writer.writerow([
                r.index, r.filename, r.cluster_id, r.cluster_name,
                f"{r.confidence * 100:.1f}",
                " | ".join(r.top_skills),
            ])
        return output.getvalue()

    def download_csv(self):
        """Download the CSV file."""
        csv_data = self.export_csv()
        return rx.download(data=csv_data.encode(), filename="skillmap-bulk.csv")
