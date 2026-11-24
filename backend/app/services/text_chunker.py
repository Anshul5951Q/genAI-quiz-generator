from pydantic import BaseModel

from app.services.document_parser import PageContent


class TextChunk(BaseModel):
    chunk_index: int
    text: str
    page_number: int | None = None
    char_count: int
    token_estimate: int


class TextChunker:
    """Splits document pages into manageable semantic chunks preserving page metadata."""

    @staticmethod
    def chunk_document(
        pages: list[PageContent], max_chunk_chars: int = 2500, overlap_chars: int = 300
    ) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        chunk_idx = 0

        for page in pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            # If page text fits in a chunk, keep it intact
            if len(page_text) <= max_chunk_chars:
                chunks.append(
                    TextChunk(
                        chunk_index=chunk_idx,
                        text=page_text,
                        page_number=page.page_number,
                        char_count=len(page_text),
                        token_estimate=len(page_text) // 4,
                    )
                )
                chunk_idx += 1
                continue

            # If page text is large, split into overlapping paragraph/sentence segments
            paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
            current_segment: list[str] = []
            current_len = 0

            for para in paragraphs:
                if current_len + len(para) > max_chunk_chars and current_segment:
                    combined_text = "\n\n".join(current_segment)
                    chunks.append(
                        TextChunk(
                            chunk_index=chunk_idx,
                            text=combined_text,
                            page_number=page.page_number,
                            char_count=len(combined_text),
                            token_estimate=len(combined_text) // 4,
                        )
                    )
                    chunk_idx += 1

                    # Retain last element for overlap if possible
                    if len(current_segment) > 1 and len(current_segment[-1]) < overlap_chars:
                        current_segment = [current_segment[-1], para]
                        current_len = len(current_segment[0]) + len(para)
                    else:
                        current_segment = [para]
                        current_len = len(para)
                else:
                    current_segment.append(para)
                    current_len += len(para)

            if current_segment:
                combined_text = "\n\n".join(current_segment)
                chunks.append(
                    TextChunk(
                        chunk_index=chunk_idx,
                        text=combined_text,
                        page_number=page.page_number,
                        char_count=len(combined_text),
                        token_estimate=len(combined_text) // 4,
                    )
                )
                chunk_idx += 1

        if not chunks and pages:
            # Fallback for short content
            combined = "\n\n".join(p.text for p in pages if p.text)
            chunks.append(
                TextChunk(
                    chunk_index=0,
                    text=combined,
                    page_number=pages[0].page_number if pages else 1,
                    char_count=len(combined),
                    token_estimate=len(combined) // 4,
                )
            )

        return chunks
