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
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(render_markdown(memo));return p
def write_json(memo, path):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(memo.model_dump_json(indent=2));return p

_CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#050A12;--panel:#0A1424;--border:#16263C;--teal:#00E5C4;--teal2:#1FB6A6;--cyan:#22D3EE;--gold:#E7C878;--green:#34D399;--amber:#FBBF24;--red:#F97070;--violet:#B794F4;--ink:#D8E3F0;--dim:#5E738C;--dim2:#33465E;
--display:'Rajdhani',system-ui,sans-serif;--hud:'Electrolize',system-ui,sans-serif;--body:'Inter',system-ui,sans-serif;--mono:'JetBrains Mono',ui-monospace,monospace;}
html,body{height:100%;margin:0;overflow:hidden;background:var(--bg);color:var(--ink);font-family:var(--body);-webkit-font-smoothing:antialiased}
.app{position:fixed;inset:0;display:flex;flex-direction:column;z-index:1}
.atmo{position:fixed;inset:0;z-index:0;pointer-events:none;background:radial-gradient(1200px 800px at 50% 40%,rgba(0,229,196,.05),transparent 62%)}
.atmo .grid{position:absolute;inset:-20%;opacity:.35;background-image:linear-gradient(rgba(22,38,60,.6) 1px,transparent 1px),linear-gradient(90deg,rgba(22,38,60,.6) 1px,transparent 1px);background-size:60px 60px;-webkit-mask-image:radial-gradient(1200px 820px at 50% 44%,#000,transparent 78%);mask-image:radial-gradient(1200px 820px at 50% 44%,#000,transparent 78%);animation:drift 80s linear infinite}
@keyframes drift{to{transform:translate(60px,60px)}}
.mono{font-family:var(--mono)}

/* header */
.hdr{display:flex;align-items:center;gap:18px;padding:14px 26px;border-bottom:1px solid var(--border);flex:none;opacity:0;transform:translateY(-10px);transition:.6s}
.hdr.in{opacity:1;transform:none}
.brand{display:flex;align-items:center;gap:11px}
.logo{width:30px;height:30px;flex:none;border:1px solid rgba(0,229,196,.55);position:relative;--c:7px;clip-path:polygon(var(--c) 0,100% 0,100% calc(100% - var(--c)),calc(100% - var(--c)) 100%,0 100%,0 var(--c));box-shadow:inset 0 0 12px rgba(0,229,196,.25)}
.logo::after{content:"";position:absolute;inset:8px;border:2px solid var(--teal);border-radius:50%;box-shadow:0 0 8px rgba(0,229,196,.7)}
.wm{font-family:var(--display);font-weight:700;font-size:19px;letter-spacing:.24em;color:#fff;text-shadow:0 0 12px rgba(0,229,196,.5)}
.hdr .verdict{flex:1;min-width:0}
.hdr .vpre{font-family:var(--hud);font-size:8.5px;letter-spacing:.3em;color:var(--teal);text-transform:uppercase}
.hdr .vtext{font-family:var(--display);font-weight:600;font-size:19px;color:#fff;letter-spacing:.01em;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hdr .right{display:flex;gap:8px;flex:none}
.tag{font-family:var(--mono);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);border:1px solid var(--border);padding:5px 9px}
.tag.model{color:var(--gold);border-color:rgba(231,200,120,.4)}
.vbadge{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;color:var(--green);border:1px solid rgba(52,211,153,.45);padding:5px 9px;display:inline-flex;align-items:center;gap:6px;text-transform:uppercase}
.vbadge i{width:6px;height:6px;border-radius:50%;background:var(--green);box-shadow:0 0 8px rgba(52,211,153,.9);animation:pulse 2.4s ease-in-out infinite}
@keyframes pulse{50%{opacity:.4}}

/* FIELD (hero, full-bleed) */
.stage{position:relative;flex:1;overflow:hidden}
#field{position:absolute;inset:20px 26px}
.axline{position:absolute;background:rgba(22,38,60,.7)}
.ax{position:absolute;font-family:var(--mono);font-size:9px;letter-spacing:.18em;color:var(--dim2);text-transform:uppercase}
.ax.x{bottom:2px;right:6px}.ax.y{top:2px;left:2px;writing-mode:vertical-lr}
.sweetz{position:absolute;left:0;top:0;width:42%;height:46%;background:radial-gradient(130% 130% at 0 0,rgba(0,229,196,.08),transparent 70%);opacity:0;transition:opacity 1.2s}
.sweetz.on{opacity:1}
.sweetz span{position:absolute;left:14px;top:12px;font-family:var(--hud);font-size:9px;letter-spacing:.22em;color:rgba(0,229,196,.55);text-transform:uppercase}
/* radar sweep */
#radar{position:absolute;inset:0;--a:0deg;pointer-events:none;opacity:0;transition:opacity .5s;background:conic-gradient(from var(--a) at 50% 50%,rgba(0,229,196,.16),rgba(0,229,196,.02) 13%,transparent 22%)}
#radar.on{opacity:1}
/* nodes */
.node{position:absolute;transform:translate(-50%,50%) scale(0);z-index:3;transition:left 1s cubic-bezier(.2,.9,.3,1),bottom 1s cubic-bezier(.2,.9,.3,1),transform .5s cubic-bezier(.2,1.3,.4,1),opacity .5s,filter .6s}
.node.shown{transform:translate(-50%,50%) scale(1)}
.node .glow{width:14px;height:14px;border-radius:50%;background:var(--dim2);position:relative;display:grid;place-items:center;transition:.5s}
.node.on .glow{width:38px;height:38px;background:radial-gradient(circle at 35% 30%,#5ff0dc,var(--teal));box-shadow:0 0 18px rgba(0,229,196,.6),inset 0 0 7px rgba(255,255,255,.45);animation:breathe 3.4s ease-in-out infinite}
.node.on.rank1 .glow{background:radial-gradient(circle at 35% 30%,#f4dc9a,var(--gold));box-shadow:0 0 24px rgba(231,200,120,.75);animation:breathe1 3.4s ease-in-out infinite}
@keyframes breathe{0%,100%{box-shadow:0 0 14px rgba(0,229,196,.5),inset 0 0 7px rgba(255,255,255,.4)}50%{box-shadow:0 0 26px rgba(0,229,196,.8),inset 0 0 7px rgba(255,255,255,.5)}}
@keyframes breathe1{0%,100%{box-shadow:0 0 20px rgba(231,200,120,.6)}50%{box-shadow:0 0 34px rgba(231,200,120,.95)}}
.node .rk{font-family:var(--mono);font-weight:700;font-size:13px;color:#04121a;opacity:0;transition:.4s}
.node.ranked .rk{opacity:1}
.node.on{cursor:pointer}.node.on:hover{z-index:8}.node.on:hover .glow{transform:scale(1.12)}
.node.excl{filter:grayscale(1) brightness(.6)}
.node.excl .glow{width:14px;height:14px;background:transparent;border:1px dashed rgba(94,115,140,.55)}
/* lock bracket */
.lock{position:absolute;inset:-13px;opacity:0;transform:scale(1.5);transition:opacity .35s,transform .45s cubic-bezier(.2,1.4,.4,1);pointer-events:none}
.node.locked .lock{opacity:1;transform:scale(1)}
.lock i{position:absolute;width:9px;height:9px;border:1.5px solid var(--teal)}
.node.rank1 .lock i{border-color:var(--gold)}
.lock .a{top:0;left:0;border-right:0;border-bottom:0}.lock .b{top:0;right:0;border-left:0;border-bottom:0}.lock .c{bottom:0;left:0;border-right:0;border-top:0}.lock .d{bottom:0;right:0;border-left:0;border-top:0}
/* reject */
.rej{position:absolute;inset:-9px;opacity:0;transition:opacity .4s;pointer-events:none}
.node.rejected .rej{opacity:1}
.rej::before,.rej::after{content:"";position:absolute;left:50%;top:50%;width:22px;height:1px;background:var(--red);transform-origin:center}
.rej::before{transform:translate(-50%,-50%) rotate(45deg)}.rej::after{transform:translate(-50%,-50%) rotate(-45deg)}
.rej b{position:absolute;left:50%;top:-14px;transform:translateX(-50%);font-family:var(--mono);font-size:7px;letter-spacing:.15em;color:var(--red);white-space:nowrap}
/* callout */
.callout{position:absolute;left:26px;top:50%;transform:translateY(-50%);pointer-events:none;opacity:0;transition:opacity .4s;z-index:9;background:rgba(5,10,18,.94);border:1px solid rgba(0,229,196,.4);padding:10px 14px;min-width:190px;box-shadow:0 10px 30px rgba(0,0,0,.6)}
.callout.on{opacity:1}
.callout .cn{font-family:var(--display);font-weight:700;font-size:16px;color:#fff}
.callout .cs{font-family:var(--mono);font-size:9px;color:var(--dim);text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px}
.callout .row{display:flex;justify-content:space-between;gap:16px;font-family:var(--mono);font-size:11px;padding:2px 0}
.callout .row span{color:var(--dim)}.callout .row b{color:var(--teal)}

/* chapter title card */
#chapter{position:absolute;inset:0;display:grid;place-items:center;pointer-events:none;z-index:20}
#chapter .card{text-align:center;opacity:0;transform:translateY(10px)}
#chapter .card.in{animation:chapIn 1.4s ease both}
@keyframes chapIn{0%{opacity:0;transform:translateY(14px)}18%,72%{opacity:1;transform:none}100%{opacity:0;transform:translateY(-10px)}}
#chapter .num{font-family:var(--mono);font-size:12px;letter-spacing:.4em;color:var(--teal);margin-bottom:12px}
#chapter .ttl{font-family:var(--display);font-weight:700;font-size:52px;letter-spacing:.14em;color:#fff;text-shadow:0 0 30px rgba(0,229,196,.35)}
#chapter .sub{font-family:var(--mono);font-size:11px;letter-spacing:.16em;color:var(--dim);margin-top:12px;text-transform:uppercase}

/* tip */
#tip{position:fixed;z-index:60;pointer-events:none;opacity:0;transform:translate(14px,-50%);transition:opacity .15s;background:rgba(5,10,18,.96);border:1px solid rgba(0,229,196,.4);padding:8px 11px;font-family:var(--mono);font-size:11px;white-space:nowrap;box-shadow:0 8px 24px rgba(0,0,0,.6)}
#tip .tn{color:#fff;font-family:var(--display);font-weight:600;font-size:13px}#tip .ts{color:var(--dim);font-size:9px;text-transform:uppercase;letter-spacing:.1em}#tip b{color:var(--teal2)}

/* rail */
.rail{display:flex;align-items:center;gap:12px;padding:12px 26px;border-top:1px solid var(--border);flex:none;opacity:0;transform:translateY(12px);transition:.6s}
.rail.in{opacity:1;transform:none}
.rail .lbl{font-family:var(--hud);font-size:9px;letter-spacing:.26em;color:var(--dim2);text-transform:uppercase}
.chips{display:flex;gap:8px;flex:1;overflow:hidden}
.chip{display:flex;align-items:center;gap:9px;padding:7px 13px 7px 10px;border:1px solid var(--border);background:rgba(10,20,36,.6);cursor:pointer;transition:.2s;--c:6px;clip-path:polygon(var(--c) 0,100% 0,100% calc(100% - var(--c)),calc(100% - var(--c)) 100%,0 100%,0 var(--c))}
.chip:hover{border-color:rgba(0,229,196,.5);background:rgba(0,229,196,.06)}
.chip.r1{border-color:rgba(231,200,120,.4)}
.chip .n{font-family:var(--mono);font-weight:600;font-size:13px;color:var(--dim2)}.chip.r1 .n{color:var(--gold)}
.chip .nm{font-family:var(--display);font-weight:600;font-size:14px;color:#fff}
.chip .rt{font-family:var(--mono);font-size:11px;color:#7FE9CE}
.rail .traj{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--teal);border:1px solid rgba(0,229,196,.4);padding:7px 12px;cursor:pointer;flex:none;transition:.2s}
.rail .traj:hover{background:rgba(0,229,196,.12)}

/* drawer */
#drawer{position:fixed;top:0;right:0;bottom:0;width:min(440px,90vw);background:linear-gradient(var(--panel),#07101d);border-left:1px solid rgba(0,229,196,.3);z-index:40;transform:translateX(100%);transition:transform .4s cubic-bezier(.3,.9,.3,1);box-shadow:-20px 0 60px rgba(0,0,0,.6);overflow-y:auto;padding:24px}
#drawer.open{transform:none}
#drawer .x{position:absolute;top:16px;right:18px;font-family:var(--mono);font-size:11px;color:var(--dim);cursor:pointer;letter-spacing:.1em}
#drawer .x:hover{color:var(--teal)}
.d-pre{font-family:var(--hud);font-size:9px;letter-spacing:.28em;color:var(--teal);text-transform:uppercase;margin-bottom:6px}
.d-name{font-family:var(--display);font-weight:700;font-size:26px;color:#fff}
.d-strat{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-bottom:16px}
.d-p{color:#C2D0E0;font-size:13.5px;line-height:1.55}
.mgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--border);border:1px solid var(--border);margin:16px 0}
.mgrid .cell{background:var(--panel);padding:9px 8px;text-align:center}.mgrid .cell b{display:block;font-family:var(--mono);font-size:13px;color:#E7EFF9}.mgrid .cell i{font-family:var(--mono);font-size:7px;letter-spacing:.08em;text-transform:uppercase;color:var(--dim2);font-style:normal}
.src-lbl{font-family:var(--hud);font-size:8.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--dim2);margin:14px 0 10px}
.chipx{display:flex;flex-wrap:wrap;gap:6px}.chipx span{font-family:var(--mono);font-size:10px;padding:5px 9px;background:rgba(8,18,32,.7);border:1px solid var(--border);color:var(--ink);display:inline-flex;align-items:center;gap:5px}
.chipx .ok{border-color:rgba(0,229,196,.4);color:#9EEBDD}.chipx .ok::before{content:"";width:4px;height:4px;border-radius:50%;background:var(--teal)}
.chipx .warn{border-color:rgba(251,191,36,.45);color:#FCD777}.chipx .warn::before{content:"";width:4px;height:4px;border-radius:50%;background:var(--amber)}
#race{width:100%;height:280px;display:block;margin-top:8px}
.race-tag{position:absolute;font-family:var(--mono);font-size:10px;padding:2px 6px;background:rgba(5,10,18,.9);border:1px solid var(--border);transform:translateY(-50%);white-space:nowrap}

/* skip */
#skip{position:fixed;bottom:70px;right:26px;z-index:30;font-family:var(--mono);font-size:9.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--dim);border:1px solid var(--border);padding:7px 12px;cursor:pointer;background:rgba(5,10,18,.6);transition:.2s}
#skip:hover{color:var(--teal);border-color:rgba(0,229,196,.4)}
body.settled #skip{display:none}
@media(max-width:720px){.hdr .vtext{display:none}#field{inset:14px}#chapter .ttl{font-size:34px}}
"""

_JS = r"""
(function(){
var A=window.AMB;
function $(s,r){return (r||document).querySelector(s)}
function $$(s,r){return [].slice.call((r||document).querySelectorAll(s))}
function el(t,c){var e=document.createElement(t);if(c)e.className=c;return e}
function wait(ms){return new Promise(function(r){setTimeout(r,ms)})}
function pct(x){return x==null?'—':(x*100).toFixed(1)+'%'} function num(x){return x==null?'—':x.toFixed(2)}
var nodes={}, aborted=false;

function buildField(){
  var f=$('#field');
  A.funds.forEach(function(d){
    var n=el('div','node '+(d.excluded?'excl':'on'+(d.rank==1?' rank1':'')));
    n.dataset.fid=d.id; n.__d=d;
    n.dataset.tip="<div class='tn'>"+d.name+"</div><div class='ts'>"+d.strategy+"</div>return <b>"+pct(d.ret)+"</b> · vol <b>"+pct(d.vol)+"</b> · sharpe <b>"+num(d.sharpe)+"</b>";
    var g=el('div','glow'); var rk=el('span','rk'); rk.textContent=d.rank?String(d.rank):''; g.appendChild(rk);
    var lock=el('div','lock'); ['a','b','c','d'].forEach(function(k){var i=el('i',k);lock.appendChild(i)});
    var rej=el('div','rej'); var rb=el('b');rb.textContent='REJECTED';rej.appendChild(rb);
    n.appendChild(lock);n.appendChild(rej);n.appendChild(g);
    n.style.left='50%';n.style.bottom='50%';
    f.appendChild(n); nodes[d.id]=n;
  });
}
function place(n){ n.classList.add('shown'); n.style.left=n.__d.x+'%'; n.style.bottom=n.__d.y+'%'; }
function zoom(){ A.funds.forEach(function(d){var n=nodes[d.id]; if(d.excluded){n.style.opacity='0';n.style.transform='translate(-50%,50%) scale(.4)';} else {n.style.left=d.xz+'%';n.style.bottom=d.yz+'%';} }); }

function callout(d){
  var c=$('#callout'); if(!c){c=el('div','callout');c.id='callout';$('.stage').appendChild(c)}
  c.innerHTML="<div class='cn'>"+d.name+"</div><div class='cs'>"+d.strategy+"</div>"+
    "<div class='row'><span>return</span><b>"+pct(d.ret)+"</b></div>"+
    "<div class='row'><span>sharpe</span><b>"+num(d.sharpe)+"</b></div>"+
    "<div class='row'><span>max dd</span><b>"+pct(d.maxdd)+"</b></div>";
  c.classList.add('on'); return c;
}
function chapter(num,ttl,sub){
  var c=$('#chapter'); c.innerHTML="<div class='card'><div class='num'>"+num+"</div><div class='ttl'>"+ttl+"</div><div class='sub'>"+sub+"</div></div>";
  var card=$('.card',c); void card.offsetWidth; card.classList.add('in');
}

async function story(){
  // header
  $('.hdr').classList.add('in'); typeVerdict(false);
  // radar
  var rad=$('#radar'); 
  // ① universe
  chapter('CHAPTER 01','THE UNIVERSE', A.funds.length+' candidates in the mandate space');
  await wait(700);
  var order=A.funds.slice();
  for(var i=0;i<order.length;i++){ if(aborted)return; place(nodes[order[i].id]); await wait(130); }
  await wait(900);
  // ② mandate — radar sweep + reject excluded
  chapter('CHAPTER 02','THE MANDATE', 'filtering for liquidity + risk');
  await wait(600);
  rad.classList.add('on'); rad.__spin=spin(rad); 
  var excl=A.funds.filter(function(d){return d.excluded});
  for(var j=0;j<excl.length;j++){ if(aborted)return; nodes[excl[j].id].classList.add('rejected'); await wait(420); }
  await wait(600); rad.classList.remove('on');
  await wait(500);
  zoom(); await wait(1150);
  // ③ acquisition — lock survivors in rank order + callout
  chapter('CHAPTER 03','ACQUISITION', 'ranking the survivors');
  await wait(700);
  var sl=A.funds.filter(function(d){return !d.excluded}).sort(function(a,b){return a.rank-b.rank});
  for(var k=0;k<sl.length;k++){ if(aborted)return; var n=nodes[sl[k].id];
    n.classList.add('locked','ranked'); var c=callout(sl[k]);
    await wait(640); c.classList.remove('on'); await wait(150);
  }
  $('.sweetz').classList.add('on');
  await wait(400);
  // ④ the call
  chapter('CHAPTER 04','THE CALL', A.funds.filter(function(d){return d.rank==1})[0].name);
  await wait(1500);
  settle();
}
function spin(rad){var a=0,run=true;(function step(){if(!run||!rad.classList.contains('on'))return;a=(a+2.6)%360;rad.style.setProperty('--a',a+'deg');requestAnimationFrame(step)})();return function(){run=false}}

var vTimer;
function typeVerdict(instant){var el2=$('#vtext'); var t=A.verdict; if(instant){el2.textContent=t;return} var i=0; clearInterval(vTimer); vTimer=setInterval(function(){el2.textContent=t.slice(0,i++);if(i>t.length)clearInterval(vTimer)},22)}

function settle(){
  document.body.classList.add('settled');
  $('#chapter').innerHTML='';
  $('.rail').classList.add('in');
  // unlock brackets remain on winner only
  A.funds.forEach(function(d){ if(!d.excluded && d.rank!=1) nodes[d.id].classList.remove('locked'); });
  typeVerdict(false);
}

/* drawer */
function openDrawer(html){var d=$('#drawer');d.innerHTML="<div class='x' id='dx'>✕ close</div>"+html;d.classList.add('open');$('#dx').addEventListener('click',closeDrawer)}
function closeDrawer(){$('#drawer').classList.remove('open')}
function fundDrawer(fid){var d=A.funds.filter(function(f){return f.id==fid})[0];if(!d)return;
  openDrawer("<div class='d-pre'>◆ Fund brief · rank "+(d.rank?String(d.rank).padStart(2,'0'):'—')+"</div><div class='d-name'>"+d.name+"</div><div class='d-strat'>"+d.strategy+"</div>"+d.detail);
}
function trajDrawer(){
  openDrawer("<div class='d-pre'>◆ 36-month trajectory</div><div class='d-name' style='font-size:20px'>Growth of $1</div><div class='d-strat'>cumulative, shortlisted funds</div><div style='position:relative'><svg id='race'></svg></div>");
  buildRace($('#race'));
}
function buildRace(svg){
  var host=svg.parentNode; var W=400,H=280,pad=8;
  var funds=A.funds.filter(function(d){return !d.excluded && d.wealth&&d.wealth.length}).sort(function(a,b){return a.rank-b.rank});
  var lo=1e9,hi=-1e9,n=funds[0].wealth.length; funds.forEach(function(d){d.wealth.forEach(function(w){lo=Math.min(lo,w);hi=Math.max(hi,w)})});
  var X=function(i){return pad+i/(n-1)*(W-2*pad)},Y=function(w){return H-pad-(w-lo)/((hi-lo)||1)*(H-2*pad)};
  var COLORS=['#E7C878','#00E5C4','#22D3EE','#34D399','#B794F4'];
  svg.setAttribute('viewBox','0 0 '+W+' '+H);svg.setAttribute('preserveAspectRatio','none');
  var ns='http://www.w3.org/2000/svg';
  funds.forEach(function(d,idx){var col=COLORS[Math.min(idx,4)];var pts=d.wealth.map(function(w,i){return X(i)+','+Y(w)}).join(' ');
    var pl=document.createElementNS(ns,'polyline');pl.setAttribute('points',pts);pl.setAttribute('fill','none');pl.setAttribute('stroke',col);pl.setAttribute('stroke-width','2');pl.setAttribute('vector-effect','non-scaling-stroke');pl.style.filter='drop-shadow(0 0 3px '+col+'88)';pl.style.strokeDasharray='2000';pl.style.strokeDashoffset='2000';svg.appendChild(pl);
    setTimeout(function(){pl.style.transition='stroke-dashoffset 1.3s ease';pl.style.strokeDashoffset='0'},60+idx*90);
    var t=el('div','race-tag');t.style.color=col;t.style.borderColor=col+'66';t.innerHTML=d.name.split(' ')[0]+" <b style='color:#fff'>+"+((d.wealth[n-1]-1)*100).toFixed(0)+"%</b>";t.style.right='6px';t.style.top=(Y(d.wealth[n-1])/H*100)+'%';host.appendChild(t);
  });
}

function wire(){
  var tip=$('#tip');
  document.addEventListener('mousemove',function(e){var n=e.target.closest('.node');if(n&&n.dataset.tip&&document.body.classList.contains('settled')){tip.innerHTML=n.dataset.tip;tip.style.opacity=1;tip.style.left=e.clientX+'px';tip.style.top=e.clientY+'px'}else tip.style.opacity=0});
  document.addEventListener('click',function(e){
    var n=e.target.closest('.node.on'); if(n&&document.body.classList.contains('settled')){fundDrawer(n.dataset.fid);return}
    var ch=e.target.closest('.chip'); if(ch){fundDrawer(ch.dataset.fid);return}
    if(e.target.closest('#traj')){trajDrawer();return}
  });
  var sk=$('#skip'); if(sk)sk.addEventListener('click',function(){aborted=true;A.funds.forEach(function(d){var n=nodes[d.id];n.classList.add('shown');if(d.excluded){n.style.opacity='0';n.style.transform='translate(-50%,50%) scale(.4)';}else{n.classList.add('ranked');n.style.left=d.xz+'%';n.style.bottom=d.yz+'%';if(d.rank==1)n.classList.add('locked');}});$('.sweetz').classList.add('on');settle()});
}
window.addEventListener('DOMContentLoaded',function(){buildField();wire();story();});
})();
"""

def _detail_html(sec, full, e):
    cells="".join(f'<div class="cell"><b>{(_pct(full.get(k)) if k in _PCT else _num(full.get(k)))}</b><i>{k.replace("_"," ")}</i></div>' for k in METRIC_KEYS)
    chips=""
    if sec:
        for c in sec.claims:
            k="ok" if c.verified else "warn";src=e("; ".join(c.source_refs) or "no source")
            chips+=f'<span class="{k}" title="{src}">{e(c.text)}</span>'
    body=e(sec.body) if sec else ""
    return (f'<p class="d-p">{body}</p><div class="mgrid">{cells}</div>'
            f'<div class="src-lbl">Sources · verified against the metrics engine</div><div class="chipx">{chips}</div>')

def render_html(memo, ctx=None):
    e=html.escape;a=memo.audit;sl=memo.shortlist
    ranks={s.fund_id:s.rank for s in sl}
    series=(ctx.series_by_fund if ctx else {}) or {}
    mbf=(ctx.metrics_by_fund if ctx else {s.fund_id:s.metrics for s in sl})
    secs_by_fund={}
    for i,s in enumerate(sl):
        secs_by_fund[s.fund_id]=memo.sections[1+i] if 1+i<len(memo.sections) else None

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
                "x":round(12+(m["ann_vol"]-vmin)/vr*76,1),"y":round(12+(m["ann_return"]-rmin)/rr*76,1),
                "ret":m.get("ann_return"),"vol":m.get("ann_vol"),"sharpe":m.get("sharpe"),"maxdd":m.get("max_drawdown"),
                "wealth":wealth,"detail":_detail_html(secs_by_fund.get(fid),mbf.get(fid,{}),e)})
    # zoomed positions: survivors normalized to their own range (fills the field)
    surv=[d for d in fd if not d["excluded"]]
    if surv:
        zv=[d["vol"] for d in surv];zr=[d["ret"] for d in surv]
        zvmin,zvmax=min(zv),max(zv);zrmin,zrmax=min(zr),max(zr);zvr=(zvmax-zvmin) or 1;zrr=(zrmax-zrmin) or 1
        for d in surv:
            d["xz"]=round(14+(d["vol"]-zvmin)/zvr*72,1);d["yz"]=round(14+(d["ret"]-zrmin)/zrr*72,1)
    for d in fd:
        d.setdefault("xz",d["x"]);d.setdefault("yz",d["y"])
    top=sl[0] if sl else None
    verdict=f"{top.name} leads the shortlist on risk-adjusted return." if top else "No fund met the mandate."
    DATA={"funds":fd,"verdict":verdict,"model":memo.generated_by,"verified":a.get("verified_count",0),"total":a.get("claim_count",0),"mandate":memo.mandate}

    chips="".join(
        f'<div class="chip{" r1" if s.rank==1 else ""}" data-fid="{e(s.fund_id)}"><span class="n">{s.rank:02d}</span>'
        f'<span class="nm">{e(s.name)}</span><span class="rt">{_pct(s.metrics.get("ann_return"))}</span></div>' for s in sl)

    header=(f'<div class="hdr"><div class="brand"><div class="logo"></div><div class="wm">EQUI</div></div>'
            f'<div class="verdict"><div class="vpre">◆ Recommendation</div><div class="vtext" id="vtext"></div></div>'
            f'<div class="right"><span class="tag model">{e(memo.generated_by)}</span>'
            f'<span class="vbadge"><i></i>{a.get("verified_count",0)}/{a.get("claim_count",0)} verified</span></div></div>')

    stage=('<div class="stage"><div id="field"><div class="sweetz"><span>◤ sweet spot · high return / low risk</span></div>'
           '<div class="ax y">Return →</div><div class="ax x">Risk · volatility →</div>'
           '<div id="radar"></div></div>'
           '<div id="chapter"></div></div>')

    rail=(f'<div class="rail"><div class="lbl">Shortlist</div><div class="chips">{chips}</div>'
          f'<div class="traj" id="traj">▸ 36-mo trajectory</div></div>')

    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(memo.title)}</title>'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Electrolize&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
            f'<style>{_CSS}</style></head><body>'
            '<div class="atmo"><div class="grid"></div></div><div id="tip"></div>'
            f'<div class="app">{header}{stage}{rail}</div>'
            '<div id="drawer"></div><div id="skip">▸ skip intro</div>'
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
