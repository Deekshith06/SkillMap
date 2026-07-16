from __future__ import annotations

import io

import pytest
from docx import Document

from skillmap.adapters.document_parser import DocumentValidationError, parse_document
from skillmap.config.settings import Settings


def _pdf_bytes(text: str = "Python resume") -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(output)


def test_parses_pdf() -> None:
    result = parse_document(_pdf_bytes(), "resume.pdf", "application/pdf")

    assert result.file_type == "pdf"
    assert result.page_count == 1
    assert "Python resume" in result.text


def test_parses_docx() -> None:
    buffer = io.BytesIO()
    document = Document()
    document.add_paragraph("Python and Kubernetes")
    document.save(buffer)

    result = parse_document(
        buffer.getvalue(),
        "resume.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert result.file_type == "docx"
    assert result.text == "Python and Kubernetes"


def test_parses_utf8_txt_and_sanitizes_name() -> None:
    result = parse_document(b"Python and SQL", "../../resume.txt", "text/plain")

    assert result.filename == "resume.txt"
    assert result.text == "Python and SQL"


@pytest.mark.parametrize(
    ("filename", "content_type", "category"),
    [
        ("resume.exe", "application/octet-stream", "unsupported_extension"),
        ("resume.pdf", "text/plain", "mime_mismatch"),
        ("resume.pdf", "application/pdf", "signature_mismatch"),
    ],
)
def test_rejects_invalid_file_types(filename: str, content_type: str, category: str) -> None:
    with pytest.raises(DocumentValidationError) as error:
        parse_document(b"not a document", filename, content_type)

    assert error.value.category == category


def test_rejects_oversized_file_before_parsing() -> None:
    settings = Settings(max_resume_size_mb=1)

    with pytest.raises(DocumentValidationError) as error:
        parse_document(
            b"x" * (settings.max_resume_bytes + 1),
            "resume.txt",
            "text/plain",
            settings,
        )

    assert error.value.category == "file_size_limit"


def test_rejects_empty_document() -> None:
    with pytest.raises(DocumentValidationError) as error:
        parse_document(b"   \n", "resume.txt", "text/plain")

    assert error.value.category == "empty_document"
