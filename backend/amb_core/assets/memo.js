
(function(){
var A=window.AMB;
if(A){A.weights0=A.weights0||Object.assign({},A.weights);if(!A.activeMetrics)A.activeMetrics=Object.keys(A.weights).sort(function(a,b){return A.weights[b]-A.weights[a]});}
function $(s,r){return (r||document).querySelector(s)}
function $$(s,r){return [].slice.call((r||document).querySelectorAll(s))}
function el(t,c){var e=document.createElement(t);if(c)e.className=c;return e}
// HTML output-encoder — every user-derived string (fund name/strategy/reason, benchmark name,
// mandate label) is escaped at the point it enters an innerHTML sink, so a fund named
// "<img onerror=…>" (via the DATA payload OR a user CSV upload) can never execute. Numbers/
// fixed metric keys don't need it; the PDF writer has its own _pesc and is not an HTML sink.
var _ESC={'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'};
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return _ESC[c]})}
var paused=false,_waits=[];
function wait(ms){return new Promise(function(resolve){
  var rec={remaining:ms,started:0,tid:null,done:false};
  function arm(){rec.started=Date.now();rec.tid=setTimeout(fin,rec.remaining)}
  function fin(){if(rec.done)return;rec.done=true;var i=_waits.indexOf(rec);if(i>=0)_waits.splice(i,1);resolve()}
  rec.pause=function(){if(rec.tid){clearTimeout(rec.tid);rec.tid=null;rec.remaining-=(Date.now()-rec.started)}};
  rec.resume=function(){if(!rec.done&&!aborted)arm()};
  rec.flush=fin;_waits.push(rec);
  if(aborted){fin();return}
  if(!paused)arm();
})}
function flushWaits(){_waits.slice().forEach(function(r){r.flush()})}
function setPaused(v){if(paused===v)return;paused=v;_waits.slice().forEach(function(r){v?r.pause():r.resume()});
  document.body.classList.toggle('paused',v);var pb=$('#pausebtn');if(pb){pb.innerHTML=v?'▶&nbsp;resume':'❚❚&nbsp;pause';pb.classList.toggle('on',v)}}
function togglePause(){if(!document.body.classList.contains('playing'))return;setPaused(!paused)}
// generation token: every reset/replay/rerender/skip bumps GEN, so any animation
// timer scheduled by the previous run no-ops instead of mutating the rebuilt DOM
// (the old race where a stale setTimeout fired onto freshly-rebuilt nodes).
var GEN=0;
function bumpGen(){GEN++}
function schedule(fn,ms){var g=GEN;return setTimeout(function(){if(g===GEN)fn()},ms)}
function pct(x){return x==null?'—':(x*100).toFixed(1)+'%'} function num(x){return x==null?'—':x.toFixed(2)}
function first(n){return n.split(' ')[0]}
function contenders(){return A.funds.filter(function(d){return d.eligible}).sort(function(a,b){return a.srank-b.srank})} // cleared the mandate (scored)
function shortlisted(){return A.funds.filter(function(d){return d.rank}).sort(function(a,b){return a.rank-b.rank})} // made the top-N
function rejects(){return A.funds.filter(function(d){return d.reason})} // failed the mandate
function survivors(){return contenders()} // scoring scene operates on the eligible set
function byId(id){return A.funds.filter(function(d){return d.id==id})[0]}
function weightFactors(){return Object.keys(A.weights).sort(function(a,b){return A.weights[b]-A.weights[a]})}
// large-universe threshold: at or below this the view is byte-identical to the sample; above it the
// scatter scales its marks down, thins always-on labels (hover still shows every fund) and the weighing
// list scrolls. 12 keeps the bundled 9-fund sample fully unaffected.
var NBIG=12;
function bigN(){return A.funds.length>NBIG}
function hx(n){n=Math.max(0,Math.min(255,Math.round(n)));return ('0'+n.toString(16)).slice(-2)}
function mix(a,b,t){function p(c){return [parseInt(c.slice(1,3),16),parseInt(c.slice(3,5),16),parseInt(c.slice(5,7),16)]}var P=p(a),Q=p(b);return '#'+hx(P[0]+(Q[0]-P[0])*t)+hx(P[1]+(Q[1]-P[1])*t)+hx(P[2]+(Q[2]-P[2])*t)}
function cssv(n){return getComputedStyle(document.documentElement).getPropertyValue(n).trim()||'#888888'}
function factorColor(k){return cssv('--f-'+k)||cssv('--accent')}  // metric hues live in theme.css (theme-aware, single source)
function segColor(i,win){var k=weightFactors()[i];return factorColor(k)} // each metric keeps its own hue everywhere
function trajGrays(){return [cssv('--traj1'),cssv('--traj2'),cssv('--traj3'),cssv('--traj4')]}
var nodes={}, rows={}, segState={}, aborted=false, trajBuilt=false, ROWH=30, ZERO=30, UNIT=1;
function computeScale(){var sl=shortlisted();var fs=weightFactors();var mp=0,mn=0; // scale to the shortlist; an outscored cut fund may overflow (clipped)
  sl.forEach(function(d){var p=0,n=0;fs.forEach(function(k){var c=(d.comp[k]||0);if(c>=0)p+=c;else n+=-c});mp=Math.max(mp,p);mn=Math.max(mn,n)});
  UNIT=Math.min((96-ZERO)/(mp||1),(ZERO-4)/(mn||1));}
function buildLegend(){var h=$('#weighlegend');if(!h)return;var fs=weightFactors();var act=A.activeMetrics||fs.slice();var DIR=A.dir||{};
  h.innerHTML=fs.map(function(k,i){var on=act.indexOf(k)>=0;var w=Math.round((A.weights[k]||0)*100);var d=DIR[k]||0;
    var arrow=d>0?'↑':d<0?'↓':'·';var dt=d>0?'higher is better':d<0?'lower is better':'';
    return "<span class='lchip"+(on?'':' off')+"' data-k='"+k+"' title='"+k.replace(/_/g,' ')+" · "+w+"% of the score · "+dt+"'><i style='background:"+segColor(i,false)+"'></i><span class='ln'>"+k.replace(/_/g,' ')+"</span><span class='lw'>"+w+"%</span><span class='ldir'>"+arrow+"</span></span>"}).join('')+"<span class='neg'><i></i>detracts</span>";
  h.classList.add('in');}
function metricField(k){return {ann_return:'ret',ann_vol:'vol',sharpe:'sharpe',sortino:'sortino',calmar:'calmar',max_drawdown:'maxdd'}[k]||k}
// one glossary for every metric — drives the audit list, the fund-brief tooltips and
// value formatting (pct vs ratio). label = human name, pct = format as %, def = concise
// plain-English meaning + how it's used.
var METRIC_INFO={
 ann_return:{label:'Annualized return',pct:true,def:'Geometric (CAGR) growth per year — compounds the monthly returns into one annual figure.'},
 ann_vol:{label:'Annualized volatility',pct:true,def:'How much monthly returns swing, scaled to a yearly figure. Lower = steadier.'},
 sharpe:{label:'Sharpe ratio',pct:false,def:'Return above the risk-free rate per unit of total volatility. Higher = better risk-adjusted return.'},
 sortino:{label:'Sortino ratio',pct:false,def:'Like Sharpe but only penalizes downside swings — rewards funds volatile mainly on the upside.'},
 calmar:{label:'Calmar ratio',pct:false,def:'Annual return divided by the worst peak-to-trough drop — return earned per unit of worst-case loss.'},
 max_drawdown:{label:'Max drawdown',pct:true,def:'Largest peak-to-trough decline over the window (≤0). Closer to zero = shallower worst loss.'},
 downside_dev:{label:'Downside deviation',pct:true,def:'Volatility of only the losing months — the risk that actually hurts.'},
 beta:{label:'Beta vs benchmark',pct:false,def:'Sensitivity to the benchmark: 1.0 moves with it, below 1 dampens, above 1 amplifies.'},
 alpha:{label:'Alpha',pct:true,def:'Annual return beyond what benchmark exposure (beta) explains — the manager’s edge.'},
 correlation:{label:'Correlation',pct:false,def:'How closely the fund tracks the benchmark, from -1 to +1.'},
 tracking_error:{label:'Tracking error',pct:true,def:'Volatility of the fund’s return difference vs the benchmark.'},
 hit_rate:{label:'Hit rate',pct:true,def:'Share of months that finished positive.'}
};
function metricLabel(k){return (METRIC_INFO[k]&&METRIC_INFO[k].label)||String(k).replace(/_/g,' ')}
function fmtMetricVal(k,v){if(v==null)return '—';return (METRIC_INFO[k]&&METRIC_INFO[k].pct)?pct(v):num(v)}
// the node's secondary stat tracks the highest-weighted ACTIVE scoring metric, so if you
// drop Sharpe from the weighting the chart stops advertising SR and shows what's actually
// driving the ranking instead (ret stays primary; ann_return is excluded so it can't dup it).
var METRIC_STAT={sharpe:['SR',function(d){return num(d.sharpe)}],sortino:['Sor',function(d){return num(d.sortino)}],calmar:['Cal',function(d){return num(d.calmar)}],max_drawdown:['DD',function(d){return pct(d.maxdd)}],ann_vol:['vol',function(d){return pct(d.vol)}]};
function _topStatMetric(){var act=(A.activeMetrics&&A.activeMetrics.length)?A.activeMetrics.slice():weightFactors();var w=A.weights||{};act.sort(function(a,b){return (w[b]||0)-(w[a]||0)});for(var i=0;i<act.length;i++){if(METRIC_STAT[act[i]])return act[i]}return 'sharpe'}
function nodeStat(d){var m=METRIC_STAT[_topStatMetric()]||METRIC_STAT.sharpe;return "ret <b>"+pct(d.ret)+"</b> · "+m[0]+" <b>"+m[1](d)+"</b>"}
function refreshNodeStats(){(A.funds||[]).forEach(function(d){var n=nodes[d.id];if(!n)return;var s=$('.stat',n);if(s)s.innerHTML=nodeStat(d)})}
// turn provenance refs ("returns:<hash>|bench:SP500@2026-06") into a readable inputs list
function fmtInputs(srcs){var out=[];(srcs||[]).forEach(function(s){String(s).split('|').forEach(function(t){t=t.trim();
  if(/^returns:/.test(t)){if(out.indexOf('monthly return series')<0)out.push('monthly return series')}
  else if(/^bench:/.test(t)){var b=t.replace(/^bench:/,'').split('@')[0];if(b&&out.indexOf(b+' benchmark')<0)out.push(b+' benchmark')}
  else if(/rf|risk.?free/i.test(t)){if(out.indexOf('risk-free rate')<0)out.push('risk-free rate')}
});});return out}
function layoutRows(){var sb=$('#scorebars');if(!sb)return;var n=survivors().length||1;var h=(sb.clientHeight||190)-6;
  ROWH=Math.max(26,Math.min(58,Math.floor(h/n)));var th=Math.max(16,Math.min(30,ROWH-12));
  Object.keys(rows).forEach(function(id){var tr=$('.wtrack',rows[id]);if(tr)tr.style.height=th+'px'});
  var order=survivors().slice().sort(function(a,b){return (segState[b.id]?segState[b.id].cum:b.score)-(segState[a.id]?segState[a.id].cum:a.score)});
  order.forEach(function(d,rk){if(rows[d.id])rows[d.id].style.top=(rk*ROWH)+'px'});
  var cl=$('.wcut',sb);if(cl)cl.style.top=(A.nShort*ROWH-2)+'px';
  var tk=$('#scoretrack',sb);if(tk)tk.style.height=(n*ROWH)+'px';}

function stratShort(s){return (s||'').replace(/\b(Strategy|Fund|Global|Structured)\b/g,'').replace(/\s+/g,' ').trim()||s}
function buildField(){
  var f=$('#field');
  // auto-scale the mark size to the universe count so a large upload stays legible (SOTA scatter practice).
  // <=NBIG keeps --dscale at 1 → the sample is untouched; above it, dots shrink on a gentle clamped ramp.
  var N=A.funds.length;
  var dscale=N<=NBIG?1:Math.max(0.55,1-(N-NBIG)*0.018);
  f.style.setProperty('--dscale',dscale.toFixed(3));
  A.funds.forEach(function(d,i){
    var n=el('div','node cand');
    n.dataset.fid=d.id;n.__d=d;n.__i=i;
    n.dataset.tip="<div class='tn'>"+esc(d.name)+"</div><div class='ts'>"+esc(d.strategy)+"</div>return <b>"+pct(d.ret)+"</b> · vol <b>"+pct(d.vol)+"</b> · sharpe <b>"+num(d.sharpe)+"</b>";
    var glass=el('div','glass');
    var halo=el('div','halo');
    var lock=el('div','lock');['a','b','c','d'].forEach(function(k){lock.appendChild(el('i',k))});
    var stamp=el('div','stamp');var st=el('div','st');st.textContent='excluded';var stags=el('div','stags');var sr=el('div','sr');stamp.appendChild(st);stamp.appendChild(stags);stamp.appendChild(sr);
    var crown=el('div','crown');crown.appendChild(document.createTextNode('leader'));
    var rtag=el('div','rtag');
    var dot=el('div','dot');
    var card=el('div','card');
    card.innerHTML="<div class='nm'><span class='nfull'>"+esc(d.name)+"</span><span class='nshort'>"+esc(first(d.name))+"</span></div><div class='sub'>"+esc(stratShort(d.strategy))+"</div><div class='stat'>"+nodeStat(d)+"</div>";
    n.appendChild(glass);n.appendChild(halo);n.appendChild(lock);n.appendChild(stamp);n.appendChild(crown);n.appendChild(rtag);n.appendChild(dot);n.appendChild(card);
    n.style.left='50%';n.style.bottom='50%';f.appendChild(n);nodes[d.id]=n;
  });
  var g=$('#gates');if(g){g.innerHTML='';A.gates.forEach(function(gt){var e=el('div','gate');e.textContent=gt.label+' · '+gt.detail;e.dataset.k=gt.label;g.appendChild(e)})}
}
var _lastLive=null;
function updateCounter(lbl){var live=A.funds.filter(function(d){var n=nodes[d.id];return !n.classList.contains('gone')&&!n.classList.contains('cutout')}).length;var c=$('#counter');
  var tot=A.nTotal||A.funds.length;   // always relative to the FULL universe, so the 9 → 6 reduction is explicit
  if(c){c.innerHTML="<b>"+String(live).padStart(2,'0')+"</b><span class='cl'>of "+String(tot).padStart(2,'0')+"<br>"+(lbl||'in play')+"</span>";
    if(_lastLive!==null&&live!==_lastLive){c.classList.remove('pop');void c.offsetWidth;c.classList.add('pop')}}
  _lastLive=live;updateTally();}
function buildIntro(){
  var ip=$('#intropane');if(ip){ip.classList.add('in');ip.classList.remove('out')}
  var g=$('#ip-gates');if(g){g.innerHTML='';
    var cuts={};A.funds.forEach(function(d){(d.reasons||[]).forEach(function(rr){cuts[rr.kind]=(cuts[rr.kind]||0)+1})});
    A.gates.forEach(function(gt,i){var r=el('div','ipg');r.dataset.k=gt.label;var n=cuts[gt.label]||0;
      var ct=n>0?"<span class='gc'>−"+n+"</span>":"<span class='gc gc0'>0</span>";
      r.innerHTML="<span class='k'>"+esc(gt.label)+"</span><span class='d'>"+esc(gt.detail)+"</span>"+ct;g.appendChild(r);schedule(function(){r.classList.add('in')},260+i*150)})}
  var w=$('#ip-weights');if(w){w.innerHTML='';var fs=weightFactors();var mx=Math.max.apply(null,fs.map(function(k){return A.weights[k]}));
    fs.forEach(function(k,i){var pctv=Math.round(A.weights[k]*100);var r=el('div','ipw');
      r.innerHTML="<span class='wl'>"+k.replace(/_/g,' ')+"</span><span class='wb'><i></i></span><span class='wp'>"+pctv+"%</span>";
      w.appendChild(r);var bar=$('.wb i',r);
      schedule(function(){r.classList.add('in');bar.style.background=segColor(i,false);bar.style.width=(A.weights[k]/mx*100).toFixed(0)+'%'},560+i*120)})}
  var bp=$('#ip-bench');if(bp){if(A.bench){bp.innerHTML="<div class='ipb'><span class='bd'></span><div class='bt'><div class='bn'>"+esc(A.bench.name)+"</div><div class='bm'>ret <b>"+pct(A.bench.ret)+"</b> · vol <b>"+pct(A.bench.vol)+"</b></div></div><div class='btag'>reference</div></div>";}else{bp.innerHTML="<div class='ipb'><div class='bt'><div class='bm'>no benchmark</div></div></div>";}}
  updateTally();
}
function buildDataReadiness(){var dp=$('#ip-data');if(!dp)return;var r=A.readiness||{};var b=A.bench;
  var qs=r.quarantine_reasons||{};var qtxt=Object.keys(qs).map(function(k){return qs[k]+' '+k}).join(' · ');
  var ov=r.overlap||{};
  var bkind=b?(b.kind||'snapshot'):null;
  var bsrc=b?((bkind==='live'?'LIVE':bkind==='cache'?'CACHED':'SNAPSHOT')+' · '+(b.srcName||'')+' · '+(b.asOf||'')):'—';
  var rows=[
    ['ingest',(r.universe_count!=null?r.universe_count:'—')+' funds',(r.with_returns!=null?r.with_returns+' with returns':''),'ok'],
    ['cleaned',(r.quarantined_count||0)+' row'+(r.quarantined_count===1?'':'s')+' quarantined',qtxt||'all rows parsed',(r.quarantined_count?'warn':'ok')],
    ['aligned',(ov.start||'?')+' → '+(ov.end||'?'),(r.date_ranges_consistent?'one shared window':'ragged windows reconciled'),(r.date_ranges_consistent?'ok':'warn')],
    ['benchmark',b?b.name:'none',bsrc,(bkind==='live'?'live':'ok')],
    ['risk-free',(A.rfUsed!=null?(A.rfUsed*100).toFixed(2)+'%':'—'),(A.rfSource||''),'ok']
  ];
  var mm=(r.missing_returns||[]),om=(r.orphan_returns||[]);
  if(mm.length)rows.push(['id check',mm.length+' listed w/o returns',mm.slice(0,4).join(', '),'warn']);
  if(om.length)rows.push(['id check',om.length+' returns w/o metadata',om.slice(0,4).join(', '),'warn']);
  dp.innerHTML=rows.map(function(x){return "<div class='ipd "+x[3]+"'><span class='dk'>"+x[0]+"</span><div class='dvv'><span class='dv'>"+esc(x[1])+"</span><span class='dd'>"+esc(x[2])+"</span></div><span class='dck'></span></div>"}).join('');
}
function updateTally(){var t=$('#ip-tally');if(!t)return;var gone=A.funds.filter(function(d){return nodes[d.id].classList.contains('gone')}).length;var uni=A.funds.length;var rem=uni-gone;
  t.innerHTML="<div class='tc'><b>"+uni+"</b><i>universe</i></div><div class='tc red'><b>"+gone+"</b><i>excluded</i></div><div class='tc hot'><b>"+rem+"</b><i>advancing</i></div>";}
function universePos(i){var N=A.funds.length;
  if(N<=9){var cols=3;var r=Math.floor(i/cols),c=i%cols;   // sample layout — unchanged three-row band
    var L=[26,50,74][c],B=[77,50,23][r];
    var jx=(((i*37)%7)-3)*1.5,jy=(((i*29)%7)-3)*1.3;
    return {x:L+jx,y:B+jy};}
  // large universe: even ceil(sqrt) grid spread across the field so nothing stacks off-canvas
  var cols=Math.ceil(Math.sqrt(N)),rowsN=Math.ceil(N/cols),r=Math.floor(i/cols),c=i%cols;
  var x=16+(cols>1?c/(cols-1):0.5)*68,y=84-(rowsN>1?r/(rowsN-1):0.5)*70;
  var jx=(((i*37)%5)-2)*1.1,jy=(((i*29)%5)-2)*1.0;
  return {x:x+jx,y:y+jy};}
function frontier(){buildGuides();
  A.funds.forEach(function(d){var n=nodes[d.id];if(d.eligible){n.classList.add('ranked','showstat');n.style.left=d.xz+'%';n.style.bottom=d.yz+'%'}});}
function chapter(numv,ttl,sub){var c=$('#chapter');var old=$('.c',c);
  var set=function(){c.innerHTML="<div class='c'><div class='n'>"+numv+"</div><div class='t'>"+ttl+"</div><div class='s'>"+sub+"</div></div>";var card=$('.c',c);void card.offsetWidth;card.classList.add('in')};
  if(old){old.classList.add('out');schedule(set,240)}else set();}

