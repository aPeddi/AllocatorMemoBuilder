from __future__ import annotations
import html, math
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
  --bg:#070E1A;--panel:#0B1626;--border:#1B2C44;
  --teal:#00E5C4;--teal2:#1FB6A6;--cyan:#22D3EE;--gold:#E7C878;
  --green:#34D399;--amber:#FBBF24;--red:#F97070;--violet:#B794F4;
  --ink:#D8E3F0;--dim:#5E738C;--dim2:#3C4F68;
  --display:'Rajdhani',system-ui,sans-serif;--hud:'Electrolize',system-ui,sans-serif;
  --body:'Inter',system-ui,sans-serif;--mono:'JetBrains Mono',ui-monospace,monospace;
  --grain:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
html{scroll-behavior:smooth}
body{background:radial-gradient(1100px 760px at 82% -6%,rgba(0,229,196,.07),transparent 60%),radial-gradient(1200px 900px at 12% 108%,rgba(231,200,120,.045),transparent 60%),var(--bg);
  color:var(--ink);font-family:var(--body);font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased;min-height:100vh;position:relative;overflow-x:hidden}
.atmo{position:fixed;inset:0;z-index:0;pointer-events:none}
.atmo .grid{position:absolute;inset:-30%;opacity:.4;background-image:linear-gradient(rgba(27,44,68,.5) 1px,transparent 1px),linear-gradient(90deg,rgba(27,44,68,.5) 1px,transparent 1px);background-size:66px 66px;-webkit-mask-image:radial-gradient(1000px 720px at 50% 30%,#000,transparent 76%);mask-image:radial-gradient(1000px 720px at 50% 30%,#000,transparent 76%);animation:drift 70s linear infinite}
@keyframes drift{to{transform:translate(66px,66px)}}
.atmo .sweep{position:absolute;left:0;right:0;height:220px;opacity:.5;background:linear-gradient(rgba(0,229,196,0),rgba(0,229,196,.05) 46%,rgba(34,211,238,.06) 52%,rgba(0,229,196,0));animation:sweep 11s linear infinite}
@keyframes sweep{0%{transform:translateY(-240px)}100%{transform:translateY(115vh)}}
.wrap{position:relative;z-index:1;max-width:1000px;margin:0 auto;padding:44px 26px 70px}

/* reveal */
.reveal{opacity:0;transform:translateY(16px)}
.reveal.in{animation:rise .6s cubic-bezier(.2,.8,.2,1) both}
@keyframes rise{to{opacity:1;transform:none}}

.panel{position:relative;margin:15px 0;--gfill:rgba(11,22,38,.62);
  background:linear-gradient(var(--gfill),var(--gfill)) padding-box,linear-gradient(145deg,rgba(0,229,196,.5),rgba(0,229,196,.03) 44%,rgba(34,211,238,.32) 90%) border-box;
  border:1px solid transparent;--c:14px;clip-path:polygon(var(--c) 0,100% 0,100% calc(100% - var(--c)),calc(100% - var(--c)) 100%,0 100%,0 var(--c));
  box-shadow:inset 0 1px 0 rgba(255,255,255,.06),0 26px 50px -26px rgba(0,0,0,.85);padding:20px 24px}
.panel::before{content:"";position:absolute;inset:0;background-image:var(--grain);background-size:120px;opacity:.025;mix-blend-mode:overlay;pointer-events:none}
.corner{position:absolute;width:12px;height:12px;border:1px solid rgba(0,229,196,.5);filter:drop-shadow(0 0 3px rgba(0,229,196,.4))}
.corner.tl{top:6px;left:6px;border-right:0;border-bottom:0}.corner.tr{top:6px;right:6px;border-left:0;border-bottom:0}
.corner.bl{bottom:6px;left:6px;border-right:0;border-top:0}.corner.br{bottom:6px;right:6px;border-left:0;border-top:0}
.lbl{font-family:var(--hud);font-size:10.5px;letter-spacing:.3em;text-transform:uppercase;color:var(--teal);margin-bottom:12px;display:flex;align-items:center;gap:10px}
.lbl::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,rgba(0,229,196,.4),transparent)}
.lbl .hint{font-family:var(--mono);font-size:9px;letter-spacing:.12em;color:var(--dim2);text-transform:none}

