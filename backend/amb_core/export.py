from __future__ import annotations
import html, json, math
from pathlib import Path
from .memo import render_markdown
from .metrics import METRIC_KEYS
from .models import Memo

_PCT={"ann_return","ann_vol","max_drawdown","downside_dev","alpha","tracking_error","hit_rate"}
def _pct(x): return "—" if x is None else f"{x*100:.1f}%"
def _num(x): return "—" if x is None else f"{x:.2f}"

def write_markdown(memo, path):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(render_markdown(memo)); return p
def write_json(memo, path):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(memo.model_dump_json(indent=2)); return p

_CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#060C16;--panel:#0B1626;--border:#1B2C44;--teal:#00E5C4;--teal2:#1FB6A6;--cyan:#22D3EE;--gold:#E7C878;--green:#34D399;--amber:#FBBF24;--red:#F97070;--violet:#B794F4;--ink:#D8E3F0;--dim:#5E738C;--dim2:#3C4F68;
--display:'Rajdhani',system-ui,sans-serif;--hud:'Electrolize',system-ui,sans-serif;--body:'Inter',system-ui,sans-serif;--mono:'JetBrains Mono',ui-monospace,monospace;}
html{scroll-behavior:smooth}
body{background:radial-gradient(1100px 760px at 82% -6%,rgba(0,229,196,.07),transparent 60%),radial-gradient(1200px 900px at 10% 108%,rgba(231,200,120,.04),transparent 60%),var(--bg);color:var(--ink);font-family:var(--body);font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased;min-height:100vh;position:relative;overflow-x:hidden}
.atmo{position:fixed;inset:0;z-index:0;pointer-events:none}
.atmo .grid{position:absolute;inset:-30%;opacity:.4;background-image:linear-gradient(rgba(27,44,68,.5) 1px,transparent 1px),linear-gradient(90deg,rgba(27,44,68,.5) 1px,transparent 1px);background-size:64px 64px;-webkit-mask-image:radial-gradient(1000px 720px at 50% 28%,#000,transparent 76%);mask-image:radial-gradient(1000px 720px at 50% 28%,#000,transparent 76%);animation:drift 70s linear infinite}
@keyframes drift{to{transform:translate(64px,64px)}}
.atmo .sweep{position:absolute;left:0;right:0;height:220px;opacity:.5;background:linear-gradient(rgba(0,229,196,0),rgba(0,229,196,.05) 46%,rgba(34,211,238,.06) 52%,rgba(0,229,196,0));animation:sweep 11s linear infinite}
@keyframes sweep{0%{transform:translateY(-240px)}100%{transform:translateY(115vh)}}
.wrap{position:relative;z-index:1;max-width:1000px;margin:0 auto;padding:40px 26px 70px}

/* ===== BOOT overlay ===== */
#boot{position:fixed;inset:0;z-index:60;background:var(--bg);display:grid;place-items:center;transition:opacity .6s ease}
#boot.done{opacity:0;pointer-events:none}
.boot-c{width:min(520px,80vw);font-family:var(--mono);color:var(--teal)}
.boot-ret{width:66px;height:66px;margin:0 auto 22px;position:relative}
.boot-ret::before,.boot-ret::after{content:"";position:absolute;inset:0;border:1px solid rgba(0,229,196,.6);border-radius:50%}
.boot-ret::after{inset:12px;border-style:dashed;animation:spin 3s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.boot-ret i{position:absolute;left:50%;top:50%;width:7px;height:7px;margin:-3.5px;border-radius:50%;background:var(--teal);box-shadow:0 0 12px var(--teal)}
.boot-title{font-family:var(--display);font-weight:700;font-size:22px;letter-spacing:.34em;color:#fff;text-align:center;text-shadow:0 0 16px rgba(0,229,196,.5);margin-bottom:18px}
.boot-log{font-size:11px;letter-spacing:.1em;line-height:2;color:var(--dim);min-height:120px}
.boot-log b{color:var(--teal)}.boot-log .ok{color:var(--green);float:right}
.boot-bar{height:2px;background:rgba(27,44,68,.8);margin-top:14px;overflow:hidden}
.boot-bar span{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--teal2),var(--teal));box-shadow:0 0 10px var(--teal)}

/* reveal helper */
.rev{opacity:0;transform:translateY(16px);transition:opacity .6s cubic-bezier(.2,.8,.2,1),transform .6s cubic-bezier(.2,.8,.2,1)}
.rev.in{opacity:1;transform:none}

.panel{position:relative;margin:15px 0;--gfill:rgba(11,22,38,.62);background:linear-gradient(var(--gfill),var(--gfill)) padding-box,linear-gradient(145deg,rgba(0,229,196,.5),rgba(0,229,196,.03) 44%,rgba(34,211,238,.32) 90%) border-box;border:1px solid transparent;--c:14px;clip-path:polygon(var(--c) 0,100% 0,100% calc(100% - var(--c)),calc(100% - var(--c)) 100%,0 100%,0 var(--c));box-shadow:inset 0 1px 0 rgba(255,255,255,.06),0 26px 50px -26px rgba(0,0,0,.85);padding:20px 24px}
.corner{position:absolute;width:12px;height:12px;border:1px solid rgba(0,229,196,.5)}
.corner.tl{top:6px;left:6px;border-right:0;border-bottom:0}.corner.tr{top:6px;right:6px;border-left:0;border-bottom:0}.corner.bl{bottom:6px;left:6px;border-right:0;border-top:0}.corner.br{bottom:6px;right:6px;border-left:0;border-top:0}
.lbl{font-family:var(--hud);font-size:10.5px;letter-spacing:.3em;text-transform:uppercase;color:var(--teal);margin-bottom:12px;display:flex;align-items:center;gap:10px}
.lbl::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,rgba(0,229,196,.4),transparent)}
.lbl .hint{font-family:var(--mono);font-size:9px;letter-spacing:.08em;color:var(--dim2);text-transform:none}