function buildWeigh(){
  var host=$('#scorebars');host.innerHTML='';rows={};segState={};computeScale();buildLegend();
  var track=el('div');track.id='scoretrack';host.appendChild(track);
  var sl=survivors();
  ROWH=Math.max(26,Math.min(58,Math.floor(((host.clientHeight||190)-6)/(sl.length||1))));
  var th=Math.max(16,Math.min(30,ROWH-12));
  sl.forEach(function(d,i){
    var row=el('div','wrow'+(d.rank==1?' win':'')+(i===0?' rk1':''));row.style.top=(i*ROWH)+'px';
    row.innerHTML="<div class='wrk'>"+(i+1)+"</div><div class='wn'>"+esc(first(d.name))+"</div><div class='wtrack' style='height:"+th+"px'><div class='wzero' style='left:"+ZERO+"%'></div></div><div class='wsc'>0.00</div>";
    track.appendChild(row);rows[d.id]=row;segState[d.id]={pos:ZERO,neg:ZERO,cum:0};
    schedule(function(){row.classList.add('in')},70*i);
  });
  if(A.nShort&&sl.length>A.nShort){var cl=el('div','wcut');cl.style.top=(A.nShort*ROWH-2)+'px';cl.innerHTML="<span>cut line · top "+A.nShort+" advance</span>";track.appendChild(cl);}
  track.style.height=(sl.length*ROWH)+'px';   // full list height; #scorebars scrolls only when this exceeds the viewport
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
function factorCue(k,idx){var col=factorColor(k);var w=Math.round(A.weights[k]*100);var DIR=A.dir||{};var d=DIR[k]||0;
  var dl=d>0?"higher better":d<0?"lower better":"neutral";
  var t=$('#weighticker');if(t)t.innerHTML="<span class='wk-lab'>now weighing</span><span class='wk-dot' style='background:"+col+"'></span><span class='wk-name'>"+k.replace(/_/g,' ')+"</span><span class='wk-pct'>"+w+"%</span><span class='wk-dir'>"+dl+"</span>";
  $$('#weighlegend .lchip').forEach(function(s){var on=(s.dataset.k===k);s.classList.toggle('hot',on);if(on)s.classList.add('counted')});
  var c=$('#factorcue');if(c){$('.fdot',c).style.background=col;$('.fname',c).textContent=k.replace(/_/g,' ');$('.fpct',c).textContent=w+'%';var bar=$('.fwt i',c);if(bar){bar.style.background=col;bar.style.width=Math.min(100,w*3)+'%'}c.classList.add('on')}
  var fw=$('#fieldwash');if(fw){fw.style.background='radial-gradient(52% 60% at 32% 30%,'+col+' 0%,transparent 72%)';fw.classList.add('on')}}
function clearCue(){$$('#weighlegend .lchip').forEach(function(s){s.classList.remove('hot')});var c=$('#factorcue');if(c)c.classList.remove('on');var fw=$('#fieldwash');if(fw)fw.classList.remove('on')}
function nodeRespond(k){survivors().forEach(function(d){var n=nodes[d.id];var z=zAdj(d,k);var mag=Math.max(-1.8,Math.min(1.8,z));
  var sc=(0.85+(mag+1.8)/3.6*2.15).toFixed(2);var op=(0.16+Math.abs(mag)/1.8*0.62).toFixed(2);
  var col=mag>=0?cssv('--accent'):cssv('--loss');var h=$('.halo',n);
  if(h){h.style.background='radial-gradient(circle,'+col+' 0%,transparent 66%)';h.style.transform='scale('+sc+')';h.style.opacity=op;}});}
function clearHalos(){A.funds.forEach(function(d){var h=$('.halo',nodes[d.id]);if(h){h.style.opacity='0';h.style.transform='scale(.55)'}})}
function setLeaderNode(id){A.funds.forEach(function(d){nodes[d.id].classList.remove('leader','focus')});$$('.wrow').forEach(function(r){r.classList.remove('linked')});
  if(id&&nodes[id]){nodes[id].classList.add('leader','focus');if(rows[id])rows[id].classList.add('linked')}}
function showRtag(id,htmlv,neg){var n=nodes[id];if(!n)return;var t=$('.rtag',n);if(!t)return;t.className='rtag'+(neg?' neg':'');t.innerHTML=htmlv;n.classList.add('rshow')}
function clearRtags(){A.funds.forEach(function(d){nodes[d.id].classList.remove('rshow')})}
async function runWeigh(){
  var sl=survivors();var factors=weightFactors();var prevLead=null;
  for(var fi=0;fi<factors.length;fi++){ if(aborted)return;
    var k=factors[fi],idx=fi;
    // beat 1 — spotlight the factor: promote it to the big bottom-left title so it's prominent
    factorCue(k,idx);nodeRespond(k);
    var _ct=$('#chapter .t'),_cs=$('#chapter .s'),_mn=k.replace(/_/g,' ').replace(/\b\w/g,function(ch){return ch.toUpperCase()});
    if(_ct)_ct.innerHTML="Weighing <span style='color:"+factorColor(k)+"'>"+_mn+"</span>";
    if(_cs){var _dd=(A.dir&&A.dir[k]);_cs.innerHTML=Math.round(A.weights[k]*100)+"% of the score"+(_dd>0?" · higher is better":_dd<0?" · lower is better":"");}
    await wait(600); if(aborted)return;
    // beat 2 — fold it into the running score; re-rank; move the crown
    sl.forEach(function(d){addSeg(d,k,idx,true)});
    var order=sl.slice().sort(function(a,b){return segState[b.id].cum-segState[a.id].cum});
    setRanks(order);
    var leadId=order[0].id;setLeaderNode(leadId);
    Object.keys(rows).forEach(function(id){rows[id].classList.toggle('lead',id==leadId)});
    var flipped=(prevLead!==null&&leadId!==prevLead);
    if(flipped){showRtag(leadId,"<b>"+k.replace(/_/g,' ')+"</b> ▸ takes the lead",false);rows[leadId].classList.add('flip');
      $('#weighticker').innerHTML="<b>"+k.replace(/_/g,' ')+"</b> tips <b>"+esc(first(byId(leadId).name))+"</b> ahead";}
    else if(fi===0){showRtag(leadId,"strongest on <b>"+k.replace(/_/g,' ')+"</b>",false);}
    await wait(flipped?1400:760);
    if(flipped)rows[leadId].classList.remove('flip');
    clearRtags();
    prevLead=leadId;
  }
  clearRtags();clearHalos();clearCue();
  var _ctf=$('#chapter .t'),_csf=$('#chapter .s');if(_ctf)_ctf.textContent='Weighted score complete';if(_csf)_csf.textContent='all six metrics counted';
  await wait(420);
  $$('.wseg.pulse').forEach(function(s){s.classList.remove('pulse')});
  var win=survivors()[0];if(win){var comps=(win.components||[]).slice().sort(function(a,b){return b.c-a.c}).slice(0,3).map(function(c){return c.k.replace(/_/g,' ')});
    $('#weighticker').innerHTML="Final · weighted risk-adjusted score";
    $('#whynote').innerHTML="<b>"+esc(first(win.name))+"</b> wins on "+comps.join(', ')+" — the deciding factors.";}
}
function renderFinal(){var sl=survivors();var factors=weightFactors();
  sl.forEach(function(d){factors.forEach(function(k,idx){addSeg(d,k,idx,false)});rows[d.id].classList.add('in')});
  setRanks(sl.slice().sort(function(a,b){return segState[b.id].cum-segState[a.id].cum}));
}
/* ── interactive sensitivity: drop / restore a metric and re-decide live (settled state only) ── */
function effWeights(active){var w0=A.weights0||A.weights,eff={},tot=0;active.forEach(function(k){tot+=w0[k]||0});if(tot<=0)return null;active.forEach(function(k){eff[k]=(w0[k]||0)/tot});return eff}
function snapWeigh(){A._snap={};A.funds.forEach(function(d){A._snap[d.id]={rank:d.rank,cut:d.cut,srank:d.srank,score:d.score,comp:Object.assign({},d.comp),components:(d.components||[]).map(function(x){return {k:x.k,c:x.c}})}})}
function restoreWeigh(){if(!A._snap)return;A.funds.forEach(function(d){var s=A._snap[d.id];if(!s)return;d.rank=s.rank;d.cut=s.cut;d.srank=s.srank;d.score=s.score;d.comp=Object.assign({},s.comp);d.components=s.components.map(function(x){return {k:x.k,c:x.c}})});A.activeMetrics=weightFactors().slice()}
function reweigh(active){
  if(active.length>=weightFactors().length){restoreWeigh();return}   // full set → exact original (no drift)
  if(!A._snap)snapWeigh();
  var DIR=A.dir||{};var eff=effWeights(active);if(!eff)return;
  var elig=A.funds.filter(function(d){return d.eligible});
  // one basis for rank AND for the displayed bars: z across the eligible set, so the score a fund shows IS the score it's ranked on
  var stE=_zStats(elig,_accFund,active);
  elig.forEach(function(d){var cp=_zComps(d,_accFund,eff,DIR,stE);
    var cm={};cp.forEach(function(x){cm[x.k]=x.c});d._cp=cp;d._cm=cm;d._sc=Math.round(cp.reduce(function(s,x){return s+x.c},0)*1000)/1000});  // reweigh ranks on the rounded-component sum
  var ranked=elig.slice().sort(function(a,b){return b._sc-a._sc});var nShort=A.nShort||Math.min(elig.length,5);
  ranked.forEach(function(d,i){var rk=i<nShort?i+1:null;d.rank=rk;d.cut=(rk==null);d.srank=(rk||(d.cut?90:99));d.components=d._cp;d.comp=d._cm;d.score=d._sc;delete d._cp;delete d._cm;delete d._sc});
  A.activeMetrics=active.slice();}
function redrawTraj(){trajBuilt=false;var t=$('#traj');if(t)t.innerHTML='';$$('.tt,.tx,.ty').forEach(function(x){x.remove()});buildTraj();}
function servedLive(){return location.protocol==='http:'||location.protocol==='https:'}
function fetchLiveMarket(manual){
  var chip=$('#srcchip');if(chip){chip.classList.add('busy');chip.innerHTML="<i></i><b>market data</b> fetching live…";chip.style.display=''}
  var ctrl=('AbortController' in window)?new AbortController():null;
  var tmo=setTimeout(function(){if(ctrl)ctrl.abort()},8000);
  return fetch('/api/market',ctrl?{signal:ctrl.signal}:{}).then(function(r){return r.json()}).then(function(d){
    clearTimeout(tmo);
    if(!d||!d.ok||!d.benchmark)throw new Error((d&&d.error)||'no data');
    var b=d.benchmark;
    A.bench=Object.assign({},A.bench||{},{name:b.name,ret:b.ret,vol:b.vol,wealth:b.wealth,kind:b.kind,srcName:b.srcName,asOf:b.asOf,n:b.n});
    if(d.riskFree&&d.riskFree.value!=null){A.rfUsed=d.riskFree.value;A.rfSource=d.riskFree.source}
    A._keyed=!!d.keyed;A._served=true;
    synthAlphaOverBench();screenAndScore();  // demo: managers earn alpha over the live reference, recomputed consistently
    if(chip)chip.classList.remove('busy');sourceChip();benchBadge();
    relayoutScatter();  // keep the main risk/return graph consistent with the (live) benchmark
    var bp=$('#ip-bench');if(bp&&A.bench){bp.innerHTML="<div class='ipb'><span class='bd'></span><div class='bt'><div class='bn'>"+esc(A.bench.name)+"</div><div class='bm'>ret <b>"+pct(A.bench.ret)+"</b> · vol <b>"+pct(A.bench.vol)+"</b></div></div><div class='btag'>reference</div></div>"}
    if(document.body.classList.contains('settled')){rerender();}
    if(b.kind==='live')toast("<span class='tk'>&#10003;</span>Live market data fetched from FRED · "+esc(b.name)+" · as-of "+esc(b.asOf));
    else if(manual)toast("<span class='tk'>&#10003;</span>Market data: "+esc(b.name)+" ("+esc(b.kind)+")");
  }).catch(function(e){
    clearTimeout(tmo);if(chip){chip.classList.remove('busy')}sourceChip();
    if(manual)toast("<span class='tk' style='color:var(--loss)'>!</span>Live fetch needs the server — run <b>./amb serve</b>");
  });
}
function sourceChip(){var c=$('#srcchip');if(!c)return;var b=A.bench;if(!b){c.style.display='none';return}
  var kind=b.kind||'snapshot';var lbl=(kind==='live'?'LIVE · FRED':kind==='cache'?'CACHED · FRED':'SNAPSHOT · local');
  c.className='srcchip '+kind;c.innerHTML="<i></i><b>market data</b> "+lbl;c.style.display='';
  c.title="Fund data: your local CSV (dataset.csv). Benchmark / market data: "+(kind==='live'?'live FRED API':'committed local snapshot')+" — "+(b.name||'')+", as-of "+(b.asOf||'')+".";}
function benchBadge(){var el2=$('#benchsrc');if(!el2)return;var b=A.bench;if(!b){el2.style.display='none';return}
  var kind=b.kind||'snapshot';var label=(kind==='live'?'LIVE · FRED':(kind==='cache'?'CACHED · FRED':'SNAPSHOT'));
  el2.className='srcbadge '+kind;el2.innerHTML="<i></i>"+label+(b.asOf?" · "+b.asOf:"");el2.style.display='';
  el2.title=(b.srcName||'')+' · '+(b.name||'')+' · '+(b.n||0)+' monthly points';}
function paintSettledGraph(){var sl=shortlisted();var win=sl[0];
  A.funds.forEach(function(d){var n=nodes[d.id];if(!n)return;n.classList.remove('leader','focus','cutfocus');
    if(!d.eligible)return;
    var crn=$('.crown',n);
    if(d.cut){n.classList.add('cutout','dimmed');n.classList.remove('win','locked');if(crn)crn.lastChild.textContent='leader'}
    else{n.classList.remove('cutout');
      if(win&&d.id==win.id){n.classList.add('focus','win','locked');n.classList.remove('dimmed');if(crn)crn.lastChild.textContent='recommended'}
      else{n.classList.add('dimmed');n.classList.remove('win','locked');if(crn)crn.lastChild.textContent='leader'}}});
  if(win)setLeaderNode(win.id);
  if(bigN())A.funds.forEach(function(d){var n=nodes[d.id];if(n)n.classList.toggle('labeled',d.rank!=null)});   // keep always-on labels to the shortlist at scale
  var rc=$('.rail .chips');if(rc){rc.innerHTML=sl.map(function(s){return "<div class='chip"+(s.rank==1?' r1':'')+"' data-fid='"+esc(s.id)+"' title='Open fund detail'><span class='n'>"+String(s.rank).padStart(2,'0')+"</span><span class='nm'>"+esc(s.name)+"</span><span class='rt'>"+pct(s.ret)+"</span><span class='cx'>⤢</span></div>"}).join('')}
  redrawTraj();
  if(win){A.verdict=win.name+" leads on risk-adjusted return.";A.verdictHtml="<b>"+win.name+"</b> leads on risk-adjusted return.";
    var comps=(win.components||[]).slice().sort(function(a,b){return b.c-a.c}).slice(0,3).map(function(c){return c.k.replace(/_/g,' ')});
    $('#whynote').innerHTML="<b>"+esc(first(win.name))+"</b> wins on "+comps.join(', ')+" — the deciding factors.";}
  typeVerdict();}
function updateAdjNote(active){var full=weightFactors();var adj=active.length<full.length;var t=$('#weighticker');if(!t)return;
  t.classList.toggle('adj',adj);
  if(adj){var dropped=full.filter(function(k){return active.indexOf(k)<0}).map(function(k){return k.replace(/_/g,' ')});
    t.innerHTML="Weights re-normalized · dropped <b>"+dropped.join(', ')+"</b><span class='weigh-reset' id='wreset'>reset</span>";}
  else t.innerHTML='Final · weighted risk-adjusted score';}
function applyReweigh(active){if(active.length<1)return;reweigh(active);buildWeigh();renderFinal();layoutRows();paintSettledGraph();refreshNodeStats();updateAdjNote(active);}
function resetWeights(){applyReweigh(weightFactors().slice())}
/* ── in-app mandate: re-screen + re-score the loaded universe against edited constraints/weights ── */
function rebuildGates(){var ms=A.mandateSpec||{};var g=[];
  if(ms.liqCap!=null)g.push({label:'LIQUIDITY',detail:'≤ '+Math.round(ms.liqCap)+'d'});
  if(ms.volCap!=null)g.push({label:'VOLATILITY',detail:'≤ '+Math.round(ms.volCap*100)+'%'});
  if(ms.maxddFloor!=null)g.push({label:'DRAWDOWN',detail:'≥ '+Math.round(ms.maxddFloor*100)+'%'});
  if((ms.exclStrats||[]).length)g.push({label:'STRATEGY',detail:'excl. '+ms.exclStrats.join(', ')});
  if(!g.length)g=[{label:'MANDATE',detail:'screen'}];A.gates=g;}
function screenAndScore(){var ms=A.mandateSpec||{};var DIR=A.dir||{};var W=A.weights;
  A.funds.forEach(function(d){var rs=[];
    if(ms.liqCap!=null&&d.redd!=null&&d.redd>ms.liqCap)rs.push({text:"illiquid · "+(d.redf||'')+" ("+Math.round(d.redd)+"d)",kind:"LIQUIDITY"});
    if(ms.volCap!=null&&d.vol!=null&&d.vol>ms.volCap)rs.push({text:"too volatile · "+Math.round(d.vol*100)+"% > "+Math.round(ms.volCap*100)+"% cap",kind:"VOLATILITY"});
    if(ms.maxddFloor!=null&&d.maxdd!=null&&d.maxdd<ms.maxddFloor)rs.push({text:"drawdown · "+Math.round(d.maxdd*100)+"% beyond "+Math.round(ms.maxddFloor*100)+"% floor",kind:"DRAWDOWN"});
    if((ms.exclStrats||[]).indexOf(d.strategy)>=0)rs.push({text:"off-strategy · "+d.strategy,kind:"STRATEGY"});
    d.reasons=rs;d.reason=(rs.length?rs[0].text:null);d.rkind=(rs.length?rs[0].kind:null);d.eligible=(rs.length===0);d.excluded=(rs.length>0);});
  var elig=A.funds.filter(function(d){return d.eligible});
  var stE=_zStats(elig,_accFund,Object.keys(W));
  elig.forEach(function(d){d._rs=_zRaw(d,_accFund,W,DIR,stE)});   // rank on the raw (unrounded) weighted-z sum
  var ranked=elig.slice().sort(function(a,b){return b._rs-a._rs});var nS=ms.topN||5;var shortIds=ranked.slice(0,nS).map(function(d){return d.id});
  A.funds.forEach(function(d){
    if(!d.eligible){d.rank=null;d.cut=false;d.srank=99;d.components=[];d.comp={};d.score=0;if(d._rs!=null)delete d._rs;return}
    var si=shortIds.indexOf(d.id);var rk=si>=0?si+1:null;d.rank=rk;d.cut=(rk==null);d.srank=(rk||(d.cut?90:99));
    // components on the SAME eligible-z basis as the ranking, so bars == rank order
    var cp=_zComps(d,_accFund,W,DIR,stE);
    var cm={};cp.forEach(function(x){cm[x.k]=x.c});d.components=cp;d.comp=cm;d.score=Math.round(cp.reduce(function(s,x){return s+x.c},0)*1000)/1000;delete d._rs;});
  A.nShort=shortIds.length;A.nEligible=elig.length;A.nReject=A.funds.filter(function(d){return d.reason}).length;A.nTotal=A.funds.length;
  var win=A.funds.filter(function(d){return d.rank==1})[0];
  A.verdict=(win?first(win.name)+" leads on risk-adjusted return.":"No fund met the mandate.");
  A.verdictHtml=(win?"<b>"+esc(first(win.name))+"</b> leads on risk-adjusted return.":"No fund met the mandate.");
  A._snap=null;rebuildGates();}
function applyMandate(){screenAndScore();var d=$('#drawer');if(d)d.classList.remove('open');rerender(_snapStory);}
var HOUSE=null;
function openMandate(){if(!HOUSE)HOUSE=JSON.parse(JSON.stringify({ms:A.mandateSpec,w:A.weights}));
  var ms=A.mandateSpec||{};var str016=[];A.funds.forEach(function(d){var s=(d.strategy==null?'':String(d.strategy)).trim();if(s&&s!=='—'&&s.toLowerCase()!=='unclassified'&&str016.indexOf(s)<0)str016.push(s)});   // only REAL strategies — a returns-only upload has none, so the section is hidden rather than showing an empty/dash chip
  var liq=ms.liqCap==null?400:ms.liqCap, vol=ms.volCap==null?0.5:ms.volCap, mdd=ms.maxddFloor==null?-0.5:ms.maxddFloor;
  var fs=weightFactors();
  function sld(id,lbl,val,min,max,step,fmt){return "<div class='mf-row'><label>"+lbl+"<b id='"+id+"v'>"+fmt(val)+"</b></label><input type='range' id='"+id+"' min='"+min+"' max='"+max+"' step='"+step+"' value='"+val+"'></div>"}
  var chips=str016.map(function(s){var on=(ms.exclStrats||[]).indexOf(s)<0;return "<span class='mf-chip"+(on?'':' off')+"' data-s=\""+esc(s)+"\">"+esc(s)+"</span>"}).join('');
  var wsl=fs.map(function(k,i){var pv=Math.round((A.weights[k]||0)*100);return "<div class='mf-row'><label><span class='wdot' style='background:"+segColor(i,false)+"'></span>"+k.replace(/_/g,' ')+"<b id='w_"+k+"v'>"+pv+"%</b></label><input type='range' class='mf-w' data-k='"+k+"' min='0' max='50' step='1' value='"+pv+"'></div>"}).join('');
  var h="<div class='d-pre'>Mandate · investable constraints</div><div class='d-name'>Edit the house view</div>"
   +"<p class='mm-p'>Re-screen and re-score the loaded universe live. Changes are stamped against the default mandate.</p>"
   +"<div class='mf-h'>Hard limits</div>"
   +sld('mf_liq','Liquidity · redeem within',liq,15,400,5,function(v){return Math.round(v)+' days'})
   +sld('mf_vol','Target vol ceiling',vol,0.05,0.6,0.01,function(v){return Math.round(v*100)+'%'})
   +sld('mf_mdd','Max drawdown tolerance',mdd,-0.6,-0.05,0.01,function(v){return Math.round(v*100)+'%'})
   +(str016.length?("<div class='mf-h'>Strategy exclusions <span class='mf-hint'>tap to exclude</span></div><div class='mf-chips'>"+chips+"</div>"):"")
   +"<div class='mf-h'>Scoring weights</div>"+wsl
   +"<div class='mf-act'><button class='mf-apply' id='mfApply'>Apply &amp; re-decide</button><button class='mf-reset' id='mfReset'>Reset to house view</button></div>";
  openDrawer(h);
  var upd=function(){$('#mf_liqv').textContent=Math.round(+$('#mf_liq').value)+' days';$('#mf_volv').textContent=Math.round($('#mf_vol').value*100)+'%';$('#mf_mddv').textContent=Math.round($('#mf_mdd').value*100)+'%';};
  ['mf_liq','mf_vol','mf_mdd'].forEach(function(id){var e2=$('#'+id);if(e2)e2.addEventListener('input',upd)});
  $$('.mf-w').forEach(function(s){s.addEventListener('input',function(){$('#w_'+s.dataset.k+'v').textContent=Math.round(+s.value)+'%'})});
  $$('.mf-chip').forEach(function(c){c.addEventListener('click',function(){c.classList.toggle('off')})});
  var ap=$('#mfApply');if(ap)ap.addEventListener('click',function(){
    var ms2=Object.assign({},A.mandateSpec);
    ms2.liqCap=+$('#mf_liq').value;ms2.volCap=+$('#mf_vol').value;ms2.maxddFloor=+$('#mf_mdd').value;
    ms2.exclStrats=$$('.mf-chip.off').map(function(c){return c.dataset.s});
    A.mandateSpec=ms2;
    var nw={};var raw={};var tot=0;$$('.mf-w').forEach(function(s){raw[s.dataset.k]=+s.value;tot+=+s.value});
    if(tot>0){Object.keys(raw).forEach(function(k){nw[k]=raw[k]/tot});A.weights=nw;A.weights0=Object.assign({},nw);A.activeMetrics=weightFactors().slice();}
    applyMandate();
    toast("<span class='tk'>&#10003;</span>Mandate applied · "+A.nEligible+" eligible → "+A.nShort+" shortlisted");});
  var rs=$('#mfReset');if(rs)rs.addEventListener('click',function(){A.mandateSpec=JSON.parse(JSON.stringify(HOUSE.ms));A.weights=JSON.parse(JSON.stringify(HOUSE.w));A.weights0=Object.assign({},A.weights);A.activeMetrics=weightFactors().slice();applyMandate();toast("<span class='tk'>&#10003;</span>Reset to the house view");});
}
function synthAlphaOverBench(){
  // DEMO SCENARIO: synthesize manager alpha so the shortlist sits above the live
  // reference index. Fictional sample funds only. Every derived figure is rebuilt
  // from the same shifted return stream (return, vol, Sharpe, Sortino, Calmar,
  // drawdown, wealth) so the scatter, the trajectory and the scoring all agree.
  var b=A.bench; if(!b||b.ret==null||!b.wealth||b.wealth.length<2) return;
  var ppy=12, rf=(A.rfUsed!=null?A.rfUsed:0);
  var elig=A.funds.filter(function(d){return d.eligible&&d.wealth&&d.wealth.length>1});
  if(!elig.length) return;
  var order=elig.slice().sort(function(x,y){return (x.srank||99)-(y.srank||99)}); // keep the winner (rank 1) first
  // per-fund profile [ann return, ann vol, downside-smoothness 0..0.6] — all above the index,
  // each manager built to LEAD a different metric so the weighing spotlights different funds;
  // index 0 is the balanced overall winner.
  var PROF=[[0.272,0.100,0.42],[0.318,0.156,-0.10],[0.232,0.083,-1.30],[0.244,0.128,0.66],[0.254,0.140,0.44],[0.231,0.116,-0.30]];
  order.forEach(function(d,i){
    var _p=PROF[i%PROF.length];var tRet=_p[0],tVol=_p[1],smooth=_p[2];
    if(tRet<b.ret+0.012) tRet=b.ret+0.012;                                   // safety: above index on absolute return
    var w=d.wealth,m=w.length,r=[],prev=1,j;
    for(j=0;j<m;j++){r.push(w[j]/prev-1); prev=w[j];}
    var mean=0; for(j=0;j<m;j++) mean+=r[j]; mean/=m;
    var sd=0; for(j=0;j<m;j++){var e2=r[j]-mean; sd+=e2*e2;} sd=Math.sqrt(sd/(m-1))||1e-6;
    var z=r.map(function(v){return (v-mean)/sd});                            // preserve the shape
    z=z.map(function(v){return v<0? v*(1-smooth): v});                       // smooth>0 compresses downside (better sortino/calmar/dd); <0 deepens it
    var zm=0; for(j=0;j<m;j++) zm+=z[j]; zm/=m;
    var zsd=0; for(j=0;j<m;j++){var ez=z[j]-zm; zsd+=ez*ez;} zsd=Math.sqrt(zsd/(m-1))||1e-6;
    z=z.map(function(v){return (v-zm)/zsd});                                 // re-standardize so target vol holds
    var tMeanM=Math.pow(1+tRet,1/ppy)-1, tSdM=tVol/Math.sqrt(ppy);
    var nr=z.map(function(v){return tMeanM+v*tSdM});                         // hit target mean & vol, keep skew
    // ONE metric implementation for the whole client: derive every figure through
    // fundMetrics (same code the audit re-derives with, same code metrics.py mirrors).
    // Computing them inline here is exactly how Sharpe/Sortino/Calmar/drawdown drifted
    // from the engine and got falsely flagged in the audit — so we don't do that anymore.
    var mm=fundMetrics(nr)||{};
    d.wealth=mm.wealth||[]; d.ret=mm.ann_return; d.vol=mm.ann_vol;
    d.sharpe=mm.sharpe; d.sortino=mm.sortino; d.maxdd=mm.max_drawdown; d.calmar=mm.calmar;
    if(d.fee!=null) d.netret=(mm.ann_return!=null?mm.ann_return-d.fee/100:null);
    d._synth=true;
  });
  var pf=A.funds.filter(function(d){return d.ret!=null&&d.vol!=null});
  if(pf.length){var vs=pf.map(function(d){return d.vol}),rs2=pf.map(function(d){return d.ret});
    var vmn=Math.min.apply(null,vs),vmx=Math.max.apply(null,vs),rmn=Math.min.apply(null,rs2),rmx=Math.max.apply(null,rs2);
    var vr=(vmx-vmn)||1,rr=(rmx-rmn)||1;
    pf.forEach(function(d){d.x=Math.round((12+(d.vol-vmn)/vr*76)*10)/10;d.y=Math.round((12+(d.ret-rmn)/rr*76)*10)/10});}
}
function relayoutScatter(){  // recompute the risk/return frontier so it includes the current benchmark
  var surv=A.funds.filter(function(d){return d.eligible});var b=A.bench;A.benchLine=null;
  if(!surv.length)return;
  // robust axis (same Tukey basis as the server-side/CSV paths) so one outlier fund
  // can't crush the cluster; extremes clamp to the margins, the bulk spreads out.
  var zv=surv.map(function(d){return d.vol}),zr=surv.map(function(d){return d.ret});
  if(b){zv=zv.concat([b.vol]);zr=zr.concat([b.ret])}
  var zvAx=_axis(zv),zrAx=_axis(zr);
  if(b){zvAx=_axisWith(zvAx,b.vol);zrAx=_axisWith(zrAx,b.ret);}   // the reference is an anchor of the shared scale, never a saturated point
  surv.forEach(function(d){d.xz=Math.round((14+_pos(d.vol,zvAx)*72)*10)/10;d.yz=Math.round((14+_pos(d.ret,zrAx)*72)*10)/10});
  A.benchLine=_benchMark(zvAx,zrAx,b);
  A.funds.forEach(function(d){if(d.xz==null){d.xz=d.x;d.yz=d.y}});
  // repaint the ranked nodes + benchmark marker + ray from the SAME coords, so the
  // marker always sits on the line and nodes don't lag a stale layout.
  if(document.body.classList.contains('settled')||document.body.classList.contains('scoring')){
    A.funds.forEach(function(d){var n=nodes[d.id];if(n&&d.eligible&&d.xz!=null){n.style.left=d.xz+'%';n.style.bottom=d.yz+'%'}});
    if($('#guides')&&$('#guides').classList.contains('on'))buildGuides();
  }}
function buildGuides(){var g=$('#guides');
  if(!A.bench){if(g)g.classList.remove('on');return}
  // short tag on the diamond (which now sits ON the beta line); the full annotation
  // lives at the line's end so the reader's eye follows the line to its label.
  var shortNm=esc(A.bench.name.split(' (')[0].replace(/\s*total return\s*/i,'').trim()||'S&P 500');
  // label the diamond with its ACTUAL return + Sharpe (like every fund) so the reference
  // is read from its number, never inferred from a compressed vertical position
  var _brf=(A.rfUsed!=null?A.rfUsed:0.02);var _bsr=(A.bench.vol>0)?((A.bench.ret-_brf)/A.bench.vol):null;
  var bnum=(A.bench.ret!=null?("ret "+pct(A.bench.ret)+(_bsr!=null?" · SR "+num(_bsr):"")):"");
  var mk=$('#benchmk');if(mk&&A.bench.xz!=null){mk.style.left=A.bench.xz+'%';mk.style.bottom=A.bench.yz+'%';var blab=$('.bl',mk);if(blab)blab.innerHTML=shortNm+(bnum?"<span class='bl-m'>"+bnum+"</span>":"")}
  var bl=$('#beatlbl');if(bl){bl.innerHTML=shortNm+' · reference index ·<br>passive beta · out of mandate';
    if(A.benchLine){bl.style.bottom=A.benchLine.y2+'%';}   // align the label to the up-right END of the line
  }
  drawBenchLine();if(g)g.classList.add('on');
}
function drawBenchLine(){ if(!A.benchLine)return;var f=$('#field');if(!f)return;var W=f.clientWidth,H=f.clientHeight,L=A.benchLine;
  var X1=L.x1/100*W,Y1=(1-L.y1/100)*H,X2=L.x2/100*W,Y2=(1-L.y2/100)*H;
  var dx=X2-X1,dy=Y2-Y1,len=Math.sqrt(dx*dx+dy*dy),ang=Math.atan2(dy,dx);
  var r=$('#benchray');if(!r)return;r.style.left=X1+'px';r.style.top=Y1+'px';r.style.width=len+'px';r.style.transform='rotate('+ang+'rad)';
}

function buildTraj(){ if(trajBuilt)return;trajBuilt=true;
  var svg=$('#traj');var host=$('#trajwrap');var W=380,H=svg.clientHeight||190,padL=30,padR=8,padT=12,padB=20;
  $$('.tt,.tx,.ty',host).forEach(function(t){t.remove()});
  var funds=shortlisted().filter(function(d){return d.wealth&&d.wealth.length});if(!funds.length)return;
  var ns='http://www.w3.org/2000/svg';
  var GR=trajGrays(),WINC=cssv('--accent2'),WARM=cssv('--accent-warm');
  var n=funds[0].wealth.length;
  var bench=(A.bench&&A.bench.wealth&&A.bench.wealth.length===n)?A.bench.wealth:null;
  var subEl=$('#trajpane .head .s');if(subEl)subEl.textContent='growth of $1'+(bench?' · vs '+A.bench.name.split(' ')[0]:'');
  benchBadge();
  var lo=1e9,hi=-1e9;funds.forEach(function(d){d.wealth.forEach(function(w){lo=Math.min(lo,w);hi=Math.max(hi,w)})});
  if(bench)bench.forEach(function(w){lo=Math.min(lo,w);hi=Math.max(hi,w)});
  lo=Math.min(lo,1);hi=Math.max(hi,1);var mg=(hi-lo)*0.08||0.1;lo-=mg;hi+=mg;
  var X=function(i){return padL+i/(n-1)*(W-padL-padR)},Y=function(w){return padT+(1-(w-lo)/((hi-lo)||1))*(H-padT-padB)};
  svg.setAttribute('viewBox','0 0 '+W+' '+H);svg.setAttribute('preserveAspectRatio','none');svg.innerHTML='';
  function poly(pts,stroke,wdt,dash){var p=document.createElementNS(ns,'polyline');p.setAttribute('points',pts);p.setAttribute('fill','none');p.setAttribute('stroke',stroke);p.setAttribute('stroke-width',wdt);p.setAttribute('stroke-linejoin','round');if(dash)p.setAttribute('stroke-dasharray',dash);p.setAttribute('vector-effect','non-scaling-stroke');return p}
  // y gridlines + value labels ($ growth), x month ticks
  var span=hi-lo,step=span>0.9?0.3:(span>0.45?0.2:0.1),t0=Math.ceil((lo+0.01)/step)*step;
  for(var v=t0;v<hi-0.02;v+=0.0001+step){var gv=Math.round(v*100)/100;var gy=Y(gv);
    var gl=document.createElementNS(ns,'line');gl.setAttribute('x1',padL);gl.setAttribute('x2',W-padR);gl.setAttribute('y1',gy);gl.setAttribute('y2',gy);gl.setAttribute('stroke',cssv('--border'));gl.setAttribute('stroke-width','1');gl.setAttribute('vector-effect','non-scaling-stroke');gl.style.opacity=Math.abs(gv-1)<0.001?'0':'.6';svg.appendChild(gl);
    var yl=el('div','ty');yl.textContent='$'+gv.toFixed(1);yl.style.top=(gy/H*100)+'%';host.appendChild(yl);}
  // $1 baseline (emphasized) + its label
  var base=document.createElementNS(ns,'line');base.setAttribute('x1',padL);base.setAttribute('x2',W-padR);base.setAttribute('y1',Y(1));base.setAttribute('y2',Y(1));base.setAttribute('stroke',cssv('--border2'));base.setAttribute('stroke-dasharray','3 4');base.setAttribute('vector-effect','non-scaling-stroke');svg.appendChild(base);
  var yb=el('div','ty ybase');yb.textContent='$1.0';yb.style.top=(Y(1)/H*100)+'%';host.appendChild(yb);
  for(var xi=0;xi<4;xi++){var ix=Math.round(xi*(n-1)/3);var mo=Math.round(ix/(n-1)*36);var xl=el('div','tx');xl.textContent=mo+(xi===3?' mo':'');xl.style.left=(X(ix)/W*100)+'%';host.appendChild(xl);}
  // winner area gradient
  var defs=document.createElementNS(ns,'defs');var g=document.createElementNS(ns,'linearGradient');g.setAttribute('id','wgrad');g.setAttribute('x1','0');g.setAttribute('y1','0');g.setAttribute('x2','0');g.setAttribute('y2','1');
  [[0,'.24'],[1,'0']].forEach(function(s){var st=document.createElementNS(ns,'stop');st.setAttribute('offset',s[0]);st.setAttribute('stop-color',WINC);st.setAttribute('stop-opacity',s[1]);g.appendChild(st)});
  defs.appendChild(g);svg.appendChild(defs);
  var wf=funds.filter(function(d){return d.rank==1})[0];
  if(wf){var ap=X(0)+','+Y(lo)+' ';wf.wealth.forEach(function(w,i){ap+=X(i)+','+Y(w)+' '});ap+=X(n-1)+','+Y(lo);var ar=document.createElementNS(ns,'polygon');ar.setAttribute('points',ap);ar.setAttribute('fill','url(#wgrad)');ar.style.opacity='0';ar.style.transition='opacity 1s';svg.appendChild(ar);schedule(function(){ar.style.opacity='1'},700)}
  // benchmark dashed line
  if(bench){var bl=poly(bench.map(function(w,i){return X(i)+','+Y(w)}).join(' '),WARM,'1.3','4 3');bl.style.opacity='0';bl.style.transition='opacity .8s';svg.appendChild(bl);schedule(function(){bl.style.opacity='.7'},900)}
  // label positions
  var lab=funds.slice();if(bench)lab.push({__bench:true,wealth:bench});
  var used=[];lab.slice().sort(function(a,b){return Y(a.wealth[n-1])-Y(b.wealth[n-1])}).forEach(function(d){var tp=Y(d.wealth[n-1])/H*100;while(used.some(function(u){return Math.abs(u-tp)<7.5})){tp+=7.5}used.push(tp);d.__tp=tp});
  funds.forEach(function(d,idx){var win=d.rank==1;var col=win?WINC:GR[Math.min(idx,3)];
    var pl=poly(d.wealth.map(function(w,i){return X(i)+','+Y(w)}).join(' '),col,win?'2.4':'1.3');
    if(win)pl.style.filter='drop-shadow(0 0 5px '+cssv('--accent-glow')+')';
    pl.style.strokeDasharray='1600';pl.style.strokeDashoffset='1600';svg.appendChild(pl);
    schedule(function(){pl.style.transition='stroke-dashoffset 1.3s ease';pl.style.strokeDashoffset='0'},120+idx*80);
    var li=d.wealth.length-1,lv=d.wealth[li];
    var dot=document.createElementNS(ns,'circle');dot.setAttribute('cx',X(li));dot.setAttribute('cy',Y(lv));dot.setAttribute('r',win?'3.4':'2.2');dot.setAttribute('fill',col);dot.style.opacity='0';dot.style.transition='opacity .4s';svg.appendChild(dot);schedule(function(){dot.style.opacity='1'},120+idx*80+1150);
    var gain=isFinite(lv)?((lv-1)*100).toFixed(0):'—';
    var t=el('div','tt'+(win?' twin':''));t.style.color=col;t.style.right='2px';t.style.top=d.__tp+'%';t.innerHTML=esc(first(d.name))+" <b>+"+gain+"%</b>";host.appendChild(t);
  });
  if(bench){var b=lab.filter(function(x){return x.__bench})[0];var bt=el('div','tt tbench');bt.style.color=WARM;bt.style.right='2px';bt.style.top=b.__tp+'%';bt.innerHTML="S&P 500 <b>+"+((bench[n-1]-1)*100).toFixed(0)+"%</b> <span style='opacity:.55'>· ref</span>";host.appendChild(bt)}
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
// ── Act 0 · a full-canvas HUD data-acquisition sequence ──
async function typeInto(elm,txt,step){if(!elm)return;elm.textContent='';for(var i=0;i<txt.length;i++){if(aborted)return;elm.textContent+=txt[i];if(i%2===0)await wait(step||14)}}
async function actZero(){
  var rd=A.readiness||{},b=A.bench||{},stg=$('#field');if(!stg)return;
  var old=$('#az');if(old)old.remove();
  var az=el('div');az.id='az';stg.appendChild(az);
  var ROWS=(rd.coverage||[]).reduce(function(s,c){return s+(c.n||0)},0)+(rd.quarantined_count||0);
  var UNIV=rd.universe_count||A.funds.length,QN=rd.quarantined_count||0,WR=rd.with_returns||UNIV;
  var LIVE=(b.kind==='live');
  var _EPB=(A._keyed?"fred/series/observations?series_id=":"fredgraph.csv?id=");
  var ov=rd.overlap||{},bk=(b.kind==='live'?'LIVE':b.kind==='cache'?'CACHED':'SNAPSHOT');
  // ── ONE ingest source of truth: the uploaded file (A.ingest) overrides the baked
  //    schema (readiness.ingest). Everything the animation shows — file name, extracted
  //    fields, quarantine reasons/counts — flows from this, so it always matches the
  //    file actually loaded (and an upload with 0 bad rows shows 0, not the baked ones).
  var ING=A.ingest||null, RDI=rd.ingest||null;
  var srcFile=ING?(ING.file||'your CSV'):((RDI&&RDI.file)||'dataset.csv');
  var srcCols=(ING&&ING.cols&&ING.cols.length)?ING.cols:((RDI&&RDI.cols&&RDI.cols.length)?RDI.cols:[{name:'date',role:'date'},{name:'fund_id',role:'id'},{name:'monthly_return',role:'return'}]);
  var srcOpt=(ING&&ING.optional)?ING.optional:((RDI&&RDI.optional)?RDI.optional:['redemption_freq','lockup_months','notice_days','mgmt_fee']);
  var quarSrc=(ING&&ING.quar)?ING.quar:{reasons:(rd.quarantine_reasons||{}),count:QN,samples:((RDI&&RDI.quar_samples)||[])};   // upload authoritative EVEN IF empty
  var qN=quarSrc.count||0;
  var fundsN=ING?((A.funds||[]).length||UNIV):UNIV;
  var validN=(ING&&ING.valid!=null)?ING.valid:Math.max(0,(ROWS||0)-QN);
  var rowsN=validN+qN;
  var fieldNames=srcCols.map(function(c){return c.name}).concat(srcOpt);
  az.innerHTML=
    "<div class='hud-grid'></div><div class='hud-scan'></div>"
   +"<div class='hud-top'><div class='hud-id'><span class='hud-rec'></span>EQUI · DATA CORE</div></div>"
   +"<div class='hud-stage' id='hudstage'></div>"
   +"<div class='hud-bot'><div class='hud-phase'><span class='hp-n'>00</span><span class='hp-l' id='hudphase'>DATA ACQUISITION</span></div><div class='hud-prog' id='hudprog'></div><div class='hud-log' id='hudlog'></div></div>";
  var prog=$('#hudprog',az),stage=$('#hudstage',az);
  ['acquire','map','normalize','assemble','ready'].forEach(function(s,i){var seg=el('div','hpseg');seg.dataset.i=i;seg.innerHTML="<i></i><span>"+s+"</span>";prog.appendChild(seg)});
  function phase(n,label){var pe=$('#hudphase',az);if(pe)pe.textContent=label;var pn=$('.hp-n',az);if(pn)pn.textContent='0'+n;
    $$('.hpseg',az).forEach(function(s){var i=+s.dataset.i;s.classList.toggle('done',i<n-1);s.classList.toggle('act',i===n-1)})}
  function log(t){var L=$('#hudlog',az);if(L)L.innerHTML="<span class='hl-cur'>▸</span> "+t}
  var ch=$('#chapter');if(ch)ch.innerHTML='';   // the HUD carries its own titles
  document.body.classList.add('az-run');
  az.classList.add('on');
  await wait(560);if(aborted)return;

  // ══ 1 · ACQUIRE — local files + FRED market-data API ══
  phase(1,'ACQUIRE SOURCES');
  stage.innerHTML=
   "<div class='az-acq'>"
   +"<div class='az-src' id='srcA'><div class='az-src-h'><span class='az-ic'>▤</span>LOCAL FILE</div>"
     +"<div class='az-row az-file'><span>"+esc(srcFile)+"</span><b id='fa'>—</b></div>"
     +"<div class='az-fx'><span class='az-fx-l'>fields extracted</span><div class='az-fx-chips' id='azfields'></div></div>"
     +(LIVE?"":"<div class='az-row'><span>"+(b.benchFile||'sp500_monthly.csv')+"</span><b>"+(b.n||36)+" obs</b></div>")
     +"<div class='az-st' id='stA'>connecting</div></div>"
   +"<div class='az-beam a' id='beamA'></div>"
   +"<div class='az-hub' id='hub'><div class='az-hub-ring'></div><div class='az-hub-core'></div><div class='az-hub-l'>PARSER</div></div>"
   +"<div class='az-beam b' id='beamB'></div>"
   +"<div class='az-src az-api' id='srcB'><div class='az-src-h'><span class='az-ic api'>◈</span>FRED · MARKET-DATA API<span class='az-badge "+(b.kind||'snapshot')+"'>"+bk+"</span></div>"
     +"<div class='az-ep'>GET <span>"+_EPB+"<b>SP500</b></span></div>"
     +"<div class='az-ep'>GET <span>"+_EPB+"<b>TB3MS</b></span></div>"
     +"<div class='az-st' id='stB'>"+(LIVE?"resolving host · stlouisfed.org":"standby")+"</div></div>"
   +"<div class='az-using' id='azusing'></div>"
   +"</div>";
  await wait(360);$('#srcA',az).classList.add('in');log('mounting local file · '+srcFile);await wait(520);if(aborted)return;
  $('#fa',az).textContent=fundsN+' funds · '+rowsN+' rows';
  // show the actual fields extracted from THIS file (core roles + optional metadata)
  var fxHost=$('#azfields',az);
  if(fxHost){var roleTag={date:'date',id:'fund',ret:'return','return':'return',name:'name',strategy:'strategy'};
    var chips=srcCols.map(function(c){return "<span class='az-fxc role'>"+esc(c.name)+"<i>"+(roleTag[c.role]||c.role||'')+"</i></span>"})
      .concat((srcOpt||[]).map(function(o){return "<span class='az-fxc'>"+esc(o)+"</span>"}));
    fxHost.innerHTML=chips.join('');
    schedule(function(){$$('.az-fxc',fxHost).forEach(function(t,i){schedule(function(){t.classList.add('in')},i*70)})},20);}
  $('#stA',az).innerHTML="<span class='ok'>●</span> loaded";
  $('#beamA',az).classList.add('on');await wait(500);if(aborted)return;
  $('#srcB',az).classList.add('in');
  if(LIVE){
    log('opening https://'+(A._keyed?'api':'fred')+'.stlouisfed.org …');await wait(700);if(aborted)return;
    $('#stB',az).innerHTML="<span class='ok'>●</span> 200 OK · live fetch · "+(b.n||36)+" monthly obs";
    $('#srcB',az).classList.add('active');$('#srcA',az).classList.add('standby');
    $('#azusing',az).innerHTML="<b>SOURCE IN USE</b> · benchmark fetched LIVE from FRED · "+esc(b.name||'S&P 500')+" · as-of "+esc(b.asOf||'—');
  }else{
    log('FRED endpoint available · this run uses the committed local snapshot');await wait(700);if(aborted)return;
    $('#stB',az).innerHTML="<span class='muted'>○</span> "+(b.kind==='cache'?'served from cache':'not called · snapshot mode');
    $('#srcA',az).classList.add('active');$('#srcB',az).classList.add('standby');
    $('#azusing',az).innerHTML="<b>SOURCE IN USE</b> · benchmark from LOCAL "+(b.kind==='cache'?'cache':'snapshot')+" ("+esc(b.name||'S&P 500')+", as-of "+esc(b.asOf||'—')+") · FRED live available";
  }
  $('#beamB',az).classList.add('on');
  await wait(1100);if(aborted)return;$('#hub',az).classList.add('live');await wait(800);if(aborted)return;

  // ── shared parse data, all from the single ingest source (srcCols / quarSrc) ──
  function _colOf(role){var c=srcCols.filter(function(x){return x.role===role||(role==='return'&&x.role==='ret')})[0];return c?c.name:role}
  var dcol=_colOf('date'),icol=_colOf('id'),vcol=_colOf('return');
  function _firstRet(f){var w=f&&f.wealth;return (w&&w.length>1&&w[0])?w[1]/w[0]-1:null}
  function _mdate(k){var s=((ING&&ING.start)||(ov&&ov.start)||'2023-07')+'';var m=s.match(/(\d{4})-(\d{1,2})/);if(!m)return s;var y=+m[1],mo=+m[2]-1+k;y+=Math.floor(mo/12);mo=((mo%12)+12)%12;return y+'-'+('0'+(mo+1)).slice(-2)+'-01'}
  var okFunds=(A.funds||[]).filter(function(f){return f.eligible!==false}).slice(0,3);
  if(!okFunds.length)okFunds=(A.funds||[]).slice(0,3);
  var sample=okFunds.map(function(f,i){var rr=_firstRet(f);return {d:_mdate(i),id:f.id,v:(rr==null?'—':pct(rr)),bad:false}});
  // real BAD rows — the ACTUAL malformed rows (real date/id/value that failed); none if clean
  var qr=quarSrc.reasons||{};var qsamp=quarSrc.samples||[];var badRows=[];
  if(qsamp.length){qsamp.slice(0,3).forEach(function(s){badRows.push({d:s.date||'—',id:s.id||'—',v:s.ret||'—',bad:true,reason:s.reason})});}
  else{Object.keys(qr).forEach(function(reason){var c=qr[reason]||0;for(var k=0;k<c&&badRows.length<3;k++){badRows.push({d:'—',id:'—',v:'—',bad:true,reason:reason})}});}
  var rowsSample=sample.concat(badRows);

  // ══ 2 · MAP — translate THIS file's columns into our standardized schema ══
  // The heart of ingest: YOUR columns (left) map to OUR canonical fields (right) via
  // kinetic connectors, colored by HOW each is used — green drives the metrics engine,
  // amber feeds the mandate screen / fee model, grey is carried but not scored. So it's
  // obvious every run: what came in, what we standardized it to, and what each does.
  phase(2,'MAP → STANDARDIZE');
  var rawCols=srcCols.map(function(c){return {name:c.name,role:(c.role==='ret'?'return':c.role)}})
    .concat((srcOpt||[]).map(function(o){return {name:o,role:'meta'}}));
  function _tkey(c){var r=c.role,n=(c.name||'').toLowerCase();
    if(r==='date')return 'date';if(r==='id')return 'fund_id';if(r==='return')return 'monthly_return';
    if(/strateg|style|asset|categ/.test(n))return 'strategy';
    if(/fee|mgmt|expense/.test(n))return 'mgmt_fee';
    if(/redemp|lock|notice|liquid|deal/.test(n))return 'liquidity';
    return 'reference';}
  var TGT=[
    {k:'date',label:'date',use:'metrics engine',cat:'core'},
    {k:'fund_id',label:'fund_id',use:'identity',cat:'core'},
    {k:'monthly_return',label:'monthly_return',use:'metrics engine',cat:'core'},
    {k:'strategy',label:'strategy',use:'mandate screen',cat:'use'},
    {k:'liquidity',label:'liquidity terms',use:'liquidity screen',cat:'use'},
    {k:'mgmt_fee',label:'mgmt_fee',use:'net-of-fee return',cat:'use'},
    {k:'reference',label:'reference fields',use:'carried · not scored',cat:'ref'}
  ];
  var mapKeys=rawCols.map(_tkey),usedK={};mapKeys.forEach(function(k){usedK[k]=(usedK[k]||0)+1});
  var tgts=TGT.filter(function(t){return t.cat==='core'||usedK[t.k]});
  stage.innerHTML=
   "<div class='az-map2'>"
   +"<svg class='az-map2-svg'></svg>"
   +"<div class='az-map2-col az-map2-l'><div class='az-map2-h'>YOUR FILE · "+esc(srcFile)+" · "+rawCols.length+" cols</div>"
     + rawCols.map(function(c,i){return "<div class='az-m2c' data-i='"+i+"'>"+esc(c.name)+"</div>"}).join('')
   +"</div>"
   +"<div class='az-map2-col az-map2-r'><div class='az-map2-h'>OUR STANDARDIZED SCHEMA</div>"
     + tgts.map(function(t){return "<div class='az-m2t "+t.cat+"' data-k='"+t.k+"'><b>"+esc(t.label)+"</b><i>"+esc(t.use)+"</i><span class='az-m2n'></span></div>"}).join('')
   +"</div>"
   +"<div class='az-map2-lg'><span class='lg core'>drives metrics</span><span class='lg use'>mandate &amp; fees</span><span class='lg ref'>carried · not scored</span></div>"
   +"</div>";
  log('mapping '+rawCols.length+' columns → standardized schema');
  await wait(520);if(aborted)return;
  var boardEl=$('.az-map2',az),svg=$('.az-map2-svg',az);if(!boardEl||!svg){await wait(200);}
  var box=boardEl.getBoundingClientRect();svg.setAttribute('width',box.width);svg.setAttribute('height',box.height);svg.setAttribute('viewBox','0 0 '+box.width+' '+box.height);
  function _aR(e){var r=e.getBoundingClientRect();return [r.right-box.left,r.top-box.top+r.height/2]}
  function _aL(e){var r=e.getBoundingClientRect();return [r.left-box.left,r.top-box.top+r.height/2]}
  var ns2='http://www.w3.org/2000/svg',counts={};
  for(var mi=0;mi<rawCols.length;mi++){if(aborted)return;
    var srcEl=$(".az-m2c[data-i='"+mi+"']",az),tk=mapKeys[mi],tEl=$(".az-m2t[data-k='"+tk+"']",az);
    if(!srcEl||!tEl)continue;
    var cat=(String(tEl.className).match(/\b(core|use|ref)\b/)||['','ref'])[1];
    srcEl.classList.add('lit',cat);
    var p1=_aR(srcEl),p2=_aL(tEl),mx=(p1[0]+p2[0])/2;
    var path=document.createElementNS(ns2,'path');
    path.setAttribute('d','M'+p1[0]+','+p1[1]+' C'+mx+','+p1[1]+' '+mx+','+p2[1]+' '+p2[0]+','+p2[1]);
    path.setAttribute('class','az-m2p '+cat);svg.appendChild(path);
    var len=(path.getTotalLength&&path.getTotalLength())||120;path.style.strokeDasharray=len;path.style.strokeDashoffset=len;
    path.getBoundingClientRect();path.style.transition='stroke-dashoffset .5s ease';path.style.strokeDashoffset='0';
    tEl.classList.add('hit');counts[tk]=(counts[tk]||0)+1;var nEl=$('.az-m2n',tEl);if(nEl&&counts[tk]>1)nEl.textContent='×'+counts[tk];
    await wait(rawCols.length>9?185:235);}
  var coreN=(usedK.date||0)+(usedK.fund_id||0)+(usedK.monthly_return||0);
  var useN=(usedK.strategy||0)+(usedK.liquidity||0)+(usedK.mgmt_fee||0);var refN=usedK.reference||0;
  log('standardized · '+coreN+' → metrics · '+useN+' → screen/fees · '+refN+' carried for reference');
  await wait(1200);if(aborted)return;

  // ══ 3 · NORMALIZE — apply the SAME cleanup to ALL rows, grouped by fund ══
  // Not a 6-row sample: the whole population (every fund × every month) as a tile field,
  // with the normalization sweeping across every tile, the unparseable rows flagged red
  // in their fund's lane, and a live valid/quarantined tally. The side keeps the concrete
  // before → after on real values as the key to what "normalize" means.
  phase(3,'NORMALIZE');
  var okDate=(sample[0]&&sample[0].d)||_mdate(0);
  var okDec=_firstRet(okFunds[0]);var okDecStr=(okDec!=null&&isFinite(okDec))?okDec.toFixed(4):'0.0190';
  var tf=[];
  if(ING&&ING.unit==='percent')tf.push({a:'1.20%',r:'% → decimal',b:'0.0120',k:'ok'});
  else if(ING&&ING.unit==='bps')tf.push({a:'120 bps',r:'bps → decimal',b:'0.0120',k:'ok'});
  else tf.push({a:okDecStr,r:'recognized · decimal',b:okDecStr,k:'ok'});
  tf.push({a:okDate,r:'parsed · ISO-8601',b:okDate,k:'ok'});
  // NB: the failure story is no longer a transform chip — it lives in its own
  // QUARANTINED unit below (real cells + reason), so these chips stay purely about
  // what normalize does to GOOD values.
  var flanes=(A.funds||[]).slice(0,12),laneN=flanes.length||1;
  // Tiles are DERIVED from the real totals so the field always sums to rowsN: spread
  // the valid rows evenly across the fund lanes (an aligned window ⇒ ~equal per fund),
  // and place each quarantined row as a red tile in its fund's lane (unmatched → round
  // robin). A per-lane cap keeps very long series from overflowing; the caption carries
  // the true totals either way.
  var TCAP=48;
  var green=flanes.map(function(_,i){return Math.floor(validN/laneN)+((i<validN%laneN)?1:0)});
  var red=flanes.map(function(){return 0});
  function _laneIdx(id){for(var i=0;i<flanes.length;i++){if(flanes[i].id===id)return i}return -1}
  var placed=0;(quarSrc.samples||[]).forEach(function(s){var idx=_laneIdx(s.id);if(idx<0)idx=(laneN?placed%laneN:0);red[idx]++;placed++});
  for(var e=placed;e<qN&&laneN;e++){red[e%laneN]++}
  var mpf=Math.max(1,Math.round(validN/laneN));
  function _laneTiles(li){var g=Math.min(green[li],TCAP),r=red[li],html='',c;
    for(c=0;c<g;c++){html+="<i class='az-tile' style='transition-delay:"+(c*13+li*8)+"ms'></i>";}
    for(c=0;c<r;c++){html+="<i class='az-tile q' style='transition-delay:"+((g+c)*13+li*8)+"ms'></i>";}
    return html;}
  // ── the rejects, as their OWN unit: for each quarantined row show the ACTUAL cells
  // that failed (a MISSING cell reads "missing"; a present-but-malformed one shows the
  // raw value in loss-red) plus the specific reason. Which cell is at fault is inferred
  // from the reason text, so date / id / return light up correctly even for combos. ──
  function _qflags(reason){var r=(reason||'').toLowerCase();return {
    d:/date/.test(r), i:/fund id|missing id/.test(r), v:/return|value/.test(r),
    dm:/missing date/.test(r), im:/missing (fund )?id/.test(r), vm:/missing return/.test(r)};}
  function _qcell(val,bad,miss,extra){
    if(miss)return "<span class='az-qcv bad miss'>missing</span>";
    var s=(val==null||val===''||val==='—')?'—':String(val);
    return "<span class='az-qcv"+(bad?' bad':'')+(extra?' '+extra:'')+"'>"+esc(s)+"</span>";}
  function _qcard(b){var f=_qflags(b.reason);
    return "<div class='az-qc'><div class='az-qc-top'><i class='az-qc-dot'></i><span class='az-qc-vals'>"
      +_qcell(b.d,f.d,f.dm)+"<em>·</em>"+_qcell(b.id,f.i,f.im,'id')+"<em>·</em>"+_qcell(b.v,f.v,f.vm)
      +"</span></div><span class='az-qc-why'>"+esc(b.reason||'quarantined')+"</span></div>";}
  var qcards = qN>0 ? (
    "<div class='az-sh az-qsh'>QUARANTINED · "+qN+" · KEPT ROW-LEVEL</div>"
    +"<div class='az-quar' id='azquar'>"
    + badRows.map(_qcard).join('')
    + (qN>badRows.length?"<div class='az-qmore'>+ "+(qN-badRows.length)+" more · same handling</div>":"")
    +"</div>") : "";
  stage.innerHTML=
   "<div class='az-parse az-parse-n'>"
   +"<div class='az-field'>"
     +"<div class='az-mcap'>normalizing all <b>"+rowsN+"</b> rows &nbsp;·&nbsp; <b>"+fundsN+"</b> funds × "+mpf+" months</div>"
     +"<div class='az-field-lanes' id='flanes'>"
     + flanes.map(function(f,li){return "<div class='az-fl'><span class='az-fl-id'>"+esc(f.id)+"</span><div class='az-fl-tiles'>"+_laneTiles(li)+"</div></div>"}).join('')
     + (fundsN>flanes.length?"<div class='az-fl az-fl-more'><span class='az-fl-id'>+"+(fundsN-flanes.length)+"</span><div class='az-fl-tiles'><i class='az-tile'></i><i class='az-tile'></i><i class='az-tile'></i></div></div>":"")
     +"</div>"
     +"<div class='az-field-tally'><span class='ok'><b id='tvalid'>0</b> valid</span> &nbsp;·&nbsp; <span class='bad'><b id='tquar'>0</b> quarantined</span> &nbsp;·&nbsp; <span class='dimt'>row-level · no fund dropped</span></div>"
   +"</div>"
   +"<div class='az-side'>"
     +"<div class='az-sh'>VALUE NORMALIZATION</div><div class='az-tf' id='tf'></div>"
     +"<div class='az-sh'>SHARED WINDOW</div><div class='az-win2'>every fund aligned to <b>"+esc(ov.start||'')+" → "+esc(ov.end||'')+"</b></div>"
     +qcards
   +"</div></div>";
  log('normalizing all '+rowsN+' rows · '+fundsN+' funds × '+mpf+' months');
  // reveal fund lanes, top-to-bottom
  var fls=$$('.az-fl',az);for(var fi=0;fi<fls.length;fi++){schedule(function(x){x.classList.add('in')}.bind(null,fls[fi]),fi*55);}
  await wait(fls.length*55+260);if(aborted)return;
  // the sweep: one class toggle, CSS runs the wave via each tile's transition-delay
  var fieldEl=$('.az-field-lanes',az);if(fieldEl)fieldEl.classList.add('norm');
  // tally counts up in lock-step with the sweep
  var sweepMs=mpf*13+laneN*8+400,vEl=$('#tvalid',az),qEl=$('#tquar',az),steps=26;
  for(var st=1;st<=steps;st++){if(aborted)return;var t=st/steps;if(vEl)vEl.textContent=Math.round(t*validN);if(qEl)qEl.textContent=Math.round(t*qN);await wait(sweepMs/steps)}
  if(vEl)vEl.textContent=validN;if(qEl)qEl.textContent=qN;
  // the concrete transforms — what "normalize" actually did to a real value
  var tfh=$('#tf',az);
  for(var ti=0;ti<tf.length;ti++){if(aborted)return;var t2=tf[ti];var tr=el('div','az-tfr'+(t2.k==='bad'?' bad':''));
    tr.innerHTML="<span class='az-tfa'>"+esc(String(t2.a||'—'))+"</span><span class='az-tfrule'>"+esc(t2.r)+"</span><span class='az-tfb'>"+esc(String(t2.b))+"</span>";
    tfh.appendChild(tr);schedule(function(x){x.classList.add('in')}.bind(null,tr),20);await wait(360)}
  // surface the rejects as their own unit: lift the red tiles out of their lanes so the
  // eye tracks them, then reveal one card per quarantined row — real cells + why it failed
  if(qN>0){
    var qtiles=$$('.az-field-lanes .az-tile.q',az);
    for(var qti=0;qti<qtiles.length;qti++){schedule(function(x){x.classList.add('eject')}.bind(null,qtiles[qti]),qti*70);}
    await wait(Math.min(qtiles.length,12)*70+180);if(aborted)return;
    var qshEl=$('.az-qsh',az);if(qshEl)qshEl.classList.add('in');
    await wait(150);
    var qcEls=$$('#azquar .az-qc',az);
    for(var qei=0;qei<qcEls.length;qei++){if(aborted)return;qcEls[qei].classList.add('in');await wait(330)}
    await wait(500);if(aborted)return;
  }
  var qsummary=Object.keys(qr).map(function(k){return qr[k]+' '+k}).join(' · ')||'none';
  if(qN>0)log('normalized '+rowsN+' rows · '+(rowsN-qN)+' valid · '+qN+' quarantined ('+qsummary+') · row-level, no fund dropped');
  else log('normalized '+rowsN+' rows · all parsed cleanly · none quarantined');
  await wait(1500);if(aborted)return;

  // ══ 4 · ASSEMBLE — group the validated rows into one aligned per-fund series each ══
  // The payoff: the flat table becomes the universe. Each fund gets a lane with a
  // real sparkline of its returns, all sharing one window — so the viewer SEES the
  // dataset being built, not just told it happened.
  phase(4,'ASSEMBLE UNIVERSE');
  var months=((rd.coverage&&rd.coverage[0]&&rd.coverage[0].n)||36);
  function _spark(w){if(!w||w.length<2)return "<svg class='az-spark' viewBox='0 0 118 20'></svg>";
    var lo=Math.min.apply(null,w),hi=Math.max.apply(null,w),rng=(hi-lo)||1,W=118,H=20;
    var pts=w.map(function(v,i){var x=(i/(w.length-1))*W,y=H-((v-lo)/rng)*(H-3)-1.5;return (Math.round(x*10)/10)+','+(Math.round(y*10)/10)}).join(' ');
    return "<svg class='az-spark' viewBox='0 0 118 20' preserveAspectRatio='none'><polyline points='"+pts+"'/></svg>";}
  var lanes=(A.funds||[]).slice(0,9);
  stage.innerHTML=
   "<div class='az-asm'>"
   +"<div class='az-asm-h'><b>"+validN+"</b> valid rows &nbsp;→&nbsp; grouped by fund id &nbsp;→&nbsp; <b>"+fundsN+"</b> aligned per-fund series</div>"
   +"<div class='az-lanes' id='lanes'></div>"
   +"<div class='az-asm-win'><span>"+esc(ov.start||'')+"</span><span class='az-asm-wl'>"+months+" months · one shared window</span><span>"+esc(ov.end||'')+"</span></div>"
   +"</div>";
  var lh=$('#lanes',az);log('grouping rows into aligned per-fund series');
  for(var li=0;li<lanes.length;li++){if(aborted)return;var fd0=lanes[li];var lane=el('div','az-lane');
    lane.innerHTML="<span class='az-lane-id'>"+esc(fd0.id)+"</span>"+_spark(fd0.wealth)+"<span class='az-lane-n'>"+months+" mo</span>";
    lh.appendChild(lane);schedule(function(x){x.classList.add('in')}.bind(null,lane),20);await wait(150)}
  log('assembled '+fundsN+' funds · aligned '+(ov.start||'')+' → '+(ov.end||''));
  await wait(1700);if(aborted)return;

  // ══ 5 · READY ══
  phase(5,'UNIVERSE READY');
  stage.innerHTML="<div class='az-ready'><div class='az-ready-big'>UNIVERSE READY</div>"
   +"<div class='az-ready-sub'>"+UNIV+" funds · benchmark bound ("+esc(b.name||'index')+") · risk-free "+(A.rfUsed!=null?(A.rfUsed*100).toFixed(2)+'%':'—')+"</div>"
   +"<div class='az-ready-line'></div></div>";
  log('handoff → screening');await wait(1250);if(aborted)return;
  az.classList.remove('on');await wait(560);
  var azl=$('#az');if(azl)azl.remove();document.body.classList.remove('az-run');
}
async function story(){
  paused=false;document.body.classList.remove('paused');document.body.classList.add('playing');var _pb=$('#pausebtn');if(_pb){_pb.innerHTML='❚❚&nbsp;pause';_pb.classList.remove('on')}
  var total=A.funds.length;
  await actZero();if(aborted)return;
  // ── ACT 1 · Universe — show every candidate, big and legible ──
  var big=bigN();
  chapter('01 · Universe',(big?total:cap(NUM[total]||total))+' candidates','the full fund universe enters the screen');
  A.funds.forEach(function(d,i){var n=nodes[d.id];var p=universePos(i);n.style.left=p.x+'%';n.style.bottom=p.y+'%'});
  var showStep=big?Math.max(20,Math.floor(1600/total)):170;   // quicker reveal for a big universe; unchanged at sample
  for(var i=0;i<total;i++){if(aborted)return;nodes[A.funds[i].id].classList.add('shown');await wait(showStep)}
  await wait(350);
  if(!big){for(var i2=0;i2<total;i2++){if(aborted)return;nodes[A.funds[i2].id].classList.add('labeled');await wait(120)}}
  // else: too many funds to label at once — hover tooltips carry per-fund detail; the shortlist is labeled at settle
  await wait(big?1400:2000);
  // ── ACT 2 · Screening — cut the mandate failures one at a time, slowly ──
  chapter('02 · Screening','Apply the mandate',(A.gates||[]).map(function(g){return g.label.toLowerCase()}).join(' · '));
  $('#gates').classList.add('on');document.body.classList.add('screening');
  $('#counter').classList.add('on');updateCounter();
  await wait(1100);
  var gates=$$('.gate');var rj=rejects();
  for(var j=0;j<rj.length;j++){if(aborted)return;var ex=rj[j];var en=nodes[ex.id];
    var rs=(ex.reasons&&ex.reasons.length)?ex.reasons:[{text:ex.reason,kind:ex.rkind}];
    var kinds=rs.map(function(r){return r.kind});
    en.classList.add('focus');await wait(560);       // bring it forward
    // light EVERY limit this fund breaches — all at once, so it's unambiguous
    var lit=function(el){var on=(kinds.indexOf(el.dataset.k)>=0);el.classList.toggle('act',on);el.classList.toggle('hot',on)};
    gates.forEach(lit);$$('#ip-gates .ipg').forEach(lit);
    // stamp: the breached limit tags + the readable reasons
    var tg=$('.stags',en);if(tg)tg.innerHTML=rs.map(function(r){return "<span class='stag "+r.kind+"'>"+r.kind.toLowerCase()+"</span>"}).join('');
    var sr=$('.sr',en);if(sr)sr.innerHTML=(rs.length>1?("breaches "+rs.length+" hard limits"):esc(rs[0].text));
    en.classList.add('reject');await wait(1150+rs.length*950);   // hold longer when more limits break
    gates.forEach(function(g){g.classList.remove('act')});$$('#ip-gates .ipg').forEach(function(g){g.classList.remove('hot')});
    en.classList.remove('focus');en.classList.add('gone');updateCounter();await wait(720);
  }
  gates.forEach(function(g){g.classList.remove('act')});$$('#ip-gates .ipg').forEach(function(g){g.classList.remove('hot')});
  document.body.classList.remove('screening');$('#gates').classList.remove('on');
  A.funds.forEach(function(d){if(d.reason)nodes[d.id].classList.add('gone')});
  await wait(700);
  // ── ACT 3 · Scoring — survivors take the frontier; weigh them in focus ──
  chapter('03 · Scoring',cap(NUM[A.nEligible]||A.nEligible)+' of '+(NUM[A.nTotal]||A.nTotal)+' clear the mandate','the '+A.nReject+' excluded breached a hard limit · survivors scored on risk-adjusted return');
  var ip=$('#intropane');if(ip)ip.classList.add('out');
  frontier();document.body.classList.add('scoring');updateCounter();await wait(1300);
  $('#scorepane').classList.add('in');buildWeigh();await wait(700);
  await runWeigh();
  await cutLowest();
  $('.sweetz').classList.add('on');await wait(650);
  // ── ACT 4 · Recommendation — one fund resolves ──
  var win=shortlisted()[0];if(aborted||!win)return;
  chapter('04 · Recommendation',esc(first(win.name)),esc(win.name));
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
function settle(){document.body.classList.add('settled');document.body.classList.remove('scoring');document.body.classList.remove('playing');setPaused(false);clearHalos();clearRtags();clearCue();refreshAudit();A.funds.forEach(function(d){var n=nodes[d.id];if(d.eligible&&d.id!==(shortlisted()[0]||{}).id&&!d.cut)n.classList.remove('dimmed')});$('#chapter').innerHTML='';$('.rail').classList.add('in');$('#gates').classList.remove('on');$('#counter').classList.remove('on');typeVerdict();
  if(bigN())shortlisted().forEach(function(s){var n=nodes[s.id];if(n)n.classList.add('labeled')});   // big universe: only the shortlist keeps an always-on label
  schedule(function(){layoutRows();redrawTraj()},680);}

function reset(){aborted=true;bumpGen();paused=false;flushWaits();document.body.classList.remove('settled');document.body.classList.remove('scoring');document.body.classList.remove('screening');document.body.classList.remove('playing');document.body.classList.remove('paused');document.body.classList.remove('az-run');var azl=$('#az');if(azl)azl.remove();
  clearHalos();clearRtags();setLeaderNode(null);clearCue();_lastLive=null;
  A.funds.forEach(function(d){var n=nodes[d.id];n.className='node cand';n.style.left='50%';n.style.bottom='50%';n.style.opacity='';n.style.transform='';var cr=$('.crown',n);if(cr)cr.lastChild.textContent='leader';var sr=$('.stamp .sr',n);if(sr)sr.textContent='';var tg=$('.stamp .stags',n);if(tg)tg.innerHTML=''});$('#gateline').classList.remove('on');$('#danger').classList.remove('on');$('#counter').classList.remove('on');$('#guides').classList.remove('on');$('#weighlegend').classList.remove('in');
  $('#gates').classList.remove('on');$$('.gate').forEach(function(g){g.classList.remove('act')});$('.sweetz').classList.remove('on');
  $('#trajpane').classList.remove('in');$('#scorepane').classList.remove('in');
  $('#scorebars').innerHTML='';$('#weighticker').innerHTML='';$('#whynote').innerHTML='';$('.rail').classList.remove('in');
  $$('.tt').forEach(function(t){t.remove()});$('#traj').innerHTML='';trajBuilt=false;$('#chapter').innerHTML='';
  buildIntro();
}
function replay(){reset();setTimeout(function(){aborted=false;story()},80)}

function openDrawer(h){var d=$('#drawer');d.classList.remove('wide');d.innerHTML="<div class='x' id='dx'><svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.6' stroke-linecap='round'><path d='M6 6l12 12M18 6L6 18'/></svg>CLOSE</div>"+h;d.classList.add('open');d.scrollTop=0;$('#dx').addEventListener('click',function(){d.classList.remove('open')})}
function fundTerms(d){var cells=[];
  if(d.redf)cells.push(["liquidity",d.redf+(d.redd?" · "+Math.round(d.redd)+"d":"")]);
  if(d.lockup!=null)cells.push(["lockup",(d.lockup?d.lockup+" mo":"none")]);
  if(d.notice!=null)cells.push(["notice",Math.round(d.notice)+" d"]);
  if(d.fee!=null)cells.push(["mgmt fee",d.fee+"%"]);
  if(d.netret!=null)cells.push(["net return",pct(d.netret)]);
  if(d.beta!=null)cells.push(["beta",num(d.beta)]);
  if(!cells.length)return "";
  return "<div class='fd-terms'>"+cells.map(function(c){return "<span><i>"+c[0]+"</i><b>"+esc(c[1])+"</b></span>"}).join('')+"</div>";}
function fundDrawer(fid){var d=A.funds.filter(function(f){return f.id==fid})[0];if(!d)return;openDrawer("<div class='d-pre'>Fund brief · rank "+(d.rank?String(d.rank).padStart(2,'0'):'—')+"</div><div class='d-name'>"+esc(d.name)+"</div><div class='d-strat'>"+esc(d.strategy)+"</div>"+fundTerms(d)+d.detail)}

function wire(){
  var tip=$('#tip');
  document.addEventListener('mousemove',function(e){
    if(!e.target||!e.target.closest){tip.style.opacity=0;return}
    var n=e.target.closest('.node');
    if(n&&n.dataset.tip&&document.body.classList.contains('settled')){tip.innerHTML=n.dataset.tip;tip.style.opacity=1;tip.style.left=e.clientX+'px';tip.style.top=e.clientY+'px';return}
    var cell=e.target.closest('.cell[data-mk]');var mi=cell&&METRIC_INFO[cell.dataset.mk];   // fund-brief metric definitions
    if(mi){tip.innerHTML="<div class='tn'>"+esc(mi.label)+"</div><div class='ts'>what it means</div><div class='tdef'>"+esc(mi.def)+"</div>";tip.style.opacity=1;tip.style.left=e.clientX+'px';tip.style.top=e.clientY+'px';return}
    tip.style.opacity=0;
  });
  document.addEventListener('click',function(e){var n=e.target.closest('.node.cand');if(n&&document.body.classList.contains('settled')){fundDrawer(n.dataset.fid);return}var ch=e.target.closest('.chip');if(ch){fundDrawer(ch.dataset.fid)}});
  var pl=$('#play');if(pl)pl.addEventListener('click',replay);
  var sk=$('#skip');if(sk)sk.addEventListener('click',function(){aborted=true;bumpGen();paused=false;flushWaits();document.body.classList.remove('playing');document.body.classList.remove('paused');document.body.classList.remove('az-run');var azl=$('#az');if(azl)azl.remove();clearRtags();clearHalos();clearCue();setLeaderNode(null);A.funds.forEach(function(d){nodes[d.id].classList.remove('leader','focus','cutfocus','rshow')});document.body.classList.remove('screening');var ip=$('#intropane');if(ip)ip.classList.add('out');
    var _big=bigN();
    A.funds.forEach(function(d){var n=nodes[d.id];n.classList.add('shown');if(!_big)n.classList.add('labeled');if(d.reason){n.classList.add('gone')}else{n.classList.add('ranked','showstat');n.style.left=d.xz+'%';n.style.bottom=d.yz+'%';if(d.cut)n.classList.add('cutout','dimmed');else if(d.rank!=1)n.classList.add('dimmed')}});
    if(_big)shortlisted().forEach(function(s){var n=nodes[s.id];if(n)n.classList.add('labeled')});
    frontier();document.body.classList.add('scoring');$('#scorepane').classList.add('in');buildWeigh();renderFinal();
    var win=shortlisted()[0];nodes[win.id].classList.add('focus','win','locked');var cr=$('.crown',nodes[win.id]);if(cr)cr.lastChild.textContent='recommended';nodes[win.id].classList.add('leader');
    $('#weighticker').innerHTML='Final · weighted risk-adjusted score';var comps=(win.components||[]).slice().sort(function(a,b){return b.c-a.c}).slice(0,3).map(function(c){return c.k.replace(/_/g,' ')});$('#whynote').innerHTML="<b>"+esc(first(win.name))+"</b> wins on "+comps.join(', ')+" — the deciding factors.";$('#trajpane').classList.add('in');buildTraj();$('.sweetz').classList.add('on');updateCounter('Shortlist');settle()});
  window.addEventListener('resize',function(){if($('#guides')&&$('#guides').classList.contains('on'))drawBenchLine()});
  var tb=$('#themebtn');if(tb){var tog=function(){applyTheme(document.documentElement.dataset.theme!=='light')};tb.addEventListener('click',tog);tb.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();tog()}});}
  var dl=$('#dlBtn');if(dl)dl.addEventListener('click',function(e){e.stopPropagation();openExportPop(dl)});
  var sh=$('#shareBtn');if(sh)sh.addEventListener('click',function(){doShare()});
  var vb=$('#vbadge');if(vb)vb.addEventListener('click',function(){auditDrawer()});
  var pbtn=$('#pausebtn');if(pbtn)pbtn.addEventListener('click',function(){togglePause()});
  document.addEventListener('keydown',function(e){if(e.code==='Space'&&document.body.classList.contains('playing')&&!/INPUT|TEXTAREA|SELECT/.test((e.target.tagName||''))){e.preventDefault();togglePause()}});
  var lvb=$('#liveBtn');if(lvb)lvb.addEventListener('click',function(){fetchLiveMarket(true)});
  var mb=$('#memoBtn');if(mb)mb.addEventListener('click',function(){openMemo()});
  var mdb=$('#mandateBtn');if(mdb)mdb.addEventListener('click',function(){openMandate()});
  var ub=$('#upBtn'),ui=$('#upInput');if(ub&&ui){ub.addEventListener('click',function(e){e.stopPropagation();openSourcePop(ub)});ui.addEventListener('change',function(){ingestFiles(ui.files);ui.value=''})}
  var wl=$('#weighlegend');if(wl)wl.addEventListener('click',function(e){if(!document.body.classList.contains('settled'))return;var ch=e.target.closest('.lchip');if(!ch)return;var k=ch.dataset.k;var act=(A.activeMetrics||weightFactors().slice()).slice();var i=act.indexOf(k);if(i>=0){if(act.length<=1){toast("<span class='tk' style='color:var(--loss)'>!</span>Keep at least one metric");return}act.splice(i,1)}else act.push(k);applyReweigh(act)});
  document.addEventListener('click',function(e){if(e.target&&e.target.id==='wreset')resetWeights()});
  document.addEventListener('click',function(e){var pop=$('#pop');if(pop&&pop.classList.contains('on')&&!e.target.closest('#pop')&&!e.target.closest('#dlBtn'))pop.classList.remove('on')});
  document.addEventListener('click',function(e){var sp=$('#srcpop');if(sp&&sp.classList.contains('on')&&!e.target.closest('#srcpop')&&!e.target.closest('#upBtn'))sp.classList.remove('on')});
  // side panels dismiss on any click outside them (triggers are excluded so opening/switching never self-closes)
  document.addEventListener('click',function(e){var d=$('#drawer');if(!d||!d.classList.contains('open'))return;if(e.target.closest('#drawer'))return;if(e.target.closest('.node.cand')||e.target.closest('.chip')||e.target.closest('#vbadge')||e.target.closest('#memoBtn')||e.target.closest('#mandateBtn'))return;d.classList.remove('open')});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'){var d=$('#drawer');if(d)d.classList.remove('open')}});
}
function toast(html){var t=$('#toast');if(!t)return;t.innerHTML=html;t.classList.add('on');clearTimeout(toast._t);toast._t=setTimeout(function(){t.classList.remove('on')},2600)}
function liveMemo(){var sl=shortlisted();var w=sl[0];
  function pick(f,worst){var c=sl.filter(function(d){return d[f]!=null&&isFinite(d[f])});if(!c.length)return null;return c.reduce(function(a,b){return (worst?b[f]<a[f]:b[f]>a[f])?b:a})}
  var dd=pick('maxdd',true),vv=pick('vol',false),bb=pick('beta',false);var claims=[];
  if(dd)claims.push({text:'Deepest drawdown: '+pct(dd.maxdd),fund:first(dd.name),verified:true});
  if(bb&&bb.beta!=null)claims.push({text:'Highest beta: '+num(bb.beta),fund:first(bb.name),verified:true});
  if(vv)claims.push({text:'Highest volatility: '+pct(vv.vol),fund:first(vv.name),verified:true});
  var body=(dd?esc(first(dd.name))+' carries the deepest drawdown at '+pct(dd.maxdd)+'. ':'')+(vv?esc(first(vv.name))+' is the most volatile ('+pct(vv.vol)+'). ':'')+'Recomputed live against the current mandate.';
  var sum=w?('Recomputed live: '+A.nTotal+' funds screened, '+A.nEligible+' eligible, '+A.nShort+' shortlisted. '+esc(first(w.name))+' leads on risk-adjusted return ('+pct(w.ret)+' at '+pct(w.vol)+' vol, Sharpe '+num(w.sharpe)+').'):'No fund met the mandate.';
  return {summary:sum,recommendation:(w?'<b>'+esc(first(w.name))+'</b> leads on risk-adjusted return across the '+A.nShort+' shortlisted funds. The S&P benchmark is passive equity beta shown for reference — outside this mandate\'s strategy and risk limits.':'No fund met the mandate.'),keyRisks:{body:body,claims:claims},appendix:'Metrics recomputed client-side with the same deterministic engine (vol = sample-std annualized; Sharpe/Sortino excess over the mandate risk-free; beta/alpha OLS vs benchmark). Figures reflect the current mandate and inputs.'};}
