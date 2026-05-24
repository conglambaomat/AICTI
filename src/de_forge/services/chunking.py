from __future__ import annotations


def chunk_text(text: str, *, chunk_size: int = 400) -> list[dict[str, int | str]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")

    chunks: list[dict[str, int | str]] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append({"text": text[start:end], "start": start, "end": end})
        start = end

    if not chunks:
        chunks.append({"text": "", "start": 0, "end": 0})
    return chunks
