"""`./amb demo` — the full pipeline on bundled sample data, with a polished
rich-powered terminal experience (staged progress, provenance, ranked shortlist,
verification, exports). Degrades to plain text if `rich` isn't installed."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from .config import get_settings
from .export import export_all
from .pipeline import load_mandate, run

SAMPLES = Path("data/samples")
MANDATE = Path("data/mandates/default.yaml")

ACCENT = "#4E9E77"
WARM = "#B79363"


def _fmt_pct(x: Optional[float]) -> str:
    return "—" if x is None else f"{x * 100:.1f}%"


def _fmt_num(x: Optional[float]) -> str:
    return "—" if x is None else f"{x:.2f}"


def _human_size(p: Path) -> str:
    try:
        n = float(p.stat().st_size)
    except OSError:
        return "—"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.0f} B"


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
    label = "deterministic template · offline"
    if "--template" not in argv:
        try:
            from .llm import select_claims_provider
            provider = select_claims_provider()  # None -> deterministic template
            if provider is not None:
                model = s.strong_model if s.llm_provider == "anthropic" else s.openai_model
                label = f"{s.llm_provider} · {model}"
        except Exception as e:  # noqa: BLE001
            print(f"! LLM unavailable ({e}); falling back to template.")

    try:
        return _rich_run(mandate, funds_csv, returns_csv, provider, label, s)
    except ImportError:
        return _plain_run(mandate, funds_csv, returns_csv, provider, label, s)


def _rich_run(mandate, funds_csv, returns_csv, provider, label, s) -> int:
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
    from rich.table import Table
    from rich.text import Text

    con = Console()
    con.print()
    con.print(Panel(
        Text.assemble(("◆ EQUI", f"bold {ACCENT}"), ("  ·  Allocator Memo Builder", "dim"),
                      ("\ningest → metrics → screen → score → auditable IC memo", "italic dim")),
        border_style=ACCENT, padding=(0, 2)))
    con.print(Text.assemble(("  memo drafting: ", "dim"), (label, f"bold {ACCENT}")))
    con.print()

    # No percentage bar: the deterministic stages finish in milliseconds, so the only
    # step that takes real time is the LLM memo draft — and its duration isn't knowable
    # in advance. An animated spinner + stage label + elapsed clock is the honest signal
    # (it keeps moving during the untrackable model call) rather than a bar stuck at ~83%.
    memo = ctx = None
    with Progress(
        SpinnerColumn(style=ACCENT),
        TextColumn("[progress.description]{task.description}"),
        TextColumn("[dim]·[/]"), TimeElapsedColumn(),
        console=con, transient=True,
    ) as prog:
        task = prog.add_task("Starting…", total=None)  # indeterminate — see note above

        def on_step(lbl: str) -> None:
            prog.update(task, description=lbl)

        memo, ctx = run(funds_csv, returns_csv, mandate, provider, on_step=on_step)
        prog.update(task, description="Exporting artifacts")
        exports = export_all(memo, ctx, "exports")

    # ── provenance ──
    b = ctx.benchmark
    bkind = {"live": "LIVE · FRED", "cache": "CACHED · FRED", "snapshot": "SNAPSHOT · local"}.get(
        getattr(b, "source_kind", ""), getattr(b, "source_kind", "—")) if b else "—"
    prov = Table.grid(padding=(0, 2))
    prov.add_column(style="dim", justify="right")
    prov.add_column(style="bold")
    prov.add_row("mandate", mandate.name)
    prov.add_row("benchmark", f"{b.name} · {bkind} · as-of {b.as_of}" if b else "none")
    prov.add_row("risk-free", f"{ctx.rf_used * 100:.2f}%  ({ctx.rf_source})")
    prov.add_row("universe", f"{len(ctx.metrics_by_fund)} funds  →  {len(memo.shortlist)} shortlisted")
    if ctx.quarantined:
        prov.add_row("quarantined", f"[{WARM}]{len(ctx.quarantined)} row(s) — kept row-level[/]")
    con.print(Panel(prov, title="[dim]provenance[/]", border_style="grey37", padding=(1, 1)))

    # ── ranked shortlist ──
    tbl = Table(title=None, expand=False, border_style="grey30", header_style=f"bold {ACCENT}", pad_edge=False)
    tbl.add_column("#", justify="right", style="dim")
    tbl.add_column("Fund", no_wrap=True)
    for h in ("Ret", "Vol", "SR", "Sor", "Cal", "DD", "Score"):
        tbl.add_column(h, justify="right", no_wrap=True)
    for e in memo.shortlist:
        m = e.metrics
        win = e.rank == 1
        nm = Text(e.name[:30], style=f"bold {ACCENT}" if win else "")
        cells = [_fmt_pct(m.get("ann_return")), _fmt_pct(m.get("ann_vol")), _fmt_num(m.get("sharpe")),
                 _fmt_num(m.get("sortino")), _fmt_num(m.get("calmar")), _fmt_pct(m.get("max_drawdown")),
                 f"{e.score:+.2f}"]
        style = ACCENT if win else None
        tbl.add_row(("★" if win else str(e.rank)), nm, *cells, style=style)
    con.print(tbl)

    # ── verification + exports ──
    a = memo.audit
    vc, cc = a.get("verified_count", 0), a.get("claim_count", 0)
    ok = vc == cc and cc > 0
    con.print()
    con.print(Text.assemble(
        ("  ✓ " if ok else "  ! ", f"bold {ACCENT}" if ok else "bold red"),
        (f"{vc}/{cc} claims re-verified against the deterministic metrics engine",
         ACCENT if ok else "red")))
    ex = Table.grid(padding=(0, 2))
    ex.add_column(style=f"{ACCENT}")
    ex.add_column(style="bold")
    ex.add_column(style="dim")
    for kind, pth in exports.items():
        ex.add_row("✓", f"{kind.upper()}", f"{pth}  ·  {_human_size(Path(pth))}")
    con.print(Panel(ex, title="[dim]exports[/]", border_style="grey37", padding=(1, 1)))
    con.print()
    return 0


def _plain_run(mandate, funds_csv, returns_csv, provider, label, s) -> int:
    """Fallback when rich is unavailable — the original plain output."""
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
            f"  {ent.rank:>2}  {ent.name[:26]:<26} {_fmt_pct(m.get('ann_return')):>8} "
            f"{_fmt_num(m.get('sharpe')):>7} {_fmt_num(m.get('sortino')):>7} {_fmt_num(m.get('calmar')):>7} "
            f"{_fmt_pct(m.get('max_drawdown')):>8}"
        )
    a = memo.audit
    print(f"\n✓ claims verified: {a['verified_count']}/{a['claim_count']}")
    for kind, pth in export_all(memo, ctx, "exports").items():
        print(f"✓ {kind:<4} → {pth}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
