from __future__ import annotations
import html, json, math
from pathlib import Path
from .memo import render_markdown
from .metrics import METRIC_KEYS
from .scoring import DIRECTION, DEFAULT_WEIGHTS
from .models import Memo

_PCT={"ann_return","ann_vol","max_drawdown","downside_dev","alpha","tracking_error","hit_rate"}
def _pct(x): return "—" if x is None else f"{x*100:.1f}%"
def _num(x): return "—" if x is None else f"{x:.2f}"

def write_markdown(memo, path):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(render_markdown(memo));return p
def write_json(memo, path):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(memo.model_dump_json(indent=2));return p

_CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
:root{
 --bg:#0D0F13;--panel:#141821;--panel2:#191E28;--border:#232A36;--border2:#2E3745;
 --ink:#D7DCE4;--ink2:#AEB6C2;--ink-hi:#FFFFFF;--dim:#788393;--dim2:#4A5464;--on-accent:#F6F9FB;
 --accent:#5E8CA8;--accent2:#84AEC8;--accent-dim:#39515F;
 --accent-warm:#B79363;--accent-warm2:#CDAD7C;
 --gain:#6E9E82;--loss:#C0736A;
 --g2:#98A1AE;--g3:#6E7889;--g4:#525C6B;
 --glass:rgba(13,15,19,.6);--glass2:rgba(13,15,19,.92);--tipbg:rgba(13,15,19,.97);
 --grid:rgba(35,42,54,.5);--atmo:rgba(94,140,168,.05);--sweet:rgba(94,140,168,.07);
 --accent-soft:rgba(94,140,168,.18);--accent-glow:rgba(94,140,168,.55);--accent-line:rgba(94,140,168,.5);
 --warm-line:rgba(183,147,99,.6);--warm-soft:rgba(183,147,99,.16);
 --loss-line:rgba(192,115,106,.55);--loss-soft:rgba(192,115,106,.08);--loss-bd:rgba(192,115,106,.4);--gain-bd:rgba(110,158,130,.4);
 --seg-div:rgba(13,15,19,.55);
 --seg-a:#39414D;--seg-b:#9BA5B2;--segw-a:#33505F;--segw-b:#9DC4DA;
 --traj1:#C2CAD4;--traj2:#98A1AE;--traj3:#6E7889;--traj4:#525C6B;
 --winface1:#2A3F4D;--winface2:#1A2A34;--shadow:rgba(0,0,0,.5);
 --glass-fill:rgba(24,29,39,.5);--glass-bd:rgba(255,255,255,.10);--glass-hi:rgba(255,255,255,.07);
 --sans:'Inter',system-ui,sans-serif;--mono:'JetBrains Mono',ui-monospace,monospace;
}
:root[data-theme=light]{
 --bg:#EAE7DF;--panel:#F6F4EF;--panel2:#FCFBF7;--border:#DBD6CB;--border2:#C8C2B4;
 --ink:#24272C;--ink2:#4B515A;--ink-hi:#16191E;--dim:#6E727A;--dim2:#A49E90;--on-accent:#F6F9FB;
 --accent:#4E82A0;--accent2:#2C5872;--accent-dim:#B7CDDA;
 --accent-warm:#8A6A34;--accent-warm2:#6F5326;
 --gain:#3E7A59;--loss:#AE5148;
 --g2:#8A93A0;--g3:#6E7889;--g4:#525C6B;
 --glass:rgba(246,244,239,.78);--glass2:rgba(255,255,255,.94);--tipbg:rgba(255,255,255,.97);
 --grid:rgba(90,86,74,.10);--atmo:rgba(78,130,160,.06);--sweet:rgba(78,130,160,.08);
 --accent-soft:rgba(78,130,160,.16);--accent-glow:rgba(78,130,160,.30);--accent-line:rgba(78,130,160,.55);
 --warm-line:rgba(138,106,52,.55);--warm-soft:rgba(138,106,52,.14);
 --loss-line:rgba(174,81,72,.5);--loss-soft:rgba(174,81,72,.08);--loss-bd:rgba(174,81,72,.4);--gain-bd:rgba(62,122,89,.4);
 --seg-div:rgba(255,255,255,.7);
 --seg-a:#C6CBD2;--seg-b:#59626E;--segw-a:#A8C6D8;--segw-b:#2C5872;
 --traj1:#565E6A;--traj2:#7B828E;--traj3:#9BA1AB;--traj4:#BDC1C8;
 --winface1:#D3E2EC;--winface2:#B7D0DD;--shadow:rgba(70,64,52,.16);
 --glass-fill:rgba(255,255,255,.5);--glass-bd:rgba(30,35,45,.12);--glass-hi:rgba(255,255,255,.75);
}
html{transition:background .4s ease}
.hdr,.rail,.pane,.side,.node .dot,.wtrack,.chip,#drawer,.gate,.tag,.vbadge{transition:background .4s ease,border-color .4s ease,color .4s ease}
html,body{height:100%;margin:0;overflow:hidden;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:14px;-webkit-font-smoothing:antialiased;letter-spacing:-.005em}
.app{position:fixed;inset:0;display:grid;grid-template-rows:auto 1fr auto;z-index:1}
.atmo{position:fixed;inset:0;z-index:0;pointer-events:none;background:radial-gradient(1200px 800px at 30% 30%,var(--atmo),transparent 60%)}
.atmo .grid{position:absolute;inset:0;opacity:.5;background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);background-size:56px 56px;-webkit-mask-image:radial-gradient(1200px 800px at 35% 42%,#000,transparent 80%);mask-image:radial-gradient(1200px 800px at 35% 42%,#000,transparent 80%)}
.mono{font-family:var(--mono)}
.lbl{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}

/* header */
.hdr{display:flex;align-items:center;gap:16px;padding:13px 22px;border-bottom:1px solid var(--border);flex:none;background:var(--glass)}
.brand{display:flex;align-items:center;gap:10px}
.logo{width:26px;height:26px;flex:none;border:1px solid var(--border2);position:relative;border-radius:3px}
.logo::after{content:"";position:absolute;inset:7px;border:1.5px solid var(--accent);border-radius:50%}
.wm{font-weight:700;font-size:15px;letter-spacing:.18em;color:var(--ink-hi)}
.theme{position:relative;display:inline-flex;align-items:center;width:54px;height:24px;margin-left:6px;border:1px solid var(--border2);border-radius:20px;cursor:pointer;background:var(--panel2);flex:none;user-select:none;transition:border-color .25s}
.theme:hover{border-color:var(--accent-dim)}
.theme .tg{flex:1;display:grid;place-items:center;font-size:11px;z-index:2;color:var(--dim);transition:color .35s;line-height:1}
.theme .knob{position:absolute;top:2px;left:2px;width:24px;height:18px;border-radius:12px;background:var(--accent-dim);transition:transform .35s cubic-bezier(.3,.9,.3,1),background .35s;z-index:1}
.theme .tg-d{color:var(--accent2)}
:root[data-theme=light] .theme .knob{transform:translateX(26px)}
:root[data-theme=light] .theme .tg-d{color:var(--dim)}
:root[data-theme=light] .theme .tg-l{color:var(--accent2)}
.hdr .vwrap{flex:1;min-width:0}
.hdr .vpre{font-family:var(--mono);font-size:8.5px;letter-spacing:.22em;color:var(--dim2);text-transform:uppercase}
.hdr .vtext{font-weight:600;font-size:16px;color:var(--ink-hi);letter-spacing:-.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:1.2}
.hdr .vtext b{color:var(--accent2);font-weight:600}
.hdr .right{display:flex;gap:8px;flex:none}
.tag{font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);border:1px solid var(--border2);padding:5px 9px;border-radius:3px}
.vbadge{font-family:var(--mono);font-size:9px;letter-spacing:.12em;color:var(--gain);border:1px solid var(--gain-bd);padding:5px 9px;display:inline-flex;align-items:center;gap:6px;text-transform:uppercase;border-radius:3px}
.vbadge i{width:5px;height:5px;border-radius:50%;background:var(--gain)}