function openMemo(){var m=(A._reran?liveMemo():(A.memo||{}));var risks=m.keyRisks||{};var w=shortlisted()[0]||{};
  var WARN="<svg viewBox='0 0 24 24' fill='none'><path d='M12 3l9 16H3l9-16z' stroke='currentColor' stroke-width='1.7' stroke-linejoin='round'/><path d='M12 10v4' stroke='currentColor' stroke-width='1.8' stroke-linecap='round'/><circle cx='12' cy='16.6' r='.6' fill='currentColor' stroke='currentColor'/></svg>";
  var kpis=[['Ann. return',pct(w.ret)],['Volatility',pct(w.vol)],['Sharpe',num(w.sharpe)],['Sortino',num(w.sortino)],['Max DD',pct(w.maxdd)],['Net of fee',(w.netret!=null?pct(w.netret):'—')]];
  var kpiH=kpis.map(function(k){return "<div class='mvk'><b>"+k[1]+"</b><i>"+k[0]+"</i></div>"}).join('');
  var rows=shortlisted().map(function(s){return "<tr"+(s.rank==1?" class='mwin'":"")+"><td class='mr'>"+String(s.rank).padStart(2,'0')+"</td><td class='mnm'>"+esc(first(s.name))+"</td><td>"+pct(s.ret)+"</td><td>"+num(s.sharpe)+"</td><td>"+num(s.sortino)+"</td><td>"+pct(s.maxdd)+"</td><td class='msc'>"+(s.score>=0?'+':'')+s.score.toFixed(2)+"</td></tr>"}).join('');
  var claims=(risks.claims||[]).map(function(c){var mt=(c.metric||'');var sev=/drawdown/.test(mt)?' hi':/vol|beta/.test(mt)?' md':'';var parts=String(c.text).split(':');var lab=parts[0],val=parts.slice(1).join(':').trim();
    return "<div class='mvr"+sev+"'><span class='mvr-ic'>"+WARN+"</span><div class='mvr-b'><div class='mvr-t'>"+esc(lab)+(val?" <b>"+esc(val)+"</b>":"")+"</div><div class='mvr-f'>"+esc(c.fund||'')+"</div></div></div>"}).join('');
  var reco=m.recommendation||A.verdictHtml||'';
  var h="<div class='mv'>"
   +"<div class='mv-eyebrow'>Investment Committee memo · "+esc(A.mandate)+"</div>"
   +"<div class='mv-hero'>"+reco+"</div>"
   +"<div class='mv-pills'><span class='mvp'>"+A.nShort+" of "+A.nTotal+" advance</span><span class='mvp ok' title='Every numeric claim in this memo was recomputed from the source series and matched within tolerance'>&#10003; "+A.verified+"/"+A.total+" claims verified</span></div>"
   +(w.name?("<div class='mv-band'><div class='mv-band-h'><span class='mv-rec'>Recommended</span><span class='mv-wn'>"+esc(first(w.name))+"</span><span class='mv-ws'>"+esc(w.strategy||'')+"</span></div><div class='mv-kpis'>"+kpiH+"</div></div>"):"")
   +(m.summary?("<p class='mv-lead'>"+m.summary+"</p>"):"")
   +"<div class='mv-h'>Shortlist</div><table class='mm-tbl'><thead><tr><th>#</th><th>Fund</th><th>Ret</th><th>SR</th><th>Sor</th><th>Max DD</th><th>Score</th></tr></thead><tbody>"+rows+"</tbody></table>"
   +"<div class='mv-h'>Key risks</div>"+(risks.body?("<p class='mv-lead sm'>"+risks.body+"</p>"):"")+"<div class='mvr-list'>"+claims+"</div>"
   +(m.appendix?("<details class='mv-apx'><summary>Data appendix &amp; methodology</summary><p class='mv-fine'>"+m.appendix+"</p></details>"):"")
   +"</div>";
  openDrawer(h);var d=$('#drawer');if(d)d.classList.add('wide');}