/* header */
.top{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:13px}
.logo{width:38px;height:38px;flex:none;border:1px solid rgba(0,229,196,.55);position:relative;--c:9px;clip-path:polygon(var(--c) 0,100% 0,100% calc(100% - var(--c)),calc(100% - var(--c)) 100%,0 100%,0 var(--c));box-shadow:inset 0 0 16px rgba(0,229,196,.22),0 0 16px -3px rgba(0,229,196,.5)}
.logo::after{content:"";position:absolute;inset:10px;border:2px solid var(--teal);border-radius:50%;box-shadow:0 0 10px rgba(0,229,196,.7)}
.wm{font-family:var(--display);font-weight:700;font-size:28px;letter-spacing:.24em;color:#fff;line-height:1;text-shadow:0 0 14px rgba(0,229,196,.55)}
.sub{font-family:var(--mono);font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:var(--dim);margin-top:5px}
.hstat{display:flex;align-items:center;gap:9px;flex-wrap:wrap;justify-content:flex-end}
.tag{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);border:1px solid var(--border);padding:6px 10px}
.tag.model{color:var(--gold);border-color:rgba(231,200,120,.4)}
.vbadge{font-family:var(--mono);font-size:10px;letter-spacing:.14em;color:var(--green);border:1px solid rgba(52,211,153,.45);padding:6px 10px;display:inline-flex;align-items:center;gap:7px;text-transform:uppercase}
.vbadge i{width:6px;height:6px;border-radius:50%;background:var(--green);box-shadow:0 0 9px rgba(52,211,153,.9);animation:pulse 2.4s ease-in-out infinite}
@keyframes pulse{50%{opacity:.4}}