/* body grid */
.mid{display:grid;grid-template-columns:1fr 380px;min-height:0}
.stage{position:relative;overflow:hidden}
.side{border-left:1px solid var(--border);display:grid;grid-template-rows:1fr 1fr;min-height:0;position:relative}
/* intro pane — fills the side with the decision framework during universe/screening */
#intropane{position:absolute;inset:0;z-index:5;background:var(--panel);padding:20px 20px;display:flex;flex-direction:column;opacity:0;transition:opacity .7s;overflow:hidden}
#intropane.in{opacity:1}
#intropane.out{opacity:0;pointer-events:none}
.ip-h{font-weight:600;font-size:15px;color:var(--ink);letter-spacing:-.01em}
.ip-s{font-family:var(--mono);font-size:8.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--dim2);margin-top:3px}
.ip-lbl{font-family:var(--mono);font-size:8px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent2);margin:18px 0 9px;padding-bottom:6px;border-bottom:1px solid var(--border)}
.ipg{display:flex;align-items:flex-start;gap:9px;padding:7px 0;opacity:0;transform:translateX(8px);transition:opacity .5s,transform .5s}
.ipg.in{opacity:1;transform:none}
.ipg .k{font-family:var(--mono);font-size:9px;letter-spacing:.08em;text-transform:uppercase;color:var(--loss);border:1px solid var(--loss-bd);border-radius:3px;padding:3px 6px;white-space:nowrap;flex:none;margin-top:1px}
.ipg .d{font-size:12px;color:var(--ink2);line-height:1.4}
.ipw{display:grid;grid-template-columns:74px 1fr 34px;gap:9px;align-items:center;margin:8px 0;opacity:0;transform:translateX(8px);transition:opacity .5s,transform .5s}
.ipw.in{opacity:1;transform:none}
.ipw .wl{font-family:var(--mono);font-size:9.5px;letter-spacing:.04em;text-transform:uppercase;color:var(--ink2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ipw .wb{position:relative;height:7px;border-radius:4px;background:var(--panel2);border:1px solid var(--border);overflow:hidden}
.ipw .wb i{position:absolute;left:0;top:0;bottom:0;width:0;border-radius:4px;transition:width .8s cubic-bezier(.3,.85,.3,1)}
.ipw .wp{font-family:var(--mono);font-size:10px;color:var(--ink);text-align:right}
#ip-tally{margin-top:auto;display:flex;gap:0;border:1px solid var(--border);border-radius:6px;overflow:hidden}
#ip-tally .tc{flex:1;text-align:center;padding:11px 6px;background:var(--panel2)}
#ip-tally .tc+.tc{border-left:1px solid var(--border)}
#ip-tally .tc b{display:block;font-family:var(--mono);font-size:20px;color:var(--ink);line-height:1;transition:color .4s}
#ip-tally .tc.hot b{color:var(--accent2)}
#ip-tally .tc.red b{color:var(--loss)}
#ip-tally .tc i{display:block;font-family:var(--mono);font-size:7.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim2);font-style:normal;margin-top:6px}
.pane{padding:16px 18px;min-height:0;display:flex;flex-direction:column;opacity:0;transition:opacity .6s}
.pane.in{opacity:1}
.pane+.pane{border-top:1px solid var(--border)}
.pane .head{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:12px}
.pane .head .t{font-weight:600;font-size:13px;color:var(--ink)}
.pane .head .s{font-family:var(--mono);font-size:8.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim2)}

/* field */
#field{position:absolute;inset:26px 30px 22px 34px}
.ax{position:absolute;font-family:var(--mono);font-size:8.5px;letter-spacing:.16em;color:var(--dim2);text-transform:uppercase}
.ax.x{bottom:-2px;right:0}.ax.y{top:0;left:-6px;writing-mode:vertical-lr}
.sweetz{position:absolute;left:0;top:0;width:40%;height:44%;background:linear-gradient(135deg,var(--sweet),transparent 62%);opacity:0;transition:opacity 1s}
.sweetz.on{opacity:1}
.sweetz span{position:absolute;left:10px;top:8px;font-family:var(--mono);font-size:8px;letter-spacing:.16em;color:var(--accent-dim);text-transform:uppercase}
/* gate chips */
.gates{position:absolute;top:-4px;left:0;display:flex;gap:8px;opacity:0;transition:opacity .5s}
.gates.on{opacity:1}
.gate{font-family:var(--mono);font-size:8.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);border:1px solid var(--border2);padding:4px 8px;border-radius:3px;background:var(--panel)}
.gate.act{color:var(--accent2);border-color:var(--accent-dim)}
/* nodes — larger, information-bearing tokens */
.node{position:absolute;transform:translate(-50%,50%) scale(0);z-index:3;transition:left 1.15s cubic-bezier(.3,.85,.3,1),bottom 1.15s cubic-bezier(.3,.85,.3,1),transform .6s cubic-bezier(.3,1.2,.4,1),opacity .6s,filter .6s}
.node.shown{transform:translate(-50%,50%) scale(1)}
.node .dot{width:17px;height:17px;border-radius:50%;background:var(--panel2);border:1.5px solid var(--ink2);display:grid;place-items:center;transition:width .5s cubic-bezier(.3,1.2,.4,1),height .5s cubic-bezier(.3,1.2,.4,1),border-color .5s,box-shadow .5s,background .5s;position:relative}
.node.cand{cursor:pointer}.node.cand:hover .dot{border-color:var(--accent2)}
.node.win .dot,.node.locked .dot{border-color:var(--accent);background:radial-gradient(circle at 38% 34%,var(--winface1),var(--winface2));box-shadow:0 0 0 1px var(--accent-soft),0 0 24px -3px var(--accent-glow)}
/* focus — bring the active item forward inside a glass hero panel */
.node.focus{z-index:10}
.node.focus .dot{width:28px;height:28px;border-color:var(--accent2);box-shadow:0 0 0 7px var(--accent-soft),0 0 30px -4px var(--accent-glow)}
.node .glass{position:absolute;left:50%;top:calc(50% + 12px);width:208px;height:150px;transform:translate(-50%,-50%) scale(.82);opacity:0;border-radius:16px;background:var(--glass-fill);border:1px solid var(--glass-bd);-webkit-backdrop-filter:blur(11px) saturate(1.15);backdrop-filter:blur(11px) saturate(1.15);box-shadow:0 24px 58px -14px var(--shadow),0 0 26px -10px var(--accent-glow),inset 0 1px 0 var(--glass-hi);pointer-events:none;z-index:-1;transition:opacity .5s,transform .55s cubic-bezier(.3,1.2,.4,1),border-color .4s,box-shadow .4s}
.node.focus .glass{opacity:1;transform:translate(-50%,-50%) scale(1)}
.node.reject .glass,.node.cutfocus .glass{border-color:var(--loss-bd);box-shadow:0 24px 58px -14px var(--shadow),0 0 30px -8px var(--loss),inset 0 1px 0 var(--glass-hi)}
.node.dimmed{opacity:.28;filter:saturate(.6)}
.node.cutout{opacity:.22;filter:grayscale(.7)}
body.screening .node.cand{opacity:.22;transition:opacity .55s}
body.screening .node.cand.focus{opacity:1}
body.screening .node.cand.gone{opacity:0}
.node.gone{opacity:0!important}
/* card label under the dot */
.node .card{position:absolute;left:50%;top:calc(100% + 9px);transform:translate(-50%,4px);text-align:center;white-space:nowrap;pointer-events:none;opacity:0;transition:opacity .5s,transform .5s cubic-bezier(.3,1.1,.4,1)}
.node.labeled .card{opacity:1;transform:translate(-50%,0)}
.node .card .nm{font-weight:600;font-size:12.5px;color:var(--ink);letter-spacing:-.01em;line-height:1.15}
.node .card .nm .nfull{display:none}.node.focus .card .nm .nfull{display:inline}
.node.focus .card .nm .nshort{display:none}
.node.win .card .nm,.node.leader .card .nm{color:var(--accent2)}
.node .card .sub{font-family:var(--mono);font-size:8px;letter-spacing:.11em;text-transform:uppercase;color:var(--dim);margin-top:2px}
.node .card .stat{font-family:var(--mono);font-size:9px;color:var(--ink2);margin-top:3px;max-height:0;opacity:0;overflow:hidden;transition:opacity .45s,max-height .45s}
.node.showstat .card .stat,.node.focus .card .stat{opacity:1;max-height:16px}
.node .card .stat b{color:var(--ink)}
/* corner brackets wrap the whole panel */
.lock{position:absolute;left:50%;top:calc(50% + 12px);width:226px;height:168px;transform:translate(-50%,-50%) scale(1.06);opacity:0;transition:opacity .4s,transform .5s cubic-bezier(.3,1.3,.4,1);pointer-events:none}
.node.locked .lock{opacity:1;transform:translate(-50%,-50%) scale(1)}
.lock i{position:absolute;width:14px;height:14px;border:1.5px solid var(--accent2)}
.lock .a{top:0;left:0;border-right:0;border-bottom:0}.lock .b{top:0;right:0;border-left:0;border-bottom:0}.lock .c{bottom:0;left:0;border-right:0;border-top:0}.lock .d{bottom:0;right:0;border-left:0;border-top:0}
/* exclusion header — lives inside the panel */
.node .stamp{position:absolute;left:50%;top:-56px;transform:translate(-50%,8px);opacity:0;transition:opacity .5s,transform .55s cubic-bezier(.3,1.25,.4,1);pointer-events:none;z-index:15;text-align:center}
.node.reject .stamp{opacity:1;transform:translate(-50%,0)}
.node .stamp .st{font-family:var(--mono);font-size:9.5px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--on-accent);background:var(--loss);border-radius:3px;padding:4px 9px;display:inline-block;box-shadow:0 8px 20px var(--shadow)}
.node .stamp .sr{display:block;margin-top:5px;font-family:var(--mono);font-size:9px;color:var(--loss);letter-spacing:.02em}
.node.reject .dot{border-color:var(--loss);background:transparent;box-shadow:0 0 0 4px var(--loss-soft)}

/* chapter caption (bottom-left, refined) */
#chapter{position:absolute;left:34px;bottom:22px;pointer-events:none;z-index:12}
#chapter .c{opacity:0}
#chapter .c.in{animation:capIn 2.6s ease both}
@keyframes capIn{0%{opacity:0;transform:translateY(6px)}12%,78%{opacity:1;transform:none}100%{opacity:0}}
#chapter .n{font-family:var(--mono);font-size:9px;letter-spacing:.24em;color:var(--accent2);text-transform:uppercase}
#chapter .t{font-weight:700;font-size:26px;color:var(--ink-hi);letter-spacing:-.01em;margin-top:5px}
#chapter .s{font-family:var(--mono);font-size:10px;color:var(--dim);margin-top:4px;letter-spacing:.02em}