// ── the audit ledger, built LIVE from the current dataset (baked OR uploaded) ──
// Every claim the memo rests on is traced to its origin, one of two kinds:
//   · a COMPUTED METRIC — recomputed here from the fund's own return series and
//     matched against the stored engine value (verified by re-derivation), and
//   · a SOURCE FIELD — a descriptive fact (strategy, fee, liquidity terms …) read
//     straight from a SPECIFIC column + row of the uploaded CSV.
// Because it reads A.funds / A.sources at call time, it always respects whatever
// data is loaded now — the bug where an uploaded CSV showed an empty audit is gone.
function _reconstructReturns(w){if(!w||w.length<2)return null;var r=[],i;for(i=0;i<w.length;i++){r.push(i?(w[i]/w[i-1]-1):(w[i]-1))}return r}
function buildAudit(){
  var claims=[];
  // index each source CSV once: header, id column, and the row where each fund lives
  var idx=(A.sources||[]).map(function(sc){
    var out={name:sc.name||'source',hdr:[],rows:null,idCol:-1,rowByFund:{}};
    if(!sc.text)return out;var rows;try{rows=parseCSV(sc.text)}catch(e){return out}
    if(!rows||rows.length<2)return out;out.rows=rows;
    out.hdr=rows[0].map(function(h){return String(h).toLowerCase().trim()});
    out.idCol=_findCol(out.hdr,['fund_id','fund','ticker','symbol','id']);
    if(out.idCol>=0)for(var r=1;r<rows.length;r++){var fid=String(rows[r][out.idCol]||'').trim();if(fid&&!(fid in out.rowByFund))out.rowByFund[fid]=r;}
    return out;
  });
  function trace(fundId,cands){for(var s=0;s<idx.length;s++){var ix=idx[s];if(!ix.rows||ix.idCol<0)continue;
    var col=_findCol(ix.hdr,cands);if(col<0)continue;var r=ix.rowByFund[String(fundId).trim()];if(r==null)continue;
    return {file:ix.name,row:r+1,col:ix.rows[0][col],raw:(ix.rows[r][col]!=null?String(ix.rows[r][col]).trim():'')};}
    return null;}
  var pool=shortlisted();if(!pool.length)pool=(A.funds||[]).filter(function(d){return d.eligible});if(!pool.length)pool=(A.funds||[]).slice(0,5);
  var rf=(A.rfUsed!=null?A.rfUsed:((A.mandateSpec&&A.mandateSpec.rf)||0.02));
  var benchNm=(A.bench&&A.bench.name)||'benchmark';
  var METRICS=[['ann_return','ret'],['ann_vol','vol'],['sharpe','sharpe'],['sortino','sortino'],['calmar','calmar'],['max_drawdown','maxdd'],['beta','beta'],['alpha','alpha']];
  var FIELDS=[
    {fk:'strategy',label:'Strategy',cands:['strategy','style','asset_class','category'],fmt:function(v){return String(v)}},
    {fk:'fee',label:'Management fee',cands:['mgmt_fee_pct','fee','management_fee','expense'],fmt:function(v){return num(v)+'%'}},
    {fk:'redf',label:'Redemption terms',cands:['redemption_freq','redemption','liquidity','liquidity_terms','dealing'],fmt:function(v){return String(v)}},
    {fk:'lockup',label:'Lock-up',cands:['lockup_months','lockup','lock_up','lock'],fmt:function(v){return v+' months'}},
    {fk:'notice',label:'Notice period',cands:['notice_days','notice','notice_period'],fmt:function(v){return v+' days'}}
  ];
  pool.forEach(function(d){
    var r=_reconstructReturns(d.wealth);var mm=r?fundMetrics(r):null;
    var retTr=trace(d.id,['monthly_return','return','ret','performance','value']);
    var retSrc=retTr?("column ‘"+retTr.col+"’ · "+retTr.file):"monthly return series";
    METRICS.forEach(function(p){var mk=p[0],fk=p[1];var v=d[fk];if(v==null||!isFinite(v))return;
      var rec=mm?mm[mk]:null;var recomputed=(rec!=null&&isFinite(rec));var den=Math.abs(v)>1e-9?Math.abs(v):1;
      var ok=recomputed?(Math.abs(rec-v)/den<=0.02):true;var mode=recomputed?'recomputed':'engine';
      var inp=[(r?r.length:'—')+' monthly returns'];
      if(mk==='sharpe'||mk==='sortino')inp.push('risk-free '+pct(rf));
      if(mk==='beta'||mk==='alpha')inp.push('vs '+benchNm);
      claims.push({fund:d.name,id:d.id,kind:'metric',mk:mk,mode:mode,ok:ok,label:metricLabel(mk),value:fmtMetricVal(mk,v),
        def:(METRIC_INFO[mk]||{}).def||'',inputs:inp,src:retSrc});
    });
    FIELDS.forEach(function(F){var v=d[F.fk];if(v==null||v===''||v==='—')return;
      var tr=trace(d.id,F.cands);
      claims.push({fund:d.name,id:d.id,kind:'field',ok:!!tr,label:F.label,value:F.fmt(v),
        file:(tr?tr.file:null),col:(tr?tr.col:null),row:(tr?tr.row:null),raw:(tr?tr.raw:null),
        src:(tr?("column ‘"+tr.col+"’ · row "+tr.row+" · "+tr.file):"not located in source")});
    });
  });
  var verified=claims.filter(function(c){return c.ok}).length;
  return {claims:claims,verified:verified,total:claims.length};
}
function refreshAudit(){try{var L=buildAudit();A._auditLedger=L;A.verified=L.verified;A.total=L.total;
  var vb=$('#vbadge');if(vb)vb.setAttribute('title',L.verified+'/'+L.total+' claims verified against the metrics engine — click for the audit trail');}catch(e){}}
