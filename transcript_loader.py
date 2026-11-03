import logging
from io import BytesIO

import logging_config
from docx import Document
from pypdf import PdfReader

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}


def extract_transcript(
    filename: str,
    file_bytes: bytes,
) -> str:
    """Extract text from a TXT, PDF, or DOCX transcript."""

    if not filename or not file_bytes:
        raise ValueError("The uploaded file is empty.")

    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file type. Upload a TXT, PDF, or DOCX file.")

    logger.info("Transcript file processing started | Type: %s", extension)

    try:
        if extension == ".txt":
            text = file_bytes.decode("utf-8-sig")

        elif extension == ".pdf":
            reader = PdfReader(BytesIO(file_bytes))

            if reader.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported.")

            text = "\n".join(page.extract_text() or "" for page in reader.pages)

        else:
            document = Document(BytesIO(file_bytes))

            paragraphs = [
                paragraph.text
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            ]

            text = "\n".join(paragraphs)

    except UnicodeDecodeError as exc:
        logger.warning("Transcript file has invalid UTF-8 encoding")

        raise ValueError(
            "Could not read the uploaded file. " "Please save it using UTF-8 encoding."
        ) from exc

    except ValueError:
        logger.warning("Transcript file could not be processed")
        raise

    except Exception as exc:
        logger.exception(
            "Unexpected transcript extraction failure | Type: %s",
            extension,
        )

        raise ValueError(f"Could not read the uploaded {extension} file.") from exc

    text = text.strip()

    if not text:
        logger.warning(
            "No readable text found in uploaded file | Type: %s",
            extension,
        )

        raise ValueError(
            "No readable text was found. "
            "The file may be empty or contain scanned pages."
        )

    logger.info(
        "Transcript extraction completed successfully | Characters: %d",
        len(text),
    )

    return text
