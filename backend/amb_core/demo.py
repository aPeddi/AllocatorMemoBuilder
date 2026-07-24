"""`./amb demo` — the full pipeline on bundled sample data."""
from __future__ import annotations

import sys
from pathlib import Path

from .config import get_settings
from .export import export_all
from .pipeline import load_mandate, run

SAMPLES = Path("data/samples")
MANDATE = Path("data/mandates/default.yaml")


def _fmt_pct(x):
    return "n/a" if x is None else f"{x * 100:6.1f}%"


def _fmt_num(x):
    return "n/a" if x is None else f"{x:6.2f}"


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    s = get_settings()
    funds_csv, returns_csv = SAMPLES / "funds.csv", SAMPLES / "returns.csv"
    if not (funds_csv.exists() and returns_csv.exists()):
        print(f"! sample data missing (expected {funds_csv}). Run: python data/samples/generate.py")
        return 1

    mandate = load_mandate(MANDATE) if MANDATE.exists() else None
    if mandate is None:
        print(f"! mandate missing (expected {MANDATE}).")
        return 1

    provider = None
    label = "deterministic template (offline)"
    if "--template" not in argv:
        try:
            from .llm import select_claims_provider

            provider = select_claims_provider()  # None -> deterministic template
            if provider is not None:
                model = s.strong_model if s.llm_provider == "anthropic" else s.openai_model
                label = f"{s.llm_provider} · {model}"
        except Exception as e:  # noqa: BLE001
            print(f"! LLM unavailable ({e}); falling back to template.")

    print(f"▸ Generating memo — {label}\n")
    memo, ctx = run(funds_csv, returns_csv, mandate, provider)

    print(f"Mandate: {mandate.name}")
    b = ctx.benchmark
    if b is not None:
        kind = {"live": "LIVE · FRED", "cache": "CACHED · FRED", "snapshot": "SNAPSHOT · local"}.get(b.source_kind, b.source_kind)
        print(f"Benchmark: {b.name} — {kind} · as-of {b.as_of}  (mode: {s.benchmark_mode})")
    if ctx.quarantined:
        print(f"Quarantined rows: {len(ctx.quarantined)}")
    print(f"Universe: {len(ctx.metrics_by_fund)} funds  →  shortlist {len(memo.shortlist)}\n")
    print(f"  {'#':>2}  {'fund':<26} {'ret':>8} {'sharpe':>7} {'sortino':>7} {'calmar':>7} {'maxDD':>8}")
    for ent in memo.shortlist:
        m = ent.metrics
        print(
            f"  {ent.rank:>2}  {ent.name[:26]:<26} {_fmt_pct(m.get('ann_return'))} "
            f"{_fmt_num(m.get('sharpe'))} {_fmt_num(m.get('sortino'))} {_fmt_num(m.get('calmar'))} "
            f"{_fmt_pct(m.get('max_drawdown'))}"
        )
    a = memo.audit
    print(f"\n✓ claims verified: {a['verified_count']}/{a['claim_count']}")
    for kind, pth in export_all(memo, ctx, "exports").items():
        print(f"✓ {kind:<4} → {pth}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
