from __future__ import annotations
import html
from pathlib import Path
from .memo import render_markdown
from .metrics import METRIC_KEYS
from .models import Memo

_PCT = {"ann_return","ann_vol","max_drawdown","downside_dev","alpha","tracking_error","hit_rate"}

def _pct(x): return "—" if x is None else f"{x*100:.1f}%"
def _num(x): return "—" if x is None else f"{x:.2f}"

def write_markdown(memo, path):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(render_markdown(memo)); return p

def write_json(memo, path):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(memo.model_dump_json(indent=2)); return p

_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#070E1A; --panel:#0B1626; --panel2:#0E1B2E; --border:#1B2C44;
  --teal:#00E5C4; --teal2:#1FB6A6; --cyan:#22D3EE; --gold:#E7C878;
  --green:#34D399; --amber:#FBBF24; --red:#F97070;
  --ink:#D8E3F0; --dim:#5E738C; --dim2:#3C4F68;
  --display:'Rajdhani',system-ui,sans-serif;
  --hud:'Electrolize',system-ui,sans-serif;
  --body:'Inter',system-ui,sans-serif;
  --mono:'JetBrains Mono',ui-monospace,monospace;
  --grain:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
html{scroll-behavior:smooth}
body{
  background:
    radial-gradient(1100px 760px at 82% -6%, rgba(0,229,196,.07), transparent 60%),
    radial-gradient(1200px 900px at 12% 108%, rgba(231,200,120,.045), transparent 60%),
    var(--bg);
  color:var(--ink); font-family:var(--body); font-size:15px; line-height:1.6;
  -webkit-font-smoothing:antialiased; min-height:100vh; position:relative; overflow-x:hidden;
}
.atmo{position:fixed;inset:0;z-index:0;pointer-events:none}
.atmo .grid{position:absolute;inset:-30%;opacity:.4;
  background-image:linear-gradient(rgba(27,44,68,.5) 1px,transparent 1px),linear-gradient(90deg,rgba(27,44,68,.5) 1px,transparent 1px);
  background-size:66px 66px;
  -webkit-mask-image:radial-gradient(1000px 720px at 50% 34%,#000,transparent 76%);
  mask-image:radial-gradient(1000px 720px at 50% 34%,#000,transparent 76%);
  animation:drift 70s linear infinite}
@keyframes drift{to{transform:translate(66px,66px)}}
.atmo .sweep{position:absolute;left:0;right:0;height:220px;opacity:.55;
  background:linear-gradient(rgba(0,229,196,0),rgba(0,229,196,.05) 46%,rgba(34,211,238,.06) 52%,rgba(0,229,196,0));
  animation:sweep 11s linear infinite}
@keyframes sweep{0%{transform:translateY(-240px)}100%{transform:translateY(115vh)}}
.wrap{position:relative;z-index:1;max-width:1000px;margin:0 auto;padding:46px 28px 64px}
.panel{position:relative;margin:16px 0;
  --gfill:rgba(11,22,38,.62);
  background:linear-gradient(var(--gfill),var(--gfill)) padding-box,
    linear-gradient(145deg,rgba(0,229,196,.5),rgba(0,229,196,.03) 44%,rgba(34,211,238,.32) 90%) border-box;
  border:1px solid transparent;border-radius:2px;
  --c:14px;clip-path:polygon(var(--c) 0,100% 0,100% calc(100% - var(--c)),calc(100% - var(--c)) 100%,0 100%,0 var(--c));
  box-shadow:inset 0 1px 0 rgba(255,255,255,.06),inset 0 0 30px rgba(0,229,196,.03),0 26px 50px -26px rgba(0,0,0,.85);
  padding:22px 26px}
.panel::before{content:"";position:absolute;inset:0;background-image:var(--grain);background-size:120px;opacity:.025;mix-blend-mode:overlay;pointer-events:none}
.corner{position:absolute;width:12px;height:12px;border:1px solid rgba(0,229,196,.5);filter:drop-shadow(0 0 3px rgba(0,229,196,.4))}
.corner.tl{top:6px;left:6px;border-right:0;border-bottom:0}
.corner.tr{top:6px;right:6px;border-left:0;border-bottom:0}
.corner.bl{bottom:6px;left:6px;border-right:0;border-top:0}
.corner.br{bottom:6px;right:6px;border-left:0;border-top:0}
.lbl{font-family:var(--hud);font-size:11px;letter-spacing:.32em;text-transform:uppercase;color:var(--teal);
  margin-bottom:14px;display:flex;align-items:center;gap:10px}
.lbl::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,rgba(0,229,196,.4),transparent)}
.top{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;flex-wrap:wrap;margin-bottom:6px}
.brand{display:flex;align-items:center;gap:14px}
.logo{width:40px;height:40px;flex:none;border:1px solid rgba(0,229,196,.55);position:relative;
  --c:9px;clip-path:polygon(var(--c) 0,100% 0,100% calc(100% - var(--c)),calc(100% - var(--c)) 100%,0 100%,0 var(--c));
  box-shadow:inset 0 0 16px rgba(0,229,196,.22),0 0 16px -3px rgba(0,229,196,.5)}
