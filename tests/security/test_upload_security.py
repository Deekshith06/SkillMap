from __future__ import annotations

import io
import zipfile

import pytest

from skillmap.adapters.document_parser import DocumentValidationError, parse_document
from skillmap.services.resume_service import parse_upload

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def test_rejects_docx_zip_path_traversal() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("../outside.xml", "malicious")
        archive.writestr("[Content_Types].xml", "<Types />")

    with pytest.raises(DocumentValidationError) as error:
        parse_document(buffer.getvalue(), "resume.docx", DOCX_MIME)

    assert error.value.category == "archive_path_traversal"


class FakeUpload:
    filename = "resume.txt"
    content_type = "text/plain"

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.offset = 0
        self.closed = False

    async def read(self, size: int) -> bytes:
        chunk = self.data[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk

    async def close(self) -> None:
        self.closed = True


def test_async_upload_reader_is_bounded_and_closed() -> None:
    upload = FakeUpload(b"sensitive resume content")

    with pytest.raises(DocumentValidationError) as error:
        __import__("asyncio").run(parse_upload(upload, max_bytes=4))

    assert error.value.category == "file_size_limit"
    assert upload.closed is True