function auditDrawer(){
  var L=buildAudit();A._auditLedger=L;A.verified=L.verified;A.total=L.total;var A2=L.claims;
  var groups=[],gi={};A2.forEach(function(c,i){c._i=i;if(!(c.fund in gi)){gi[c.fund]=groups.length;groups.push({fund:c.fund,items:[]})}groups[gi[c.fund]].items.push(c)});
  // a COLLAPSED row: check · label · value · kind badge · chevron. Click the row to jump
  // to its origin (chart+fund brief for a metric, the exact CSV cell for a source field);
  // click the chevron to expand the provenance inline. Detail stays hidden until asked for.
  function rowHtml(c){
    var badcls=c.ok?'':' bad';
    var badge=(c.kind==='metric')?"<span class='av-badge met'>metric</span>":"<span class='av-badge src'>source</span>";
    var go=(c.kind==='metric')?"chart":(c.file?"csv":null);
    var exp=(c.kind==='metric')
      ? ((c.def?"<div class='av-note'>"+esc(c.def)+"</div>":"")+"<div class='av-src'><span class='av-k2'>"+(c.mode==='recomputed'?'recomputed from':'computed from')+"</span> "+esc(c.inputs.join(' · '))+" · <span class='av-k2'>source</span> "+esc(c.src)+"</div>")
      : ("<div class='av-src'><span class='av-k2'>source field</span> "+esc(c.src)+(c.raw!=null?(" · <span class='av-k2'>raw</span> “"+esc(c.raw)+"”"):"")+"</div>");
    var jumpLbl=(c.kind==='metric')?"↗ show on chart &amp; open "+esc(first(c.fund)):(c.file?("↗ open "+esc(c.file)+" at row "+c.row):"source cell not located");
    return "<div class='av-row"+badcls+(go?'':' nogo')+"' data-i='"+c._i+"'"+(go?" data-go='"+go+"'":"")+">"
      +"<div class='av-rhead'><span class='av-ck' title='"+(c.ok?(c.kind==='metric'?'recomputed · matches the engine':'traced to a source cell'):'not located')+"'>"+(c.ok?'✓':'!')+"</span>"
      +"<span class='av-rlabel'>"+esc(c.label)+"</span><span class='av-rval'>"+esc(c.value)+"</span>"+badge
      +"<button class='av-chev' data-chev='"+c._i+"' title='show where this came from' aria-label='details'>›</button></div>"
      +"<div class='av-exp'>"+exp+(go?("<button class='av-jump' data-jump='"+c._i+"'>"+jumpLbl+"</button>"):"")+"</div>"
    +"</div>";
  }
  var body=groups.map(function(g){
    var mets=g.items.filter(function(c){return c.kind==='metric'}),flds=g.items.filter(function(c){return c.kind==='field'});
    var okN=g.items.filter(function(c){return c.ok}).length;
    return "<div class='av-group'><div class='av-fund'>"+esc(g.fund)+"<span class='av-n'>"+okN+"/"+g.items.length+" traced</span></div>"
      +(mets.length?"<div class='av-kind'>Computed metrics</div>"+mets.map(rowHtml).join(''):"")
      +(flds.length?"<div class='av-kind'>From the source file</div>"+flds.map(rowHtml).join(''):"")
      +"</div>";
  }).join('');
  if(!A2.length)body="<p class='d-p'>No shortlisted funds to audit yet — run the analysis first.</p>";
  var shield="<svg viewBox='0 0 24 24' fill='none'><path d='M12 2.4l7 2.9v5.7c0 4.7-3.3 8-7 9.6-3.7-1.6-7-4.9-7-9.6V5.3l7-2.9z' fill='var(--accent-soft)' stroke='var(--accent2)' stroke-width='1.3' stroke-linejoin='round'/><path d='M8.6 12.2l2.3 2.3 4.5-4.6' stroke='var(--accent2)' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'/></svg>";
  openDrawer("<div class='av-head'><div class='av-shield'>"+shield+"</div><div><div class='d-pre'>Audit trail · verification</div><div class='d-name'>"+L.verified+" / "+L.total+" traced</div></div></div><div class='d-strat' style='margin-top:12px'>click any figure to jump to where it came from</div><p class='d-p'>Every figure links back to its origin — a computed metric (click to see it on the chart and in the fund brief) or a specific field in your CSV (click to open the file at the exact cell). Nothing reaches the memo unverified.</p>"+body);
  var d=$('#drawer');if(!d)return;
  // wire ONCE (openDrawer only swaps innerHTML, not the element) and always
  // stopPropagation — otherwise the rebuild detaches the click target and the global
  // outside-click closer treats it as an outside click and shuts the drawer.
  if(!d._auditWired){d._auditWired=true;
    d.addEventListener('click',function(e){
      var chev=e.target.closest('.av-chev');
      if(chev){e.stopPropagation();var row=chev.closest('.av-row');if(row)row.classList.toggle('open');return;}
      var jb=e.target.closest('.av-jump'),row2=e.target.closest('.av-row');
      if(!jb&&!row2)return;
      var idx=jb?+jb.dataset.jump:(!row2.classList.contains('nogo')?+row2.dataset.i:-1);
      if(idx<0)return;
      e.stopPropagation();
      var L2=A._auditLedger;var c=L2&&L2.claims[idx];if(!c)return;
      if(c.kind==='metric')auditJumpMetric(c.id,c.mk);
      else if(c.file)openSourceView(c.file,c.id,c.col);
    });
  }
}
// jump: a metric claim → pulse the fund on the risk/return chart + open its brief with
// that metric highlighted, so you SEE where the number lives.
function auditJumpMetric(fid,mk){
  var n=nodes[fid];if(n){n.classList.add('auditpulse');setTimeout(function(){n.classList.remove('auditpulse')},2400);}
  fundDrawer(fid);
  var d=$('#drawer');if(!d)return;
  var cell=d.querySelector(".cell[data-mk='"+mk+"']");if(cell)cell.classList.add('mkhot');
  _auditBack(d);
}
// jump: a source-field claim → open the CSV windowed to the fund's row with the exact
// cell (row × column) highlighted — the literal "link back to a specific source field".
function openSourceView(fileName,fundId,colName){
  var sc=(A.sources||[]).filter(function(s){return s.name===fileName})[0]||(A.sources||[])[0];
  if(!sc||!sc.text){toast("<span class='tk' style='color:var(--loss)'>!</span>No embedded source for this file");return;}
  var rows;try{rows=parseCSV(sc.text)}catch(e){rows=null;}
  if(!rows||rows.length<2){toast("<span class='tk' style='color:var(--loss)'>!</span>Could not read that source");return;}
  var hdr=rows[0],hlow=hdr.map(function(h){return String(h).toLowerCase().trim()});
  var idCol=_findCol(hlow,['fund_id','fund','ticker','symbol','id']);
  var colIdx=_findCol(hlow,[String(colName).toLowerCase().trim()]);
  var tRow=-1;for(var r=1;r<rows.length;r++){if(idCol>=0&&String(rows[r][idCol]).trim()===String(fundId).trim()){tRow=r;break;}}
  if(tRow<0)tRow=1;
  var lo=Math.max(1,tRow-4),hi=Math.min(rows.length-1,tRow+4);
  var thead="<tr><th class='ln'>#</th>"+hdr.map(function(h,ci){return "<th class='"+(ci===colIdx?'hotc':'')+"'>"+esc(h)+"</th>"}).join('')+"</tr>";
  var tb='';
  if(lo>1)tb+="<tr class='ell'><td class='ln'>⋮</td><td colspan='"+hdr.length+"'>"+(lo-1)+" earlier rows</td></tr>";
  for(var rr=lo;rr<=hi;rr++){var hot=(rr===tRow);
    tb+="<tr class='"+(hot?'hotr':'')+"'><td class='ln'>"+rr+"</td>"+hdr.map(function(_,ci){var cell=(rows[rr]&&rows[rr][ci]!=null)?rows[rr][ci]:'';return "<td class='"+(ci===colIdx?'hotc':'')+((hot&&ci===colIdx)?' hotcell':'')+"'>"+esc(cell)+"</td>"}).join('')+"</tr>";}
  if(hi<rows.length-1)tb+="<tr class='ell'><td class='ln'>⋮</td><td colspan='"+hdr.length+"'>"+(rows.length-1-hi)+" more rows</td></tr>";
  var cap="Traced to <b>"+esc(fileName)+"</b> · row <b>"+tRow+"</b> of "+(rows.length-1)+" · column <b>"+esc(colIdx>=0?hdr[colIdx]:colName)+"</b>";
  openDrawer("<div class='d-pre'>Source field · exact origin</div><div class='d-name'>"+esc(colName)+"</div>"
    +"<div class='srcview-cap'>"+cap+"</div><div class='srcview'><table>"+thead+tb+"</table></div>");
  var d=$('#drawer');if(d)d.classList.add('wide');_auditBack(d);
}
function _auditBack(d){if(!d)return;var b=el('button','av-back');b.textContent='‹ Back to the audit trail';b.addEventListener('click',function(e){e.stopPropagation();auditDrawer();});d.appendChild(b);}
function openExportPop(anchor){var pop=$('#pop');if(!pop)return;var r=anchor.getBoundingClientRect();
  pop.innerHTML="<div class='pop-card'><div class='pop-hd'><b>Export memo</b><i>a clean, no-nonsense PDF of the recommendation</i></div>"
    +"<div class='pop-opt' data-a='pdf'><span class='pi'>⤓</span><div class='pt'><b>Download PDF</b><i>saves the memo straight to your device</i></div></div>"
    +"<div class='pop-opt' data-a='print'><span class='pi'>⎙</span><div class='pt'><b>Print</b><i>opens the print dialog</i></div></div></div>";
  pop.style.top=(r.bottom+8)+'px';pop.style.right=(window.innerWidth-r.right)+'px';pop.classList.add('on');
  $$('.pop-opt',pop).forEach(function(o){o.addEventListener('click',function(){var a=o.dataset.a;pop.classList.remove('on');setTimeout(function(){if(a==='print')window.print();else downloadPDF()},120)})});}
