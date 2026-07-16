from __future__ import annotations

import base64
import io
import logging
import os
from typing import TYPE_CHECKING, Any

from dotenv import load_dotenv

if TYPE_CHECKING:
    from openai import OpenAI

try:
    from openai import OpenAI as OpenAIRuntime, OpenAIError
except ImportError:  # pragma: no cover - handled at runtime
    OpenAIRuntime = None
    OpenAIError = Exception

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - handled at runtime
    PdfReader = None

try:
    from docx import Document
except ImportError:  # pragma: no cover - handled at runtime
    Document = None


load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = 0.2
MAX_SUMMARY_CHARACTERS = 2000

TEXT_EXTENSIONS = {"txt"}
PDF_EXTENSIONS = {"pdf"}
DOCX_EXTENSIONS = {"docx"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}

IMAGE_DESCRIPTION_SYSTEM_PROMPT = (
    "You describe screenshots attached to customer support tickets. Provide a concise, "
    "factual description only. Do not classify, prioritize, summarize intent, or route "
    "the ticket - only describe what is visibly in the image."
)
IMAGE_DESCRIPTION_USER_PROMPT = (
    "Describe this screenshot in 2-3 sentences. Note any visible error messages, "
    "dialog boxes, or UI details that would help a support agent understand the issue."
)


def _build_openai_client() -> OpenAI:
    """Build an OpenAI client using the same credentials/configuration as the rest of the app."""
    if OpenAIRuntime is None:
        raise RuntimeError(
            "The 'openai' package is required to describe image attachments. Install it from requirements.txt."
        )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured. Add it to your environment or .env file.")

    return OpenAIRuntime(api_key=api_key)


def _get_filename(uploaded_file: Any) -> str:
    """Return a safe display filename for an uploaded attachment, defaulting when unavailable."""
    return str(getattr(uploaded_file, "name", "") or "attachment")


def _get_file_extension(filename: str) -> str:
    """Return the lowercase file extension (without the dot), or an empty string if there is none."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _read_file_bytes(uploaded_file: Any) -> bytes:
    """Read the raw bytes from an uploaded file-like object without disturbing its read position.

    Prefers `.getvalue()` (used by Streamlit's UploadedFile, non-destructive) and falls back to
    `.read()` with a position restore for plain file-like objects, so the caller can still reuse
    the same object afterward.
    """
    if hasattr(uploaded_file, "getvalue"):
        return uploaded_file.getvalue()

    if hasattr(uploaded_file, "read"):
        position = uploaded_file.tell() if hasattr(uploaded_file, "tell") else None
        data = uploaded_file.read()
        if position is not None and hasattr(uploaded_file, "seek"):
            uploaded_file.seek(position)
        return data

    raise TypeError("Uploaded attachment does not expose readable bytes (.getvalue() or .read()).")


def _truncate_text(text: str, max_length: int = MAX_SUMMARY_CHARACTERS) -> str:
    """Cap extracted text to a bounded length so it stays safe to embed in downstream AI prompts."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "\n... [content truncated]"


def _extract_text_from_txt(file_bytes: bytes) -> str:
    """Decode a plain-text attachment, tolerating encodings other than UTF-8."""
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("utf-8", errors="replace")


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF attachment, page by page."""
    if PdfReader is None:
        raise RuntimeError("The 'pypdf' package is required to read PDF attachments.")

    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages_text)


def _extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX attachment, paragraph by paragraph."""
    if Document is None:
        raise RuntimeError("The 'python-docx' package is required to read DOCX attachments.")

    document = Document(io.BytesIO(file_bytes))
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs)


def _describe_image_with_ai(file_bytes: bytes, extension: str) -> str:
    """Ask the configured OpenAI model for a concise, objective description of a screenshot.

    This only describes what is visible - it does not classify, prioritize, or route the ticket.
    """
    client = _build_openai_client()
    mime_type = "image/png" if extension == "png" else "image/jpeg"
    encoded_image = base64.b64encode(file_bytes).decode("utf-8")

    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            temperature=DEFAULT_TEMPERATURE,
            messages=[
                {"role": "system", "content": IMAGE_DESCRIPTION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": IMAGE_DESCRIPTION_USER_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"},
                        },
                    ],
                },
            ],
        )
    except OpenAIError as exc:
        raise RuntimeError("The AI service could not describe this image.") from exc

    description = response.choices[0].message.content
    if not description or not description.strip():
        raise ValueError("OpenAI returned an empty image description.")

    return description.strip()


def extract_attachment_content(uploaded_file: Any) -> str:
    """Extract and summarize the content of a single support-ticket attachment.

    Supports TXT, PDF, and DOCX (text extraction) and PNG, JPG, and JPEG (an AI-generated
    description of the screenshot). Returns an empty string when no attachment is provided.
    Unsupported file types and unreadable/corrupted files are handled gracefully - this
    function never raises, always returning a clean, human-readable summary string.
    """
    if uploaded_file is None:
        return ""

    filename = _get_filename(uploaded_file)
    extension = _get_file_extension(filename)

    try:
        file_bytes = _read_file_bytes(uploaded_file)
    except Exception:
        logger.exception("Unable to read attachment '%s'.", filename)
        return f"[Attachment: {filename}]\nUnable to read this attachment."

    if not file_bytes:
        return f"[Attachment: {filename}]\nThe attachment is empty."

    try:
        if extension in TEXT_EXTENSIONS:
            content = _extract_text_from_txt(file_bytes)
        elif extension in PDF_EXTENSIONS:
            content = _extract_text_from_pdf(file_bytes)
        elif extension in DOCX_EXTENSIONS:
            content = _extract_text_from_docx(file_bytes)
        elif extension in IMAGE_EXTENSIONS:
            content = _describe_image_with_ai(file_bytes, extension)
        else:
            return (
                f"[Attachment: {filename}]\n"
                f"Unsupported file type '.{extension or 'unknown'}'. "
                "Supported types: TXT, PDF, DOCX, PNG, JPG, JPEG."
            )
    except Exception:  # pragma: no cover - safety net, must never crash the caller
        logger.exception("Failed to process attachment '%s'.", filename)
        return f"[Attachment: {filename}]\nUnable to process this attachment."

    if not content.strip():
        return f"[Attachment: {filename}]\nNo readable content was found in this attachment."

    return f"[Attachment: {filename}]\n{_truncate_text(content.strip())}"
