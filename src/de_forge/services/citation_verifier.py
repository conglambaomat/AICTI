from __future__ import annotations


def verify_citation(text: str, quote: str, start_offset: int, end_offset: int) -> bool:
    if start_offset < 0 or end_offset < 0 or end_offset < start_offset or end_offset > len(text):
        raise ValueError("invalid citation offsets")
    return text[start_offset:end_offset] == quote