/* score bars (why panel) */
.sbar{display:grid;grid-template-columns:20px 1fr auto;gap:9px;align-items:center;margin:7px 0;opacity:0;transform:translateX(8px);transition:.5s}
.sbar.in{opacity:1;transform:none}
.sbar .r{font-family:var(--mono);font-size:11px;color:var(--dim2);text-align:right}
.sbar.win .r{color:var(--accent2)}
.sbar .track{position:relative;height:22px;background:var(--panel2);border:1px solid var(--border);border-radius:3px;overflow:hidden}
.sbar .fill{position:absolute;left:0;top:0;bottom:0;width:0;background:linear-gradient(90deg,var(--g4),var(--g2));transition:width 1s cubic-bezier(.3,.85,.3,1)}
.sbar.win .fill{background:linear-gradient(90deg,var(--accent-dim),var(--accent))}
.sbar .nm{position:absolute;left:8px;top:50%;transform:translateY(-50%);font-size:11px;font-weight:600;color:var(--ink-hi);white-space:nowrap;z-index:2}
.sbar .sc{font-family:var(--mono);font-size:11px;color:var(--ink2)}
.why-note{margin-top:auto;padding-top:10px;font-family:var(--mono);font-size:9.5px;line-height:1.6;color:var(--dim)}
.why-note b{color:var(--accent2)}

/* trajectory */
#trajwrap{position:relative;flex:1;min-height:0}
#traj{width:100%;height:100%;display:block}
.tt{position:absolute;font-family:var(--mono);font-size:9px;padding:1px 5px;transform:translateY(-50%);white-space:nowrap;background:var(--glass2);border-radius:2px}

/* rail */
.rail{display:flex;align-items:center;gap:10px;padding:10px 22px;border-top:1px solid var(--border);flex:none;background:var(--glass);opacity:0;transition:opacity .6s}
.rail.in{opacity:1}
.rail .rl{font-family:var(--mono);font-size:8.5px;letter-spacing:.2em;color:var(--dim2);text-transform:uppercase}
.chips{display:flex;gap:7px;flex:1;overflow:hidden}
.chip{display:flex;align-items:center;gap:8px;padding:6px 11px 6px 9px;border:1px solid var(--border);background:var(--panel);cursor:pointer;transition:.2s;border-radius:4px}
.chip:hover{border-color:var(--accent);background:var(--accent);transform:translateY(-1px);box-shadow:0 6px 16px -6px var(--accent-glow)}
.chip:hover .n,.chip:hover .nm,.chip:hover .rt{color:var(--on-accent)}
.chip.r1{border-color:var(--accent-dim)}
.chip .n{font-family:var(--mono);font-weight:600;font-size:11px;color:var(--dim2)}.chip.r1 .n{color:var(--accent2)}
.chip .nm{font-weight:600;font-size:12.5px;color:var(--ink-hi)}
.chip .rt{font-family:var(--mono);font-size:10.5px;color:var(--ink2)}

/* drawer */
#drawer{position:fixed;top:0;right:0;bottom:0;width:min(430px,90vw);background:var(--panel);border-left:1px solid var(--border2);z-index:40;transform:translateX(100%);transition:transform .38s cubic-bezier(.3,.9,.3,1);box-shadow:-16px 0 50px rgba(0,0,0,.5);overflow-y:auto;padding:22px}
#drawer.open{transform:none}
#drawer .x{position:absolute;top:15px;right:17px;font-family:var(--mono);font-size:10.5px;color:var(--dim);cursor:pointer;letter-spacing:.08em}#drawer .x:hover{color:var(--accent2)}
.d-pre{font-family:var(--mono);font-size:8.5px;letter-spacing:.2em;color:var(--accent2);text-transform:uppercase;margin-bottom:5px}
.d-name{font-weight:700;font-size:22px;color:var(--ink-hi);letter-spacing:-.01em}
.d-strat{font-family:var(--mono);font-size:9px;letter-spacing:.08em;text-transform:uppercase;color:var(--dim);margin-bottom:15px}
.d-p{color:var(--ink2);font-size:13px;line-height:1.6}
.mgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--border);border:1px solid var(--border);margin:15px 0;border-radius:4px;overflow:hidden}
.mgrid .cell{background:var(--panel2);padding:9px 8px;text-align:center}.mgrid .cell b{display:block;font-family:var(--mono);font-size:13px;color:var(--ink)}.mgrid .cell i{font-family:var(--mono);font-size:7px;letter-spacing:.06em;text-transform:uppercase;color:var(--dim2);font-style:normal}
.src-lbl{font-family:var(--mono);font-size:8px;letter-spacing:.16em;text-transform:uppercase;color:var(--dim2);margin:14px 0 9px}
.chipx{display:flex;flex-wrap:wrap;gap:6px}.chipx span{font-family:var(--mono);font-size:9.5px;padding:5px 8px;background:var(--panel2);border:1px solid var(--border);color:var(--ink2);display:inline-flex;align-items:center;gap:5px;border-radius:3px}
.chipx .ok::before{content:"✓";color:var(--accent2)}.chipx .warn::before{content:"!";color:var(--loss)}

#tip{position:fixed;z-index:60;pointer-events:none;opacity:0;transform:translate(13px,-50%);transition:opacity .15s;background:var(--tipbg);border:1px solid var(--border2);padding:8px 11px;font-family:var(--mono);font-size:11px;white-space:nowrap;box-shadow:0 8px 24px var(--shadow);border-radius:4px}
#tip .tn{color:var(--ink-hi);font-weight:600;font-size:12px;font-family:var(--sans)}#tip .ts{color:var(--dim);font-size:8.5px;text-transform:uppercase;letter-spacing:.08em}#tip b{color:var(--accent2)}
#skip{position:fixed;bottom:64px;right:22px;z-index:30;font-family:var(--mono);font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim);border:1px solid var(--border2);padding:6px 11px;cursor:pointer;background:var(--glass);border-radius:3px}
#skip:hover{color:var(--accent2)}body.settled #skip{display:none}