.logo::after{content:"";position:absolute;inset:11px;border:2px solid var(--teal);border-radius:50%;
  box-shadow:0 0 10px rgba(0,229,196,.7)}
.wm{font-family:var(--display);font-weight:700;font-size:30px;letter-spacing:.24em;color:#fff;line-height:1;
  text-shadow:0 0 14px rgba(0,229,196,.55),0 0 34px rgba(0,229,196,.22)}
.sub{font-family:var(--mono);font-size:10.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--dim);margin-top:5px}
.hstat{display:flex;align-items:center;gap:9px;flex-wrap:wrap;justify-content:flex-end}
.tag{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);
  border:1px solid var(--border);padding:6px 11px;white-space:nowrap}
.tag.model{color:var(--gold);border-color:rgba(231,200,120,.4)}
.vbadge{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;color:var(--green);
  border:1px solid rgba(52,211,153,.45);padding:6px 11px;display:inline-flex;align-items:center;gap:8px;
  box-shadow:inset 0 0 12px rgba(52,211,153,.08),0 0 12px -3px rgba(52,211,153,.4);text-transform:uppercase}
.vbadge i{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 9px rgba(52,211,153,.9)}
.doctitle{font-family:var(--display);font-weight:700;font-size:25px;letter-spacing:.11em;color:#EEF4FB;
  margin:26px 0 4px;padding-bottom:14px;border-bottom:1px solid var(--border);text-shadow:0 0 20px rgba(0,229,196,.16)}
.mandate{font-family:var(--mono);font-size:12px;letter-spacing:.05em;color:var(--dim)}
.mandate b{color:var(--teal2);font-weight:500}
.hero .lead{font-size:18px;line-height:1.62;color:#EAF2FB;font-weight:400}
.hero{--gfill:rgba(12,26,44,.66)}
.rowhead{display:grid;grid-template-columns:46px 1.9fr repeat(5,1fr);gap:8px;padding:2px 6px 10px;
  font-family:var(--mono);font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--dim2)}
.rowhead div:nth-child(n+3){text-align:right}
.row{display:grid;grid-template-columns:46px 1.9fr repeat(5,1fr);gap:8px;align-items:center;
  padding:13px 6px;border-top:1px solid rgba(27,44,68,.7);transition:.18s}
