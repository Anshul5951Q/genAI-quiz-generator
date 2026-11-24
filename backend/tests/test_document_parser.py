import pytest

try:
    import fitz
except ImportError:
    fitz = None

if fitz is None:
    pytest.skip("PyMuPDF (fitz) is not installed; skipping PDF parsing tests", allow_module_level=True)

from app.services.document_parser import DocumentParser, DocumentParserError


def test_txt_parsing_valid():
    text_content = "This is a comprehensive study material on distributed systems and vector clocks."
    result = DocumentParser.parse_txt_bytes(text_content.encode("utf-8"), filename="distributed.txt")
    assert result.source_type == "txt"
    assert result.filename == "distributed.txt"
    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert "distributed systems" in result.full_text


def test_txt_parsing_empty():
    with pytest.raises(DocumentParserError, match="TXT file is empty"):
        DocumentParser.parse_txt_bytes(b"", filename="empty.txt")


def test_pasted_text_limits():
    # Too short
    with pytest.raises(DocumentParserError, match="too short"):
        DocumentParser.parse_pasted_text("short")

    # Valid
    valid_text = "This is a valid piece of study material with sufficient character count for processing."
    result = DocumentParser.parse_pasted_text(valid_text)
    assert result.source_type == "pasted"
    assert result.total_characters == len(valid_text)


def test_pdf_parsing_with_pages():
    # Create an in-memory PDF using PyMuPDF (fitz)
    doc = fitz.open()
    # Page 1
    p1 = doc.new_page()
    p1.insert_text((50, 50), "Page 1: Fundamental principles of computer networks and packet switching.")
    # Page 2
    p2 = doc.new_page()
    p2.insert_text((50, 50), "Page 2: Cryptographic protocols such as TLS and secure handshakes.")

    pdf_bytes = doc.tobytes()
    doc.close()

    result = DocumentParser.parse_pdf_bytes(pdf_bytes, filename="test_network.pdf")
    assert result.source_type == "pdf"
    assert len(result.pages) == 2
    assert result.pages[0].page_number == 1
    assert "packet switching" in result.pages[0].text
    assert result.pages[1].page_number == 2
    assert "Cryptographic protocols" in result.pages[1].text


def test_pdf_parsing_empty_or_image_only():
    # Empty page PDF
    doc = fitz.open()
    doc.new_page()  # blank page without text
    pdf_bytes = doc.tobytes()
    doc.close()

    with pytest.raises(DocumentParserError, match="No usable text found in this PDF"):
        DocumentParser.parse_pdf_bytes(pdf_bytes, filename="blank.pdf")


def test_unsupported_file_extension():
    with pytest.raises(DocumentParserError, match="Unsupported file format"):
        DocumentParser.validate_file_metadata("malicious.exe", 1024)
