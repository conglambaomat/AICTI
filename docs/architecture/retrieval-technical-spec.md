# Retrieval Technical Specification (No-OCR)

Date: 2026-05-20
Scope: Hybrid retrieval for text-based TXT/PDF reports

## 1. Purpose
Define exact chunking, indexing, retrieval, fusion, and reranking strategies for evidence-grounded agentic pipeline.

## 2. Chunking Strategy

### Semantic Chunking (Primary)
- Target chunk size: 512 tokens
- Overlap: 64 tokens
- Boundary detection: sentence boundaries preferred
- Preserve paragraph structure where possible

### Implementation
```python
def chunk_report(report_text: str, target_tokens: int = 512, overlap_tokens: int = 64) -> list[Chunk]:
    """
    Returns list of Chunk objects with:
    - chunk_id (deterministic hash)
    - text
    - start_offset (char)
    - end_offset (char)
    - token_count
    - chunk_index
    """
```

### Determinism Requirement
- Same input text must produce identical chunk boundaries and IDs.
- Use deterministic tokenizer (e.g., tiktoken with fixed encoding).

## 3. Indexing

### Sparse Index (BM25)
- Engine: BM25 via `rank_bm25` or equivalent
- Parameters:
  - k1 = 1.5
  - b = 0.75
- Index fields: chunk_text
- Preprocessing: lowercase, remove stopwords (minimal set)

### Dense Index (Embeddings)
- Model: `text-embedding-3-small` (OpenAI) or equivalent
- Dimension: 1536
- Storage: in-memory numpy array for MVP, migrate to pgvector for production
- Normalization: L2 normalize embeddings before storage

### Index Build
```python
def build_index(report_id: str, chunks: list[Chunk]) -> Index:
    """
    1. Build BM25 index from chunk texts
    2. Generate embeddings for all chunks
    3. Store embeddings with chunk_id mapping
    4. Persist index metadata (report_id, chunk_count, index_hash)
    """
```

## 4. Retrieval

### Query Planning
- Input: stage objective + report context
- Output: 1-3 focused queries
- Strategy: behavior-driven terms preferred over tool names

### Dual Retrieval
```python
def retrieve(query: str, report_id: str, k: int = 10) -> list[ScoredChunk]:
    """
    1. Sparse retrieval: BM25 top-k
    2. Dense retrieval: cosine similarity top-k
    3. Return both score sets
    """
```

### Score Normalization
- Sparse scores: min-max normalize to [0, 1]
- Dense scores: already in [-1, 1], shift to [0, 1]

## 5. Fusion

### Reciprocal Rank Fusion (RRF)
```python
def fuse_scores(sparse_results: list, dense_results: list, k: int = 60) -> list[FusedResult]:
    """
    RRF formula:
    score(chunk) = sum(1 / (k + rank_sparse)) + sum(1 / (k + rank_dense))
    
    k = 60 (standard RRF constant)
    """
```

### Fusion Output
- Top-k fused candidates (k=20 for reranking input)
- Each candidate includes: chunk_id, text, score_sparse, score_dense, score_fused

## 6. Reranking

### Reranker Model
- Option A (MVP): LLM-based reranker (lightweight prompt)
- Option B (production): cross-encoder model (e.g., `ms-marco-MiniLM-L-6-v2`)

### LLM Reranker Prompt (MVP)
```text
Given query and candidate chunks, score each chunk 0-1 for relevance.
Query: {query}
Chunks: {chunks}
Return JSON: [{"chunk_id": "...", "score": 0.95}, ...]
```

### Rerank Output
- Top-k reranked (k=5 for agent consumption)
- Final ranking by rerank_score descending

## 7. Caching and Invalidation

### Cache Strategy
- Cache embeddings per chunk_id (immutable after creation)
- Cache retrieval results per (query_hash, report_id, k) for 1 hour
- Invalidate on report update or index rebuild

### Cache Keys
```python
embedding_cache_key = f"emb:{chunk_id}"
retrieval_cache_key = f"retr:{hash(query)}:{report_id}:{k}"
```

## 8. Performance Targets

### Latency (p95)
- Chunking: <= 2s per report
- Indexing: <= 5s per report
- Retrieval (sparse+dense): <= 500ms
- Reranking: <= 1s

### Throughput
- Support 10 concurrent retrieval requests

## 9. Quality Metrics

### Retrieval Quality
- Recall@5: target >= 0.85 (evidence in top-5)
- Recall@10: target >= 0.95
- MRR (Mean Reciprocal Rank): target >= 0.75

### Faithfulness
- Citation accuracy: 100% (hard requirement)
- Provenance completeness: >= 99%

## 10. Error Handling

### Retrieval Failures
- Empty results: return abstain signal to agent
- Timeout: retry once with reduced k
- Index missing: fail-fast with clear error

### Embedding Failures
- API error: retry with backoff (max 3)
- Rate limit: queue and batch
- Persistent failure: fall back to sparse-only retrieval

## 11. Implementation Modules

### Core Service
- `src/de_forge/services/retrieval.py`
  - `index_chunks(report_id)`
  - `retrieve(query, report_id, k)`
  - `rerank(query, candidates)`

### Supporting Utilities
- `src/de_forge/core/chunking.py`
- `src/de_forge/core/embeddings.py`
- `src/de_forge/core/fusion.py`

### Tests
- `tests/integration/services/test_retrieval_service.py`
- `tests/unit/core/test_chunking.py`
- `tests/unit/core/test_fusion.py`

## 12. Migration Path

### Phase 1 (MVP)
- In-memory BM25 + numpy embeddings
- LLM-based reranker
- No persistent cache

### Phase 2 (Production)
- Migrate to pgvector for embeddings
- Add cross-encoder reranker
- Redis cache for retrieval results
- Async batch embedding generation