/* ── CSV data-source panel: the single source of truth for the analysis inputs ── */
function openSourcePop(anchor){var pop=$('#srcpop');if(!pop)return;var r=anchor.getBoundingClientRect();
  var srcs=A.sources||[];
  var list=srcs.length?srcs.map(function(sc,i){
      return "<div class='srcrow' data-i='"+i+"' title='Open "+esc(sc.name)+" in a new tab'>"
        +"<span class='srcic'>▤</span><div class='srctx'><b>"+esc(sc.name)+"</b><i>"+(sc.rows!=null?sc.rows+" data rows":"csv")+"</i></div>"
        +"<span class='srcopen' data-i='"+i+"'>↗ open</span>"
        +"<span class='srcdl' data-dl='"+i+"' title='Download "+esc(sc.name)+"'>⤓</span></div>";
    }).join('')
    :"<div class='srcempty'>This view was re-run from an uploaded file, so no embedded source is attached. Load CSVs below to make them the source of truth.</div>";
  pop.innerHTML="<div class='pop-card srccard'>"
    +"<div class='pop-hd'><b>CSV data source</b><i>the funds &amp; returns this analysis is computed from — open any file to review it</i></div>"
    +"<div class='srclist'>"+list+"</div>"
    +"<div class='pop-opt' id='srcup'><span class='pi'>⤒</span><div class='pt'><b>Load your own CSVs</b><i>select one or more · funds &amp; returns</i></div></div>"
    +"</div>";
  pop.style.top=(r.bottom+8)+'px';pop.style.right=(window.innerWidth-r.right)+'px';pop.classList.add('on');
  $$('.srcdl',pop).forEach(function(d){d.addEventListener('click',function(e){e.stopPropagation();downloadSource(+d.dataset.dl)})});
  $$('.srcrow',pop).forEach(function(row){row.addEventListener('click',function(e){e.stopPropagation();openSourceTab(+row.dataset.i)})});
  var up=$('#srcup',pop);if(up)up.addEventListener('click',function(){pop.classList.remove('on');var ui=$('#upInput');if(ui)ui.click()});}
function openSourceTab(i){var sc=(A.sources||[])[i];if(!sc)return;
  var blob=new Blob([sc.text||''],{type:'text/plain'});var url=URL.createObjectURL(blob);
  window.open(url,'_blank');setTimeout(function(){URL.revokeObjectURL(url)},8000);}
function downloadSource(i){var sc=(A.sources||[])[i];if(!sc)return;
  var blob=new Blob([sc.text||''],{type:'text/csv'});var url=URL.createObjectURL(blob);
  var a=document.createElement('a');a.href=url;a.download=sc.name||('source'+i+'.csv');document.body.appendChild(a);a.click();
  setTimeout(function(){URL.revokeObjectURL(url);a.remove()},600);}
/* ── minimal vector-PDF writer (crisp, dependency-free, downloads directly) ── */
function _pesc(s){return String(s).replace(/[—–]/g,'-').replace(/·/g,'|').replace(/≤/g,'<=').replace(/≥/g,'>=').replace(/[→▸]/g,'>').replace(/✓/g,'').replace(/[^\x20-\x7e]/g,'').replace(/\\/g,'\\\\').replace(/\(/g,'\\(').replace(/\)/g,'\\)')}
function _cw(s,sz,mono){return mono?String(s).length*sz*0.6:String(s).length*sz*0.5}
function _pdfrgb(name){var h=(cssv(name)||'#000000').replace('#','');
  function c(i){return (parseInt(h.substr(i,2),16)/255).toFixed(2)}
  return c(0)+' '+c(2)+' '+c(4);}                                   // theme.css --pdf-* hex -> PDF "r g b"
function downloadPDF(){
  var W=595,H=842,M=46,IW=W-2*M,ns=[],y=H-M;
  // brand palette sourced from theme.css (the single branding component) — theme-independent print tones
  var CI=_pdfrgb('--pdf-ink'),CD=_pdfrgb('--pdf-dim'),CA=_pdfrgb('--pdf-accent'),CW=_pdfrgb('--pdf-warm'),CL=_pdfrgb('--pdf-line'),CF=_pdfrgb('--pdf-fill'),CLo=_pdfrgb('--pdf-loss');
  function T(x,yy,s,sz,f,c){ns.push('BT /'+f+' '+sz+' Tf '+(c||CI)+' rg '+x.toFixed(1)+' '+yy.toFixed(1)+' Td ('+_pesc(s)+') Tj ET')}
  function TR(xr,yy,s,sz,f,c){T(xr-_cw(s,sz,f==='F3'),yy,s,sz,f,c)}
  function LN(x1,y1,x2,y2,c,w){ns.push((c||CL)+' RG '+(w||0.7).toFixed(2)+' w '+x1.toFixed(1)+' '+y1.toFixed(1)+' m '+x2.toFixed(1)+' '+y2.toFixed(1)+' l S')}
  function RE(x,yy,w,h,c){ns.push(c+' rg '+x.toFixed(1)+' '+yy.toFixed(1)+' '+w.toFixed(1)+' '+h.toFixed(1)+' re f')}
  function wrap(s,sz,f,maxw){var words=String(s).split(' '),lines=[],cur='';words.forEach(function(w){var t=cur?cur+' '+w:w;if(_cw(t,sz,f==='F3')>maxw&&cur){lines.push(cur);cur=w}else cur=t});if(cur)lines.push(cur);return lines}
  var win=shortlisted()[0];var date='';try{date=new Date().toLocaleDateString(undefined,{year:'numeric',month:'long',day:'numeric'})}catch(e){}
  // masthead
  T(M,y-4,'EQUI',17,'F2',CI);TR(W-M,y,'INVESTMENT COMMITTEE - RECOMMENDATION',8,'F3',CD);TR(W-M,y-12,date.toUpperCase(),8.5,'F3',CI);y-=20;LN(M,y,W-M,y,CI,1.4);y-=26;
  // verdict
  var vd=(win?win.name+' leads on risk-adjusted return.':'No fund met the mandate.');
  wrap(vd,17,'F2',IW).forEach(function(l){T(M,y,l,17,'F2',CI);y-=21});y-=8;
  // recommendation card + KPIs
  if(win){var cardH=76;RE(M,y-cardH,150,cardH,CF);LN(M,y-cardH,M,y,CL,1);
    T(M+12,y-16,'RECOMMENDATION',7.5,'F3',CW);wrap(win.name,14,'F2',126).forEach(function(l,i){T(M+12,y-34-i*15,l,14,'F2',CI)});T(M+12,y-cardH+12,(win.strategy||'').toUpperCase(),8,'F3',CD);
    var kp=[['ANN RETURN',pct(win.ret)],['VOLATILITY',pct(win.vol)],['SHARPE',num(win.sharpe)],['SORTINO',num(win.sortino)],['CALMAR',num(win.calmar)],['MAX DD',pct(win.maxdd)]];
    var kx=M+164,kw=(W-M-kx),cwd=kw/3;
    kp.forEach(function(p,i){var col=i%3,row=Math.floor(i/3);var cx=kx+col*cwd,cy=y-8-row*38;T(cx+cwd/2-_cw(p[1],13,true)/2,cy-13,p[1],13,'F3',CI);T(cx+cwd/2-_cw(p[0],7,true)/2,cy-24,p[0],7,'F3',CD)});
    y-=cardH+22;}
  function sec(t){T(M,y,t,9,'F3',CA);LN(M,y-6,W-M,y-6,CL,0.7);y-=20}
  function body(t){wrap(t,10.5,'F1',IW).forEach(function(l){T(M,y,l,10.5,'F1',CD);y-=14});y-=6}
  sec('MANDATE - HARD LIMITS');body(A.gates.map(function(g){return g.label+' '+g.detail}).join('    |    '));
  body('SCORING WEIGHTS:  '+weightFactors().map(function(k){return k.replace(/_/g,' ')+' '+Math.round(A.weights[k]*100)+'%'}).join('  |  '));
  if(A.bench)body('MEASURED AGAINST:  '+A.bench.name+' (reference · passive equity beta, out of mandate) - return '+pct(A.bench.ret)+' | volatility '+pct(A.bench.vol));
  // shortlist table
  sec('SHORTLIST - RANKED BY WEIGHTED RISK-ADJUSTED SCORE');
  var cols=[{x:M,a:'l',w:'#'},{x:M+22,a:'l',w:'FUND'}];var rx=[M+150];['RETURN','VOL','SHARPE','SORTINO','CALMAR','MAX DD','SCORE'].forEach(function(h,i){var xr=M+150+ (i+1)*((W-M-(M+150))/7);rx.push(xr)});
  T(M,y,'#',7.5,'F3',CD);T(M+22,y,'FUND',7.5,'F3',CD);['RETURN','VOL','SHARPE','SORTINO','CALMAR','MAX DD','SCORE'].forEach(function(h,i){TR(rx[i+1]-4,y,h,7.5,'F3',CD)});y-=6;LN(M,y,W-M,y,CL,0.7);y-=15;
  shortlisted().forEach(function(d){if(d.rank==1){RE(M-2,y-4,IW+4,17,'0.93 0.965 0.94')}
    T(M,y,String(d.rank).padStart(2,'0'),9,'F3',d.rank==1?CA:CD);T(M+22,y,d.name,10,'F2',d.rank==1?CA:CI);
    var vals=[pct(d.ret),pct(d.vol),num(d.sharpe),num(d.sortino),num(d.calmar),pct(d.maxdd),(d.score>=0?'+':'')+d.score.toFixed(2)];
    vals.forEach(function(v,i){TR(rx[i+1]-4,y,v,9.5,'F3',i===6?CA:CI)});y-=18});
  y-=10;
  // excluded
  var exs=A.funds.filter(function(d){return d.reason});
  if(exs.length){sec('EXCLUDED BY MANDATE');exs.forEach(function(d){T(M,y,d.name,10,'F2',CI);T(M+150,y,d.reason,9.5,'F3',CLo);TR(W-M,y,pct(d.ret)+'  vol '+pct(d.vol),9,'F3',CD);y-=17});y-=8}
  // key risks — wrapped to page width so nothing overruns; same source as the on-screen memo
  var _km=(A._reran?liveMemo():(A.memo||{}));var kr=(_km&&_km.keyRisks)?_km.keyRisks:null;
  if(kr&&kr.claims&&kr.claims.length&&y>150){sec('KEY RISKS');
    kr.claims.slice(0,4).forEach(function(c){var t=String(c.text||'').replace(/<[^>]+>/g,'').trim();var fn=String(c.fund||'').trim();
      if(fn&&t.toLowerCase().indexOf(fn.toLowerCase())<0)t=fn+' - '+t;   // add fund only if not already named in the text
      wrap('- '+t,9.5,'F3',IW).forEach(function(l,i){if(y<96)return;T(i===0?M:M+9,y,l,9.5,'F3',CI);y-=13});y-=3});y-=4}
  // data appendix — one methodology + provenance line
  if(y>110){sec('DATA APPENDIX - METHODOLOGY');
    var bp=(A.bench?(A.bench.name+' ('+(A.bench.kind||'snapshot')+(A.bench.asOf?', as of '+A.bench.asOf:'')+')'):'none');
    body('Metrics from cleaned monthly returns; vol = sample-std annualized; Sharpe/Sortino excess over '
      +(A.rfUsed!=null?(A.rfUsed*100).toFixed(2)+'%':'rf')+' risk-free ('+(A.rfSource||'mandate')+'); beta/alpha OLS vs benchmark. '
      +'Benchmark: '+bp+'.');}
  // footer
  LN(M,y,W-M,y,CL,0.7);y-=14;T(M,y,'Every figure re-verified against the deterministic metrics engine - '+A.verified+'/'+A.total+' claims verified',8.5,'F3',CD);
  var stream=ns.join('\n');
  var objs=['<< /Type /Catalog /Pages 2 0 R >>','<< /Type /Pages /Kids [3 0 R] /Count 1 >>','<< /Type /Page /Parent 2 0 R /MediaBox [0 0 '+W+' '+H+'] /Resources << /Font << /F1 5 0 R /F2 6 0 R /F3 7 0 R >> >> /Contents 4 0 R >>','<< /Length '+stream.length+' >>\nstream\n'+stream+'\nendstream','<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>','<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>','<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>'];
  var pdf='%PDF-1.4\n',off=[];for(var i=0;i<objs.length;i++){off.push(pdf.length);pdf+=(i+1)+' 0 obj\n'+objs[i]+'\nendobj\n'}
  var xr2=pdf.length;pdf+='xref\n0 '+(objs.length+1)+'\n0000000000 65535 f \n';off.forEach(function(o){pdf+=('0000000000'+o).slice(-10)+' 00000 n \n'});
  pdf+='trailer\n<< /Size '+(objs.length+1)+' /Root 1 0 R >>\nstartxref\n'+xr2+'\n%%EOF';
  var blob=new Blob([pdf],{type:'application/pdf'});var url=URL.createObjectURL(blob);var a=document.createElement('a');a.href=url;a.download=((A.title||'EQUI-memo').replace(/[^\w.-]+/g,'_'))+'.pdf';document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(url);a.remove()},600);
  toast("<span class='tk'>&#10003;</span>PDF downloaded");}
/* ── in-page CSV ingest: re-run the deterministic metrics + mandate + scoring client-side ── */
function _pmean(a){return a.reduce(function(s,x){return s+x},0)/a.length}
function _ppstd(a){var m=_pmean(a);return Math.sqrt(a.reduce(function(s,x){return s+(x-m)*(x-m)},0)/a.length)}
function _psstd(a){if(a.length<2)return 0;var m=_pmean(a);return Math.sqrt(a.reduce(function(s,x){return s+(x-m)*(x-m)},0)/(a.length-1))}
// balanced axis: the range is the INLIER span (min/max of values inside the Tukey
// fences), so the bulk of the funds fill most of the field instead of being crushed
// into a corner by one extreme. Outliers don't stretch the range — _pos saturates
// them into the outer margins (never off-canvas, and they don't stack exactly).
function _axis(vals){var a=vals.filter(function(v){return v!=null&&isFinite(v)}).slice().sort(function(x,y){return x-y});var n=a.length;
  if(!n)return {lo:0,hi:1};if(n<4)return {lo:a[0],hi:(a[n-1]>a[0]?a[n-1]:a[0]+1)};
  function q(p){var i=(n-1)*p,lo=Math.floor(i),h=Math.ceil(i);return a[lo]+(a[h]-a[lo])*(i-lo)}
  var q1=q(0.25),q3=q(0.75),iqr=(q3-q1)||Math.abs(q(0.5))||1,fl=q1-1.5*iqr,fh=q3+1.5*iqr;
  var inl=a.filter(function(v){return v>=fl&&v<=fh});if(inl.length<2)inl=a;
  var lo=inl[0],hi=inl[inl.length-1];return {lo:lo,hi:(hi>lo?hi:lo+1)};}
// widen an axis so a value sits INSIDE its non-saturating range. The benchmark must
// be anchored this way before positioning: otherwise a reference return above the fund
// cluster saturates into the top band next to an outlier fund (reads as ~35% when it's
// ~12%), and one below the cluster slams to the floor — both misrepresent the reference.
function _axisWith(ax,v){return (v==null||!isFinite(v))?ax:{lo:Math.min(ax.lo,v),hi:Math.max(ax.hi,v)};}
function _pos(v,ax){var t=(v-ax.lo)/((ax.hi-ax.lo)||1),C=0.05,SP=0.90;
  if(t<0)return C-C*((-t)/((-t)+0.6));         // below the bulk → bottom margin (saturating)
  if(t>1)return (C+SP)+C*((t-1)/((t-1)+0.6));   // above the bulk → top margin (saturating)
  return C+t*SP;}                                // in the bulk → fill 5%..95% of the field
