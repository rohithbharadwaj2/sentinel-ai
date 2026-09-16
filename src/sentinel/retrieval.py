from __future__ import annotations

import re

from sentinel.models import Evidence


_TOKEN = re.compile(r"[a-zA-Z0-9_./:-]+")


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN.findall(text) if len(token) > 2}


class EvidenceStore:
    """Small deterministic retrieval layer used before vector search is introduced."""

    def __init__(self) -> None:
        self._items: dict[str, Evidence] = {}

    def add(self, evidence: Evidence) -> Evidence:
        self._items[evidence.id] = evidence
        return evidence

    def add_many(self, items: list[Evidence]) -> list[Evidence]:
        for item in items:
            self.add(item)
        return items

    def get(self, evidence_id: str) -> Evidence | None:
        return self._items.get(evidence_id)

    def all(self) -> list[Evidence]:
        return list(self._items.values())

    def search(self, query: str, limit: int = 5) -> list[Evidence]:
        query_tokens = _tokens(query)
        if not query_tokens:
            return []

        scored: list[tuple[float, Evidence]] = []
        for item in self._items.values():
            item_tokens = _tokens(f"{item.source} {item.content}")
            overlap = query_tokens & item_tokens
            if not overlap:
                continue
            score = len(overlap) / len(query_tokens)
            scored.append((score, item))

        scored.sort(key=lambda pair: (-pair[0], pair[1].id))
        return [item for _, item in scored[:limit]]
