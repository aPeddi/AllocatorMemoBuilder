"""Provenance helpers: content hashing + audit-map assembly."""
from __future__ import annotations

import hashlib
from typing import Iterable


def content_hash(values: Iterable[float], digits: int = 8) -> str:
    """Stable short hash of a numeric series (order-sensitive)."""
    rounded = ",".join(f"{float(v):.{digits}f}" for v in values)
    return hashlib.sha256(rounded.encode()).hexdigest()[:12]


def build_audit_map(memo) -> dict:
    """Flatten every claim in the memo into a sentence -> sources map."""
    entries = []
    for section in memo.sections:
        for c in section.claims:
            entries.append(
                {
                    "text": c.text,
                    "metric": c.metric,
                    "fund_id": c.fund_id,
                    "value": c.value,
                    "sources": c.source_refs,
                    "verified": c.verified,
                }
            )
    verified = sum(1 for e in entries if e["verified"])
    return {
        "claims": entries,
        "claim_count": len(entries),
        "verified_count": verified,
        "unverified_count": len(entries) - verified,
    }
