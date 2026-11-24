"""
Resume parsing service: extracts text from PDF and DOCX resume files.
Reuses existing DocumentParser infrastructure where possible.
"""
import io
import os

from app.core.config import settings
from app.core.logging import logger
from app.services.document_parser import DocumentParser, DocumentParserError


class ResumeParserError(Exception):
    """User-safe resume parsing error."""


class ResumeParser:
    """
    Parses resume files (PDF, DOCX) into clean text for AI extraction.
    Extends the existing document parser with DOCX support.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

    @staticmethod
    def validate_resume_file(filename: str, file_size: int) -> str:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ResumeParser.SUPPORTED_EXTENSIONS:
            raise ResumeParserError(
                f"Unsupported resume format '{ext}'. Please upload a PDF or DOCX file."
            )
        max_bytes = settings.RESUME_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise ResumeParserError(
                f"File size exceeds the {settings.RESUME_UPLOAD_SIZE_MB}MB limit for resumes."
            )
        if file_size == 0:
            raise ResumeParserError("Uploaded file is empty.")
        return ext

    @staticmethod
    def parse_pdf_resume(pdf_bytes: bytes, filename: str = "resume.pdf") -> str:
        """Extract text from a PDF resume."""
        try:
            result = DocumentParser.parse_pdf_bytes(pdf_bytes, filename)
            return result.full_text
        except DocumentParserError as e:
            raise ResumeParserError(str(e))
        except Exception as e:
            logger.error(f"PDF resume parsing failed: {type(e).__name__}")
            raise ResumeParserError("Failed to extract text from PDF resume. Ensure it is a text-based PDF.")

    @staticmethod
    def parse_docx_resume(docx_bytes: bytes, filename: str = "resume.docx") -> str:
        """Extract text from a DOCX resume."""
        try:
            from docx import Document
            doc = Document(io.BytesIO(docx_bytes))
            paragraphs = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)
            # Also extract table content
            for table in doc.tables:
                for row in table.rows:
                    row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_texts:
                        paragraphs.append(" | ".join(row_texts))
            full_text = "\n".join(paragraphs).strip()
            if not full_text or len(full_text) < 50:
                raise ResumeParserError(
                    "No usable text found in this DOCX file. The document may be empty or image-only."
                )
            return full_text
        except ResumeParserError:
            raise
        except Exception as e:
            logger.error(f"DOCX resume parsing failed: {type(e).__name__}")
            raise ResumeParserError("Failed to extract text from DOCX resume. Ensure it is a valid Word document.")

    @classmethod
    def parse_resume(cls, file_bytes: bytes, filename: str) -> str:
        """Route to correct parser based on file extension."""
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            return cls.parse_pdf_resume(file_bytes, filename)
        elif ext == ".docx":
            return cls.parse_docx_resume(file_bytes, filename)
        else:
            raise ResumeParserError(f"Unsupported format: {ext}")

    @staticmethod
    def save_resume_file(file_bytes: bytes, filename: str, resume_id: str) -> str:
        """Save uploaded resume to disk and return the file path."""
        upload_dir = os.path.join(settings.UPLOAD_DIR, "resumes")
        os.makedirs(upload_dir, exist_ok=True)
        # Sanitize filename
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in filename)
        file_path = os.path.join(upload_dir, f"{resume_id}_{safe_name}")
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        return file_path
