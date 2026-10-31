from io import BytesIO

import pytest
from docx import Document
from pypdf import PdfWriter

from transcript_loader import extract_transcript


def test_extract_txt():
    text = extract_transcript(
        "meeting.txt",
        b"Meeting notes: Ananya owns testing.",
    )
    assert "Ananya owns testing" in text


def test_extract_docx():
    buffer = BytesIO()
    document = Document()
    document.add_paragraph("Meeting notes: Ananya owns testing.")
    document.save(buffer)

    text = extract_transcript("meeting.docx", buffer.getvalue())

    assert "Ananya owns testing" in text


def test_extract_pdf():
    buffer = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    writer.write(buffer)

    with pytest.raises(ValueError, match="No readable text"):
        extract_transcript("meeting.pdf", buffer.getvalue())


def test_reject_unsupported_file():
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_transcript("meeting.xlsx", b"some data")


def test_reject_empty_file():
    with pytest.raises(ValueError, match="empty"):
        extract_transcript("meeting.txt", b"")


def test_reject_invalid_txt_encoding():
    with pytest.raises(ValueError, match="Could not read"):
        extract_transcript("meeting.txt", b"\xff\xfe\xfa")
