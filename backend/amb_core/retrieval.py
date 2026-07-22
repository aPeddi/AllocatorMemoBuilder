"""The typed retrieval layer — the ONLY way the memo reaches numbers.

Deterministic accessors over the computed analysis. This is what the memo uses
to fetch exact values and to re-verify every LLM claim (ADR-0002, ADR-0003).
"""
from __future__ import annotations

from typing import Optional

from .models import Benchmark, Fund, Mandate, MetricResult, ShortlistEntry


class AnalysisContext:
    def __init__(
        self,
        funds: list[Fund],
        benchmark: Optional[Benchmark],
        metrics_by_fund: dict[str, dict[str, Optional[float]]],
        metric_results: dict[str, list[MetricResult]],
        shortlist: list[ShortlistEntry],
        mandate: Mandate,
        quarantined: Optional[list[dict]] = None,
        series_by_fund: Optional[dict] = None,
    ):
        self.funds = {f.fund_id: f for f in funds}
        self.benchmark = benchmark
        self.metrics_by_fund = metrics_by_fund
        self.metric_results = metric_results
        self.shortlist = shortlist
        self.mandate = mandate
        self.quarantined = quarantined or []
        self.series_by_fund = series_by_fund or {}

    def get_fund(self, fund_id: str) -> Optional[Fund]:
        return self.funds.get(fund_id)

    def metric_value(self, fund_id: str, metric: str) -> Optional[float]:
        return self.metrics_by_fund.get(fund_id, {}).get(metric)

    def get_metric(self, fund_id: str, metric: str) -> Optional[MetricResult]:
        for mr in self.metric_results.get(fund_id, []):
            if mr.metric == metric:
                return mr
        return None

    def shortlist_ids(self) -> list[str]:
        return [s.fund_id for s in self.shortlist]

    def facts_table(self) -> str:
        """A compact, exact facts block for the LLM prompt. The model narrates
        from these numbers; it does not compute them."""
        lines = []
        for s in self.shortlist:
            f = self.funds[s.fund_id]
            m = self.metrics_by_fund[s.fund_id]

            def pct(x):
                return "n/a" if x is None else f"{x * 100:.1f}%"

            def num(x):
                return "n/a" if x is None else f"{x:.2f}"

            lines.append(
                f"[{s.fund_id}] {f.name} — {f.strategy}\n"
                f"    ann_return={pct(m.get('ann_return'))}  vol={pct(m.get('ann_vol'))}  "
                f"sharpe={num(m.get('sharpe'))}  sortino={num(m.get('sortino'))}  "
                f"calmar={num(m.get('calmar'))}  max_drawdown={pct(m.get('max_drawdown'))}  "
                f"alpha={pct(m.get('alpha'))}  beta={num(m.get('beta'))}  "
                f"hit_rate={pct(m.get('hit_rate'))}"
            )
        return "\n".join(lines)
