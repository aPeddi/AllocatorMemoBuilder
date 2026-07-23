#!/usr/bin/env python3
"""Synthesize a small, realistic fund universe for a NYC allocator (Equi-style).

Stdlib only + a fixed seed, so it is reproducible and runs anywhere (no numpy).
Writes:
  data/samples/funds.csv         fund metadata
  data/samples/returns.csv       36 monthly returns per fund (decimals) + a few
                                 deliberately messy rows to exercise quarantine
  data/benchmarks/sp500_monthly.csv   as-of benchmark snapshot (ADR-0005)
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

SEED = 42
N_MONTHS = 36
START = (2023, 7)  # 2023-07 .. 2026-06

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "data" / "samples"
BENCH = ROOT / "data" / "benchmarks"

# fund_id, name, strategy, aum_mm, inception, fee, beta, alpha_m, idio, notes
FUNDS = [
    ("EQ-LS", "Hudson Long/Short", "Long/Short Equity", 420, "2016-03-01", 1.5, 0.60, 0.0020, 0.025, "Concentrated single-name L/S, net ~50%."),
    ("MAC", "Gotham Global Macro", "Global Macro", 610, "2014-09-01", 2.0, 0.20, 0.0035, 0.030, "Discretionary rates + FX."),
    ("MN", "Empire Market Neutral", "Market Neutral", 300, "2018-01-01", 1.25, 0.05, 0.0025, 0.012, "Beta-neutral quant equity."),
    ("ED", "Liberty Event-Driven", "Event-Driven", 275, "2015-06-01", 1.75, 0.40, 0.0015, 0.020, "Merger arb + special situations."),
    ("CR", "Tribeca Structured Credit", "Structured Credit", 540, "2013-11-01", 1.5, 0.25, 0.0020, 0.015, "Securitized + corporate credit."),
    ("MS", "Manhattan Multi-Strategy", "Multi-Strategy", 900, "2012-04-01", 2.0, 0.35, 0.0030, 0.014, "Multi-PM platform, tight risk."),
    ("VEN", "SoHo Venture I", "Venture", 180, "2019-02-01", 2.5, 0.90, 0.0040, 0.060, "Early-stage; illiquid, quarterly marks."),
    ("RA", "Battery Real Assets", "Real Assets", 350, "2017-08-01", 1.5, 0.30, 0.0010, 0.020, "Infra + real estate."),
    ("DA", "Chelsea Digital Assets", "Digital Assets", 120, "2020-10-01", 2.0, 1.20, 0.0020, 0.110, "Liquid crypto; very high vol."),
]


def months(y, m, count):
    out = []
    for _ in range(count):
        out.append(f"{y:04d}-{m:02d}-01")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def main() -> int:
    rnd = random.Random(SEED)
    SAMPLES.mkdir(parents=True, exist_ok=True)
    BENCH.mkdir(parents=True, exist_ok=True)
    dates = months(*START, N_MONTHS)

    # market (S&P) monthly returns
    market = [rnd.gauss(0.008, 0.045) for _ in dates]

    with (BENCH / "sp500_monthly.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "return"])
        for d, r in zip(dates, market):
            w.writerow([d, round(r, 6)])

    # liquidity terms per fund: (redemption_freq, lockup_months, notice_days)
    LIQUIDITY = {
        "EQ-LS": ("Monthly", 12, 30), "MAC": ("Monthly", 0, 15), "MN": ("Monthly", 0, 30),
        "ED": ("Quarterly", 12, 45), "CR": ("Quarterly", 24, 60), "MS": ("Quarterly", 12, 45),
        "VEN": ("Illiquid", 60, 90), "RA": ("Annual", 36, 90), "DA": ("Daily", 0, 5),
    }
    with (SAMPLES / "funds.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["fund_id", "name", "strategy", "aum_mm", "inception_date", "mgmt_fee_pct",
                    "redemption_freq", "lockup_months", "notice_days", "notes"])
        for f in FUNDS:
            fid, name, strat, aum, inc, fee, notes = f[0], f[1], f[2], f[3], f[4], f[5], f[9]
            rf, lk, nd = LIQUIDITY.get(fid, ("Monthly", 0, 30))
            w.writerow([fid, name, strat, aum, inc, fee, rf, lk, nd, notes])

    rows = []
    for fid, _name, _strat, _aum, _inc, _fee, beta, alpha_m, idio, _notes in FUNDS:
        for d, mk in zip(dates, market):
            r = alpha_m + beta * mk + rnd.gauss(0.0, idio)
            rows.append([d, fid, round(r, 6)])

    # a few deliberately messy rows -> should be quarantined, not counted
    rows.append(["", "MAC", 0.01])          # missing date
    rows.append(["2026-06-01", "MN", ""])   # missing return
    rows.append(["not-a-date", "ED", "n/a"])  # junk

    with (SAMPLES / "returns.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "fund_id", "monthly_return"])
        w.writerows(rows)

    print(f"wrote {len(FUNDS)} funds, {len(rows)} return rows (incl. 3 messy), {len(dates)} benchmark points")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
