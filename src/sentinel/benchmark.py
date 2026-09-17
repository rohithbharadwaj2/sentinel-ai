from __future__ import annotations

import json
from dataclasses import dataclass
from time import perf_counter

from sentinel.hybrid_retrieval import BM25Retriever, HybridRetriever
from sentinel.chunking import chunk_evidence
from sentinel.models import Evidence, EvidenceKind


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    relevant_ids: set[str]


def benchmark_fixture() -> tuple[list[Evidence], list[RetrievalCase]]:
    evidence = [
        Evidence(id="ev_db_pool", kind=EvidenceKind.LOG, source="checkout.log",
                 content="Database connection pool exhausted while checkout requests wait for a connection."),
        Evidence(id="ev_pool_deploy", kind=EvidenceKind.DEPLOYMENT, source="deploy-42",
                 content="Release reduced checkout DB_POOL_SIZE from 40 connections to 8."),
        Evidence(id="ev_cache", kind=EvidenceKind.LOG, source="catalog.log",
                 content="Product catalog cache miss ratio increased after cache eviction."),
        Evidence(id="ev_memory", kind=EvidenceKind.METRIC, source="worker-memory",
                 content="Image worker resident memory climbs continuously until the container is restarted."),
        Evidence(id="ev_oom", kind=EvidenceKind.LOG, source="worker.log",
                 content="Kernel terminated image worker because the process exceeded its memory limit."),
        Evidence(id="ev_auth", kind=EvidenceKind.LOG, source="auth.log",
                 content="Authentication requests fail because signing key identifier is unknown."),
        Evidence(id="ev_key_rotation", kind=EvidenceKind.DEPLOYMENT, source="auth-release",
                 content="JWT signing key was rotated but verifier configuration retained the previous key id."),
        Evidence(id="ev_runbook", kind=EvidenceKind.DOCUMENT, source="runbook.md",
                 content="When database requests stall, inspect connection capacity and pool saturation."),
    ]
    cases = [
        RetrievalCase("checkout requests slow waiting for database connections", {"ev_db_pool", "ev_pool_deploy", "ev_runbook"}),
        RetrievalCase("image worker killed after memory keeps growing", {"ev_memory", "ev_oom"}),
        RetrievalCase("login tokens rejected after credential rotation", {"ev_auth", "ev_key_rotation"}),
    ]
    return evidence, cases


def evaluate(search, cases: list[RetrievalCase], k: int = 5) -> dict[str, float]:
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    latencies: list[float] = []
    for case in cases:
        start = perf_counter()
        hits = search(case.query, k)
        latencies.append((perf_counter() - start) * 1000)
        ids = [hit.chunk.evidence_id for hit in hits]
        retrieved_relevant = len(set(ids) & case.relevant_ids)
        recalls.append(retrieved_relevant / len(case.relevant_ids))
        rank = next((index for index, item in enumerate(ids, 1) if item in case.relevant_ids), None)
        reciprocal_ranks.append(1 / rank if rank else 0.0)
    return {
        f"recall@{k}": round(sum(recalls) / len(recalls), 4),
        "mrr": round(sum(reciprocal_ranks) / len(reciprocal_ranks), 4),
        "mean_latency_ms": round(sum(latencies) / len(latencies), 4),
    }


def main() -> None:
    evidence, cases = benchmark_fixture()
    chunks = [chunk for item in evidence for chunk in chunk_evidence(item)]
    bm25 = BM25Retriever(chunks)
    hybrid = HybridRetriever(evidence)
    results = {
        "bm25": evaluate(bm25.search, cases),
        "hybrid": evaluate(hybrid.search, cases),
        "cases": len(cases),
        "evidence_items": len(evidence),
        "note": "Synthetic development benchmark; not a production-quality claim.",
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
