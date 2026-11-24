from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.logging import logger
from app.services.document_parser import (
    DocumentExtractionResult,
    DocumentParser,
    DocumentParserError,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/extract", response_model=DocumentExtractionResult)
async def extract_document(file: UploadFile | None = File(None), pasted_text: str | None = Form(None)):
    """
    Extracts text and page structure from an uploaded PDF, TXT file, or direct pasted text.
    Validates file sizes, content types, and page counts.
    """
    if file:
        filename = file.filename or "uploaded_file"
        file_bytes = await file.read()
        file_size = len(file_bytes)

        try:
            ext = DocumentParser.validate_file_metadata(filename, file_size)
            if ext == ".pdf":
                return DocumentParser.parse_pdf_bytes(file_bytes, filename=filename)
            elif ext == ".txt":
                return DocumentParser.parse_txt_bytes(file_bytes, filename=filename)
            elif ext in {".pptx", ".ppt"}:
                return DocumentParser.parse_pptx_bytes(file_bytes, filename=filename)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported format '{ext}'.")
        except DocumentParserError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error during document extraction: {type(e).__name__}")
            raise HTTPException(status_code=500, detail="Failed to parse document content.")

    elif pasted_text and pasted_text.strip():
        try:
            return DocumentParser.parse_pasted_text(pasted_text)
        except DocumentParserError as e:
            raise HTTPException(status_code=400, detail=str(e))

    raise HTTPException(status_code=400, detail="Either a valid file or pasted text must be provided.")
