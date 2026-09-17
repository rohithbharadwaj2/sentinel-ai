from __future__ import annotations

from dataclasses import dataclass

from sentinel.models import Evidence


@dataclass(frozen=True)
class EvidenceChunk:
    id: str
    evidence_id: str
    source: str
    text: str
    start: int
    end: int


def chunk_evidence(evidence: Evidence, chunk_size: int = 500, overlap: int = 80) -> list[EvidenceChunk]:
    """Split evidence into overlapping character windows while retaining provenance."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")

    text = evidence.content.strip()
    if not text:
        return []

    chunks: list[EvidenceChunk] = []
    start = 0
    index = 0
    while start < len(text):
        hard_end = min(start + chunk_size, len(text))
        end = hard_end
        if hard_end < len(text):
            boundary = text.rfind(" ", start, hard_end)
            if boundary > start + chunk_size // 2:
                end = boundary
        piece = text[start:end].strip()
        if piece:
            chunks.append(EvidenceChunk(
                id=f"{evidence.id}:chunk:{index}",
                evidence_id=evidence.id,
                source=evidence.source,
                text=piece,
                start=start,
                end=end,
            ))
            index += 1
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks
