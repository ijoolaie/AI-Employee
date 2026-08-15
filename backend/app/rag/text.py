from __future__ import annotations
import re


def chunk_text(text: str, *, chunk_size: int = 1200, overlap: int = 200) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    chunks=[]; start=0
    while start < len(text):
        end=min(len(text), start+chunk_size)
        if end < len(text):
            boundary=text.rfind(" ", start, end)
            if boundary > start + chunk_size//2: end=boundary
        piece=text[start:end].strip()
        if piece: chunks.append(piece)
        if end >= len(text): break
        start=max(end-overlap, start+1)
    return chunks