.row:hover{background:linear-gradient(90deg,rgba(0,229,196,.05),transparent)}
.row.top{background:linear-gradient(90deg,rgba(231,200,120,.06),transparent)}
.rk{font-family:var(--mono);font-size:20px;font-weight:600;color:var(--dim2);text-align:center}
.row.top .rk{color:var(--gold);text-shadow:0 0 12px rgba(231,200,120,.5)}
.fn{font-family:var(--display);font-weight:600;font-size:16px;letter-spacing:.02em;color:#fff}
.fs{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-top:1px}
.bar{height:3px;margin-top:8px;background:rgba(27,44,68,.8);border-radius:2px;overflow:hidden;max-width:220px}
.bar span{display:block;height:100%;background:linear-gradient(90deg,var(--teal2),var(--teal));box-shadow:0 0 8px rgba(0,229,196,.6)}
.row.top .bar span{background:linear-gradient(90deg,#B99A50,var(--gold))}
.mx{text-align:right;font-family:var(--mono)}
.mx b{display:block;font-size:15px;font-weight:600;color:#E7EFF9}
.mx i{font-size:8.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim2);font-style:normal}
.mx b.pos{color:#7FE9CE} .mx b.neg{color:var(--red)}
.card h3{font-family:var(--display);font-weight:600;font-size:20px;letter-spacing:.02em;color:#fff;margin-bottom:9px}
.card p{color:#C2D0E0;font-size:14.5px}
.src-lbl{font-family:var(--hud);font-size:9.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--dim2);
  margin:18px 0 11px;display:flex;align-items:center;gap:10px}
.src-lbl::after{content:"";flex:1;height:1px;background:var(--border)}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{font-family:var(--mono);font-size:11px;letter-spacing:.02em;padding:6px 11px;border-radius:2px;
  background:rgba(8,18,32,.7);border:1px solid var(--border);color:var(--ink);display:inline-flex;align-items:center;gap:6px}
.chip.ok{border-color:rgba(0,229,196,.4);color:#9EEBDD}
.chip.ok::before{content:"";width:5px;height:5px;border-radius:50%;background:var(--teal);box-shadow:0 0 7px rgba(0,229,196,.9)}
.chip.warn{border-color:rgba(251,191,36,.45);color:#FCD777}
.chip.warn::before{content:"";width:5px;height:5px;border-radius:50%;background:var(--amber);box-shadow:0 0 7px rgba(251,191,36,.8)}
.foot{font-family:var(--mono);font-size:10.5px;letter-spacing:.08em;color:var(--dim2);
  text-align:center;margin-top:40px;padding-top:20px;border-top:1px solid var(--border)}
.foot b{color:var(--teal2);font-weight:400}
@media print{
  body{background:var(--bg) !important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .atmo{display:none}.panel{break-inside:avoid}
}
@media(max-width:720px){
  .rowhead div:nth-child(n+5),.row .mx:nth-child(n+5){display:none}
  .rowhead,.row{grid-template-columns:36px 1.4fr repeat(2,1fr)}
}
"""

def _corners():
    return '<span class="corner tl"></span><span class="corner tr"></span><span class="corner bl"></span><span class="corner br"></span>'

def render_html(memo):
    e = html.escape
    a = memo.audit
    scores = [s.score for s in memo.shortlist] or [0.0]
    smin, smax = min(scores), max(scores)
    def barw(s):
        if smax == smin: return 100.0
        return 20 + 80*(s - smin)/(smax - smin)
    def cret(x): return "pos" if (x or 0) >= 0 else "neg"

    head = (
        f'<div class="top"><div class="brand"><div class="logo"></div>'
        f'<div><div class="wm">EQUI</div><div class="sub">Allocator Memo Builder</div></div></div>'
        f'<div class="hstat"><span class="tag model">{e(memo.generated_by)}</span>'
        f'<span class="vbadge"><i></i>{a.get("verified_count",0)} / {a.get("claim_count",0)} verified</span></div></div>'
        f'<div class="doctitle">Investment Committee Memo</div>'
        f'<div class="mandate">MANDATE · <b>{e(memo.mandate)}</b></div>'
    )

    rec = memo.sections[0] if memo.sections else None
    hero = ""
    if rec:
        hero = (f'<section class="panel hero">{_corners()}<div class="lbl">Recommendation</div>'
                f'<p class="lead">{e(rec.body)}</p></section>')

    rows = ('<div class="rowhead"><div></div><div>Fund</div><div>Return</div><div>Sharpe</div>'
            '<div>Sortino</div><div>Calmar</div><div>Max DD</div></div>')
    for s in memo.shortlist:
        m = s.metrics
        top = " top" if s.rank == 1 else ""
        rows += (
            f'<div class="row{top}"><div class="rk">{s.rank:02d}</div>'
            f'<div class="fund"><div class="fn">{e(s.name)}</div><div class="fs">{e(s.strategy)}</div>'
            f'<div class="bar"><span style="width:{barw(s.score):.0f}%"></span></div></div>'
            f'<div class="mx"><b class="{cret(m.get("ann_return"))}">{_pct(m.get("ann_return"))}</b><i>ann</i></div>'
            f'<div class="mx"><b>{_num(m.get("sharpe"))}</b><i>sharpe</i></div>'
            f'<div class="mx"><b>{_num(m.get("sortino"))}</b><i>sortino</i></div>'
            f'<div class="mx"><b>{_num(m.get("calmar"))}</b><i>calmar</i></div>'
            f'<div class="mx"><b class="neg">{_pct(m.get("max_drawdown"))}</b><i>peak-trough</i></div></div>'
        )
    shortlist = f'<section class="panel">{_corners()}<div class="lbl">Shortlist · {len(memo.shortlist)} funds</div>{rows}</section>'

    cards = ""
    for sec in memo.sections[1:]:
        chips = ""
        for c in sec.claims:
            k = "ok" if c.verified else "warn"
            src = e("; ".join(c.source_refs) or "no source")
            chips += f'<span class="chip {k}" title="{src}">{e(c.text)}</span>'
        srcline = (f'<div class="src-lbl">Sources · verified against the metrics engine</div><div class="chips">{chips}</div>'
                   if sec.claims else "")
        cards += (f'<section class="panel card">{_corners()}<h3>{e(sec.heading)}</h3>'
                  f'<p>{e(sec.body)}</p>{srcline}</section>')

    foot = ('<div class="foot">ALLOCATORMEMOBUILDER · every figure traces to a <b>source row + formula</b> · '
            'the model narrates, it never computes · print to PDF from your browser</div>')

    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{e(memo.title)}</title>'
        f'<link rel="preconnect" href="https://fonts.googleapis.com">'
        f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        f'<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Electrolize&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
        f'<style>{_CSS}</style></head><body>'
        f'<div class="atmo"><div class="grid"></div><div class="sweep"></div></div>'
        f'<div class="wrap">{head}{hero}{shortlist}{cards}{foot}</div>'
        f'</body></html>'
    )

def write_html(memo, path):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(render_html(memo)); return p

def write_xlsx(memo, ctx, path):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); wb=Workbook()
    hf=PatternFill("solid",fgColor="0A1628"); ff=Font(bold=True,color="00E5C4")
    def sh(ws,n):
        for c in range(1,n+1): ws.cell(row=1,column=c).fill=hf; ws.cell(row=1,column=c).font=ff
    ws=wb.active; ws.title="Shortlist"
    cols=["rank","fund_id","name","strategy","score","ann_return","sharpe","sortino","calmar","max_drawdown","ann_vol"]
    ws.append([c.replace('_',' ').title() for c in cols])
    for s in memo.shortlist:
        m=s.metrics; ws.append([s.rank,s.fund_id,s.name,s.strategy,s.score,m.get('ann_return'),m.get('sharpe'),m.get('sortino'),m.get('calmar'),m.get('max_drawdown'),m.get('ann_vol')])
    sh(ws,len(cols))
    ws2=wb.create_sheet("Metrics"); hdr=["fund_id","name"]+METRIC_KEYS
    ws2.append([h.replace('_',' ').title() for h in hdr])
    for fid,vals in ctx.metrics_by_fund.items():
        f=ctx.get_fund(fid); ws2.append([fid, f.name if f else fid]+[vals.get(k) for k in METRIC_KEYS])
    sh(ws2,len(hdr))
    ws3=wb.create_sheet("Audit"); ws3.append(["fund_id","metric","value","verified","sources"])
    for c in memo.audit.get("claims",[]): ws3.append([c.get("fund_id"),c.get("metric"),c.get("value"),c.get("verified"),"; ".join(c.get("sources",[]))])
    sh(ws3,5); wb.save(p); return p

def export_all(memo, ctx=None, outdir="exports"):
    paths={"md":write_markdown(memo,Path(outdir)/"memo.md"),"json":write_json(memo,Path(outdir)/"memo.json"),"html":write_html(memo,Path(outdir)/"memo.html")}
    if ctx is not None: paths["xlsx"]=write_xlsx(memo,ctx,Path(outdir)/"memo.xlsx")
    return paths