/* header */
.top{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:13px}
.logo{width:38px;height:38px;flex:none;border:1px solid rgba(0,229,196,.55);position:relative;--c:9px;clip-path:polygon(var(--c) 0,100% 0,100% calc(100% - var(--c)),calc(100% - var(--c)) 100%,0 100%,0 var(--c));box-shadow:inset 0 0 16px rgba(0,229,196,.22),0 0 16px -3px rgba(0,229,196,.5)}
.logo::after{content:"";position:absolute;inset:10px;border:2px solid var(--teal);border-radius:50%;box-shadow:0 0 10px rgba(0,229,196,.7)}
.wm{font-family:var(--display);font-weight:700;font-size:28px;letter-spacing:.24em;color:#fff;line-height:1;text-shadow:0 0 14px rgba(0,229,196,.55),0 0 34px rgba(0,229,196,.22)}
.sub{font-family:var(--mono);font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:var(--dim);margin-top:5px}
.hstat{display:flex;align-items:center;gap:9px;flex-wrap:wrap;justify-content:flex-end}
.tag{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);border:1px solid var(--border);padding:6px 10px}
.tag.model{color:var(--gold);border-color:rgba(231,200,120,.4)}
.vbadge{font-family:var(--mono);font-size:10px;letter-spacing:.14em;color:var(--green);border:1px solid rgba(52,211,153,.45);padding:6px 10px;display:inline-flex;align-items:center;gap:7px;text-transform:uppercase;box-shadow:0 0 12px -3px rgba(52,211,153,.4)}
.vbadge i{width:6px;height:6px;border-radius:50%;background:var(--green);box-shadow:0 0 9px rgba(52,211,153,.9);animation:pulse 2.4s ease-in-out infinite}
@keyframes pulse{50%{opacity:.4}}
.doctitle{font-family:var(--display);font-weight:700;font-size:24px;letter-spacing:.11em;color:#EEF4FB;margin:22px 0 4px;text-shadow:0 0 20px rgba(0,229,196,.16)}
.mandate{font-family:var(--mono);font-size:11.5px;letter-spacing:.05em;color:var(--dim)}
.mandate b{color:var(--teal2);font-weight:500}

/* recommendation strip */
.rec{--gfill:rgba(12,26,44,.7)}
.rec .lead{font-size:17px;line-height:1.55;color:#EAF2FB}
.rec .pick{margin-top:14px;display:inline-flex;align-items:center;gap:12px;padding:9px 15px 9px 11px;border:1px solid rgba(231,200,120,.4);background:rgba(231,200,120,.05);--c:8px;clip-path:polygon(var(--c) 0,100% 0,100% calc(100% - var(--c)),calc(100% - var(--c)) 100%,0 100%,0 var(--c))}
.rec .pick .pin{font-family:var(--hud);font-size:9px;letter-spacing:.22em;color:var(--gold);text-transform:uppercase}
.rec .pick .pn{font-family:var(--display);font-weight:700;font-size:18px;color:#fff;letter-spacing:.02em}
.rec .pick .ps{font-family:var(--mono);font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:.1em}

/* ===== risk/return MAP ===== */
.plot{position:relative;height:340px;margin:6px 4px 2px;
  background:linear-gradient(rgba(27,44,68,.22) 1px,transparent 1px),linear-gradient(90deg,rgba(27,44,68,.22) 1px,transparent 1px);background-size:11.11% 20%}
.plot .sweet{position:absolute;left:0;top:0;width:46%;height:52%;background:radial-gradient(120% 120% at 0 0,rgba(0,229,196,.10),transparent 70%);pointer-events:none}
.plot .sweet span{position:absolute;left:12px;top:10px;font-family:var(--hud);font-size:8.5px;letter-spacing:.2em;color:rgba(0,229,196,.6);text-transform:uppercase}
.ax{position:absolute;font-family:var(--mono);font-size:9px;letter-spacing:.16em;color:var(--dim2);text-transform:uppercase}
.ax.x{bottom:-20px;right:4px}.ax.y{top:-2px;left:-2px;transform-origin:left;writing-mode:vertical-lr}
.axlo{position:absolute;font-family:var(--mono);font-size:8.5px;color:var(--dim2)}
.node{position:absolute;transform:translate(-50%,50%) scale(0);cursor:default;z-index:2}
.node.in{animation:pop .5s cubic-bezier(.2,1.2,.4,1) both}
@keyframes pop{to{transform:translate(-50%,50%) scale(1)}}
.node .dot{width:13px;height:13px;border-radius:50%;background:var(--dim2);border:1px solid rgba(94,115,140,.5);transition:.2s}
.node.on{cursor:pointer}
.node.on .dot{width:34px;height:34px;display:grid;place-items:center;font-family:var(--mono);font-weight:600;font-size:12px;color:#04121a;background:radial-gradient(circle at 35% 30%,#5ff0dc,var(--teal));box-shadow:0 0 16px rgba(0,229,196,.6),inset 0 0 6px rgba(255,255,255,.4);border:0}
.node.on.rank1 .dot{background:radial-gradient(circle at 35% 30%,#f4dc9a,var(--gold));box-shadow:0 0 18px rgba(231,200,120,.7)}
.node.on:hover .dot{transform:scale(1.14)}
.node.excl .dot{background:transparent;border:1px dashed rgba(94,115,140,.6)}
.node .ring{position:absolute;inset:-7px;border:1px solid rgba(0,229,196,.35);border-radius:50%;opacity:0}
.node.on:hover .ring{opacity:1;animation:ring 1.1s ease-out infinite}
@keyframes ring{from{transform:scale(.7);opacity:.7}to{transform:scale(1.5);opacity:0}}
#tip{position:fixed;z-index:50;pointer-events:none;opacity:0;transform:translate(14px,-50%);transition:opacity .15s;
  background:rgba(6,14,24,.95);border:1px solid rgba(0,229,196,.4);padding:8px 11px;font-family:var(--mono);font-size:11px;white-space:nowrap;box-shadow:0 8px 24px rgba(0,0,0,.6)}
#tip .tn{color:#fff;font-family:var(--display);font-weight:600;font-size:13px;letter-spacing:.02em}
#tip .ts{color:var(--dim);font-size:9px;text-transform:uppercase;letter-spacing:.1em}
#tip b{color:var(--teal2)}
.legend{display:flex;gap:18px;margin-top:26px;font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;color:var(--dim);text-transform:uppercase}
.legend span{display:inline-flex;align-items:center;gap:7px}
.legend i{width:10px;height:10px;border-radius:50%}
.legend .i-sl{background:var(--teal);box-shadow:0 0 8px rgba(0,229,196,.7)}
.legend .i-ex{border:1px dashed var(--dim);width:9px;height:9px}

/* ===== tiles ===== */
.tiles-lbl{font-family:var(--hud);font-size:10.5px;letter-spacing:.3em;text-transform:uppercase;color:var(--teal);margin:26px 4px 4px;display:flex;align-items:center;gap:10px}
.tiles-lbl::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,rgba(0,229,196,.4),transparent)}
.tile{margin:11px 0}
.thead{display:grid;grid-template-columns:44px 1.5fr 130px auto 46px 26px;gap:16px;align-items:center;padding:16px 20px;cursor:pointer;position:relative;z-index:1}
.med{font-family:var(--mono);font-size:19px;font-weight:600;color:var(--dim2);text-align:center}
.tile.rank1 .med{color:var(--gold);text-shadow:0 0 12px rgba(231,200,120,.5)}
.tn{font-family:var(--display);font-weight:600;font-size:17px;color:#fff;letter-spacing:.02em}
.ts{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-top:2px}
.spark{width:130px;height:34px;display:block}
.mstat{display:flex;gap:16px}
.mstat .m{text-align:right}
.mstat .m b{display:block;font-family:var(--mono);font-size:14px;font-weight:600;color:#E7EFF9}
.mstat .m b.pos{color:#7FE9CE}.mstat .m b.neg{color:var(--red)}
.mstat .m i{font-family:var(--mono);font-size:8px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim2);font-style:normal}
.dial{width:44px;height:44px}
.dial .track{fill:none;stroke:rgba(27,44,68,.9);stroke-width:4}
.dial .val{fill:none;stroke:var(--teal);stroke-width:4;stroke-linecap:round;stroke-dasharray:var(--c);stroke-dashoffset:var(--c);transform:rotate(-90deg);transform-origin:50% 50%;transition:stroke-dashoffset 1.1s cubic-bezier(.2,.8,.2,1);filter:drop-shadow(0 0 4px rgba(0,229,196,.5))}
.tile.rank1 .dial .val{stroke:var(--gold);filter:drop-shadow(0 0 4px rgba(231,200,120,.5))}
body.ready .dial .val{stroke-dashoffset:var(--off)}
.dial-wrap{position:relative;width:44px;height:44px}
.dial-wrap span{position:absolute;inset:0;display:grid;place-items:center;font-family:var(--mono);font-size:10px;font-weight:600;color:var(--ink)}
.chev{justify-self:end;width:9px;height:9px;border-right:1.5px solid var(--dim);border-bottom:1.5px solid var(--dim);transform:rotate(45deg);transition:.3s}
.tile.open .chev{transform:rotate(225deg);border-color:var(--teal)}
.detail{max-height:0;overflow:hidden;opacity:0;transition:max-height .45s ease,opacity .35s ease}
.tile.open .detail{max-height:760px;opacity:1}
.detail-in{padding:2px 20px 20px;border-top:1px solid var(--border);margin-top:2px}
.detail p{color:#C2D0E0;font-size:14px;margin:14px 0 4px}
.mgrid{display:grid;grid-template-columns:repeat(6,1fr);gap:1px;background:var(--border);border:1px solid var(--border);margin:16px 0}
.mgrid .cell{background:var(--panel);padding:9px 10px;text-align:center}
.mgrid .cell b{display:block;font-family:var(--mono);font-size:13px;color:#E7EFF9}
.mgrid .cell i{font-family:var(--mono);font-size:7.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim2);font-style:normal}
.src-lbl{font-family:var(--hud);font-size:9px;letter-spacing:.22em;text-transform:uppercase;color:var(--dim2);margin:14px 0 10px;display:flex;align-items:center;gap:10px}
.src-lbl::after{content:"";flex:1;height:1px;background:var(--border)}
.chips{display:flex;flex-wrap:wrap;gap:7px}
.chip{font-family:var(--mono);font-size:10.5px;padding:6px 10px;background:rgba(8,18,32,.7);border:1px solid var(--border);color:var(--ink);display:inline-flex;align-items:center;gap:6px}
.chip.ok{border-color:rgba(0,229,196,.4);color:#9EEBDD}
.chip.ok::before{content:"";width:5px;height:5px;border-radius:50%;background:var(--teal);box-shadow:0 0 7px rgba(0,229,196,.9)}
.chip.warn{border-color:rgba(251,191,36,.45);color:#FCD777}
.chip.warn::before{content:"";width:5px;height:5px;border-radius:50%;background:var(--amber)}
.tile.flash{animation:flash 1.2s ease}
@keyframes flash{0%,100%{}30%{box-shadow:0 0 0 2px rgba(0,229,196,.5),0 0 30px rgba(0,229,196,.3)}}
.foot{font-family:var(--mono);font-size:10px;letter-spacing:.08em;color:var(--dim2);text-align:center;margin-top:38px;padding-top:18px;border-top:1px solid var(--border)}
.foot b{color:var(--teal2);font-weight:400}
@media print{body{-webkit-print-color-adjust:exact;print-color-adjust:exact}.atmo{display:none}.detail{max-height:none!important;opacity:1!important}.panel{break-inside:avoid}}
@media(max-width:760px){.thead{grid-template-columns:36px 1fr 44px 20px}.spark,.mstat{display:none}.plot{height:280px}}
"""

_JS = """
window.addEventListener('DOMContentLoaded',function(){
  requestAnimationFrame(function(){
    document.body.classList.add('ready');
    document.querySelectorAll('.reveal').forEach(function(el,i){setTimeout(function(){el.classList.add('in')},70*i)});
    document.querySelectorAll('.node').forEach(function(el,i){setTimeout(function(){el.classList.add('in')},380+55*i)});
  });
  document.querySelectorAll('.thead').forEach(function(h){h.addEventListener('click',function(){h.parentElement.classList.toggle('open')})});
  var tip=document.getElementById('tip');
  document.querySelectorAll('.node').forEach(function(n){
    n.addEventListener('mousemove',function(e){tip.innerHTML=n.dataset.tip;tip.style.opacity=1;tip.style.left=e.clientX+'px';tip.style.top=e.clientY+'px'});
    n.addEventListener('mouseleave',function(){tip.style.opacity=0});
    if(n.classList.contains('on')) n.addEventListener('click',function(){
      var t=document.getElementById('tile-'+n.dataset.fid);
      if(t){t.classList.add('open');t.scrollIntoView({behavior:'smooth',block:'center'});t.classList.remove('flash');void t.offsetWidth;t.classList.add('flash')}
    });
  });
});
"""

def _corners():
    return '<span class="corner tl"></span><span class="corner tr"></span><span class="corner bl"></span><span class="corner br"></span>'

def _spark(vals, w=130, h=34):
    if not vals or len(vals) < 2: return ""
    wealth=[]; c=1.0
    for v in vals: c*=(1+v); wealth.append(c)
    lo=min(wealth); hi=max(wealth); rng=(hi-lo) or 1.0; n=len(wealth)
    pts=[f"{i/(n-1)*w:.1f},{h-(y-lo)/rng*(h-4)-2:.1f}" for i,y in enumerate(wealth)]
    up = wealth[-1] >= wealth[0]
    col = "#7FE9CE" if up else "#F97070"
    area = f"0,{h} " + " ".join(pts) + f" {w},{h}"
    return (f'<svg class="spark" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
            f'<defs><linearGradient id="sg{n}" x1="0" x2="0" y1="0" y2="1">'
            f'<stop offset="0" stop-color="{col}" stop-opacity=".28"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient></defs>'
            f'<polygon points="{area}" fill="url(#sg{n})"/>'
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" stroke-width="1.6" vector-effect="non-scaling-stroke"/></svg>')

def _dial(pct):
    r=15.5; circ=2*math.pi*r; off=circ*(1-max(0.04,min(1,pct)))
    return (f'<div class="dial-wrap"><svg class="dial" viewBox="0 0 40 40">'
            f'<circle class="track" cx="20" cy="20" r="{r}"/>'
            f'<circle class="val" cx="20" cy="20" r="{r}" style="--c:{circ:.1f};--off:{off:.1f}"/></svg>'
            f'<span>{round(pct*100)}</span></div>')

def render_html(memo, ctx=None):
    e=html.escape; a=memo.audit
    sl=memo.shortlist
    scores=[s.score for s in sl] or [0.0]; smin,smax=min(scores),max(scores)
    def norm(s): return 1.0 if smax==smin else (s-smin)/(smax-smin)
    ranks={s.fund_id:s.rank for s in sl}
    series = (ctx.series_by_fund if ctx else {}) or {}
    mbf = (ctx.metrics_by_fund if ctx else {s.fund_id:s.metrics for s in sl})

    # header
    head=(f'<div class="top reveal"><div class="brand"><div class="logo"></div>'
          f'<div><div class="wm">EQUI</div><div class="sub">Allocator Memo Builder</div></div></div>'
          f'<div class="hstat"><span class="tag model">{e(memo.generated_by)}</span>'
          f'<span class="vbadge"><i></i>{a.get("verified_count",0)} / {a.get("claim_count",0)} verified</span></div></div>'
          f'<div class="doctitle reveal">Investment Committee Memo</div>'
          f'<div class="mandate reveal">MANDATE · <b>{e(memo.mandate)}</b></div>')

    # recommendation
    rec=memo.sections[0] if memo.sections else None
    top=sl[0] if sl else None
    pick=""
    if top:
        pick=(f'<div class="pick"><div><div class="pin">◆ Primary</div>'
              f'<div class="pn">{e(top.name)}</div></div><div class="ps">{e(top.strategy)}<br>rank 01 · score {top.score:.2f}</div></div>')
    hero=(f'<section class="panel rec reveal">{_corners()}<div class="lbl">Recommendation</div>'
          f'<p class="lead">{e(rec.body) if rec else ""}</p>{pick}</section>') if rec else ""

    # risk/return map (all funds; shortlist bright)
    plot_funds=[(fid,m) for fid,m in mbf.items() if m.get("ann_vol") is not None and m.get("ann_return") is not None]
    nodes=""
    if plot_funds:
        vols=[m["ann_vol"] for _,m in plot_funds]; rets=[m["ann_return"] for _,m in plot_funds]
        vmin,vmax=min(vols),max(vols); rmin,rmax=min(rets),max(rets)
        vr=(vmax-vmin) or 1; rr=(rmax-rmin) or 1
        for fid,m in plot_funds:
            x=10+(m["ann_vol"]-vmin)/vr*80; y=10+(m["ann_return"]-rmin)/rr*80
            f=ctx.get_fund(fid) if ctx else None
            nm=f.name if f else fid; strat=f.strategy if f else ""
            on=fid in ranks
            tip=(f"<div class='tn'>{e(nm)}</div><div class='ts'>{e(strat)}</div>"
                 f"return <b>{_pct(m.get('ann_return'))}</b> · vol <b>{_pct(m.get('ann_vol'))}</b> · sharpe <b>{_num(m.get('sharpe'))}</b>")
            if on:
                rk=ranks[fid]; cls=f'node on{" rank1" if rk==1 else ""}'
                inner=f'<span class="ring"></span><div class="dot">{rk:02d}</div>'
            else:
                cls='node excl'; inner='<div class="dot"></div>'
            nodes+=(f'<div class="{cls}" data-fid="{e(fid)}" data-tip="{tip}" '
                    f'style="left:{x:.1f}%;bottom:{y:.1f}%">{inner}</div>')
    the_map=(f'<section class="panel reveal">{_corners()}'
             f'<div class="lbl">Risk / Return Map <span class="hint">· click a node to open its brief</span></div>'
             f'<div class="plot"><div class="sweet"><span>◤ sweet spot</span></div>'
             f'<div class="ax y">Return →</div><div class="ax x">Risk (volatility) →</div>{nodes}</div>'
             f'<div class="legend"><span><i class="i-sl"></i>shortlisted</span>'
             f'<span><i class="i-ex"></i>considered · excluded by mandate</span></div></section>')

    # tiles (shortlist) with detail from per-fund sections (same order)
    fund_secs=memo.sections[1:]
    tiles=""
    for i,s in enumerate(sl):
        m=s.metrics; sec=fund_secs[i] if i<len(fund_secs) else None
        r1=" rank1" if s.rank==1 else ""
        vals=series.get(s.fund_id).values if series.get(s.fund_id) else []
        chips=""
        if sec:
            for c in sec.claims:
                k="ok" if c.verified else "warn"; src=e("; ".join(c.source_refs) or "no source")
                chips+=f'<span class="chip {k}" title="{src}">{e(c.text)}</span>'
        full=mbf.get(s.fund_id,{})
        cells="".join(f'<div class="cell"><b>{(_pct(full.get(k)) if k in _PCT else _num(full.get(k)))}</b><i>{k.replace("_"," ")}</i></div>' for k in METRIC_KEYS)
        detail=(f'<div class="detail"><div class="detail-in">'
                f'<p>{e(sec.body) if sec else ""}</p>'
                f'<div class="mgrid">{cells}</div>'
                f'<div class="src-lbl">Sources · verified against the metrics engine</div>'
                f'<div class="chips">{chips}</div></div></div>')
        head_row=(f'<div class="thead"><div class="med">{s.rank:02d}</div>'
                  f'<div><div class="tn">{e(s.name)}</div><div class="ts">{e(s.strategy)}</div></div>'
                  f'<div>{_spark(vals)}</div>'
                  f'<div class="mstat"><div class="m"><b class="{"pos" if (m.get("ann_return") or 0)>=0 else "neg"}">{_pct(m.get("ann_return"))}</b><i>return</i></div>'
                  f'<div class="m"><b>{_num(m.get("sharpe"))}</b><i>sharpe</i></div>'
                  f'<div class="m"><b class="neg">{_pct(m.get("max_drawdown"))}</b><i>max dd</i></div></div>'
                  f'{_dial(0.5 + 0.5*norm(s.score))}<div class="chev"></div></div>')
        tiles+=f'<section class="panel tile reveal{r1}" id="tile-{e(s.fund_id)}">{_corners()}{head_row}{detail}</section>'
    tiles_block=f'<div class="tiles-lbl">Shortlist · {len(sl)} funds <span style="font-family:var(--mono);font-size:9px;letter-spacing:.1em;color:var(--dim2)">· click to expand</span></div>{tiles}'

    foot=('<div class="foot reveal">ALLOCATORMEMOBUILDER · every figure traces to a <b>source row + formula</b> · '
          'the model narrates, it never computes · print to PDF from your browser</div>')

    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(memo.title)}</title>'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Electrolize&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
            f'<style>{_CSS}</style></head><body>'
            '<div class="atmo"><div class="grid"></div><div class="sweep"></div></div><div id="tip"></div>'
            f'<div class="wrap">{head}{hero}{the_map}{tiles_block}{foot}</div>'
            f'<script>{_JS}</script></body></html>')

def write_html(memo, path, ctx=None):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(render_html(memo, ctx)); return p

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
    paths={"md":write_markdown(memo,Path(outdir)/"memo.md"),"json":write_json(memo,Path(outdir)/"memo.json"),"html":write_html(memo,Path(outdir)/"memo.html",ctx)}
    if ctx is not None: paths["xlsx"]=write_xlsx(memo,ctx,Path(outdir)/"memo.xlsx")
    return paths
