"""Typed domain models. Every number that reaches the memo is one of these,
and each carries enough provenance to trace it back to a source row + formula.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# the constraint operators the screener understands — a closed set, so a typo in a
# mandate YAML (op: "=>") is rejected at load time instead of silently never matching.
Op = Literal[">=", "<=", ">", "<", "==", "!=", "in", "not_in"]

# a fund's computed metrics, keyed by the stable METRIC_KEYS names (metrics.py).
Metrics = dict[str, Optional[float]]


class _Model(BaseModel):
    """Immutable value-object base. Frozen so a domain object is constructed once
    and never silently mutated downstream (parse-don't-mutate); attribute writes
    raise instead of corrupting shared state."""

    model_config = ConfigDict(frozen=True)


class Fund(_Model):
    fund_id: str
    name: str
    strategy: str
    aum_mm: Optional[float] = None
    inception: Optional[date] = None
    mgmt_fee_pct: Optional[float] = None
    notes: Optional[str] = None
    # liquidity terms (allocator-grade screening inputs)
    redemption_freq: Optional[str] = None   # Daily | Weekly | Monthly | Quarterly | Annual | Illiquid
    lockup_months: Optional[float] = None
    notice_days: Optional[float] = None
    redemption_days: Optional[float] = None  # derived ordinal: freq -> days-to-liquidity
    source_ref: Optional[str] = None  # e.g. "funds.csv:row=3"


class ReturnPoint(_Model):
    period: date
    value: float


class ReturnSeries(_Model):
    fund_id: str
    frequency: str                 # monthly | quarterly | daily | annual
    periods_per_year: int
    points: list[ReturnPoint]
    source_hash: str               # content hash of the cleaned values

    @property
    def values(self) -> list[float]:
        return [p.value for p in self.points]


class Benchmark(_Model):
    benchmark_id: str
    name: str
    as_of: date
    frequency: str
    periods_per_year: int
    points: list[ReturnPoint]
    source: str
    source_kind: str = "snapshot"          # live | cache | snapshot
    source_name: str = "bundled snapshot"  # e.g. "FRED"
    fetched_at: Optional[datetime] = None

    @property
    def values(self) -> list[float]:
        return [p.value for p in self.points]


class MandateConstraint(_Model):
    field: str                     # a Fund attribute or a metric name
    op: Op                         # validated against the closed operator set
    value: Any


class Mandate(_Model):
    name: str
    constraints: list[MandateConstraint] = Field(default_factory=list)
    weights: dict[str, float] = Field(default_factory=dict)   # metric -> weight
    risk_free_annual: float = 0.02
    benchmark_id: str = "SP500"
    top_n: int = 5


class MetricResult(_Model):
    fund_id: str
    metric: str
    value: Optional[float]
    formula_id: str                # stable id, e.g. "sharpe.v1"
    inputs_ref: str                # e.g. "returns:<hash>|bench:SP500@2026-06"


class Claim(_Model):
    text: str
    metric: Optional[str] = None
    fund_id: Optional[str] = None
    value: Optional[float] = None
    source_refs: list[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    verified: Optional[bool] = None   # value re-checked against MetricResult


class ShortlistEntry(_Model):
    rank: int
    fund_id: str
    name: str
    strategy: str
    score: float
    metrics: dict[str, Optional[float]] = Field(default_factory=dict)
    # signed weighted-z contribution of each metric to `score` — the ranking's own
    # explanation, so the view never has to recompute the scoring math.
    components: list[dict] = Field(default_factory=list)


class MemoSection(_Model):
    heading: str
    body: str
    claims: list[Claim] = Field(default_factory=list)


class Memo(_Model):
    title: str
    mandate: str
    generated_by: str              # model id or "template"
    sections: list[MemoSection]
    shortlist: list[ShortlistEntry]
    audit: dict[str, Any] = Field(default_factory=dict)
    version: str = "v0.1"