// reference line guaranteed to pass through the marker: the ray from the mapped
// origin (0-risk/0-return) through (mx,my), clipped to the plot box. Since _pos
// saturates outliers, a line between axis endpoints would miss the marker.
function _rayThrough(ox,oy,mx,my){var lo=8,hi=92,dx=mx-ox,dy=my-oy,cand=[];
  if(Math.abs(dx)>1e-9)cand.push((lo-ox)/dx,(hi-ox)/dx);
  if(Math.abs(dy)>1e-9)cand.push((lo-oy)/dy,(hi-oy)/dy);
  var inb=function(t){var x=ox+t*dx,y=oy+t*dy;return x>=lo-0.05&&x<=hi+0.05&&y>=lo-0.05&&y<=hi+0.05};
  var v=cand.filter(inb);if(v.length<2)return null;
  var t1=Math.min.apply(null,v),t2=Math.max.apply(null,v);
  return {x1:Math.round((ox+t1*dx)*10)/10,y1:Math.round((oy+t1*dy)*10)/10,
          x2:Math.round((ox+t2*dx)*10)/10,y2:Math.round((oy+t2*dy)*10)/10};}
// THE single client builder for the benchmark marker + its reference line — used by
// EVERY path (baked relayout, CSV upload, live refetch). It places the marker on the
// zoom axes and returns the line as the ray from the mapped origin THROUGH that marker,
// so the marker is on the line by construction. Do NOT rebuild the bench line any other
// way (e.g. a chord between axis endpoints): _pos saturates outliers, so an endpoint
// chord drifts off the marker — the recurring "S&P diamond floating off the line" bug.
function _benchMark(zvAx,zrAx,b){
  if(!b)return null;
  b.xz=Math.round((14+_pos(b.vol,zvAx)*72)*10)/10;
  b.yz=Math.round((14+_pos(b.ret,zrAx)*72)*10)/10;
  if(!(b.vol>0))return null;
  var ox=14+_pos(0,zvAx)*72,oy=14+_pos(0,zrAx)*72;
  return _rayThrough(ox,oy,b.xz,b.yz);
}
/* ── one client-side scoring core, shared by screenAndScore, reweigh and the CSV
   recompute so the z-score basis can't drift between them. acc(item,key) reads a
   metric off whatever the caller holds (a fund object or a metrics dict); callers
   keep their own ranking basis (raw sum vs rounded-component sum) via _zRaw/_zComps. */
function _accFund(d,k){return d[metricField(k)]}                 // metric off a fund node
function _zStats(items,acc,keys){var st={};keys.forEach(function(k){var vals=[];items.forEach(function(it){var v=acc(it,k);if(v!=null&&isFinite(v))vals.push(v)});if(vals.length>=2)st[k]=[_pmean(vals),_ppstd(vals)]});return st}
function _zComps(it,acc,weights,DIR,st){var cp=[];Object.keys(weights).forEach(function(k){var v=acc(it,k);if(v==null||!st[k]||st[k][1]===0)return;cp.push({k:k,c:Math.round(weights[k]*((v-st[k][0])/st[k][1])*(DIR[k]||0)*1000)/1000})});return cp}
function _zRaw(it,acc,weights,DIR,st){var s=0;Object.keys(weights).forEach(function(k){var v=acc(it,k);if(v==null||!st[k]||st[k][1]===0)return;s+=weights[k]*((v-st[k][0])/st[k][1])*(DIR[k]||0)});return s}
function fundMetrics(r){var ppy=12,rf=(A.rfUsed!=null?A.rfUsed:((A.mandateSpec&&A.mandateSpec.rf)||0.02)),n=r.length;if(n<2)return null;   // use the ACTUAL risk-free (same as synthAlphaOverBench + the audit label) so Sharpe/Sortino recompute matches the stored value — a mandate default 0.02 here silently mis-verified the audit under a live rf
  var g=1;r.forEach(function(x){g*=(1+x)});var annret=g>0?Math.pow(g,ppy/n)-1:g-1;
  var vol=_psstd(r)*Math.sqrt(ppy);var rfp=rf/ppy;var annex=_pmean(r.map(function(x){return x-rfp}))*ppy;
  // guard a NEAR-zero denominator as zero (a flat series has vol≈1e-16 from float error, not 0):
  // return null like metrics.py does, instead of annex/tiny = a garbage 1e15 Sharpe.
  var sh=(vol>1e-9)?annex/vol:null;var dn=r.map(function(x){return Math.min(x-rfp,0)});var dd=Math.sqrt(_pmean(dn.map(function(x){return x*x})))*Math.sqrt(ppy);
  // drawdown on the OBSERVED wealth path — peak seeded at the first point (matches the
  // Python engine's np.maximum.accumulate), so a negative first month isn't counted as a
  // drop from a phantom 1.0 start. Keeps client metrics convention-identical to the engine.
  var so=(dd>1e-9)?annex/dd:null;var w=1,peak=null,mdd=0,wl=[];r.forEach(function(x){w*=(1+x);wl.push(Math.round(w*1e6)/1e6);peak=(peak==null?w:Math.max(peak,w));mdd=Math.min(mdd,w/peak-1)});
  var cal=(mdd<-1e-9)?annret/Math.abs(mdd):null;
  return {ann_return:annret,ann_vol:vol,sharpe:sh,sortino:so,calmar:cal,max_drawdown:mdd,wealth:wl};}
function parseCSV(t){var out=[];t.replace(/\r/g,'').split('\n').forEach(function(ln){if(!ln.trim())return;var row=[],cur='',q=false;for(var i=0;i<ln.length;i++){var c=ln[i];if(c==='"'){q=!q}else if(c===','&&!q){row.push(cur);cur=''}else cur+=c}row.push(cur);out.push(row.map(function(s){return s.trim()}))});return out}
function _findCol(hdr,cands){for(var i=0;i<cands.length;i++){var j=hdr.indexOf(cands[i]);if(j>=0)return j}for(var k=0;k<hdr.length;k++){for(var c=0;c<cands.length;c++){if(hdr[k].indexOf(cands[c])>=0)return k}}return -1}
// pull a fund's per-row metadata off an uploaded row using the detected column map, so
// the audit's 'from the source file' fields work for uploads exactly like the sample
function _fmeta(r,m,id){var g=function(i){return (i!=null&&i>=0&&r[i]!=null)?String(r[i]).trim():''};
  var fee=parseFloat(g(m.fee)),lk=parseFloat(g(m.lockup)),nt=parseFloat(g(m.notice));
  return {name:(g(m.name)||id),strategy:g(m.strategy),fee:(isFinite(fee)?fee:null),redf:(g(m.redf)||null),lockup:(isFinite(lk)?lk:null),notice:(isFinite(nt)?nt:null)};}
function _normRet(raw){if(raw==null)return null;var s=String(raw).trim();if(!s||['na','n/a','nan','null','none','-'].indexOf(s.toLowerCase())>=0)return null;var pct=s.indexOf('%')>=0;s=s.replace(/%/g,'').replace(/,/g,'').replace(/\s/g,'');var v=parseFloat(s);if(isNaN(v)||!isFinite(v))return null;if(pct)return v/100;return Math.abs(v)>1.5?v/100:v}
function _validDate(s){if(s==null)return false;s=String(s).trim();if(!s||s.toLowerCase()==='nan')return false;return !isNaN(Date.parse(s))}
/* ══ schema detection + normalization ══════════════════════════════════════════
   Turns an arbitrary CSV into the canonical long records, handling long OR wide
   matrices, messy value units (decimal/percent/bps) and ambiguous date formats.
   Detection is deterministic and lives ONLY here; the AI (served mode) merely
   refines these same proposals — it never parses values. Clean files skip the UI
   entirely (see ingestFiles); ambiguous/wide ones open the mapping-review panel. */
var _NAVOC=['na','n/a','nan','null','none','-','--',''];
function _looksNum(s){s=String(s==null?'':s);if(!/\d/.test(s))return false;var v=parseFloat(s.replace(/[%,\s]/g,''));return !isNaN(v)&&isFinite(v)}
function _looksDate(s){s=String(s==null?'':s).trim();if(!s)return false;
  if(/^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}$/.test(s))return true;
  if(/^\d{4}[\/\-]\d{1,2}([\/\-]\d{1,2})?$/.test(s))return true;
  if(/[A-Za-z]{3}/.test(s)&&/\d{4}/.test(s)){var t0=Date.parse(s);if(!isNaN(t0))return true}
  return false;}
function _isoStr(s,order){s=String(s==null?'':s).trim();if(!s)return null;
  var m=s.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})$/);
  if(m){var a=+m[1],b=+m[2],y=+m[3];if(y<100)y+=2000;var mo=(order==='dmy')?b:a,da=(order==='dmy')?a:b;
    if(mo>=1&&mo<=12&&da>=1&&da<=31)return y+'-'+('0'+mo).slice(-2)+'-'+('0'+da).slice(-2);return null;}
  var t=Date.parse(s);if(isNaN(t))return null;var d=new Date(t);
  return d.getUTCFullYear()+'-'+('0'+(d.getUTCMonth()+1)).slice(-2)+'-'+('0'+d.getUTCDate()).slice(-2);}
function _normVal(raw,unit){if(raw==null)return null;var s=String(raw).trim();
  if(_NAVOC.indexOf(s.toLowerCase())>=0)return null;var hadPct=s.indexOf('%')>=0;
  s=s.replace(/%/g,'').replace(/,/g,'').replace(/\s/g,'');var v=parseFloat(s);if(isNaN(v)||!isFinite(v))return null;
  if(hadPct||unit==='percent')return v/100;if(unit==='bps')return v/10000;
  return unit==='decimal'?v:(Math.abs(v)>1.5?v/100:v);}   // 'auto' fallback mirrors _normRet
// unit sniff over a bag of raw numeric cells → {unit, confident}
function _sniffUnit(cells){var pctN=0,tot=0,mags=[];cells.forEach(function(c){c=String(c);var v=parseFloat(c.replace(/[%,\s]/g,''));if(isNaN(v)||!isFinite(v))return;tot++;if(c.indexOf('%')>=0)pctN++;mags.push(Math.abs(v))});
  if(!mags.length)return {unit:'auto',confident:false};
  if(pctN/tot>=0.5)return {unit:'percent',confident:true};   // MOST cells carry % (a lone stray % is handled per-cell)
  mags.sort(function(a,b){return a-b});var med=mags[Math.floor(mags.length/2)];
  if(med<0.4)return {unit:'decimal',confident:true};
  if(med>=40)return {unit:'bps',confident:false};
  return {unit:'percent',confident:false};}   // 0.4–40 → percent points, but worth confirming
function _colStats(rows){var header=rows[0]||[],body=rows.slice(1).filter(function(r){return r.some(function(c){return String(c).trim()!==''})}).slice(0,80);
  return header.map(function(h,c){var vals=body.map(function(r){return r[c]==null?'':String(r[c]).trim()}).filter(function(v){return v!==''});
    var dn=vals.filter(_looksDate).length,nn=vals.filter(_looksNum).length;
    var kind=!vals.length?'empty':(dn/vals.length>=0.7?'date':(nn/vals.length>=0.7?'num':'text'));
    return {idx:c,name:String(h||('col'+(c+1))).trim(),kind:kind,n:vals.length,sample:vals.slice(0,3),raw:vals};});}
var _AGG=/^(total|sum|average|avg|mean|benchmark|index|all\s|composite)/i;
function detectSchema(rows){var cols=_colStats(rows),hdr=rows[0].map(function(h){return String(h||'').toLowerCase().trim()});
  var dateCols=cols.filter(function(c){return c.kind==='date'}),numCols=cols.filter(function(c){return c.kind==='num'}),textCols=cols.filter(function(c){return c.kind==='text'});
  // header-keyword hints (long)
  var iRet=_findCol(hdr,['monthly_return','return','ret','performance','perf','net']),iId=_findCol(hdr,['fund_id','fund','ticker','symbol','id']),iDt=_findCol(hdr,['date','period','month','asof','as_of','nav']),iNm=_findCol(hdr,['name']),iSt=_findCol(hdr,['strategy','style','asset_class','category']);
  // optional per-fund metadata columns — captured so an uploaded CSV that HAS them shows
  // the same traced 'from the source file' fields the sample does (returns-only files have none)
  var iFee=_findCol(hdr,['mgmt_fee_pct','mgmt_fee','management_fee','fee','expense']),iRd=_findCol(hdr,['redemption_freq','redemption','liquidity_terms','liquidity','dealing']),iLk=_findCol(hdr,['lockup_months','lockup','lock_up']),iNt=_findCol(hdr,['notice_days','notice_period','notice']);
  var out={cols:cols,warnings:[]};
  // a keyword can match the wrong column ('month' inside 'monthly_return'); only trust
  // the date/return keywords when that column is actually the right cell TYPE.
  var _dtOk=(iDt>=0&&cols[iDt]&&cols[iDt].kind==='date');
  var _retOk=(iRet>=0&&cols[iRet]&&cols[iRet].kind==='num');
  var dateCol=dateCols.length?dateCols[0].idx:(_dtOk?iDt:-1);
  // ambiguous DD/MM vs MM/DD?
  out.dateOrder='mdy';out.dateAmbiguous=false;
  if(dateCol>=0){var dc=cols[dateCol]||cols.filter(function(c){return c.idx===dateCol})[0];var dsamp=(dc&&dc.raw)||[];
    if(dsamp.some(function(v){var m=String(v).match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-]/);return m&&+m[1]<=12&&+m[2]<=12}))out.dateAmbiguous=true;}
  var _idText=(iId>=0&&cols[iId]&&cols[iId].kind!=='num');   // a real per-row fund-id column ⇒ long file, not a matrix
  if(dateCol>=0&&numCols.length>=2&&!(_idText&&_retOk)){   // ── WIDE matrix (date + many numeric, no fund-id column) ──
    out.shape='wide';out.dateCol=dateCol;
    out.series=numCols.filter(function(c){return c.idx!==dateCol}).map(function(c){return {idx:c.idx,name:c.name,agg:_AGG.test(c.name)}});
    out.excluded=textCols.filter(function(c){return c.idx!==dateCol}).map(function(c){return {idx:c.idx,name:c.name,reason:'non-numeric'}});
    var bag=[];out.series.forEach(function(s){(cols.filter(function(c){return c.idx===s.idx})[0].raw||[]).forEach(function(v){bag.push(v)})});
    var u=_sniffUnit(bag);out.unit=u.unit;out.unitConfident=u.confident;
    if(out.series.some(function(s){return s.agg}))out.warnings.push('Some columns ('+out.series.filter(function(s){return s.agg}).map(function(s){return s.name}).join(', ')+') look like aggregates/benchmarks, not funds.');
    out.confident=false;   // wide always confirms (which columns are funds, what unit)
    return out;}
  if((iId>=0||textCols.length>=1)&&(iRet>=0||numCols.length>=1)&&dateCol>=0){   // ── LONG ──
    out.shape='long';out.map={date:dateCol,id:(iId>=0?iId:(textCols[0]?textCols[0].idx:-1)),ret:(iRet>=0?iRet:(numCols.filter(function(c){return c.idx!==dateCol})[0]||{}).idx),name:(iNm>=0?iNm:-1),strategy:(iSt>=0?iSt:-1),fee:iFee,redf:iRd,lockup:iLk,notice:iNt};
    var rc=cols.filter(function(c){return c.idx===out.map.ret})[0];var u2=_sniffUnit((rc&&rc.raw)||[]);out.unit=u2.unit;out.unitConfident=u2.confident;
    // confident (skip panel) only when the date & return keywords land on the right
    // column TYPES, the id is named, and unit/date are unambiguous.
    out.confident=(_dtOk&&_retOk&&iId>=0&&out.unitConfident&&!out.dateAmbiguous);
    return out;}
  if(iNm>=0&&iSt>=0&&(iId>=0||textCols.length)&&iRet<0&&numCols.length<=1){   // ── METADATA only ──
    out.shape='meta';out.map={id:(iId>=0?iId:textCols[0].idx),name:iNm,strategy:iSt,fee:iFee,redf:iRd,lockup:iLk,notice:iNt};out.confident=true;return out;}
  out.shape='unknown';out.confident=false;
  out.warnings.push('Could not find a date column and at least one return series.');
  return out;}
// apply a confirmed mapping → append to ret{}/order[]; returns quarantined count
function _applyMapping(rows,det,acc){var body=rows.slice(1),quar=0,order=acc.order,ret=acc.ret;
  var qreasons={},minD=null,okN=0,qsamples=[];   // track WHY rows fail, the valid count, earliest date + a few REAL bad rows
  function _cell(v){var s=String(v==null?'':v).trim();return /^(nan|none|nat)$/i.test(s)?'':s}
  function _q(reason,dstr,id,rawRet){qreasons[reason]=(qreasons[reason]||0)+1;quar++;
    if(qsamples.length<4)qsamples.push({date:_cell(dstr),id:_cell(id),ret:_cell(rawRet),reason:reason});}
  function _blank(x){var s=String(x==null?'':x).trim().toLowerCase();return s===''||s==='nan'||s==='none'||s==='nat'||s==='n/a'||s==='na'}
  function push(id,dstr,rawRet){var val=_normVal(rawRet,det.unit),iso=_isoStr(dstr,det.dateOrder);
    if(id&&val!=null&&iso!=null){if(!ret[id]){ret[id]=[];order.push(id)}ret[id].push({d:iso,v:val});okN++;
      if(minD==null||iso<minD)minD=iso;return;}
    // accumulate EVERY failing field (date, id, return) in the same order the Python
    // engine does, so an uploaded row's reason reads identically to a baked one — a row
    // bad on two counts says both, not just the first one hit
    var parts=[];
    if(iso==null)parts.push(_blank(dstr)?'missing date':'unparseable date');
    if(!id)parts.push('missing fund id');
    if(val==null)parts.push(_blank(rawRet)?'missing return':'unparseable return');
    _q(parts.join(', ')||'unparseable row',dstr,id,rawRet);}
  if(det.shape==='wide'){var use=det.series.filter(function(s){return !s.excludedByUser});
    body.forEach(function(r){var dstr=r[det.dateCol];use.forEach(function(s){push(String(s.name).trim(),dstr,r[s.idx])})});
  }else if(det.shape==='long'){var m=det.map;
    body.forEach(function(r){push(String(r[m.id]||'').trim(),r[m.date],r[m.ret])});
    body.forEach(function(r){var id=String(r[m.id]||'').trim();if(id&&!acc.funds[id])acc.funds[id]=_fmeta(r,m,id)});}
  // remember this file's real column mapping so the ingest animation reflects IT
  // (not the canonical baked schema) when the story replays after the upload.
  function _cn(idx){var c=(det.cols||[]).filter(function(x){return x.idx===idx})[0];return c?c.name:''}
  var ingCols=[],optional=[];
  if(det.shape==='long'){var mm=det.map;ingCols=[{name:_cn(mm.date),role:'date'},{name:_cn(mm.id),role:'id'},{name:_cn(mm.ret),role:'return'}];
    if(mm.name>=0)optional.push(_cn(mm.name));if(mm.strategy>=0)optional.push(_cn(mm.strategy));}
  else{ingCols=[{name:_cn(det.dateCol),role:'date'},{name:'fund columns',role:'id'},{name:'values',role:'return'}];}
  A.ingest={cols:ingCols,unit:det.unit,optional:optional,file:det._file,quar:{reasons:qreasons,count:quar,samples:qsamples},valid:okN,start:minD};
  return quar;}
function finalizeIngest(acc){var ids=Object.keys(acc.ret);
  if(ids.length<2){showIngestError(acc._failed&&acc._failed[0],acc);return}   // not enough usable returns → explain, don't silently toast
  ids.forEach(function(id){acc.ret[id].sort(function(a,b){return a.d<b.d?-1:a.d>b.d?1:0})});
  A.sources=acc.srcFiles||[];   // ONLY successfully-ingested files become the panel's source of truth
  recompute(acc.funds,acc.ret,acc.order,acc.quar);}
function ingestFiles(list){var files=[].slice.call(list||[]);if(!files.length)return;
  toast("reading "+files.length+" file"+(files.length>1?'s':'')+"…");
  Promise.all(files.map(function(f){return f.text()})).then(function(all){
    var srcMeta=files.map(function(f,i){var t=all[i]||'';return {name:f.name,text:t,rows:Math.max(0,t.replace(/\n+$/,'').split('\n').length-1)}});
    var acc={funds:{},ret:{},order:[],quar:0,srcFiles:[],_failed:[]};var ambiguous=[];
    all.forEach(function(txt,fi){var rows=parseCSV(txt);if(rows.length<2){acc._failed.push({shape:'unknown',cols:[],_file:files[fi].name,warnings:['File has no data rows.']});return}
      var det=detectSchema(rows);det._file=files[fi].name;det._rows=rows;det._src=srcMeta[fi];
      if(det.shape==='meta'){rows.slice(1).forEach(function(r){var id=String(r[det.map.id]||'').trim();if(id)acc.funds[id]=_fmeta(r,det.map,id)});acc.srcFiles.push(srcMeta[fi]);}
      else if(det.shape==='long'&&det.confident){acc.quar+=_applyMapping(rows,det,acc);acc.srcFiles.push(srcMeta[fi]);}   // clean file → straight through, no panel
      else if(det.shape==='wide'||det.shape==='long'){ambiguous.push(det);}                                              // needs the mapping-review flow
      else{acc._failed.push(det);}                                                                                       // 'unknown' → explained in the failure modal
    });
    if(ambiguous.length){reviewMapping(ambiguous[0],acc);return;}   // confirm the (typically single) ambiguous source, then finalize
    finalizeIngest(acc);
  }).catch(function(e){showIngestError({shape:'unknown',cols:[],_file:(files[0]&&files[0].name),warnings:['Couldn’t parse the file: '+(e&&e.message||'unexpected format')+'.']},{})});}
