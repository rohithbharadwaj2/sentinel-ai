# Sentinel Architecture

## Objective

Sentinel turns heterogeneous incident artifacts into an evidence-grounded investigation. The architecture deliberately separates **evidence acquisition**, **retrieval**, **analysis**, **diagnosis**, and **mutation/validation** so that future LLM components do not become an opaque agent loop.

## Core contracts

Every evidence artifact has a stable ID, kind, source, content, metadata, and timestamp. Every `Finding` must carry one or more evidence IDs when it makes a supported claim. `Diagnosis` aggregates those IDs so the UI/API can expose the provenance behind a conclusion.

## v0.1 execution path

1. Evidence enters an `EvidenceStore`.
2. `TriageAgent` retrieves incident-relevant artifacts.
3. `LogAgent` detects operational failure signals.
4. `CodeAgent` looks for resource/configuration controls in code or deployment evidence.
5. `RetrievalAgent` supplies additional incident-context matches.
6. `IncidentOrchestrator` merges findings while retaining evidence IDs.
7. `RemediationAgent` proposes human-approved next actions.

The v0.1 agents are deterministic on purpose. They create an executable baseline against which later LLM and vector-retrieval versions can be measured.

## Planned production architecture

```text
                    ┌───────────────────────────────┐
                    │ Incident API / Web Console    │
                    └───────────────┬───────────────┘
                                    │
              ┌─────────────────────▼─────────────────────┐
              │            Incident Orchestrator          │
              └──────┬────────┬────────┬────────┬─────────┘
                     │        │        │        │
                 Triage     Logs     Code    Metrics/Trace
                     │        │        │        │
                     └────────┴────┬───┴────────┘
                                  │
                       ┌──────────▼──────────┐
                       │ Hybrid Retrieval    │
                       │ BM25 + embeddings   │
                       └──────────┬──────────┘
                                  │
        ┌──────────────┬──────────┼──────────┬──────────────┐
        │              │          │          │              │
      Logs          GitHub      Docs       OTel        Images/UI
        │              │          │          │              │
        └──────────────┴──────────┼──────────┴──────────────┘
                                  │
                         Evidence / citations
                                  │
                         ┌────────▼────────┐
                         │ Diagnosis      │
                         └────────┬────────┘
                                  │
                         Remediation Agent
                                  │
                         candidate patch
                                  │
                         ┌────────▼────────┐
                         │ Docker sandbox │
                         │ tests / eval   │
                         └────────┬────────┘
                                  │
                           human approval
                                  │
                            GitHub PR
```

## Evaluation plan

Sentinel will not use a single vague "accuracy" number. Planned measurements include:

- retrieval recall@k on incident evidence;
- citation precision and unsupported-claim rate;
- root-cause top-k accuracy on labeled synthetic incidents;
- remediation test-pass rate;
- regression rate after candidate patches;
- end-to-end latency and token/API cost;
- abstention quality when evidence is insufficient.

A synthetic incident benchmark will be added before claims about diagnosis quality are made.

## Safety boundary

Analysis is read-only. Proposed code changes must later pass sandbox execution and tests. Repository mutation and production actions remain explicit human-approval operations. This boundary is part of the architecture, not a prompt instruction.
