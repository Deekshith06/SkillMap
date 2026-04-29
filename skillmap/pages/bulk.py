import reflex as rx
from skillmap.components.layout import page_layout
import asyncio

class BulkState(rx.State):
    files: list[str] = []
    is_processing: bool = False
    progress: int = 0
    results: list[dict] = []
    
    async def handle_upload(self, files: list[rx.UploadFile]):
        self.is_processing = True
        self.progress = 0
        self.files = [f.filename for f in files]
        yield
        
        for i, filename in enumerate(self.files):
            # Simulate processing
            await asyncio.sleep(0.5)
            self.progress = int(((i + 1) / len(self.files)) * 100)
            self.results.append({
                "filename": filename,
                "score": 70 + (i * 2) % 25,
                "status": "Completed",
                "category": "Engineering" if i % 2 == 0 else "Product",
            })
            yield
            
        self.is_processing = False
        yield

    def clear_files(self):
        self.files = []
        self.results = []
        self.progress = 0

def bulk_upload() -> rx.Component:
    return page_layout(
        rx.vstack(
            rx.vstack(
                rx.text("Bulk Analysis", font_size="24px", font_weight="700", color="var(--text-primary)"),
                rx.text("Process hundreds of resumes simultaneously with AI clustering.", font_size="14px", color="var(--text-secondary)"),
                spacing="1",
                align_items="flex-start",
                margin_bottom="24px",
            ),
            
            rx.cond(
                BulkState.is_processing | (BulkState.files.length() > 0),
                rx.vstack(
                    rx.box(
                        rx.hstack(
                            rx.vstack(
                                rx.text(f"Processing {BulkState.files.length()} files...", font_size="15px", font_weight="600"),
                                rx.text(f"{BulkState.progress}% complete", font_size="13px", color="var(--text-secondary)"),
                                align_items="flex-start",
                                spacing="0",
                            ),
                            rx.spacer(),
                            rx.button("Cancel", size="2", variant="ghost", color_scheme="red", on_click=BulkState.clear_files),
                            width="100%",
                            align_items="center",
                            margin_bottom="16px",
                        ),
                        rx.box(
                            rx.box(
                                width=BulkState.progress.to_string() + "%",
                                height="8px",
                                bg="var(--orange)",
                                border_radius="var(--r-pill)",
                                transition="width 0.3s ease-in-out",
                            ),
                            width="100%",
                            height="8px",
                            bg="var(--bg-page)",
                            border_radius="var(--r-pill)",
                        ),
                        class_name="card",
                        padding="24px",
                        width="100%",
                    ),
                    
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("File Name"),
                                    rx.table.column_header_cell("Category"),
                                    rx.table.column_header_cell("ATS Score"),
                                    rx.table.column_header_cell("Status"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    BulkState.results,
                                    lambda r: rx.table.row(
                                        rx.table.cell(r["filename"]),
                                        rx.table.cell(rx.badge(r["category"], color_scheme="orange")),
                                        rx.table.cell(
                                            rx.text(r["score"].to_string() + "%", font_weight="600", color="var(--orange)")
                                        ),
                                        rx.table.cell(
                                            rx.hstack(
                                                rx.icon(tag="circle-check", size=14, color="green"),
                                                rx.text("Success", font_size="13px"),
                                                spacing="1",
                                                align_items="center",
                                            )
                                        ),
                                    )
                                )
                            ),
                            width="100%",
                        ),
                        class_name="card",
                        padding="0px",
                        overflow="hidden",
                        width="100%",
                        margin_top="16px",
                    ),
                    width="100%",
                    spacing="4",
                ),
                rx.upload(
                    rx.vstack(
                        rx.center(
                            rx.icon(tag="cloud-upload", size=40, color="var(--orange)", opacity=0.8),
                            width="80px",
                            height="80px",
                            bg="rgba(232, 92, 4, 0.05)",
                            border_radius="50%",
                            margin_bottom="16px",
                        ),
                        rx.text("Drop multiple resumes here", font_size="18px", font_weight="600", color="var(--text-primary)"),
                        rx.text("PDF, DOCX, or TXT (Max 500 files)", font_size="14px", color="var(--text-secondary)"),
                        rx.button("Select Files", margin_top="20px", class_name="btn-primary"),
                        align_items="center",
                        spacing="1",
                    ),
                    multiple=True,
                    on_drop=BulkState.handle_upload(rx.upload_files()),
                    class_name="upload-zone-large",
                    padding="80px",
                    width="100%",
                ),
            ),
            width="100%",
        ),
    )