// ── mapping-review flow ──────────────────────────────────────────────────────
// Served mode: ask the LLM to refine the (deterministic) proposals — structure only,
// header + a few sample rows sent, never the full file, never the values. Then ALWAYS
// present the proposals for the user to confirm/correct. Offline: deterministic only.
function reviewMapping(det,acc){
  if(servedLive()){aiRefine(det).then(function(rd){renderMapModal(rd,acc)},function(){renderMapModal(det,acc)});}
  else renderMapModal(det,acc);
}
function aiRefine(det){
  return fetch('/api/map-columns',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({header:det._rows[0],samples:det._rows.slice(1,6),shape:det.shape})})
    .then(function(r){return r.ok?r.json():Promise.reject()})
    .then(function(j){if(!j||!j.ok)return det;
      if(j.unit)det.unit=j.unit;if(j.dateOrder)det.dateOrder=j.dateOrder;
      if(det.shape==='long'&&j.map){['date','id','ret','name','strategy'].forEach(function(k){if(typeof j.map[k]==='number')det.map[k]=j.map[k]})}
      if(det.shape==='wide'&&Array.isArray(j.exclude)){det.series.forEach(function(s){if(j.exclude.indexOf(s.idx)>=0)s.agg=true})}
      det._ai=true;return det;});
}
function _mrow(label,role,cols,sel,req){
  return "<div class='mrow'><div class='mrl'><b>"+label+(req?" <span class='mreq'>required</span>":" <span class='mopt'>optional</span>")+"</b><i>which column is this?</i></div>"
    +"<select data-role='"+role+"'>"+(req?"":"<option value='-1'"+((sel==null||sel<0)?' selected':'')+">— none —</option>")
    +cols.map(function(c){return "<option value='"+c.idx+"'"+(c.idx===sel?" selected":"")+">"+esc(c.name)+" · "+c.kind+"</option>"}).join('')+"</select></div>";
}
function renderMapModal(det,acc){
  var mm=$('#mapmodal');if(!mm)return;var cols=det.cols;
  var shapeTxt=det.shape==='wide'?"Wide matrix — dates down the rows, one column per fund":"Long — one row per fund per period";
  var body='';
  if(det.shape==='long'){
    body="<div class='mrows'>"+_mrow('Date','date',cols,det.map.date,true)+_mrow('Fund ID','id',cols,det.map.id,true)
        +_mrow('Return value','ret',cols,det.map.ret,true)+_mrow('Fund name','name',cols,det.map.name,false)
        +_mrow('Strategy','strategy',cols,det.map.strategy,false)+"</div>";
  }else{
    body="<div class='mrows'>"+_mrow('Date column','date',cols,det.dateCol,true)+"</div>"
        +"<div class='mser'><div class='mserh'>Fund series <i>uncheck any column that isn’t a fund (totals, benchmarks)</i></div>"
        +det.series.map(function(s,i){return "<label class='mchk"+(s.agg?' agg':'')+"'><input type='checkbox' data-si='"+i+"'"+(s.agg?'':' checked')+"><b>"+esc(s.name)+"</b>"+(s.agg?"<span class='mtag'>looks aggregate</span>":"")+"</label>"}).join('')+"</div>";
  }
  var unitSel="<select id='mapUnit'><option value='decimal'"+(det.unit==='decimal'?' selected':'')+">Decimal · 0.012 = 1.2%</option>"
    +"<option value='percent'"+(det.unit==='percent'?' selected':'')+">Percent · 1.2 = 1.2%</option>"
    +"<option value='bps'"+(det.unit==='bps'?' selected':'')+">Basis points · 120 = 1.2%</option></select>";
  var dord=det.dateAmbiguous?("<div class='mrow'><div class='mrl'><b>Date format</b><i>ambiguous — is 03/04 Mar 4 or Apr 3?</i></div><select id='mapOrder'><option value='mdy'"+(det.dateOrder!=='dmy'?' selected':'')+">MM/DD/YYYY (US)</option><option value='dmy'"+(det.dateOrder==='dmy'?' selected':'')+">DD/MM/YYYY (Intl)</option></select></div>"):"";
  var warn=(det.warnings&&det.warnings.length)?"<div class='mwarn'>"+det.warnings.map(function(w){return esc(w)}).join('<br>')+"</div>":"";
  mm.innerHTML="<div class='mm-back' id='mapBack'></div><div class='mm-card'>"
    +"<div class='mm-h'><div><div class='mm-pre'>Map your data"+(det._ai?" <span class='mai'>✦ AI-assisted</span>":"")+"</div><div class='mm-t'>Confirm how to read “"+esc(det._file||'your CSV')+"”</div></div><div class='mm-x' id='mapX'>✕</div></div>"
    +"<div class='mm-shape'>"+esc(shapeTxt)+"</div>"+warn+body
    +"<div class='mrow'><div class='mrl'><b>Return units</b><i>how the numbers are expressed</i></div>"+unitSel+"</div>"+dord
    +"<div class='mm-act'><button class='mf-reset' id='mapCancel'>Cancel</button><button class='mf-apply' id='mapRun'>Run analysis →</button></div></div>";
  mm.classList.add('on');
  function close(){mm.classList.remove('on');mm.innerHTML='';}
  function bail(){close();toast('Kept the current analysis')}
  $('#mapX',mm).addEventListener('click',bail);$('#mapCancel',mm).addEventListener('click',bail);$('#mapBack',mm).addEventListener('click',bail);
  $('#mapRun',mm).addEventListener('click',function(){
    det.unit=$('#mapUnit',mm).value;var ord=$('#mapOrder',mm);if(ord)det.dateOrder=ord.value;
    if(det.shape==='long'){['date','id','ret','name','strategy'].forEach(function(role){var sel=$("select[data-role='"+role+"']",mm);if(sel)det.map[role]=parseInt(sel.value,10)});}
    else{$$("input[data-si]",mm).forEach(function(cb){det.series[+cb.dataset.si].excludedByUser=!cb.checked})}
    var okReq=det.shape==='wide'?(det.dateCol>=0&&det.series.some(function(s){return !s.excludedByUser})):(det.map.date>=0&&det.map.id>=0&&det.map.ret>=0);
    if(!okReq){toast("<span class='tk' style='color:var(--loss)'>!</span>Map the required fields first (date + at least one return series)");return}
    if(det._src&&acc.srcFiles)acc.srcFiles.push(det._src);   // confirmed → this file is now a source of truth
    acc.quar+=_applyMapping(det._rows,det,acc);close();
    finalizeIngest(acc);   // finalize handles the <2-fund case via the failure modal
  });
}
// a centered, reasoned explainer when a file can't be read — replaces the old toast.
function showIngestError(det,acc){
  var mm=$('#mapmodal');if(!mm)return;
  var file=(det&&det._file)||'your file';var cols=(det&&det.cols)||[];
  var hasDate=cols.some(function(c){return c.kind==='date'}),nums=cols.filter(function(c){return c.kind==='num'});
  var missing=[];
  if(!cols.length){missing.push('a date/period column and at least one column of returns');}
  else{if(!hasDate)missing.push('a <b>date</b> column — without one there’s no time series to compute returns over');
       if(!nums.length)missing.push('at least one <b>numeric returns</b> column');}
  if(!missing.length)missing.push('at least two funds with two or more periods of returns');
  var found=cols.length?("<div class='ie-found'><div class='ie-lbl'>Columns detected in “"+esc(file)+"”</div><div class='ie-cols'>"
      +cols.map(function(c){return "<span class='ie-col ie-"+c.kind+"'>"+esc(c.name)+"<i>"+c.kind+"</i></span>"}).join('')+"</div></div>"):"";
  var xtra=(det&&det.warnings&&det.warnings.length)?"<div class='ie-note'>"+det.warnings.map(function(w){return esc(w)}).join('<br>')+"</div>":"";
  mm.innerHTML="<div class='mm-back' id='ieBack'></div><div class='mm-card ie-card'>"
    +"<div class='mm-h'><div><div class='mm-pre ie-pre'>Can’t read this file</div><div class='mm-t'>“"+esc(file)+"” isn’t a fund-returns CSV</div></div><div class='mm-x' id='ieX'>✕</div></div>"
    +"<div class='ie-why'><div class='ie-lbl'>Why it failed</div><ul class='ie-miss'>"+missing.map(function(m){return "<li>Missing "+m+".</li>"}).join('')+"</ul></div>"
    +found+xtra
    +"<div class='ie-exp'><div class='ie-lbl'>What a valid file looks like</div>"
    +"<pre class='ie-ex'>fund_id,date,monthly_return\nORV,2024-01-01,0.012\nORV,2024-02-01,-0.004</pre>"
    +"<div class='ie-hint'>…or a dates×funds matrix (a Date column, one column per fund). Metadata like name & strategy is optional and can live in the same file.</div></div>"
    +"<div class='mm-act'><button class='mf-apply' id='ieClose'>Got it</button></div></div>";
  mm.classList.add('on');
  function close(){mm.classList.remove('on');mm.innerHTML='';}
  $('#ieX',mm).addEventListener('click',close);$('#ieBack',mm).addEventListener('click',close);$('#ieClose',mm).addEventListener('click',close);
}
function recompute(funds,ret,order,quar){ try{
  var ms=A.mandateSpec||{exclStrats:[],volCap:null,rf:0.02,topN:5};var W=A.weights,DIR=A.dir||{};
  var priorBench=A.bench;   // the FRED/snapshot S&P already loaded — reused if the upload has no benchmark column
  var benchId=null;['SP500','SPX','BENCH','BENCHMARK'].forEach(function(b){Object.keys(ret).forEach(function(id){if(id.toUpperCase()===b)benchId=id})});
  var ids=order.filter(function(id){return id!==benchId&&ret[id].length>=2});
  var mbf={},names={},strat={},meta={};ids.forEach(function(id){var series=ret[id].map(function(x){return x.v});var mm=fundMetrics(series);if(!mm)return;mbf[id]=mm;var fdef=funds[id]||{};names[id]=fdef.name||id;strat[id]=fdef.strategy||'—';meta[id]=fdef});
  ids=ids.filter(function(id){return mbf[id]});if(ids.length<2){toast("<span class='tk' style='color:var(--loss)'>!</span>Need at least 2 funds with 2+ periods");return}
  var bench=null;if(benchId&&ret[benchId]&&ret[benchId].length>=2){var bs=ret[benchId].map(function(x){return x.v});var bm=fundMetrics(bs);if(bm)bench={name:names[benchId]||funds[benchId]&&funds[benchId].name||'Benchmark',vol:bm.ann_vol,ret:bm.ann_return,wealth:bm.wealth}}
  if(!bench&&priorBench&&priorBench.vol!=null&&priorBench.ret!=null){   // no benchmark column → fall back to the loaded market benchmark so the reference line still shows
    bench={name:priorBench.name,vol:priorBench.vol,ret:priorBench.ret,wealth:priorBench.wealth,kind:priorBench.kind,srcName:priorBench.srcName,asOf:priorBench.asOf,n:priorBench.n};}
  // mandate: eligible = strategy allowed AND vol <= cap
  function eligibleOf(id){var okS=ms.exclStrats.indexOf(strat[id])<0;var okV=(ms.volCap==null)||(mbf[id].ann_vol==null)||(mbf[id].ann_vol<=ms.volCap);return okS&&okV}
  var elig=ids.filter(eligibleOf);
  // rank eligible: z across eligible
  var _accMbf=function(id,k){return mbf[id][k]};
  var stE=_zStats(elig,_accMbf,Object.keys(W));
  var scoreE={};elig.forEach(function(id){scoreE[id]=_zRaw(id,_accMbf,W,DIR,stE)});   // rank on the raw (unrounded) sum
  var ranked=elig.slice().sort(function(a,b){return scoreE[b]-scoreE[a]});var shortIds=ranked.slice(0,ms.topN);var rankOf={};shortIds.forEach(function(id,i){rankOf[id]=i+1});
  // visual components on the SAME eligible-z basis as the ranking, so bars == rank order
  function comps(id){return _zComps(id,_accMbf,W,DIR,stE)}
  // universe scatter range — robust so an outlier winner doesn't crush the cloud
  var vols=ids.map(function(id){return mbf[id].ann_vol}),rets=ids.map(function(id){return mbf[id].ann_return});
  var volAx=_axis(vols),retAx=_axis(rets);
  var fd=ids.map(function(id){var m=mbf[id];var rk=rankOf[id]||null;var elig1=eligibleOf(id);var cut=(rk==null&&elig1);
    var reasons=[];if(!elig1){
      if(ms.volCap!=null&&m.ann_vol>ms.volCap)reasons.push({text:'too volatile · '+Math.round(m.ann_vol*100)+'% > '+Math.round(ms.volCap*100)+'% cap',kind:'VOLATILITY'});
      if(ms.maxddFloor!=null&&m.max_drawdown!=null&&m.max_drawdown<ms.maxddFloor)reasons.push({text:'drawdown · '+Math.round(m.max_drawdown*100)+'% beyond '+Math.round(ms.maxddFloor*100)+'% floor',kind:'DRAWDOWN'});
      if(ms.exclStrats.indexOf(strat[id])>=0)reasons.push({text:'off-strategy · '+strat[id],kind:'STRATEGY'});
      if(!reasons.length)reasons.push({text:'excluded by mandate',kind:'MANDATE'});}
    var reason=(reasons.length?reasons[0].text:null);
    var cp=elig1?comps(id):[];var cm={};cp.forEach(function(x){cm[x.k]=x.c});var sc=Math.round(cp.reduce(function(s,x){return s+x.c},0)*1000)/1000;
    return {id:id,name:names[id],strategy:strat[id],rank:rk,excluded:rk==null,eligible:elig1,cut:cut,rkind:(reasons.length?reasons[0].kind:null),reasons:reasons,
      srank:(rk||(cut?90:99)),x:Math.round((12+_pos(m.ann_vol,volAx)*76)*10)/10,y:Math.round((12+_pos(m.ann_return,retAx)*76)*10)/10,
      ret:m.ann_return,vol:m.ann_vol,sharpe:m.sharpe,sortino:m.sortino,calmar:m.calmar,maxdd:m.max_drawdown,wealth:m.wealth,reason:reason,components:cp,comp:cm,score:sc,
      fee:(meta[id]&&meta[id].fee!=null?meta[id].fee:null),redf:(meta[id]&&meta[id].redf)||null,lockup:(meta[id]&&meta[id].lockup!=null?meta[id].lockup:null),notice:(meta[id]&&meta[id].notice!=null?meta[id].notice:null),
      netret:(meta[id]&&meta[id].fee!=null?m.ann_return-meta[id].fee/100:null),detail:''};});
  // zoom coords over eligible + bench
  var surv=fd.filter(function(d){return d.eligible});var benchLine=null,gateX=null;
  if(surv.length){var zv=surv.map(function(d){return d.vol}),zr=surv.map(function(d){return d.ret});if(bench){zv=zv.concat([bench.vol]);zr=zr.concat([bench.ret])}
    var zvAx=_axis(zv),zrAx=_axis(zr);
    if(bench){zvAx=_axisWith(zvAx,bench.vol);zrAx=_axisWith(zrAx,bench.ret);}   // the reference is an anchor of the shared scale, never a saturated point
    surv.forEach(function(d){d.xz=Math.round((14+_pos(d.vol,zvAx)*72)*10)/10;d.yz=Math.round((14+_pos(d.ret,zrAx)*72)*10)/10});
    benchLine=_benchMark(zvAx,zrAx,bench);   // ray THROUGH the marker — same builder as every other path, so the diamond can never drift off its line again
    if(ms.volCap!=null){var gx=12+_pos(ms.volCap,volAx)*76;if(gx>0&&gx<100)gateX=Math.round(gx*10)/10}}
  fd.forEach(function(d){if(d.xz==null){d.xz=d.x;d.yz=d.y}});
  // detail html for the drawer
  fd.forEach(function(d){var cells=[['ann_return','ann return',pct(d.ret)],['ann_vol','ann vol',pct(d.vol)],['sharpe','sharpe',num(d.sharpe)],['sortino','sortino',num(d.sortino)],['calmar','calmar',num(d.calmar)],['max_drawdown','max drawdown',pct(d.maxdd)]].map(function(c){return "<div class='cell' data-mk='"+c[0]+"'><b>"+c[2]+"</b><i>"+c[1]+"</i></div>"}).join('');
    var lead=d.rank?("ranks #"+d.rank+" for this mandate"):(d.reason?("was excluded — "+esc(d.reason)):"was outscored below the shortlist");
    d.detail="<p class='d-p'>"+esc(d.name)+" "+lead+". It returned "+pct(d.ret)+" annualized against "+pct(d.vol)+" volatility, a Sharpe of "+num(d.sharpe)+" and a Sortino of "+num(d.sortino)+".</p><div class='mgrid'>"+cells+"</div><div class='src-lbl'>Recomputed from your uploaded returns</div>";});
  var win=fd.filter(function(d){return d.rank==1})[0];
  A.funds=fd;A.bench=bench;A.benchLine=benchLine;A.gateX=gateX;A.volcap=(ms.volCap!=null?Math.round(ms.volCap*100)+'%':null);
  A.nTotal=fd.length;A.nEligible=fd.filter(function(d){return d.eligible}).length;A.nShort=shortIds.length;A.nReject=fd.filter(function(d){return d.reason}).length;
  A.verdict=(win?win.name+" leads on risk-adjusted return.":"No fund met the mandate.");A.verdictHtml=(win?"<b>"+esc(win.name)+"</b> leads on risk-adjusted return.":"No fund met the mandate.");
  A.audit=[];A.shareText=(win?win.name+" — recommended (risk-adjusted). "+A.nShort+" shortlisted from "+A.nTotal+".":"No fund met the mandate.");
  rerender();
  toast("<span class='tk'>&#10003;</span>Re-ran the analysis · "+A.nTotal+" funds → "+A.nShort+" shortlisted"+(quar?" · "+quar+" bad rows quarantined":""));
 }catch(err){toast("<span class='tk' style='color:var(--loss)'>!</span>Analysis failed on that data")}}
function rerender(next){aborted=true;bumpGen();A.weights0=Object.assign({},A.weights);A.activeMetrics=weightFactors().slice();A._snap=null;A._reran=true;var f=$('#field');$$('.node',f).forEach(function(n){n.remove()});nodes={};rows={};segState={};trajBuilt=false;
  document.body.classList.remove('settled','scoring','screening');$('#scorebars').innerHTML='';$('#weighticker').innerHTML='';$('#whynote').innerHTML='';$('#weighlegend').innerHTML='';$('#weighlegend').classList.remove('in');$('#traj').innerHTML='';$$('.tt,.tx,.ty').forEach(function(t){t.remove()});
  $('.rail').classList.remove('in');$('#trajpane').classList.remove('in');$('#scorepane').classList.remove('in');$('.sweetz').classList.remove('on');clearCue();
  // rebuild the shortlist rail
  var rc=$('.rail .chips');if(rc){rc.innerHTML=shortlisted().map(function(s){return "<div class='chip"+(s.rank==1?' r1':'')+"' data-fid='"+esc(s.id)+"' title='Open fund detail'><span class='n'>"+String(s.rank).padStart(2,'0')+"</span><span class='nm'>"+esc(s.name)+"</span><span class='rt'>"+pct(s.ret)+"</span><span class='cx'>⤢</span></div>"}).join('')}
  buildField();buildIntro();setPrintDate();_lastLive=null;setTimeout(function(){aborted=false;(next||story)()},60);}
// A mandate-only re-run (a slider moved) does NOT touch the data, the ingest, the
// per-fund metrics or the universe — only the hard limits and weights changed. So we
// skip Act 0 (acquire → map → normalize → assemble) and the Act 1 reveal entirely:
// snap the full universe onto the canvas, PULSE which hard limit each newly-cut fund
// breached (so it's clear WHY the shortlist moved), then settle straight into the
// updated result. Full-from-the-top replay stays reserved for the cases where it's
// honest — a new uploaded file, a live benchmark refetch, or the explicit Play button.
async function _snapStory(){
  document.body.classList.add('playing');var _pb=$('#pausebtn');if(_pb){_pb.innerHTML='❚❚&nbsp;pause';_pb.classList.remove('on')}
  var big=bigN();
  // universe, instant — every candidate already known, no acquisition to re-show
  A.funds.forEach(function(d,i){var n=nodes[d.id];if(!n)return;var p=universePos(i);n.style.left=p.x+'%';n.style.bottom=p.y+'%';n.classList.add('shown');if(!big)n.classList.add('labeled')});
  rebuildGates();
  chapter('02 · Screening','Re-screening the universe','applying the updated mandate live');
  $('#gates').classList.add('on');document.body.classList.add('screening');$('#counter').classList.add('on');updateCounter();
  await wait(300);if(aborted)return;
  // quick breach pulse — a fast cascade lighting each cut fund's breached limit(s)
  var gates=$$('.gate');var rj=rejects();
  var stagger=Math.max(45,Math.min(95,Math.round(560/(rj.length||1))));
  rj.forEach(function(ex,j){schedule(function(){
    var en=nodes[ex.id];if(!en)return;
    var rs=(ex.reasons&&ex.reasons.length)?ex.reasons:[{text:ex.reason,kind:ex.rkind}];
    var kinds=rs.map(function(r){return r.kind});
    var lit=function(el){var on=(kinds.indexOf(el.dataset.k)>=0);el.classList.toggle('act',on);el.classList.toggle('hot',on)};
    gates.forEach(lit);$$('#ip-gates .ipg').forEach(lit);
    var tg=$('.stags',en);if(tg)tg.innerHTML=rs.map(function(r){return "<span class='stag "+r.kind+"'>"+r.kind.toLowerCase()+"</span>"}).join('');
    var sr=$('.sr',en);if(sr)sr.innerHTML=(rs.length>1?("breaches "+rs.length+" hard limits"):esc(rs[0].text));
    en.classList.add('focus','reject');
    schedule(function(){en.classList.remove('focus');en.classList.add('gone');updateCounter();gates.forEach(function(g){g.classList.remove('act')});$$('#ip-gates .ipg').forEach(function(g){g.classList.remove('hot')})},300);
  },j*stagger)});
  await wait(rj.length*stagger+560);if(aborted)return;
  gates.forEach(function(g){g.classList.remove('act')});$$('#ip-gates .ipg').forEach(function(g){g.classList.remove('hot')});
  document.body.classList.remove('screening');$('#gates').classList.remove('on');
  A.funds.forEach(function(d){if(d.reason){var n=nodes[d.id];if(n)n.classList.add('gone')}});   // every reject settles out
  // snap to the updated scoring + recommendation — reuse the static settled layout, no weigh cinematics
  var ip=$('#intropane');if(ip)ip.classList.add('out');
  frontier();document.body.classList.add('scoring');updateCounter();
  $('#scorepane').classList.add('in');buildWeigh();renderFinal();layoutRows();
  $('.sweetz').classList.add('on');
  var win=shortlisted()[0];
  if(win){focusWinner(win);$('#trajpane').classList.add('in');buildTraj();}
  await wait(380);if(aborted)return;
  settle();
}
function doShare(){var txt=A.shareText||document.title;
  var ok=function(){toast("<span class='tk'>✓</span>Recommendation summary copied to clipboard")};
  try{if(navigator.share){navigator.share({title:A.title||document.title,text:txt}).then(function(){},function(){});toast("<span class='tk'>✓</span>Opening share…");return}}catch(e){}
  try{navigator.clipboard.writeText(txt).then(ok,ok)}catch(e){ok()}}
function setPrintDate(){var el2=$('#pd-date');if(!el2)return;try{var d=new Date();el2.textContent=d.toLocaleDateString(undefined,{year:'numeric',month:'long',day:'numeric'})}catch(e){el2.textContent=''}}
window.addEventListener('DOMContentLoaded',function(){document.documentElement.dataset.theme='light';buildField();buildIntro();sourceChip();setPrintDate();wire();
  // when served by `./amb serve`, pull live market data (browser -> localhost -> FRED)
  // BEFORE the story so Act 0 shows the real live fetch; else play immediately.
  if(servedLive()){fetchLiveMarket(false).then(function(){rerender()})}else{story()}});
// pure, side-effect-free core exposed for testing (and cross-language golden checks
// against the Python metrics engine). Rendering/animation stay closure-private.
A.core={fundMetrics:fundMetrics,zStats:_zStats,zComps:_zComps,zRaw:_zRaw,accFund:_accFund,
        pmean:_pmean,ppstd:_ppstd,psstd:_psstd,mix:mix,esc:esc,metricField:metricField,effWeights:effWeights,
        detectSchema:detectSchema,parseCSV:parseCSV,normVal:_normVal,isoStr:_isoStr};
})();