/* verdict hero */
.verdict{margin:26px 0 4px;min-height:66px}
.verdict .pre{font-family:var(--hud);font-size:10.5px;letter-spacing:.3em;text-transform:uppercase;color:var(--teal);margin-bottom:8px}
.verdict h1{font-family:var(--display);font-weight:700;font-size:34px;line-height:1.12;letter-spacing:.01em;color:#fff;text-shadow:0 0 26px rgba(0,229,196,.18)}
.verdict h1 .cur{color:var(--teal);animation:blink 1s step-end infinite}
@keyframes blink{50%{opacity:0}}
.verdict .mandate{font-family:var(--mono);font-size:11px;letter-spacing:.05em;color:var(--dim);margin-top:10px}
.verdict .mandate b{color:var(--teal2);font-weight:500}

/* race panel */
#race{height:250px;position:relative;margin:2px 2px}
#race svg{width:100%;height:100%;display:block;overflow:visible}
.race-tag{position:absolute;font-family:var(--mono);font-size:10px;padding:2px 7px;background:rgba(6,12,22,.85);border:1px solid var(--border);white-space:nowrap;transform:translateY(-50%);opacity:0;transition:opacity .5s}
.race-tag.in{opacity:1}
.race-ax{position:absolute;font-family:var(--mono);font-size:9px;letter-spacing:.12em;color:var(--dim2);text-transform:uppercase}

/* field */
#field{position:relative;height:360px;margin:6px 4px 2px;background:linear-gradient(rgba(27,44,68,.22) 1px,transparent 1px),linear-gradient(90deg,rgba(27,44,68,.22) 1px,transparent 1px);background-size:11.11% 20%}
#field .sweet{position:absolute;left:0;top:0;width:46%;height:52%;background:radial-gradient(120% 120% at 0 0,rgba(0,229,196,.10),transparent 70%);opacity:0;transition:opacity 1s}
#field.lit .sweet{opacity:1}
#field .sweet span{position:absolute;left:12px;top:10px;font-family:var(--hud);font-size:8.5px;letter-spacing:.2em;color:rgba(0,229,196,.6);text-transform:uppercase}
.ax{position:absolute;font-family:var(--mono);font-size:9px;letter-spacing:.16em;color:var(--dim2);text-transform:uppercase}
.ax.x{bottom:-20px;right:4px}.ax.y{top:-2px;left:-4px;writing-mode:vertical-lr}
.node{position:absolute;left:50%;bottom:50%;transform:translate(-50%,50%) scale(0);z-index:2;transition:left 1.1s cubic-bezier(.2,.9,.3,1),bottom 1.1s cubic-bezier(.2,.9,.3,1),transform .5s cubic-bezier(.2,1.3,.4,1),opacity .6s}
.node.shown{transform:translate(-50%,50%) scale(1)}
.node .dot{width:13px;height:13px;border-radius:50%;background:var(--dim2);border:1px solid rgba(94,115,140,.5);transition:.4s;display:grid;place-items:center;font-family:var(--mono);font-weight:600;font-size:12px;color:#04121a}
.node.on{cursor:pointer}
.node.on .dot{width:34px;height:34px;background:radial-gradient(circle at 35% 30%,#5ff0dc,var(--teal));box-shadow:0 0 16px rgba(0,229,196,.6),inset 0 0 6px rgba(255,255,255,.4);border:0}
.node.on.rank1 .dot{background:radial-gradient(circle at 35% 30%,#f4dc9a,var(--gold));box-shadow:0 0 18px rgba(231,200,120,.7)}
.node .rk{opacity:0;transition:opacity .4s}
.node.ranked .rk{opacity:1}
.node.on:hover .dot{transform:scale(1.14)}
.node.excl .dot{width:13px;height:13px;background:transparent;border:1px dashed rgba(94,115,140,.55);font-size:0}
.node .ring{position:absolute;inset:-7px;border:1px solid rgba(0,229,196,.35);border-radius:50%;opacity:0}
.node.on:hover .ring{opacity:1;animation:ring 1.1s ease-out infinite}
@keyframes ring{from{transform:scale(.7);opacity:.7}to{transform:scale(1.6);opacity:0}}
#tip{position:fixed;z-index:70;pointer-events:none;opacity:0;transform:translate(14px,-50%);transition:opacity .15s;background:rgba(6,12,22,.96);border:1px solid rgba(0,229,196,.4);padding:8px 11px;font-family:var(--mono);font-size:11px;white-space:nowrap;box-shadow:0 8px 24px rgba(0,0,0,.6)}
#tip .tn{color:#fff;font-family:var(--display);font-weight:600;font-size:13px}#tip .ts{color:var(--dim);font-size:9px;text-transform:uppercase;letter-spacing:.1em}#tip b{color:var(--teal2)}
.field-foot{display:flex;justify-content:space-between;align-items:center;margin-top:26px;flex-wrap:wrap;gap:10px}
.legend{display:flex;gap:16px;font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;color:var(--dim);text-transform:uppercase}
.legend span{display:inline-flex;align-items:center;gap:7px}.legend i{width:10px;height:10px;border-radius:50%}
.legend .i-sl{background:var(--teal);box-shadow:0 0 8px rgba(0,229,196,.7)}.legend .i-ex{border:1px dashed var(--dim);width:9px;height:9px}
.replay{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--teal);border:1px solid rgba(0,229,196,.4);background:rgba(0,229,196,.05);padding:7px 13px;cursor:pointer;transition:.2s}
.replay:hover{background:rgba(0,229,196,.14);box-shadow:0 0 14px -3px rgba(0,229,196,.5)}

/* tiles */
.tiles-lbl{font-family:var(--hud);font-size:10.5px;letter-spacing:.3em;text-transform:uppercase;color:var(--teal);margin:26px 4px 4px;display:flex;align-items:center;gap:10px}
.tiles-lbl::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,rgba(0,229,196,.4),transparent)}
.tile{margin:11px 0}
.thead{display:grid;grid-template-columns:44px 1.5fr 130px auto 46px 26px;gap:16px;align-items:center;padding:15px 20px;cursor:pointer}
.med{font-family:var(--mono);font-size:19px;font-weight:600;color:var(--dim2);text-align:center}
.tile.rank1 .med{color:var(--gold);text-shadow:0 0 12px rgba(231,200,120,.5)}
.tn{font-family:var(--display);font-weight:600;font-size:17px;color:#fff}.ts{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-top:2px}
.spark{width:130px;height:34px;display:block}
.mstat{display:flex;gap:16px}.mstat .m{text-align:right}.mstat .m b{display:block;font-family:var(--mono);font-size:14px;font-weight:600;color:#E7EFF9}.mstat .m b.pos{color:#7FE9CE}.mstat .m b.neg{color:var(--red)}
.mstat .m i{font-family:var(--mono);font-size:8px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim2);font-style:normal}
.dial{width:44px;height:44px}.dial .track{fill:none;stroke:rgba(27,44,68,.9);stroke-width:4}
.dial .val{fill:none;stroke:var(--teal);stroke-width:4;stroke-linecap:round;stroke-dasharray:var(--c);stroke-dashoffset:var(--c);transform:rotate(-90deg);transform-origin:50% 50%;transition:stroke-dashoffset 1.1s cubic-bezier(.2,.8,.2,1);filter:drop-shadow(0 0 4px rgba(0,229,196,.5))}
.tile.rank1 .dial .val{stroke:var(--gold)}
body.lit .dial .val{stroke-dashoffset:var(--off)}
.dial-wrap{position:relative;width:44px;height:44px}.dial-wrap span{position:absolute;inset:0;display:grid;place-items:center;font-family:var(--mono);font-size:10px;font-weight:600;color:var(--ink)}
.chev{justify-self:end;width:9px;height:9px;border-right:1.5px solid var(--dim);border-bottom:1.5px solid var(--dim);transform:rotate(45deg);transition:.3s}
.tile.open .chev{transform:rotate(225deg);border-color:var(--teal)}
.detail{max-height:0;overflow:hidden;opacity:0;transition:max-height .45s ease,opacity .35s ease}.tile.open .detail{max-height:800px;opacity:1}
.detail-in{padding:2px 20px 20px;border-top:1px solid var(--border);margin-top:2px}.detail p{color:#C2D0E0;font-size:14px;margin:14px 0 4px}
.mgrid{display:grid;grid-template-columns:repeat(6,1fr);gap:1px;background:var(--border);border:1px solid var(--border);margin:16px 0}
.mgrid .cell{background:var(--panel);padding:9px 10px;text-align:center}.mgrid .cell b{display:block;font-family:var(--mono);font-size:13px;color:#E7EFF9}.mgrid .cell i{font-family:var(--mono);font-size:7.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim2);font-style:normal}
.src-lbl{font-family:var(--hud);font-size:9px;letter-spacing:.22em;text-transform:uppercase;color:var(--dim2);margin:14px 0 10px;display:flex;align-items:center;gap:10px}.src-lbl::after{content:"";flex:1;height:1px;background:var(--border)}
.chips{display:flex;flex-wrap:wrap;gap:7px}.chip{font-family:var(--mono);font-size:10.5px;padding:6px 10px;background:rgba(8,18,32,.7);border:1px solid var(--border);color:var(--ink);display:inline-flex;align-items:center;gap:6px}
.chip.ok{border-color:rgba(0,229,196,.4);color:#9EEBDD}.chip.ok::before{content:"";width:5px;height:5px;border-radius:50%;background:var(--teal);box-shadow:0 0 7px rgba(0,229,196,.9)}
.chip.warn{border-color:rgba(251,191,36,.45);color:#FCD777}.chip.warn::before{content:"";width:5px;height:5px;border-radius:50%;background:var(--amber)}
.tile.flash{animation:flash 1.2s ease}@keyframes flash{30%{box-shadow:0 0 0 2px rgba(0,229,196,.5),0 0 30px rgba(0,229,196,.3)}}
.foot{font-family:var(--mono);font-size:10px;letter-spacing:.08em;color:var(--dim2);text-align:center;margin-top:38px;padding-top:18px;border-top:1px solid var(--border)}.foot b{color:var(--teal2);font-weight:400}
@media print{#boot{display:none!important}.rev{opacity:1!important;transform:none!important}.detail{max-height:none!important;opacity:1!important}.atmo{display:none}.node{transition:none}}
@media(max-width:760px){.thead{grid-template-columns:36px 1fr 44px 20px}.spark,.mstat{display:none}#field{height:300px}#race{height:200px}}
"""

_JS = r"""
(function(){
var A=window.AMB, RED='var(--red)';
var COLORS=['#E7C878','#00E5C4','#22D3EE','#34D399','#B794F4','#FBBF24'];
function $(s,r){return (r||document).querySelector(s)}
function el(t,c){var e=document.createElement(t);if(c)e.className=c;return e}
function reveal(list,step,cb){list.forEach(function(n,i){setTimeout(function(){n.classList.add('in');if(cb)cb(n,i)},step*i)})}

// ---- build risk/return field nodes ----
function buildField(){
  var f=$('#field');
  A.funds.forEach(function(d){
    var n=el('div','node '+(d.excluded?'excl':'on'+(d.rank==1?' rank1':'')));
    n.dataset.fid=d.id;
    n.dataset.tip="<div class='tn'>"+d.name+"</div><div class='ts'>"+d.strategy+"</div>return <b>"+pct(d.ret)+"</b> · vol <b>"+pct(d.vol)+"</b> · sharpe <b>"+num(d.sharpe)+"</b>";
    var dot=el('div','dot'); var rk=el('span','rk'); rk.textContent=d.rank?String(d.rank).padStart(2,'0'):''; dot.appendChild(rk);
    var ring=el('div','ring'); n.appendChild(ring); n.appendChild(dot);
    n.__x=d.x; n.__y=d.y; f.appendChild(n);
  });
}
function pct(x){return x==null?'—':(x*100).toFixed(1)+'%'} function num(x){return x==null?'—':x.toFixed(2)}

// ---- equity-curve race ----
function buildRace(){
  var host=$('#race'); var W=1000,H=250,pad=10;
  var funds=A.funds.filter(function(d){return !d.excluded && d.wealth && d.wealth.length});
  funds.sort(function(a,b){return a.rank-b.rank});
  var lo=1e9,hi=-1e9,n=funds[0].wealth.length;
  funds.forEach(function(d){d.wealth.forEach(function(w){lo=Math.min(lo,w);hi=Math.max(hi,w)})});
  var X=function(i){return pad+i/(n-1)*(W-2*pad)}, Y=function(w){return H-pad-(w-lo)/((hi-lo)||1)*(H-2*pad)};
  var ns='http://www.w3.org/2000/svg';
  var svg=document.createElementNS(ns,'svg'); svg.setAttribute('viewBox','0 0 '+W+' '+H); svg.setAttribute('preserveAspectRatio','none');
  // baseline
  var base=document.createElementNS(ns,'line');base.setAttribute('x1',pad);base.setAttribute('x2',W-pad);base.setAttribute('y1',Y(1));base.setAttribute('y2',Y(1));base.setAttribute('stroke','rgba(94,115,140,.35)');base.setAttribute('stroke-dasharray','3 4');svg.appendChild(base);
  var paths=[];
  funds.forEach(function(d,idx){
    var col=COLORS[Math.min(idx,COLORS.length-1)];
    var pts=d.wealth.map(function(w,i){return X(i)+','+Y(w)}).join(' ');
    var pl=document.createElementNS(ns,'polyline'); pl.setAttribute('points',pts); pl.setAttribute('fill','none');
    pl.setAttribute('stroke',col); pl.setAttribute('stroke-width','2'); pl.setAttribute('vector-effect','non-scaling-stroke');
    pl.setAttribute('stroke-linejoin','round'); pl.style.filter='drop-shadow(0 0 4px '+col+'88)';
    var len=pl.getTotalLength?800:800; pl.style.strokeDasharray='2000'; pl.style.strokeDashoffset='2000';
    svg.appendChild(pl); paths.push({pl:pl,col:col,d:d,endx:X(n-1),endy:Y(d.wealth[n-1])});
  });
  // sweep line
  var sweep=document.createElementNS(ns,'line');sweep.setAttribute('y1',pad);sweep.setAttribute('y2',H-pad);sweep.setAttribute('stroke','rgba(0,229,196,.5)');sweep.setAttribute('stroke-width','1');sweep.setAttribute('x1',pad);sweep.setAttribute('x2',pad);svg.appendChild(sweep);
  host.appendChild(svg);
  host._paths=paths;host._sweep=sweep;host._W=W;host._pad=pad;host._svg=svg;
  // end tags (positioned after race)
  var used=[];paths.slice().sort(function(a,b){return a.endy-b.endy}).forEach(function(p){var tp=p.endy/H*100;while(used.some(function(u){return Math.abs(u-tp)<7.5})){tp+=7.5}used.push(tp);p.tagTop=tp});
  paths.forEach(function(p){var t=el('div','race-tag');t.style.color=p.col;t.style.borderColor=p.col+'66';t.innerHTML=p.d.name.split(' ')[0]+' <b style="color:#fff">+'+((p.d.wealth[n-1]-1)*100).toFixed(0)+'%</b>';t.style.right='2px';t.style.top=p.tagTop+'%';host.appendChild(t);p.tag=t;});
}
function runRace(){
  var host=$('#race'); if(!host._paths)return; var paths=host._paths, dur=1500, t0=null;
  paths.forEach(function(p){p.pl.style.transition='none';p.pl.style.strokeDashoffset='2000';p.tag.classList.remove('in')});
  function step(ts){ if(!t0)t0=ts; var k=Math.min(1,(ts-t0)/dur); var e=1-Math.pow(1-k,3);
    paths.forEach(function(p){p.pl.style.strokeDashoffset=String(2000*(1-e))});
    host._sweep.setAttribute('x1',host._pad+e*(host._W-2*host._pad)); host._sweep.setAttribute('x2',host._pad+e*(host._W-2*host._pad));
    if(k<1)requestAnimationFrame(step); else {host._sweep.setAttribute('x1',-9);host._sweep.setAttribute('x2',-9);paths.forEach(function(p,i){setTimeout(function(){p.tag.classList.add('in')},60*i)})}
  }
  requestAnimationFrame(step);
}

// ---- timeline ----
var typed=null;
function typeVerdict(){var h=$('#verdict-h'); var txt=A.verdict; h.innerHTML=''; var i=0; var cur=el('span','cur');cur.textContent='▋';h.appendChild(cur);
  clearInterval(typed); typed=setInterval(function(){ if(i<=txt.length){cur.insertAdjacentText('beforebegin',txt[i-1]||'');cur.previousSibling; h.textContent=txt.slice(0,i);h.appendChild(cur);i++} else {clearInterval(typed);cur.style.animation='blink 1s step-end infinite'} },26);
}
function igniteField(){
  var nodes=[].slice.call(document.querySelectorAll('.node'));
  // 1: ignite all at center
  reveal(nodes,60,function(n){n.classList.add('shown')});
  // 2: move to positions
  setTimeout(function(){nodes.forEach(function(n){n.style.left=n.__x+'%';n.style.bottom=n.__y+'%'})},700);
  // 3: filter — excluded already styled; pulse the field sweet spot
  setTimeout(function(){$('#field').classList.add('lit')},1500);
  // 4: assign ranks
  setTimeout(function(){document.querySelectorAll('.node.on').forEach(function(n){n.classList.add('ranked')})},2000);
}
function settle(){ document.body.classList.add('lit'); }

function play(){
  // reset
  document.body.classList.remove('lit'); $('#field').classList.remove('lit');
  document.querySelectorAll('.node').forEach(function(n){n.classList.remove('shown','ranked');n.style.left='50%';n.style.bottom='50%'});
  var revs=[].slice.call(document.querySelectorAll('.rev'));
  revs.forEach(function(r){r.classList.remove('in')});
  var T=0, S=function(f,d){setTimeout(f,T+=d)};
  // header + verdict
  S(function(){$('.top').classList.add('in')},120);
  S(function(){$('#verdict').classList.add('in');typeVerdict()},180);
  // race
  S(function(){$('#race-panel').classList.add('in');buildRaceOnce();runRace()},420);
  // field
  S(function(){$('#field-panel').classList.add('in');igniteField()},600);
  // tiles
  S(function(){document.querySelectorAll('.tile,.foot,.tiles-lbl').forEach(function(t,i){setTimeout(function(){t.classList.add('in')},60*i)});settle()},1300);
}
var raceBuilt=false; function buildRaceOnce(){if(!raceBuilt){buildRace();raceBuilt=true}}

function boot(){
  var log=$('#boot-log'), bar=$('#boot-bar');
  var lines=['◇ init cockpit .................','◇ load fund universe · '+A.funds.length+' funds','◇ apply mandate filter','◇ compute allocator metrics','◇ verify '+A.verified+' claims','◇ render brief'];
  var i=0;
  bootIv=setInterval(function(){ if(i<lines.length){var d=el('div');d.innerHTML=lines[i]+" <span class='ok'>OK</span>";log.appendChild(d);if(bar)bar.style.width=((i+1)/lines.length*100)+'%';i++} else {clearInterval(bootIv); setTimeout(finishBoot,260)} },230);
}
var _fin=false;
function finishBoot(){ if(_fin)return; _fin=true; var b=$('#boot'); if(b){b.classList.add('done');setTimeout(function(){b.style.display='none'},650)} buildField(); play(); }

// interactions
function wire(){
  document.addEventListener('click',function(e){var h=e.target.closest('.thead');if(h)h.parentElement.classList.toggle('open')});
  $('#replay') && $('#replay').addEventListener('click',play);
  var b=$('#boot'); if(b)b.addEventListener('click',function(){clearInterval(bootIv);finishBoot()});
  var tip=$('#tip');
  document.addEventListener('mousemove',function(e){var n=e.target.closest('.node');if(n&&n.dataset.tip){tip.innerHTML=n.dataset.tip;tip.style.opacity=1;tip.style.left=e.clientX+'px';tip.style.top=e.clientY+'px'}else tip.style.opacity=0});
  document.addEventListener('click',function(e){var n=e.target.closest('.node.on');if(n){var t=$('#tile-'+n.dataset.fid);if(t){t.classList.add('open');t.scrollIntoView({behavior:'smooth',block:'center'});t.classList.remove('flash');void t.offsetWidth;t.classList.add('flash')}}});
}
var bootIv;
window.addEventListener('DOMContentLoaded',function(){ wire(); boot(); setTimeout(function(){var b=$('#boot');if(b&&!b.classList.contains('done'))finishBoot()},6000); });
})();
"""

def _spark(vals,w=130,h=34):
    if not vals or len(vals)<2: return ""
    wealth=[];c=1.0
    for v in vals: c*=(1+v);wealth.append(c)
    lo=min(wealth);hi=max(wealth);rng=(hi-lo) or 1.0;n=len(wealth)
    pts=[f"{i/(n-1)*w:.1f},{h-(y-lo)/rng*(h-4)-2:.1f}" for i,y in enumerate(wealth)]
    up=wealth[-1]>=wealth[0];col="#7FE9CE" if up else "#F97070"
    area=f"0,{h} "+" ".join(pts)+f" {w},{h}"
    return (f'<svg class="spark" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
            f'<defs><linearGradient id="sg{n}x{int(wealth[-1]*100)}" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{col}" stop-opacity=".28"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient></defs>'
            f'<polygon points="{area}" fill="url(#sg{n}x{int(wealth[-1]*100)})"/>'
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" stroke-width="1.6" vector-effect="non-scaling-stroke"/></svg>')

def _dial(pct):
    r=15.5;circ=2*math.pi*r;off=circ*(1-max(0.04,min(1,pct)))
    return (f'<div class="dial-wrap"><svg class="dial" viewBox="0 0 40 40"><circle class="track" cx="20" cy="20" r="{r}"/>'
            f'<circle class="val" cx="20" cy="20" r="{r}" style="--c:{circ:.1f};--off:{off:.1f}"/></svg><span>{round(pct*100)}</span></div>')

def render_html(memo, ctx=None):
    e=html.escape;a=memo.audit;sl=memo.shortlist
    scores=[s.score for s in sl] or [0.0];smin,smax=min(scores),max(scores)
    def norm(s): return 1.0 if smax==smin else (s-smin)/(smax-smin)
    ranks={s.fund_id:s.rank for s in sl}
    series=(ctx.series_by_fund if ctx else {}) or {}
    mbf=(ctx.metrics_by_fund if ctx else {s.fund_id:s.metrics for s in sl})

    # DATA for JS
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
            fd.append({"id":fid,"name":(f.name if f else fid),"strategy":(f.strategy if f else ""),
                "rank":rk,"excluded":rk is None,
                "x":round(10+(m["ann_vol"]-vmin)/vr*80,1),"y":round(10+(m["ann_return"]-rmin)/rr*80,1),
                "ret":m.get("ann_return"),"vol":m.get("ann_vol"),"sharpe":m.get("sharpe"),"wealth":wealth})
    top=sl[0] if sl else None
    verdict = f"{top.name} leads the shortlist on risk-adjusted return." if top else "No fund met the mandate."
    DATA={"funds":fd,"verdict":verdict,"model":memo.generated_by,"verified":a.get("verified_count",0),"total":a.get("claim_count",0),"mandate":memo.mandate}

    head=(f'<div class="top rev"><div class="brand"><div class="logo"></div>'
          f'<div><div class="wm">EQUI</div><div class="sub">Allocator Memo Builder</div></div></div>'
          f'<div class="hstat"><span class="tag model">{e(memo.generated_by)}</span>'
          f'<span class="vbadge"><i></i>{a.get("verified_count",0)} / {a.get("claim_count",0)} verified</span></div></div>')
    verdict_html=(f'<div class="verdict rev" id="verdict"><div class="pre">◆ Recommendation</div>'
                  f'<h1 id="verdict-h"></h1>'
                  f'<div class="mandate">MANDATE · <b>{e(memo.mandate)}</b></div></div>')

    race_html=(f'<section class="panel rev" id="race-panel">{"".join([f"<span class=corner></span>"])}'
               f'<span class="corner tl"></span><span class="corner tr"></span><span class="corner bl"></span><span class="corner br"></span>'
               f'<div class="lbl">36-Month Trajectory <span class="hint">· growth of $1, cumulative</span></div>'
               f'<div id="race"></div></section>')

    field_html=('<section class="panel rev" id="field-panel">'
                '<span class="corner tl"></span><span class="corner tr"></span><span class="corner bl"></span><span class="corner br"></span>'
                '<div class="lbl">Risk / Return Field <span class="hint">· hover a node for its brief · click to open</span></div>'
                '<div id="field"><div class="sweet"><span>◤ sweet spot</span></div>'
                '<div class="ax y">Return →</div><div class="ax x">Risk (volatility) →</div></div>'
                '<div class="field-foot"><div class="legend"><span><i class="i-sl"></i>shortlisted</span>'
                '<span><i class="i-ex"></i>considered · excluded</span></div>'
                '<button class="replay" id="replay">▸ replay</button></div></section>')

    # tiles
    fund_secs=memo.sections[1:]
    tiles=""
    for i,s in enumerate(sl):
        m=s.metrics;sec=fund_secs[i] if i<len(fund_secs) else None;r1=" rank1" if s.rank==1 else ""
        vals=series.get(s.fund_id).values if series.get(s.fund_id) else []
        chips=""
        if sec:
            for c in sec.claims:
                k="ok" if c.verified else "warn";src=e("; ".join(c.source_refs) or "no source")
                chips+=f'<span class="chip {k}" title="{src}">{e(c.text)}</span>'
        full=mbf.get(s.fund_id,{})
        cells="".join(f'<div class="cell"><b>{(_pct(full.get(k)) if k in _PCT else _num(full.get(k)))}</b><i>{k.replace("_"," ")}</i></div>' for k in METRIC_KEYS)
        detail=(f'<div class="detail"><div class="detail-in"><p>{e(sec.body) if sec else ""}</p>'
                f'<div class="mgrid">{cells}</div><div class="src-lbl">Sources · verified against the metrics engine</div>'
                f'<div class="chips">{chips}</div></div></div>')
        hrow=(f'<div class="thead"><div class="med">{s.rank:02d}</div>'
              f'<div><div class="tn">{e(s.name)}</div><div class="ts">{e(s.strategy)}</div></div>'
              f'<div>{_spark(vals)}</div>'
              f'<div class="mstat"><div class="m"><b class="{"pos" if (m.get("ann_return") or 0)>=0 else "neg"}">{_pct(m.get("ann_return"))}</b><i>return</i></div>'
              f'<div class="m"><b>{_num(m.get("sharpe"))}</b><i>sharpe</i></div>'
              f'<div class="m"><b class="neg">{_pct(m.get("max_drawdown"))}</b><i>max dd</i></div></div>'
              f'{_dial(0.5+0.5*norm(s.score))}<div class="chev"></div></div>')
        tiles+=f'<section class="panel tile rev{r1}" id="tile-{e(s.fund_id)}"><span class="corner tl"></span><span class="corner tr"></span><span class="corner bl"></span><span class="corner br"></span>{hrow}{detail}</section>'
    tiles_block=f'<div class="tiles-lbl rev">Shortlist · {len(sl)} funds <span style="font-family:var(--mono);font-size:9px;letter-spacing:.1em;color:var(--dim2)">· click to expand</span></div>{tiles}'

    foot='<div class="foot rev">ALLOCATORMEMOBUILDER · every figure traces to a <b>source row + formula</b> · the model narrates, it never computes · print to PDF from your browser</div>'

    boot=('<div id="boot"><div class="boot-c"><div class="boot-ret"><i></i></div>'
          '<div class="boot-title">EQUI // IC BRIEF</div><div class="boot-log" id="boot-log"></div>'
          '<div class="boot-bar"><span id="boot-bar"></span></div>'
          '<div style="text-align:center;margin-top:16px;font-size:9px;letter-spacing:.2em;color:var(--dim2)">CLICK TO SKIP</div></div></div>')

    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(memo.title)}</title>'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Electrolize&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
            f'<style>{_CSS}</style></head><body>'
            '<div class="atmo"><div class="grid"></div><div class="sweep"></div></div><div id="tip"></div>'
            f'{boot}<div class="wrap">{head}{verdict_html}{race_html}{field_html}{tiles_block}{foot}</div>'
            f'<script>window.AMB={json.dumps(DATA)};</script><script>{_JS}</script></body></html>')

def write_html(memo, path, ctx=None):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(render_html(memo,ctx));return p

def write_xlsx(memo, ctx, path):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);wb=Workbook()
    hf=PatternFill("solid",fgColor="0A1628");ff=Font(bold=True,color="00E5C4")
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
