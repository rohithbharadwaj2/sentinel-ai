from sentinel.benchmark import benchmark_fixture, evaluate
from sentinel.chunking import chunk_evidence
from sentinel.hybrid_retrieval import BM25Retriever, HybridRetriever
from sentinel.models import Evidence, EvidenceKind


def test_chunking_preserves_evidence_provenance() -> None:
    evidence = Evidence(id="ev_test", kind=EvidenceKind.DOCUMENT, source="runbook", content="alpha " * 200)
    chunks = chunk_evidence(evidence, chunk_size=120, overlap=20)
    assert len(chunks) > 1
    assert all(chunk.evidence_id == "ev_test" for chunk in chunks)
    assert len({chunk.id for chunk in chunks}) == len(chunks)


def test_hybrid_retrieval_finds_database_pool_evidence() -> None:
    evidence, _ = benchmark_fixture()
    hits = HybridRetriever(evidence).search("checkout database connection capacity", limit=3)
    ids = {hit.chunk.evidence_id for hit in hits}
    assert "ev_db_pool" in ids or "ev_pool_deploy" in ids


def test_benchmark_metrics_are_bounded() -> None:
    evidence, cases = benchmark_fixture()
    chunks = [chunk for item in evidence for chunk in chunk_evidence(item)]
    metrics = evaluate(BM25Retriever(chunks).search, cases, k=5)
    assert 0 <= metrics["recall@5"] <= 1
    assert 0 <= metrics["mrr"] <= 1
    assert metrics["mean_latency_ms"] >= 0
