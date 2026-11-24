import os

from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger


class PageContent(BaseModel):
    page_number: int  # 1-indexed
    text: str
    char_count: int


class DocumentExtractionResult(BaseModel):
    source_type: str  # "pdf", "txt", "pasted", "pptx"
    filename: str | None = None
    total_characters: int
    pages: list[PageContent]
    full_text: str


class DocumentParserError(Exception):
    """Custom exception for user-safe document parsing errors."""


class DocumentParser:
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".pptx", ".ppt"}

    @staticmethod
    def validate_file_metadata(filename: str, file_size: int) -> str:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in DocumentParser.SUPPORTED_EXTENSIONS:
            raise DocumentParserError(
                f"Unsupported file format '{ext}'. Only .pptx, .ppt, .pdf, and .txt files are supported."
            )
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise DocumentParserError(f"File size exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit.")
        if file_size == 0:
            raise DocumentParserError("Uploaded file is empty.")
        return ext

    @staticmethod
    def parse_pptx_bytes(pptx_bytes: bytes, filename: str = "uploaded.pptx") -> DocumentExtractionResult:
        if not pptx_bytes:
            raise DocumentParserError("Presentation file is empty.")

        ext = os.path.splitext(filename)[1].lower()
        if ext == ".ppt" and not pptx_bytes.startswith(b"PK"):
            raise DocumentParserError(
                "Legacy binary PowerPoint (.ppt) format is not directly supported. "
                "Please save or export your presentation as modern PowerPoint (.pptx) or PDF."
            )

        try:
            import io

            from pptx import Presentation

            prs = Presentation(io.BytesIO(pptx_bytes))
        except Exception as e:
            logger.warning(f"Failed to open PowerPoint presentation: {type(e).__name__}")
            raise DocumentParserError("Corrupted or invalid PowerPoint presentation. Unable to read slides.")

        pages: list[PageContent] = []
        total_extracted_text = []

        for slide_idx, slide in enumerate(prs.slides, start=1):
            slide_texts: list[str] = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        text = paragraph.text.strip()
                        if text:
                            slide_texts.append(text)
                elif shape.has_table:
                    for row in shape.table.rows:
                        row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                        if row_texts:
                            slide_texts.append(" | ".join(row_texts))

            # Include notes slide text if present
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes = slide.notes_slide.notes_text_frame.text.strip()
                if notes:
                    slide_texts.append(f"[Notes: {notes}]")

            combined_slide = "\n".join(slide_texts).strip()
            if combined_slide:
                pages.append(PageContent(page_number=slide_idx, text=combined_slide, char_count=len(combined_slide)))
                total_extracted_text.append(f"--- Slide {slide_idx} ---\n" + combined_slide)

        full_text = "\n\n".join(total_extracted_text).strip()

        if not full_text or not pages:
            raise DocumentParserError(
                "No usable text found in this presentation. The slides may contain only images, shapes without text, "
                "or scanned content. Please provide a presentation with text content."
            )

        if len(full_text) > settings.MAX_INPUT_CHARACTERS:
            logger.info(f"PPTX text length ({len(full_text)}) exceeds max input ({settings.MAX_INPUT_CHARACTERS})")

        return DocumentExtractionResult(
            source_type="pptx",
            filename=filename,
            total_characters=len(full_text),
            pages=pages,
            full_text=full_text,
        )

    @staticmethod
    def parse_pdf_bytes(pdf_bytes: bytes, filename: str = "uploaded.pdf") -> DocumentExtractionResult:
        if not pdf_bytes:
            raise DocumentParserError("PDF file is empty.")

        pages: list[PageContent] = []
        total_extracted_text = []

        # 1. Try PyMuPDF (fitz) if installed
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if doc.is_encrypted:
                doc.close()
                raise DocumentParserError("Password-protected PDFs are not supported. Please remove the password.")
            try:
                for page_idx in range(len(doc)):
                    page = doc[page_idx]
                    text = page.get_text("text").strip()
                    if text:
                        pages.append(PageContent(page_number=page_idx + 1, text=text, char_count=len(text)))
                        total_extracted_text.append(text)
            finally:
                doc.close()
        except ImportError:
            # 2. Seamless fallback to pure-Python pypdf (lightweight ~420KB, no C++ binaries)
            try:
                import io
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                if reader.is_encrypted:
                    raise DocumentParserError("Password-protected PDFs are not supported. Please remove the password.")
                for page_idx, page in enumerate(reader.pages):
                    text = (page.extract_text() or "").strip()
                    if text:
                        pages.append(PageContent(page_number=page_idx + 1, text=text, char_count=len(text)))
                        total_extracted_text.append(text)
            except ImportError:
                raise DocumentParserError(
                    "No PDF parsing library available. Please install 'pypdf' or 'pymupdf'."
                )
            except DocumentParserError:
                raise
            except Exception as e:
                logger.warning(f"pypdf extraction failed: {type(e).__name__}")
                raise DocumentParserError("Corrupted or invalid PDF file. Unable to read document.")
        except DocumentParserError:
            raise
        except Exception as e:
            logger.warning(f"Failed to open PDF stream: {type(e).__name__}")
            raise DocumentParserError("Corrupted or invalid PDF file. Unable to read document.")

        full_text = "\n\n".join(total_extracted_text).strip()

        if not full_text:
            raise DocumentParserError(
                "No usable text found in this PDF. The document may be scanned or image-only. "
                "Text-based PDFs or pasted text are required."
            )

        if len(full_text) > settings.MAX_INPUT_CHARACTERS:
            # We preserve pages up to max chars with clear warning
            logger.info(f"PDF text length ({len(full_text)}) exceeds max input ({settings.MAX_INPUT_CHARACTERS})")

        return DocumentExtractionResult(
            source_type="pdf",
            filename=filename,
            total_characters=len(full_text),
            pages=pages,
            full_text=full_text,
        )

    @staticmethod
    def parse_txt_bytes(txt_bytes: bytes, filename: str = "uploaded.txt") -> DocumentExtractionResult:
        if not txt_bytes:
            raise DocumentParserError("TXT file is empty.")

        decoded_text = ""
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                decoded_text = txt_bytes.decode(encoding).strip()
                break
            except UnicodeDecodeError:
                continue

        if not decoded_text:
            raise DocumentParserError("Unable to decode text file. Ensure it is encoded in valid UTF-8 or ASCII.")

        pages = [PageContent(page_number=1, text=decoded_text, char_count=len(decoded_text))]

        return DocumentExtractionResult(
            source_type="txt",
            filename=filename,
            total_characters=len(decoded_text),
            pages=pages,
            full_text=decoded_text,
        )

    @staticmethod
    def parse_pasted_text(text: str) -> DocumentExtractionResult:
        cleaned = text.strip() if text else ""
        if len(cleaned) < 20:
            raise DocumentParserError(
                "Source text is too short. Please provide at least 20 characters of study material."
            )
        if len(cleaned) > settings.MAX_INPUT_CHARACTERS:
            raise DocumentParserError(
                f"Source text exceeds maximum limit of {settings.MAX_INPUT_CHARACTERS} characters. "
                "Please shorten your input."
            )

        pages = [PageContent(page_number=1, text=cleaned, char_count=len(cleaned))]
        return DocumentExtractionResult(
            source_type="pasted",
            filename=None,
            total_characters=len(cleaned),
            pages=pages,
            full_text=cleaned,
        )
