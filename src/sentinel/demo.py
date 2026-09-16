from __future__ import annotations

import json

from sentinel.models import Evidence, EvidenceKind, Incident
from sentinel.orchestrator import IncidentOrchestrator
from sentinel.retrieval import EvidenceStore


def build_demo() -> tuple[Incident, EvidenceStore]:
    incident = Incident(
        id="inc_checkout_latency",
        title="Checkout API latency spike after deployment",
        description="Checkout p95 latency increased shortly after release 2026.09.16.",
        service="checkout-api",
        severity="SEV-2",
        symptoms=["p95 latency", "database timeout", "after deployment"],
    )
    store = EvidenceStore()
    store.add_many([
        Evidence(
            id="ev_log_pool_timeout",
            kind=EvidenceKind.LOG,
            source="checkout-api/app.log",
            content="ERROR database connection pool exhausted; acquire timeout after 2000ms",
        ),
        Evidence(
            id="ev_deploy_pool_change",
            kind=EvidenceKind.DEPLOYMENT,
            source="release-2026.09.16",
            content="Changed DB_POOL_SIZE from 40 to 8 for checkout-api during deployment.",
        ),
        Evidence(
            id="ev_runbook",
            kind=EvidenceKind.DOCUMENT,
            source="runbooks/checkout-latency.md",
            content="For checkout latency, inspect database pool saturation and downstream timeouts.",
        ),
    ])
    return incident, store


def main() -> None:
    incident, store = build_demo()
    result = IncidentOrchestrator(store).analyze(incident)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