.node.leader .dot{box-shadow:0 0 0 2px var(--accent),0 0 22px -2px var(--accent-glow)}
#weighticker{font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-bottom:9px;min-height:12px}
#weighticker b{color:var(--accent2)}
#weighlegend{display:flex;flex-wrap:wrap;gap:6px 11px;margin-bottom:10px;opacity:0;transition:opacity .5s}
#weighlegend.in{opacity:1}
#weighlegend span{display:inline-flex;align-items:center;gap:5px;font-family:var(--mono);font-size:8px;letter-spacing:.09em;text-transform:uppercase;color:var(--dim2)}
#weighlegend i{width:9px;height:6px;border-radius:1px;display:inline-block}
#weighlegend .neg i{background:var(--loss)}
#scorebars{position:relative;height:190px}
.wrow{position:absolute;left:0;right:0;height:26px;display:grid;grid-template-columns:20px 52px 1fr 44px;gap:7px;align-items:center;transition:top .55s cubic-bezier(.3,.85,.3,1);opacity:0}
.wrow.in{opacity:1}
.wrk{font-family:var(--mono);font-size:12px;font-weight:600;color:var(--dim2);text-align:center;transition:color .4s,transform .4s cubic-bezier(.3,1.3,.4,1)}
.wrow.rk1 .wrk{color:var(--accent2);transform:scale(1.2)}
.wrow .wn{font-size:12px;font-weight:600;color:var(--ink2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.wrow.win .wn,.wrow.rk1 .wn{color:var(--accent2)}
/* shortlist cut line — the tier boundary */
.wcut{position:absolute;left:0;right:0;height:0;border-top:1px dashed var(--loss-line);transition:top .55s cubic-bezier(.3,.85,.3,1);pointer-events:none;z-index:4}
.wcut span{position:absolute;right:0;top:-7px;font-family:var(--mono);font-size:7.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--loss);background:var(--panel);padding:0 5px}
.wtrack{position:relative;height:19px;background:var(--panel2);border:1px solid var(--border);border-radius:3px;overflow:hidden}
.wzero{position:absolute;top:0;bottom:0;width:1px;background:var(--border2);z-index:1}
.wseg{position:absolute;top:1px;bottom:1px;opacity:0;border-right:1px solid var(--seg-div);transition:opacity .4s cubic-bezier(.3,.85,.3,1)}
.wseg.in{opacity:1}
.wseg.neg{border-right:0;border-left:1px solid var(--seg-div)}
.wseg.pulse{box-shadow:0 0 0 1px var(--accent2)}
.wrow.lead .wtrack{box-shadow:0 0 0 1px var(--accent-dim)}
.wrow.flip .wtrack{box-shadow:0 0 0 1px var(--accent2),0 0 14px -3px var(--accent)}
.wsc{font-family:var(--mono);font-size:11px;color:var(--ink2);text-align:right}
.wrow.win .wsc{color:var(--accent2)}
#play{position:fixed;bottom:24px;right:24px;z-index:35;display:none;align-items:center;gap:9px;padding:10px 16px;border:1px solid var(--accent-dim);background:var(--glass2);color:var(--accent2);cursor:pointer;font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;border-radius:5px;transition:.2s}
#play::before{content:'\25B6';font-size:10px}
#play:hover{background:var(--accent-dim);color:var(--ink-hi);box-shadow:0 0 18px -5px var(--accent)}
body.settled #play{display:inline-flex}
/* screening visuals */
.gateline{position:absolute;top:0;bottom:-18px;width:0;border-left:1px dashed var(--loss-line);opacity:0;transition:opacity .5s;z-index:2}
.gateline.on{opacity:1}
.gateline span{position:absolute;top:2px;left:7px;font-family:var(--mono);font-size:8px;letter-spacing:.1em;color:var(--loss);text-transform:uppercase;white-space:nowrap}
.danger{position:absolute;top:0;bottom:0;right:0;opacity:0;transition:opacity .6s;z-index:1;background:linear-gradient(90deg,transparent,var(--loss-soft))}
.danger.on{opacity:1}
#counter{position:absolute;top:-2px;right:2px;font-family:var(--mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);opacity:0;transition:opacity .5s;z-index:3}
#counter.on{opacity:1}#counter b{color:var(--ink)}
/* field guides: benchmark anchor + risk-adjusted reference line */
#guides{position:absolute;inset:0;pointer-events:none;z-index:1;opacity:0;transition:opacity .9s}
#guides.on{opacity:1}
#benchray{position:absolute;height:0;border-top:1px dashed var(--warm-line);transform-origin:0 0;left:0;top:0;width:0}
#benchmk{position:absolute;transform:translate(-50%,50%);z-index:2}
#benchmk .dm{width:9px;height:9px;background:var(--panel2);border:1px solid var(--accent-warm);transform:rotate(45deg);box-shadow:0 0 0 3px var(--warm-soft)}
#benchmk .bl{position:absolute;left:50%;top:calc(100% + 7px);transform:translateX(-50%);white-space:nowrap;font-family:var(--mono);font-size:8px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim)}
#beatlbl{position:absolute;left:1.5%;top:3%;font-family:var(--mono);font-size:8px;letter-spacing:.11em;text-transform:uppercase;color:var(--accent-warm);max-width:118px;line-height:1.55}
/* ===== cinematic decision layer ===== */
/* focus vignette while scoring */
.stage::after{content:'';position:absolute;inset:0;pointer-events:none;z-index:4;opacity:0;transition:opacity 1s;background:radial-gradient(115% 88% at 46% 44%,transparent 44%,rgba(0,0,0,.34) 100%)}
body.scoring .stage::after{opacity:1}
:root[data-theme=light] .stage::after{background:radial-gradient(115% 88% at 46% 44%,transparent 46%,rgba(44,42,34,.12) 100%)}
/* per-factor response halo (behind the dot) */
.node .halo{position:absolute;inset:-6px;border-radius:50%;pointer-events:none;opacity:0;z-index:-1;transform:scale(.55);transition:transform .6s cubic-bezier(.3,1.05,.4,1),opacity .55s,background .4s}
/* cumulative leader: bright ring + crown */
.node .crown{position:absolute;left:50%;top:-46px;transform:translate(-50%,6px) scale(.8);opacity:0;transition:opacity .4s,transform .45s cubic-bezier(.3,1.3,.4,1);pointer-events:none;font-family:var(--mono);font-size:8px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent2);white-space:nowrap;display:flex;align-items:center;gap:5px;z-index:15}
.node .crown::before{content:'';width:0;height:0;border-left:3.5px solid transparent;border-right:3.5px solid transparent;border-bottom:5px solid var(--accent)}
.node.leader{opacity:1!important}
.node.leader .crown{opacity:1;transform:translate(-50%,0) scale(1)}
.node.leader .dot{box-shadow:0 0 0 2px var(--accent),0 0 22px -2px var(--accent-glow)}
/* reasoning tag anchored above a node */
.node .rtag{position:absolute;left:50%;bottom:calc(100% + 72px);transform:translate(-50%,7px);opacity:0;transition:opacity .4s,transform .45s cubic-bezier(.3,1.25,.4,1);pointer-events:none;white-space:nowrap;font-family:var(--mono);font-size:8.5px;letter-spacing:.02em;color:var(--ink);background:var(--glass2);border:1px solid var(--border2);border-radius:5px;padding:5px 9px;z-index:16;box-shadow:0 8px 22px var(--shadow)}
.node .rtag::after{content:'';position:absolute;left:50%;top:100%;transform:translateX(-50%);border:5px solid transparent;border-top-color:var(--border2)}
.node.rshow .rtag{opacity:1;transform:translate(-50%,0)}
.node .rtag b{color:var(--accent2)} .node .rtag.neg b{color:var(--loss)}
/* factor spotlight cue (top-center of field) */
#factorcue{position:absolute;left:50%;top:2px;transform:translateX(-50%) translateY(-10px);opacity:0;transition:opacity .5s,transform .5s cubic-bezier(.3,1.1,.4,1);z-index:13;display:flex;align-items:center;gap:11px;background:var(--glass2);border:1px solid var(--border2);border-radius:30px;padding:7px 15px 7px 12px;box-shadow:0 10px 26px var(--shadow)}
#factorcue.on{opacity:1;transform:translateX(-50%) translateY(0)}
#factorcue .fdot{width:10px;height:10px;border-radius:3px;flex:none}
#factorcue .fname{font-family:var(--mono);font-size:10px;letter-spacing:.13em;text-transform:uppercase;color:var(--ink)}
#factorcue .fwt{position:relative;width:56px;height:4px;border-radius:2px;background:var(--panel2);overflow:hidden}
#factorcue .fwt i{position:absolute;left:0;top:0;bottom:0;width:0;transition:width .55s cubic-bezier(.3,.85,.3,1)}
#factorcue .fpct{font-family:var(--mono);font-size:9px;letter-spacing:.06em;color:var(--dim)}
@media(max-width:900px){.mid{grid-template-columns:1fr}.side{display:none}.hdr .vtext{font-size:14px}}
"""

_JS = r"""
(function(){
var A=window.AMB;
function $(s,r){return (r||document).querySelector(s)}
function $$(s,r){return [].slice.call((r||document).querySelectorAll(s))}
function el(t,c){var e=document.createElement(t);if(c)e.className=c;return e}
function wait(ms){return new Promise(function(r){setTimeout(r,ms)})}
function pct(x){return x==null?'—':(x*100).toFixed(1)+'%'} function num(x){return x==null?'—':x.toFixed(2)}
function first(n){return n.split(' ')[0]}
function contenders(){return A.funds.filter(function(d){return d.eligible}).sort(function(a,b){return a.srank-b.srank})} // cleared the mandate (scored)
function shortlisted(){return A.funds.filter(function(d){return d.rank}).sort(function(a,b){return a.rank-b.rank})} // made the top-N
function rejects(){return A.funds.filter(function(d){return d.reason})} // failed the mandate
function survivors(){return contenders()} // scoring scene operates on the eligible set
function byId(id){return A.funds.filter(function(d){return d.id==id})[0]}
function weightFactors(){return Object.keys(A.weights).sort(function(a,b){return A.weights[b]-A.weights[a]})}
function hx(n){n=Math.max(0,Math.min(255,Math.round(n)));return ('0'+n.toString(16)).slice(-2)}
function mix(a,b,t){function p(c){return [parseInt(c.slice(1,3),16),parseInt(c.slice(3,5),16),parseInt(c.slice(5,7),16)]}var P=p(a),Q=p(b);return '#'+hx(P[0]+(Q[0]-P[0])*t)+hx(P[1]+(Q[1]-P[1])*t)+hx(P[2]+(Q[2]-P[2])*t)}
function cssv(n){return getComputedStyle(document.documentElement).getPropertyValue(n).trim()||'#888888'}
function segColor(i,win){var FN=weightFactors().length;var t=FN>1?(FN-1-i)/(FN-1):1;return win?mix(cssv('--segw-a'),cssv('--segw-b'),t):mix(cssv('--seg-a'),cssv('--seg-b'),t)}
function trajGrays(){return [cssv('--traj1'),cssv('--traj2'),cssv('--traj3'),cssv('--traj4')]}
var nodes={}, rows={}, segState={}, aborted=false, trajBuilt=false, ROWH=30, ZERO=30, UNIT=1;
function computeScale(){var sl=shortlisted();var fs=weightFactors();var mp=0,mn=0; // scale to the shortlist; an outscored cut fund may overflow (clipped)
  sl.forEach(function(d){var p=0,n=0;fs.forEach(function(k){var c=(d.comp[k]||0);if(c>=0)p+=c;else n+=-c});mp=Math.max(mp,p);mn=Math.max(mn,n)});
  UNIT=Math.min((96-ZERO)/(mp||1),(ZERO-4)/(mn||1));}
function buildLegend(){var h=$('#weighlegend');if(!h)return;var fs=weightFactors();
  h.innerHTML=fs.map(function(k,i){return "<span><i style='background:"+segColor(i,false)+"'></i>"+k.replace(/_/g,' ')+"</span>"}).join('')+"<span class='neg'><i></i>detracts</span>";
  h.classList.add('in');}

function stratShort(s){return (s||'').replace(/\b(Strategy|Fund|Global|Structured)\b/g,'').replace(/\s+/g,' ').trim()||s}
function buildField(){
  var f=$('#field');
  A.funds.forEach(function(d,i){
    var n=el('div','node cand');
    n.dataset.fid=d.id;n.__d=d;n.__i=i;
    n.dataset.tip="<div class='tn'>"+d.name+"</div><div class='ts'>"+d.strategy+"</div>return <b>"+pct(d.ret)+"</b> · vol <b>"+pct(d.vol)+"</b> · sharpe <b>"+num(d.sharpe)+"</b>";
    var glass=el('div','glass');
    var halo=el('div','halo');
    var lock=el('div','lock');['a','b','c','d'].forEach(function(k){lock.appendChild(el('i',k))});
    var stamp=el('div','stamp');var st=el('div','st');st.textContent='excluded';var sr=el('div','sr');stamp.appendChild(st);stamp.appendChild(sr);
    var crown=el('div','crown');crown.appendChild(document.createTextNode('leader'));
    var rtag=el('div','rtag');
    var dot=el('div','dot');
    var card=el('div','card');
    card.innerHTML="<div class='nm'><span class='nfull'>"+d.name+"</span><span class='nshort'>"+first(d.name)+"</span></div><div class='sub'>"+stratShort(d.strategy)+"</div><div class='stat'>ret <b>"+pct(d.ret)+"</b> · SR <b>"+num(d.sharpe)+"</b></div>";
    n.appendChild(glass);n.appendChild(halo);n.appendChild(lock);n.appendChild(stamp);n.appendChild(crown);n.appendChild(rtag);n.appendChild(dot);n.appendChild(card);
    n.style.left='50%';n.style.bottom='50%';f.appendChild(n);nodes[d.id]=n;
  });
  var g=$('#gates');A.gates.forEach(function(gt){var e=el('div','gate');e.textContent=gt.label+' · '+gt.detail;e.dataset.k=gt.label;g.appendChild(e)});
}
function updateCounter(lbl){var live=A.funds.filter(function(d){var n=nodes[d.id];return !n.classList.contains('gone')&&!n.classList.contains('cutout')}).length;var c=$('#counter');if(c)c.innerHTML=(lbl||'Candidates')+' · <b>'+String(live).padStart(2,'0')+'</b>';updateTally();}
function buildIntro(){
  var ip=$('#intropane');if(ip){ip.classList.add('in');ip.classList.remove('out')}
  var g=$('#ip-gates');if(g){g.innerHTML='';A.gates.forEach(function(gt,i){var r=el('div','ipg');r.innerHTML="<span class='k'>"+gt.label+"</span><span class='d'>"+gt.detail+"</span>";g.appendChild(r);setTimeout(function(){r.classList.add('in')},260+i*150)})}
  var w=$('#ip-weights');if(w){w.innerHTML='';var fs=weightFactors();var mx=Math.max.apply(null,fs.map(function(k){return A.weights[k]}));
    fs.forEach(function(k,i){var pctv=Math.round(A.weights[k]*100);var r=el('div','ipw');
      r.innerHTML="<span class='wl'>"+k.replace(/_/g,' ')+"</span><span class='wb'><i></i></span><span class='wp'>"+pctv+"%</span>";
      w.appendChild(r);var bar=$('.wb i',r);
      setTimeout(function(){r.classList.add('in');bar.style.background=segColor(i,false);bar.style.width=(A.weights[k]/mx*100).toFixed(0)+'%'},560+i*120)})}
  updateTally();
}
function updateTally(){var t=$('#ip-tally');if(!t)return;var gone=A.funds.filter(function(d){return nodes[d.id].classList.contains('gone')}).length;var uni=A.funds.length;var rem=uni-gone;
  t.innerHTML="<div class='tc'><b>"+uni+"</b><i>universe</i></div><div class='tc red'><b>"+gone+"</b><i>excluded</i></div><div class='tc hot'><b>"+rem+"</b><i>advancing</i></div>";}
function universePos(i){var cols=3;var r=Math.floor(i/cols),c=i%cols;
  var L=[26,50,74][c],B=[77,50,23][r];
  var jx=(((i*37)%7)-3)*1.5,jy=(((i*29)%7)-3)*1.3;
  return {x:L+jx,y:B+jy};}
function frontier(){buildGuides();$('#guides').classList.add('on');
  A.funds.forEach(function(d){var n=nodes[d.id];if(d.eligible){n.classList.add('ranked','showstat');n.style.left=d.xz+'%';n.style.bottom=d.yz+'%'}});}
function chapter(numv,ttl,sub){var c=$('#chapter');c.innerHTML="<div class='c'><div class='n'>"+numv+"</div><div class='t'>"+ttl+"</div><div class='s'>"+sub+"</div></div>";var card=$('.c',c);void card.offsetWidth;card.classList.add('in')}

function buildWeigh(){
  var host=$('#scorebars');host.innerHTML='';rows={};segState={};computeScale();buildLegend();
  var sl=survivors();
  sl.forEach(function(d,i){
    var row=el('div','wrow'+(d.rank==1?' win':'')+(i===0?' rk1':''));row.style.top=(i*ROWH)+'px';
    row.innerHTML="<div class='wrk'>"+(i+1)+"</div><div class='wn'>"+first(d.name)+"</div><div class='wtrack'><div class='wzero' style='left:"+ZERO+"%'></div></div><div class='wsc'>0.00</div>";
    host.appendChild(row);rows[d.id]=row;segState[d.id]={pos:ZERO,neg:ZERO,cum:0};
    setTimeout(function(){row.classList.add('in')},70*i);
  });
  if(A.nShort&&sl.length>A.nShort){var cl=el('div','wcut');cl.style.top=(A.nShort*ROWH-2)+'px';cl.innerHTML="<span>cut line · top "+A.nShort+" advance</span>";host.appendChild(cl);}
}
function setRanks(order){order.forEach(function(d,rk){var r=rows[d.id];if(!r)return;r.style.top=(rk*ROWH)+'px';var b=$('.wrk',r);if(b)b.textContent=(rk+1);r.classList.toggle('rk1',rk===0)})}
function addSeg(d,k,idx,animate){
  var st=segState[d.id];var c=(d.comp[k]||0);var r=rows[d.id];var tr=$('.wtrack',r);
  var seg=el('div','wseg'+(c<0?' neg':''));var w=Math.abs(c)*UNIT;
  if(c>=0){seg.style.left=st.pos+'%';seg.style.width=w+'%';seg.style.background=segColor(idx,d.rank==1);st.pos+=w;}
  else{st.neg-=w;seg.style.left=st.neg+'%';seg.style.width=w+'%';seg.style.background=cssv('--loss');}
  st.cum+=c;seg.dataset.k=k;tr.appendChild(seg);
  if(animate){if(d.rank==1)seg.classList.add('pulse');requestAnimationFrame(function(){seg.classList.add('in')});}
  else seg.classList.add('in');
  $('.wsc',r).textContent=(st.cum>=0?'+':'')+st.cum.toFixed(2);
  return seg;
}
/* ---- cinematic decision choreography (the graph tells the story) ---- */
function zAdj(d,k){return A.weights[k]?((d.comp[k]||0)/A.weights[k]):0} // direction-adjusted z-score
function factorCue(k,idx){var c=$('#factorcue');if(!c)return;var col=segColor(idx,false);
  $('.fdot',c).style.background=col;$('.fname',c).textContent=k.replace(/_/g,' ');
  var w=Math.round(A.weights[k]*100);$('.fpct',c).textContent=w+'%';var bar=$('.fwt i',c);bar.style.background=col;bar.style.width=Math.min(100,w*2.6)+'%';
  c.classList.add('on');}
function nodeRespond(k){survivors().forEach(function(d){var n=nodes[d.id];var z=zAdj(d,k);var mag=Math.max(-1.8,Math.min(1.8,z));
  var sc=(0.85+(mag+1.8)/3.6*2.15).toFixed(2);var op=(0.16+Math.abs(mag)/1.8*0.62).toFixed(2);
  var col=mag>=0?cssv('--accent'):cssv('--loss');var h=$('.halo',n);
  if(h){h.style.background='radial-gradient(circle,'+col+' 0%,transparent 66%)';h.style.transform='scale('+sc+')';h.style.opacity=op;}});}
function clearHalos(){A.funds.forEach(function(d){var h=$('.halo',nodes[d.id]);if(h){h.style.opacity='0';h.style.transform='scale(.55)'}})}
function setLeaderNode(id){A.funds.forEach(function(d){nodes[d.id].classList.remove('leader','focus')});if(id&&nodes[id])nodes[id].classList.add('leader','focus')}
function showRtag(id,htmlv,neg){var n=nodes[id];if(!n)return;var t=$('.rtag',n);if(!t)return;t.className='rtag'+(neg?' neg':'');t.innerHTML=htmlv;n.classList.add('rshow')}
function clearRtags(){A.funds.forEach(function(d){nodes[d.id].classList.remove('rshow')})}
async function runWeigh(){
  var sl=survivors();var factors=weightFactors();var prevLead=null;
  for(var fi=0;fi<factors.length;fi++){ if(aborted)return;
    var k=factors[fi],idx=fi;
    // beat 1 — spotlight the factor; every survivor's halo shows how it scores on it
    factorCue(k,idx);nodeRespond(k);
    $('#weighticker').innerHTML="Weighing · <b>"+k.replace(/_/g,' ')+"</b> · "+Math.round(A.weights[k]*100)+"%";
    await wait(600); if(aborted)return;
    // beat 2 — fold it into the running score; re-rank; move the crown
    sl.forEach(function(d){addSeg(d,k,idx,true)});
    var order=sl.slice().sort(function(a,b){return segState[b.id].cum-segState[a.id].cum});
    setRanks(order);
    var leadId=order[0].id;setLeaderNode(leadId);
    Object.keys(rows).forEach(function(id){rows[id].classList.toggle('lead',id==leadId)});
    var flipped=(prevLead!==null&&leadId!==prevLead);
    if(flipped){showRtag(leadId,"<b>"+k.replace(/_/g,' ')+"</b> ▸ takes the lead",false);rows[leadId].classList.add('flip');
      $('#weighticker').innerHTML="<b>"+k.replace(/_/g,' ')+"</b> tips <b>"+first(byId(leadId).name)+"</b> ahead";}
    else if(fi===0){showRtag(leadId,"strongest on <b>"+k.replace(/_/g,' ')+"</b>",false);}
    await wait(flipped?1400:760);
    if(flipped)rows[leadId].classList.remove('flip');
    clearRtags();
    prevLead=leadId;
  }
  clearRtags();clearHalos();var fc=$('#factorcue');if(fc)fc.classList.remove('on');
  await wait(420);
  $$('.wseg.pulse').forEach(function(s){s.classList.remove('pulse')});
  var win=survivors()[0];if(win){var comps=(win.components||[]).slice().sort(function(a,b){return b.c-a.c}).slice(0,3).map(function(c){return c.k.replace(/_/g,' ')});
    $('#weighticker').innerHTML="Final · weighted risk-adjusted score";
    $('#whynote').innerHTML="<b>"+first(win.name)+"</b> wins on "+comps.join(', ')+" — the deciding factors.";}
}
function renderFinal(){var sl=survivors();var factors=weightFactors();
  sl.forEach(function(d){factors.forEach(function(k,idx){addSeg(d,k,idx,false)});rows[d.id].classList.add('in')});
  setRanks(sl.slice().sort(function(a,b){return segState[b.id].cum-segState[a.id].cum}));
}
function buildGuides(){ if(!A.bench)return;
  var mk=$('#benchmk');if(mk&&A.bench.xz!=null){mk.style.left=A.bench.xz+'%';mk.style.bottom=A.bench.yz+'%';$('.bl',mk).textContent=A.bench.name}
  var bl=$('#beatlbl');if(bl)bl.innerHTML='above line ·<br>beats index<br>risk-adjusted';
  drawBenchLine();
}
function drawBenchLine(){ if(!A.benchLine)return;var f=$('#field');if(!f)return;var W=f.clientWidth,H=f.clientHeight,L=A.benchLine;
  var X1=L.x1/100*W,Y1=(1-L.y1/100)*H,X2=L.x2/100*W,Y2=(1-L.y2/100)*H;
  var dx=X2-X1,dy=Y2-Y1,len=Math.sqrt(dx*dx+dy*dy),ang=Math.atan2(dy,dx);
  var r=$('#benchray');if(!r)return;r.style.left=X1+'px';r.style.top=Y1+'px';r.style.width=len+'px';r.style.transform='rotate('+ang+'rad)';
}

function buildTraj(){ if(trajBuilt)return;trajBuilt=true;
  var svg=$('#traj');var host=$('#trajwrap');var W=380,H=svg.clientHeight||190,pad=6;
  $$('.tt',host).forEach(function(t){t.remove()});
  var funds=shortlisted().filter(function(d){return d.wealth&&d.wealth.length});if(!funds.length)return;
  var GR=trajGrays(),WINC=cssv('--accent2');
  var lo=1e9,hi=-1e9,n=funds[0].wealth.length;funds.forEach(function(d){d.wealth.forEach(function(w){lo=Math.min(lo,w);hi=Math.max(hi,w)})});
  var X=function(i){return pad+i/(n-1)*(W-2*pad)},Y=function(w){return H-pad-(w-lo)/((hi-lo)||1)*(H-2*pad)};
  svg.setAttribute('viewBox','0 0 '+W+' '+H);svg.setAttribute('preserveAspectRatio','none');svg.innerHTML='';
  var ns='http://www.w3.org/2000/svg';
  var base=document.createElementNS(ns,'line');base.setAttribute('x1',pad);base.setAttribute('x2',W-pad);base.setAttribute('y1',Y(1));base.setAttribute('y2',Y(1));base.setAttribute('stroke',cssv('--border2'));base.setAttribute('stroke-dasharray','2 4');svg.appendChild(base);
  var used=[];funds.slice().sort(function(a,b){return Y(a.wealth[n-1])-Y(b.wealth[n-1])}).forEach(function(d){var tp=Y(d.wealth[n-1])/H*100;while(used.some(function(u){return Math.abs(u-tp)<7})){tp+=7}used.push(tp);d.__tp=tp});
  funds.forEach(function(d,idx){var win=d.rank==1;var col=win?WINC:GR[Math.min(idx,3)];
    var pts=d.wealth.map(function(w,i){return X(i)+','+Y(w)}).join(' ');
    var pl=document.createElementNS(ns,'polyline');pl.setAttribute('points',pts);pl.setAttribute('fill','none');pl.setAttribute('stroke',col);pl.setAttribute('stroke-width',win?'2':'1.3');pl.setAttribute('vector-effect','non-scaling-stroke');pl.style.strokeDasharray='1600';pl.style.strokeDashoffset='1600';svg.appendChild(pl);
    setTimeout(function(){pl.style.transition='stroke-dashoffset 1.2s ease';pl.style.strokeDashoffset='0'},80+idx*70);
    var t=el('div','tt');t.style.color=col;t.style.right='2px';t.style.top=d.__tp+'%';t.innerHTML=first(d.name)+" <b style='color:var(--ink-hi)'>+"+((d.wealth[n-1]-1)*100).toFixed(0)+"%</b>";host.appendChild(t);
  });
}
function recolorSegs(){$$('.wrow').forEach(function(r){var win=r.classList.contains('win');$$('.wseg',r).forEach(function(s){if(s.classList.contains('neg')){s.style.background=cssv('--loss')}else{var idx=weightFactors().indexOf(s.dataset.k);s.style.background=segColor(idx,win)}})})}
function applyTheme(light){document.documentElement.dataset.theme=light?'light':'dark';var t=$('#themebtn');if(t)t.setAttribute('aria-pressed',light?'true':'false');
  recolorSegs();if($('#weighlegend')&&$('#weighlegend').children.length)buildLegend();
  if(trajBuilt){trajBuilt=false;buildTraj()}
  if($('#guides')&&$('#guides').classList.contains('on'))drawBenchLine();
}

var vTimer;
function typeVerdict(){var e=$('#vtext');var t=A.verdict;var i=0;clearInterval(vTimer);vTimer=setInterval(function(){e.textContent=t.slice(0,i++);if(i>t.length){clearInterval(vTimer);e.innerHTML=A.verdictHtml}},20)}

var NUM=['','one','two','three','four','five','six','seven','eight','nine','ten'];
function cap(s){return s.charAt(0).toUpperCase()+s.slice(1)}
async function story(){
  var total=A.funds.length;
  // ── ACT 1 · Universe — show every candidate, big and legible ──
  chapter('01 · Universe',cap(NUM[total]||total)+' candidates','the full fund universe enters the screen');
  A.funds.forEach(function(d,i){var n=nodes[d.id];var p=universePos(i);n.style.left=p.x+'%';n.style.bottom=p.y+'%'});
  for(var i=0;i<total;i++){if(aborted)return;nodes[A.funds[i].id].classList.add('shown');await wait(170)}
  await wait(350);
  for(var i2=0;i2<total;i2++){if(aborted)return;nodes[A.funds[i2].id].classList.add('labeled');await wait(120)}
  await wait(2000);
  // ── ACT 2 · Screening — cut the mandate failures one at a time, slowly ──
  chapter('02 · Screening','Apply the mandate','liquidity + volatility limits');
  $('#gates').classList.add('on');document.body.classList.add('screening');
  $('#counter').classList.add('on');updateCounter();
  await wait(1100);
  var gates=$$('.gate');var rj=rejects();
  for(var j=0;j<rj.length;j++){if(aborted)return;var ex=rj[j];var en=nodes[ex.id];
    gates.forEach(function(g){g.classList.toggle('act',(''+ex.reason).toUpperCase().indexOf(g.dataset.k)>=0)});
    $('.sr',en).textContent=ex.reason;             // fill the readable reason
    en.classList.add('focus');await wait(750);      // bring it forward
    en.classList.add('reject');await wait(1900);     // stamp it — hold long enough to read
    en.classList.remove('focus');en.classList.add('gone');updateCounter();await wait(820);
  }
  gates.forEach(function(g){g.classList.remove('act')});
  document.body.classList.remove('screening');$('#gates').classList.remove('on');
  A.funds.forEach(function(d){if(d.reason)nodes[d.id].classList.add('gone')});
  await wait(700);
  // ── ACT 3 · Scoring — survivors take the frontier; weigh them in focus ──
  chapter('03 · Scoring',cap(NUM[A.nEligible]||A.nEligible)+' clear the mandate','scored on risk-adjusted return');
  var ip=$('#intropane');if(ip)ip.classList.add('out');
  frontier();document.body.classList.add('scoring');updateCounter();await wait(1300);
  $('#scorepane').classList.add('in');buildWeigh();await wait(700);
  await runWeigh();
  await cutLowest();
  $('.sweetz').classList.add('on');await wait(650);
  // ── ACT 4 · Recommendation — one fund resolves ──
  var win=shortlisted()[0];if(aborted||!win)return;
  chapter('04 · Recommendation',first(win.name),win.name);
  focusWinner(win);
  $('#trajpane').classList.add('in');buildTraj();
  await wait(2100);settle();
}
async function cutLowest(){var c=A.funds.filter(function(d){return d.cut})[0];if(!c||aborted)return;
  var n=nodes[c.id];clearHalos();setLeaderNode(null);
  n.classList.add('focus','cutfocus');showRtag(c.id,"outscored · <b>below the top "+A.nShort+"</b>",true);await wait(1800);
  n.classList.remove('focus','cutfocus');n.classList.add('cutout','dimmed');clearRtags();updateCounter('Shortlist');await wait(700);}
function focusWinner(win){A.funds.forEach(function(d){var n=nodes[d.id];if(d.id==win.id){n.classList.add('focus','win','locked');}else if(d.eligible&&!d.cut){n.classList.add('dimmed')}});
  setLeaderNode(win.id);var cr=$('.crown',nodes[win.id]);if(cr)cr.lastChild.textContent='recommended';}
function settle(){document.body.classList.add('settled');document.body.classList.remove('scoring');clearHalos();clearRtags();var fc=$('#factorcue');if(fc)fc.classList.remove('on');A.funds.forEach(function(d){var n=nodes[d.id];if(d.eligible&&d.id!==(shortlisted()[0]||{}).id&&!d.cut)n.classList.remove('dimmed')});$('#chapter').innerHTML='';$('.rail').classList.add('in');$('#gates').classList.remove('on');$('#counter').classList.remove('on');typeVerdict();}

function reset(){aborted=true;document.body.classList.remove('settled');document.body.classList.remove('scoring');document.body.classList.remove('screening');
  clearHalos();clearRtags();setLeaderNode(null);var fc=$('#factorcue');if(fc)fc.classList.remove('on');
  A.funds.forEach(function(d){var n=nodes[d.id];n.className='node cand';n.style.left='50%';n.style.bottom='50%';n.style.opacity='';n.style.transform='';var cr=$('.crown',n);if(cr)cr.lastChild.textContent='leader';var sr=$('.stamp .sr',n);if(sr)sr.textContent=''});$('#gateline').classList.remove('on');$('#danger').classList.remove('on');$('#counter').classList.remove('on');$('#guides').classList.remove('on');$('#weighlegend').classList.remove('in');
  $('#gates').classList.remove('on');$$('.gate').forEach(function(g){g.classList.remove('act')});$('.sweetz').classList.remove('on');
  $('#trajpane').classList.remove('in');$('#scorepane').classList.remove('in');
  $('#scorebars').innerHTML='';$('#weighticker').innerHTML='';$('#whynote').innerHTML='';$('.rail').classList.remove('in');
  $$('.tt').forEach(function(t){t.remove()});$('#traj').innerHTML='';trajBuilt=false;$('#chapter').innerHTML='';
  buildIntro();
}
function replay(){reset();setTimeout(function(){aborted=false;story()},80)}

function openDrawer(h){var d=$('#drawer');d.innerHTML="<div class='x' id='dx'>✕ close</div>"+h;d.classList.add('open');$('#dx').addEventListener('click',function(){d.classList.remove('open')})}
function fundDrawer(fid){var d=A.funds.filter(function(f){return f.id==fid})[0];if(!d)return;openDrawer("<div class='d-pre'>Fund brief · rank "+(d.rank?String(d.rank).padStart(2,'0'):'—')+"</div><div class='d-name'>"+d.name+"</div><div class='d-strat'>"+d.strategy+"</div>"+d.detail)}

function wire(){
  var tip=$('#tip');
  document.addEventListener('mousemove',function(e){var n=e.target.closest('.node');if(n&&n.dataset.tip&&document.body.classList.contains('settled')){tip.innerHTML=n.dataset.tip;tip.style.opacity=1;tip.style.left=e.clientX+'px';tip.style.top=e.clientY+'px'}else tip.style.opacity=0});
  document.addEventListener('click',function(e){var n=e.target.closest('.node.cand');if(n&&document.body.classList.contains('settled')){fundDrawer(n.dataset.fid);return}var ch=e.target.closest('.chip');if(ch){fundDrawer(ch.dataset.fid)}});
  var pl=$('#play');if(pl)pl.addEventListener('click',replay);
  var sk=$('#skip');if(sk)sk.addEventListener('click',function(){aborted=true;clearRtags();clearHalos();document.body.classList.remove('screening');var ip=$('#intropane');if(ip)ip.classList.add('out');
    A.funds.forEach(function(d){var n=nodes[d.id];n.classList.add('shown','labeled');if(d.reason){n.classList.add('gone')}else{n.classList.add('ranked','showstat');n.style.left=d.xz+'%';n.style.bottom=d.yz+'%';if(d.cut)n.classList.add('cutout','dimmed');else if(d.rank!=1)n.classList.add('dimmed')}});
    frontier();document.body.classList.add('scoring');$('#scorepane').classList.add('in');buildWeigh();renderFinal();
    var win=shortlisted()[0];nodes[win.id].classList.add('focus','win','locked');var cr=$('.crown',nodes[win.id]);if(cr)cr.lastChild.textContent='recommended';nodes[win.id].classList.add('leader');
    $('#weighticker').innerHTML='Final · weighted risk-adjusted score';var comps=(win.components||[]).slice().sort(function(a,b){return b.c-a.c}).slice(0,3).map(function(c){return c.k.replace(/_/g,' ')});$('#whynote').innerHTML="<b>"+first(win.name)+"</b> wins on "+comps.join(', ')+" — the deciding factors.";$('#trajpane').classList.add('in');buildTraj();$('.sweetz').classList.add('on');updateCounter('Shortlist');settle()});
  window.addEventListener('resize',function(){if($('#guides')&&$('#guides').classList.contains('on'))drawBenchLine()});
  var tb=$('#themebtn');if(tb){var tog=function(){applyTheme(document.documentElement.dataset.theme!=='light')};tb.addEventListener('click',tog);tb.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();tog()}});}
}
window.addEventListener('DOMContentLoaded',function(){document.documentElement.dataset.theme='dark';buildField();buildIntro();wire();story()});
})();
"""

def _detail_html(sec, full, e):
    cells="".join(f'<div class="cell"><b>{(_pct(full.get(k)) if k in _PCT else _num(full.get(k)))}</b><i>{k.replace("_"," ")}</i></div>' for k in METRIC_KEYS)
    chips=""
    if sec:
        for c in sec.claims:
            k="ok" if c.verified else "warn";src=e("; ".join(c.source_refs) or "no source")
            chips+=f'<span class="{k}" title="{src}"> {e(c.text)}</span>'
    body=e(sec.body) if sec else ""
    return (f'<p class="d-p">{body}</p><div class="mgrid">{cells}</div>'
            f'<div class="src-lbl">Sources · verified against the metrics engine</div><div class="chipx">{chips}</div>')

def _reason(f, mandate):
    strat=f.strategy; vol=None
    for c in mandate.constraints:
        if c.field=="strategy" and c.op=="not_in" and strat in (c.value or []):
            return f"illiquid · {strat}", "LIQUIDITY"
    return None, None

def render_html(memo, ctx=None):
    e=html.escape;a=memo.audit;sl=memo.shortlist
    ranks={s.fund_id:s.rank for s in sl}
    series=(ctx.series_by_fund if ctx else {}) or {}
    mbf=(ctx.metrics_by_fund if ctx else {s.fund_id:s.metrics for s in sl})
    mandate=ctx.mandate if ctx else None
    secs={}
    for i,s in enumerate(sl): secs[s.fund_id]=memo.sections[1+i] if 1+i<len(memo.sections) else None

    # score components across shortlist
    weights=(mandate.weights if (mandate and mandate.weights) else DEFAULT_WEIGHTS)
    import statistics
    stats={}
    for k in weights:
        vals=[mbf[s.fund_id].get(k) for s in sl if mbf[s.fund_id].get(k) is not None]
        if len(vals)>=2: stats[k]=(statistics.fmean(vals),statistics.pstdev(vals))
    def components(fid):
        out=[]
        for k,w in weights.items():
            v=mbf[fid].get(k)
            if v is None or k not in stats: continue
            mu,sd=stats[k]
            if sd==0: continue
            out.append({"k":k,"c":round(w*((v-mu)/sd)*DIRECTION.get(k,0),3)})
        return out

    # benchmark point (same conventions as the metrics engine: CAGR + sample-std annualized vol)
    bench=None
    bmk=getattr(ctx,"benchmark",None) if ctx else None
    if bmk and getattr(bmk,"points",None):
        bvals=bmk.values; nb=len(bvals); bppy=bmk.periods_per_year or 12
        if nb>=2:
            growth=1.0
            for v in bvals: growth*=(1.0+v)
            bret=(growth**(bppy/nb)-1.0) if growth>0 else growth-1.0
            bmean=sum(bvals)/nb
            bvar=sum((v-bmean)**2 for v in bvals)/(nb-1)
            bvol=(bvar**0.5)*(bppy**0.5)
            bench={"name":bmk.name,"vol":bvol,"ret":bret}

    # gates
    gates=[]
    if mandate:
        for c in mandate.constraints:
            if c.field=="strategy" and c.op=="not_in": gates.append({"label":"LIQUIDITY","detail":"exclude illiquid"})
            elif c.field=="ann_vol" and c.op=="<=": gates.append({"label":"VOLATILITY","detail":f"≤ {c.value*100:.0f}%"})
            else: gates.append({"label":c.field.upper()[:9],"detail":f"{c.op} {c.value}"})
    if not gates: gates=[{"label":"MANDATE","detail":"screen"}]

    volcap=None
    if mandate:
        volcap=next((c.value for c in mandate.constraints if c.field=="ann_vol" and c.op=="<="),None)
    gateX=None
    plist=[(fid,m) for fid,m in mbf.items() if m.get("ann_vol") is not None and m.get("ann_return") is not None]
    fd=[]
    if plist:
        vols=[m["ann_vol"] for _,m in plist];rets=[m["ann_return"] for _,m in plist]
        vmin,vmax=min(vols),max(vols);rmin,rmax=min(rets),max(rets);vr=(vmax-vmin) or 1;rr=(rmax-rmin) or 1
        for fid,m in plist:
            f=ctx.get_fund(fid) if ctx else None;ser=series.get(fid)
            wealth=[];c=1.0
            if ser:
                for v in ser.values:c*=(1+v);wealth.append(round(c,4))
            rk=ranks.get(fid)
            reason=None; reason_kind=None
            if rk is None and mandate and f:
                excl_strats=next((cn.value for cn in mandate.constraints if cn.field=="strategy" and cn.op=="not_in"),[]) or []
                volcap=next((cn.value for cn in mandate.constraints if cn.field=="ann_vol" and cn.op=="<="),None)
                if f.strategy in excl_strats:
                    reason=f"LIQUIDITY · {f.strategy}"; reason_kind="LIQUIDITY"
                elif volcap is not None and m.get("ann_vol") is not None and m["ann_vol"]>volcap:
                    reason=f"VOLATILITY · {m['ann_vol']*100:.0f}% > {volcap*100:.0f}%"; reason_kind="VOLATILITY"
                # else: eligible but outscored -> no rejection reason
            eligible=(reason is None)                 # passed the mandate (ranked OR outscored)
            cut=(rk is None and eligible)             # eligible but below the top-N shortlist
            comps=components(fid) if eligible else []
            fd.append({"id":fid,"name":(f.name if f else fid),"strategy":(f.strategy if f else ""),
                "rank":rk,"excluded":rk is None,"eligible":eligible,"cut":cut,"rkind":reason_kind,
                "srank":(rk if rk else (90 if cut else 99)),
                "x":round(12+(m["ann_vol"]-vmin)/vr*76,1),"y":round(12+(m["ann_return"]-rmin)/rr*76,1),
                "ret":m.get("ann_return"),"vol":m.get("ann_vol"),"sharpe":m.get("sharpe"),"maxdd":m.get("max_drawdown"),
                "wealth":wealth,"reason":reason,"components":comps,"comp":{x["k"]:x["c"] for x in comps},"score":round(sum(x["c"] for x in comps),3),
                "detail":_detail_html(secs.get(fid),mbf.get(fid,{}),e)})
    # zoom positions (all mandate-eligible funds + benchmark, shared range so the
    # frontier reads against the index and the corners carry meaning)
    surv=[d for d in fd if d["eligible"]]
    benchLine=None
    if surv:
        zv=[d["vol"] for d in surv];zr=[d["ret"] for d in surv]
        if bench: zv=zv+[bench["vol"]];zr=zr+[bench["ret"]]
        zvmin,zvmax=min(zv),max(zv);zrmin,zrmax=min(zr),max(zr);zvr=(zvmax-zvmin) or 1;zrr=(zrmax-zrmin) or 1
        for d in surv: d["xz"]=round(14+(d["vol"]-zvmin)/zvr*72,1);d["yz"]=round(14+(d["ret"]-zrmin)/zrr*72,1)
        if bench:
            bench["xz"]=round(14+(bench["vol"]-zvmin)/zvr*72,1)
            bench["yz"]=round(14+(bench["ret"]-zrmin)/zrr*72,1)
            if bench["vol"]>0:
                s=bench["ret"]/bench["vol"]  # index return-per-unit-risk
                def _mapxy(vol):
                    return (round(14+(vol-zvmin)/zvr*72,1), round(14+(s*vol-zrmin)/zrr*72,1))
                x1,y1=_mapxy(zvmin);x2,y2=_mapxy(zvmax)
                benchLine={"x1":x1,"y1":y1,"x2":x2,"y2":y2}
    for d in fd: d.setdefault("xz",d["x"]);d.setdefault("yz",d["y"])

    if plist and volcap is not None:
        gx=12+(volcap-vmin)/vr*76
        if 0<gx<100: gateX=round(gx,1)
    top=sl[0] if sl else None
    vplain=f"{top.name} leads on risk-adjusted return." if top else "No fund met the mandate."
    vhtml=(f"<b>{e(top.name)}</b> leads on risk-adjusted return." if top else "No fund met the mandate.")
    DATA={"funds":fd,"gates":gates,"verdict":vplain,"verdictHtml":vhtml,"model":memo.generated_by,
          "verified":a.get("verified_count",0),"total":a.get("claim_count",0),"mandate":memo.mandate,"gateX":gateX,"volcap":(f"{volcap*100:.0f}%" if volcap is not None else None),"weights":{k:round(float(v),3) for k,v in weights.items()},
          "bench":({k:(round(v,4) if isinstance(v,float) else v) for k,v in bench.items()} if bench else None),"benchLine":benchLine,
          "nTotal":len(fd),"nEligible":sum(1 for d in fd if d["eligible"]),"nShort":len(sl),"nReject":sum(1 for d in fd if d.get("reason"))}

    chips="".join(f'<div class="chip{" r1" if s.rank==1 else ""}" data-fid="{e(s.fund_id)}"><span class="n">{s.rank:02d}</span><span class="nm">{e(s.name)}</span><span class="rt">{_pct(s.metrics.get("ann_return"))}</span></div>' for s in sl)

    header=(f'<div class="hdr"><div class="brand"><div class="logo"></div><div class="wm">EQUI</div>'
            '<div class="theme" id="themebtn" role="button" tabindex="0" aria-label="Toggle light or dark theme" aria-pressed="false"><i class="tg tg-d">☾</i><i class="tg tg-l">☀︎</i><span class="knob"></span></div></div>'
            f'<div class="vwrap"><div class="vpre">Investment Committee · Recommendation</div><div class="vtext" id="vtext"></div></div>'
            f'<div class="right"><span class="tag">{e(memo.generated_by)}</span>'
            f'<span class="vbadge"><i></i>{a.get("verified_count",0)}/{a.get("claim_count",0)} verified</span></div></div>')

    stage=('<div class="stage"><div id="field"><div class="sweetz"><span>sweet spot · high return / low risk</span></div>'
           '<div id="guides"><div id="benchray"></div><div id="benchmk"><div class="dm"></div><div class="bl"></div></div><div id="beatlbl"></div></div>'
           '<div class="gates" id="gates"></div><div class="gateline" id="gateline"><span></span></div><div class="danger" id="danger"></div><div id="counter"></div><div id="factorcue"><span class="fdot"></span><span class="fname"></span><span class="fwt"><i></i></span><span class="fpct"></span></div><div class="ax y">Return →</div><div class="ax x">Risk · volatility →</div></div>'
           '<div id="chapter"></div></div>')

    side=('<div class="side">'
          '<div id="intropane"><div class="ip-h">The mandate</div><div class="ip-s">what advances · and how it\'s scored</div>'
          '<div class="ip-lbl">Screen · hard limits</div><div id="ip-gates"></div>'
          '<div class="ip-lbl">Score · weighting</div><div id="ip-weights"></div>'
          '<div id="ip-tally"></div></div>'
          '<div class="pane" id="trajpane"><div class="head"><div class="t">36-Month Trajectory</div><div class="s">growth of $1</div></div><div id="trajwrap"><svg id="traj"></svg></div></div>'
          '<div class="pane" id="scorepane"><div class="head"><div class="t">The weighing</div><div class="s">how the ranking forms</div></div><div id="weighticker"></div><div id="weighlegend"></div><div id="scorebars"></div><div class="why-note" id="whynote"></div></div>'
          '</div>')

    rail=f'<div class="rail"><div class="rl">Shortlist</div><div class="chips">{chips}</div></div>'

    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(memo.title)}</title>'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
            f'<style>{_CSS}</style></head><body>'
            '<div class="atmo"><div class="grid"></div></div><div id="tip"></div>'
            f'<div class="app">{header}<div class="mid">{stage}{side}</div>{rail}</div>'
            '<div id="drawer"></div><div id="skip">skip intro</div><div id="play">Replay decision</div>'
            f'<script>window.AMB={json.dumps(DATA)};</script><script>{_JS}</script></body></html>')

def write_html(memo, path, ctx=None):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(render_html(memo,ctx));return p

def write_xlsx(memo, ctx, path):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);wb=Workbook()
    hf=PatternFill("solid",fgColor="141821");ff=Font(bold=True,color="84AEC8")
    def sh(ws,n):
        for c in range(1,n+1):ws.cell(row=1,column=c).fill=hf;ws.cell(row=1,column=c).font=ff
    ws=wb.active;ws.title="Shortlist"
    cols=["rank","fund_id","name","strategy","score","ann_return","sharpe","sortino","calmar","max_drawdown","ann_vol"]
    ws.append([c.replace('_',' ').title() for c in cols])
    for s in memo.shortlist:
        m=s.metrics;ws.append([s.rank,s.fund_id,s.name,s.strategy,s.score,m.get('ann_return'),m.get('sharpe'),m.get('sortino'),m.get('calmar'),m.get('max_drawdown'),m.get('ann_vol')])
    sh(ws,len(cols))
    ws2=wb.create_sheet("Metrics");hdr=["fund_id","name"]+METRIC_KEYS
    ws2.append([h.replace('_',' ').title() for h in hdr])
    for fid,vals in ctx.metrics_by_fund.items():
        f=ctx.get_fund(fid);ws2.append([fid,f.name if f else fid]+[vals.get(k) for k in METRIC_KEYS])
    sh(ws2,len(hdr))
    ws3=wb.create_sheet("Audit");ws3.append(["fund_id","metric","value","verified","sources"])
    for c in memo.audit.get("claims",[]):ws3.append([c.get("fund_id"),c.get("metric"),c.get("value"),c.get("verified"),"; ".join(c.get("sources",[]))])
    sh(ws3,5);wb.save(p);return p

def export_all(memo, ctx=None, outdir="exports"):
    paths={"md":write_markdown(memo,Path(outdir)/"memo.md"),"json":write_json(memo,Path(outdir)/"memo.json"),"html":write_html(memo,Path(outdir)/"memo.html",ctx)}
    if ctx is not None:paths["xlsx"]=write_xlsx(memo,ctx,Path(outdir)/"memo.xlsx")
    return paths
