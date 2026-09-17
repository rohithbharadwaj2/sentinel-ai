from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from sentinel.chunking import EvidenceChunk, chunk_evidence
from sentinel.models import Evidence

_TOKEN = re.compile(r"[a-zA-Z0-9_./:-]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN.findall(text) if len(token) > 2]


@dataclass(frozen=True)
class SearchHit:
    chunk: EvidenceChunk
    score: float


class BM25Retriever:
    """Dependency-free BM25 baseline over evidence chunks."""

    def __init__(self, chunks: list[EvidenceChunk], k1: float = 1.5, b: float = 0.75) -> None:
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.docs = [tokenize(chunk.text) for chunk in chunks]
        self.avgdl = sum(map(len, self.docs)) / max(len(self.docs), 1)
        self.df: Counter[str] = Counter()
        for doc in self.docs:
            self.df.update(set(doc))

    def search(self, query: str, limit: int = 5) -> list[SearchHit]:
        query_terms = tokenize(query)
        n_docs = len(self.docs)
        hits: list[SearchHit] = []
        for chunk, doc in zip(self.chunks, self.docs):
            frequencies = Counter(doc)
            score = 0.0
            for term in query_terms:
                freq = frequencies[term]
                if not freq:
                    continue
                df = self.df[term]
                idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
                denom = freq + self.k1 * (1 - self.b + self.b * len(doc) / max(self.avgdl, 1))
                score += idf * (freq * (self.k1 + 1)) / denom
            if score > 0:
                hits.append(SearchHit(chunk=chunk, score=score))
        hits.sort(key=lambda hit: (-hit.score, hit.chunk.id))
        return hits[:limit]


class SemanticHashRetriever:
    """Offline semantic-style baseline using hashed token/subword vectors.

    This keeps CI deterministic and dependency-light. A learned embedding adapter will
    replace/augment it in the next step without changing the hybrid retrieval contract.
    """

    def __init__(self, chunks: list[EvidenceChunk], dimensions: int = 256) -> None:
        self.chunks = chunks
        self.dimensions = dimensions
        self.vectors = [self._embed(chunk.text) for chunk in chunks]

    def _embed(self, text: str) -> dict[int, float]:
        features: Counter[int] = Counter()
        for token in tokenize(text):
            pieces = {token}
            if len(token) >= 5:
                pieces.update(token[i:i + 3] for i in range(len(token) - 2))
            for piece in pieces:
                features[hash(piece) % self.dimensions] += 1
        norm = math.sqrt(sum(value * value for value in features.values())) or 1.0
        return {key: value / norm for key, value in features.items()}

    @staticmethod
    def _cosine(left: dict[int, float], right: dict[int, float]) -> float:
        if len(left) > len(right):
            left, right = right, left
        return sum(value * right.get(key, 0.0) for key, value in left.items())

    def search(self, query: str, limit: int = 5) -> list[SearchHit]:
        query_vector = self._embed(query)
        hits = [SearchHit(chunk=chunk, score=self._cosine(query_vector, vector))
                for chunk, vector in zip(self.chunks, self.vectors)]
        hits = [hit for hit in hits if hit.score > 0]
        hits.sort(key=lambda hit: (-hit.score, hit.chunk.id))
        return hits[:limit]


class HybridRetriever:
    def __init__(self, evidence: list[Evidence]) -> None:
        self.chunks = [chunk for item in evidence for chunk in chunk_evidence(item)]
        self.lexical = BM25Retriever(self.chunks)
        self.semantic = SemanticHashRetriever(self.chunks)

    def search(self, query: str, limit: int = 5) -> list[SearchHit]:
        depth = max(limit * 3, 10)
        rankings = [self.lexical.search(query, depth), self.semantic.search(query, depth)]
        fused: dict[str, float] = {}
        by_id: dict[str, EvidenceChunk] = {}
        for ranking in rankings:
            for rank, hit in enumerate(ranking, start=1):
                by_id[hit.chunk.id] = hit.chunk
                fused[hit.chunk.id] = fused.get(hit.chunk.id, 0.0) + 1.0 / (60 + rank)
        ordered = sorted(fused.items(), key=lambda item: (-item[1], item[0]))[:limit]
        return [SearchHit(chunk=by_id[chunk_id], score=score) for chunk_id, score in ordered]
