from __future__ import annotations

import hashlib
from dataclasses import dataclass

CHUNK_SIZE_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 64
BM25_K1 = 1.5
BM25_B = 0.75
RRF_K = 60


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    start_offset: int
    end_offset: int
    token_count: int
    chunk_index: int


@dataclass(frozen=True)
class Index:
    report_id: str
    chunks: list[Chunk]


@dataclass(frozen=True)
class ScoredChunk:
    chunk_id: str
    text: str
    score_sparse: float
    score_dense: float
    score_fused: float


class RetrievalService:
    def __init__(self) -> None:
        self._indexes: dict[str, Index] = {}

    def index_chunks(self, report_id: str, report_text: str) -> Index:
        chunks = self._chunk_report(report_text)
        index = Index(report_id=report_id, chunks=chunks)
        self._indexes[report_id] = index
        return index

    def retrieve(self, query: str, report_id: str, k: int = 10) -> list[ScoredChunk]:
        if report_id not in self._indexes:
            raise ValueError(f"Index missing for report_id={report_id}")

        index = self._indexes[report_id]
        sparse_ranked = self._sparse_rank(query, index.chunks)
        dense_ranked = self._dense_rank(query, index.chunks)
        fused = self._fuse_scores(sparse_ranked, dense_ranked)
        reranked = self._rerank_stub(query, fused)
        return reranked[:k]

    def _chunk_report(self, report_text: str) -> list[Chunk]:
        tokens = report_text.split()
        if not tokens:
            return []

        chunks: list[Chunk] = []
        step = CHUNK_SIZE_TOKENS - CHUNK_OVERLAP_TOKENS
        start = 0
        chunk_index = 0

        while start < len(tokens):
            end = min(start + CHUNK_SIZE_TOKENS, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = " ".join(chunk_tokens)
            chunk_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()[:16]
            chunk_id = f"ch_{chunk_hash}"

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    start_offset=start,
                    end_offset=end,
                    token_count=len(chunk_tokens),
                    chunk_index=chunk_index,
                )
            )

            if end == len(tokens):
                break
            start += step
            chunk_index += 1

        return chunks

    def _sparse_rank(self, query: str, chunks: list[Chunk]) -> list[tuple[Chunk, float]]:
        query_terms = set(query.lower().split())
        ranked: list[tuple[Chunk, float]] = []
        for chunk in chunks:
            chunk_terms = chunk.text.lower().split()
            overlap = sum(1 for term in chunk_terms if term in query_terms)
            score = overlap * BM25_K1 / (BM25_B + 1)
            ranked.append((chunk, float(score)))
        ranked.sort(key=lambda item: (-item[1], item[0].chunk_id))
        return ranked

    def _dense_rank(self, query: str, chunks: list[Chunk]) -> list[tuple[Chunk, float]]:
        query_terms = set(query.lower().split())
        ranked: list[tuple[Chunk, float]] = []
        for chunk in chunks:
            chunk_terms = set(chunk.text.lower().split())
            union_size = len(query_terms | chunk_terms) or 1
            intersection_size = len(query_terms & chunk_terms)
            score = intersection_size / union_size
            ranked.append((chunk, float(score)))
        ranked.sort(key=lambda item: (-item[1], item[0].chunk_id))
        return ranked

    def _fuse_scores(
        self,
        sparse_ranked: list[tuple[Chunk, float]],
        dense_ranked: list[tuple[Chunk, float]],
    ) -> list[ScoredChunk]:
        sparse_lookup = {chunk.chunk_id: score for chunk, score in sparse_ranked}
        dense_lookup = {chunk.chunk_id: score for chunk, score in dense_ranked}
        sparse_ranks = {
            chunk.chunk_id: rank for rank, (chunk, _) in enumerate(sparse_ranked, start=1)
        }
        dense_ranks = {
            chunk.chunk_id: rank for rank, (chunk, _) in enumerate(dense_ranked, start=1)
        }
        chunk_lookup = {chunk.chunk_id: chunk for chunk, _ in sparse_ranked}

        fused: list[ScoredChunk] = []
        for chunk_id, chunk in chunk_lookup.items():
            rrf_score = (1 / (RRF_K + sparse_ranks[chunk_id])) + (
                1 / (RRF_K + dense_ranks[chunk_id])
            )
            fused.append(
                ScoredChunk(
                    chunk_id=chunk_id,
                    text=chunk.text,
                    score_sparse=sparse_lookup.get(chunk_id, 0.0),
                    score_dense=dense_lookup.get(chunk_id, 0.0),
                    score_fused=rrf_score,
                )
            )

        fused.sort(key=lambda item: (-item.score_fused, item.chunk_id))
        return fused

    def _rerank_stub(self, query: str, candidates: list[ScoredChunk]) -> list[ScoredChunk]:
        _ = query
        return sorted(candidates, key=lambda item: (-item.score_fused, item.chunk_id))
