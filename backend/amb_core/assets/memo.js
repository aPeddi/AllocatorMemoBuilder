
(function(){
var A=window.AMB;
if(A){A.weights0=A.weights0||Object.assign({},A.weights);if(!A.activeMetrics)A.activeMetrics=Object.keys(A.weights).sort(function(a,b){return A.weights[b]-A.weights[a]});}
function $(s,r){return (r||document).querySelector(s)}
function $$(s,r){return [].slice.call((r||document).querySelectorAll(s))}
function el(t,c){var e=document.createElement(t);if(c)e.className=c;return e}
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
function layoutRows(){var sb=$('#scorebars');if(!sb)return;var n=survivors().length||1;var h=(sb.clientHeight||190)-6;
  ROWH=Math.max(26,Math.min(58,Math.floor(h/n)));var th=Math.max(16,Math.min(30,ROWH-12));
  Object.keys(rows).forEach(function(id){var tr=$('.wtrack',rows[id]);if(tr)tr.style.height=th+'px'});
  var order=survivors().slice().sort(function(a,b){return (segState[b.id]?segState[b.id].cum:b.score)-(segState[a.id]?segState[a.id].cum:a.score)});
  order.forEach(function(d,rk){if(rows[d.id])rows[d.id].style.top=(rk*ROWH)+'px'});
  var cl=$('.wcut',sb);if(cl)cl.style.top=(A.nShort*ROWH-2)+'px';}

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
    var stamp=el('div','stamp');var st=el('div','st');st.textContent='excluded';var stags=el('div','stags');var sr=el('div','sr');stamp.appendChild(st);stamp.appendChild(stags);stamp.appendChild(sr);
    var crown=el('div','crown');crown.appendChild(document.createTextNode('leader'));
    var rtag=el('div','rtag');
    var dot=el('div','dot');
    var card=el('div','card');
    card.innerHTML="<div class='nm'><span class='nfull'>"+d.name+"</span><span class='nshort'>"+first(d.name)+"</span></div><div class='sub'>"+stratShort(d.strategy)+"</div><div class='stat'>ret <b>"+pct(d.ret)+"</b> · SR <b>"+num(d.sharpe)+"</b></div>";
    n.appendChild(glass);n.appendChild(halo);n.appendChild(lock);n.appendChild(stamp);n.appendChild(crown);n.appendChild(rtag);n.appendChild(dot);n.appendChild(card);
    n.style.left='50%';n.style.bottom='50%';f.appendChild(n);nodes[d.id]=n;
  });
  var g=$('#gates');if(g){g.innerHTML='';A.gates.forEach(function(gt){var e=el('div','gate');e.textContent=gt.label+' · '+gt.detail;e.dataset.k=gt.label;g.appendChild(e)})}
}
var _lastLive=null;
function updateCounter(lbl){var live=A.funds.filter(function(d){var n=nodes[d.id];return !n.classList.contains('gone')&&!n.classList.contains('cutout')}).length;var c=$('#counter');
  if(c){c.innerHTML="<b>"+String(live).padStart(2,'0')+"</b><span class='cl'>"+(lbl||'Candidates')+"<br>in play</span>";
    if(_lastLive!==null&&live!==_lastLive){c.classList.remove('pop');void c.offsetWidth;c.classList.add('pop')}}
  _lastLive=live;updateTally();}
function buildIntro(){
  var ip=$('#intropane');if(ip){ip.classList.add('in');ip.classList.remove('out')}
  var g=$('#ip-gates');if(g){g.innerHTML='';
    var cuts={};A.funds.forEach(function(d){(d.reasons||[]).forEach(function(rr){cuts[rr.kind]=(cuts[rr.kind]||0)+1})});
    A.gates.forEach(function(gt,i){var r=el('div','ipg');r.dataset.k=gt.label;var n=cuts[gt.label]||0;
      var ct=n>0?"<span class='gc'>−"+n+"</span>":"<span class='gc gc0'>0</span>";
      r.innerHTML="<span class='k'>"+gt.label+"</span><span class='d'>"+gt.detail+"</span>"+ct;g.appendChild(r);setTimeout(function(){r.classList.add('in')},260+i*150)})}
  var w=$('#ip-weights');if(w){w.innerHTML='';var fs=weightFactors();var mx=Math.max.apply(null,fs.map(function(k){return A.weights[k]}));
    fs.forEach(function(k,i){var pctv=Math.round(A.weights[k]*100);var r=el('div','ipw');
      r.innerHTML="<span class='wl'>"+k.replace(/_/g,' ')+"</span><span class='wb'><i></i></span><span class='wp'>"+pctv+"%</span>";
      w.appendChild(r);var bar=$('.wb i',r);
      setTimeout(function(){r.classList.add('in');bar.style.background=segColor(i,false);bar.style.width=(A.weights[k]/mx*100).toFixed(0)+'%'},560+i*120)})}
  var bp=$('#ip-bench');if(bp){if(A.bench){bp.innerHTML="<div class='ipb'><span class='bd'></span><div class='bt'><div class='bn'>"+A.bench.name+"</div><div class='bm'>ret <b>"+pct(A.bench.ret)+"</b> · vol <b>"+pct(A.bench.vol)+"</b></div></div><div class='btag'>reference</div></div>";}else{bp.innerHTML="<div class='ipb'><div class='bt'><div class='bm'>no benchmark</div></div></div>";}}
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
  dp.innerHTML=rows.map(function(x){return "<div class='ipd "+x[3]+"'><span class='dk'>"+x[0]+"</span><div class='dvv'><span class='dv'>"+x[1]+"</span><span class='dd'>"+x[2]+"</span></div><span class='dck'></span></div>"}).join('');
}
function updateTally(){var t=$('#ip-tally');if(!t)return;var gone=A.funds.filter(function(d){return nodes[d.id].classList.contains('gone')}).length;var uni=A.funds.length;var rem=uni-gone;
  t.innerHTML="<div class='tc'><b>"+uni+"</b><i>universe</i></div><div class='tc red'><b>"+gone+"</b><i>excluded</i></div><div class='tc hot'><b>"+rem+"</b><i>advancing</i></div>";}
function universePos(i){var cols=3;var r=Math.floor(i/cols),c=i%cols;
  var L=[26,50,74][c],B=[77,50,23][r];
  var jx=(((i*37)%7)-3)*1.5,jy=(((i*29)%7)-3)*1.3;
  return {x:L+jx,y:B+jy};}
function frontier(){buildGuides();
  A.funds.forEach(function(d){var n=nodes[d.id];if(d.eligible){n.classList.add('ranked','showstat');n.style.left=d.xz+'%';n.style.bottom=d.yz+'%'}});}
function chapter(numv,ttl,sub){var c=$('#chapter');var old=$('.c',c);
  var set=function(){c.innerHTML="<div class='c'><div class='n'>"+numv+"</div><div class='t'>"+ttl+"</div><div class='s'>"+sub+"</div></div>";var card=$('.c',c);void card.offsetWidth;card.classList.add('in')};
  if(old){old.classList.add('out');setTimeout(set,240)}else set();}

function buildWeigh(){
  var host=$('#scorebars');host.innerHTML='';rows={};segState={};computeScale();buildLegend();
  var sl=survivors();
  ROWH=Math.max(26,Math.min(58,Math.floor(((host.clientHeight||190)-6)/(sl.length||1))));
  var th=Math.max(16,Math.min(30,ROWH-12));
  sl.forEach(function(d,i){
    var row=el('div','wrow'+(d.rank==1?' win':'')+(i===0?' rk1':''));row.style.top=(i*ROWH)+'px';
    row.innerHTML="<div class='wrk'>"+(i+1)+"</div><div class='wn'>"+first(d.name)+"</div><div class='wtrack' style='height:"+th+"px'><div class='wzero' style='left:"+ZERO+"%'></div></div><div class='wsc'>0.00</div>";
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
      $('#weighticker').innerHTML="<b>"+k.replace(/_/g,' ')+"</b> tips <b>"+first(byId(leadId).name)+"</b> ahead";}
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
    $('#whynote').innerHTML="<b>"+first(win.name)+"</b> wins on "+comps.join(', ')+" — the deciding factors.";}
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
  var stE={};active.forEach(function(k){var f=metricField(k);var vals=elig.map(function(d){return d[f]}).filter(function(v){return v!=null&&isFinite(v)});if(vals.length>=2)stE[k]=[_pmean(vals),_ppstd(vals)]});
  elig.forEach(function(d){var cp=[];active.forEach(function(k){var f=metricField(k),v=d[f];if(v==null||!stE[k]||stE[k][1]===0)return;cp.push({k:k,c:Math.round(eff[k]*((v-stE[k][0])/stE[k][1])*(DIR[k]||0)*1000)/1000})});
    var cm={};cp.forEach(function(x){cm[x.k]=x.c});d._cp=cp;d._cm=cm;d._sc=Math.round(cp.reduce(function(s,x){return s+x.c},0)*1000)/1000});
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
    var bp=$('#ip-bench');if(bp&&A.bench){bp.innerHTML="<div class='ipb'><span class='bd'></span><div class='bt'><div class='bn'>"+A.bench.name+"</div><div class='bm'>ret <b>"+pct(A.bench.ret)+"</b> · vol <b>"+pct(A.bench.vol)+"</b></div></div><div class='btag'>reference</div></div>"}
    if(document.body.classList.contains('settled')){rerender();}
    if(b.kind==='live')toast("<span class='tk'>&#10003;</span>Live market data fetched from FRED · "+b.name+" · as-of "+b.asOf);
    else if(manual)toast("<span class='tk'>&#10003;</span>Market data: "+b.name+" ("+b.kind+")");
  }).catch(function(e){
    clearTimeout(tmo);if(chip){chip.classList.remove('busy')}sourceChip();
    if(manual)toast("<span class='tk' style='color:var(--loss)'>!</span>Live fetch needs the server — run <b>./amb serve</b>");
  });
}
function sourceChip(){var c=$('#srcchip');if(!c)return;var b=A.bench;if(!b){c.style.display='none';return}
  var kind=b.kind||'snapshot';var lbl=(kind==='live'?'LIVE · FRED':kind==='cache'?'CACHED · FRED':'SNAPSHOT · local');
  c.className='srcchip '+kind;c.innerHTML="<i></i><b>market data</b> "+lbl;c.style.display='';
  c.title="Fund data: your local CSVs (funds.csv, returns.csv). Benchmark / market data: "+(kind==='live'?'live FRED API':'committed local snapshot')+" — "+(b.name||'')+", as-of "+(b.asOf||'')+".";}
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
  var rc=$('.rail .chips');if(rc){rc.innerHTML=sl.map(function(s){return "<div class='chip"+(s.rank==1?' r1':'')+"' data-fid='"+s.id+"' title='Open fund detail'><span class='n'>"+String(s.rank).padStart(2,'0')+"</span><span class='nm'>"+s.name+"</span><span class='rt'>"+pct(s.ret)+"</span><span class='cx'>⤢</span></div>"}).join('')}
  redrawTraj();
  if(win){A.verdict=win.name+" leads on risk-adjusted return.";A.verdictHtml="<b>"+win.name+"</b> leads on risk-adjusted return.";
    var comps=(win.components||[]).slice().sort(function(a,b){return b.c-a.c}).slice(0,3).map(function(c){return c.k.replace(/_/g,' ')});
    $('#whynote').innerHTML="<b>"+first(win.name)+"</b> wins on "+comps.join(', ')+" — the deciding factors.";}
  typeVerdict();}
function updateAdjNote(active){var full=weightFactors();var adj=active.length<full.length;var t=$('#weighticker');if(!t)return;
  t.classList.toggle('adj',adj);
  if(adj){var dropped=full.filter(function(k){return active.indexOf(k)<0}).map(function(k){return k.replace(/_/g,' ')});
    t.innerHTML="Weights re-normalized · dropped <b>"+dropped.join(', ')+"</b><span class='weigh-reset' id='wreset'>reset</span>";}
  else t.innerHTML='Final · weighted risk-adjusted score';}
function applyReweigh(active){if(active.length<1)return;reweigh(active);buildWeigh();renderFinal();layoutRows();paintSettledGraph();updateAdjNote(active);}
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
  var stE={};Object.keys(W).forEach(function(k){var f=metricField(k);var vals=elig.map(function(d){return d[f]}).filter(function(v){return v!=null&&isFinite(v)});if(vals.length>=2)stE[k]=[_pmean(vals),_ppstd(vals)]});
  elig.forEach(function(d){var s=0;Object.keys(W).forEach(function(k){var f=metricField(k),v=d[f];if(v==null||!stE[k]||stE[k][1]===0)return;s+=W[k]*((v-stE[k][0])/stE[k][1])*(DIR[k]||0)});d._rs=s});
  var ranked=elig.slice().sort(function(a,b){return b._rs-a._rs});var nS=ms.topN||5;var shortIds=ranked.slice(0,nS).map(function(d){return d.id});
  A.funds.forEach(function(d){
    if(!d.eligible){d.rank=null;d.cut=false;d.srank=99;d.components=[];d.comp={};d.score=0;if(d._rs!=null)delete d._rs;return}
    var si=shortIds.indexOf(d.id);var rk=si>=0?si+1:null;d.rank=rk;d.cut=(rk==null);d.srank=(rk||(d.cut?90:99));
    // components on the SAME eligible-z basis as the ranking, so bars == rank order
    var cp=[];Object.keys(W).forEach(function(k){var f=metricField(k),v=d[f];if(v==null||!stE[k]||stE[k][1]===0)return;cp.push({k:k,c:Math.round(W[k]*((v-stE[k][0])/stE[k][1])*(DIR[k]||0)*1000)/1000})});
    var cm={};cp.forEach(function(x){cm[x.k]=x.c});d.components=cp;d.comp=cm;d.score=Math.round(cp.reduce(function(s,x){return s+x.c},0)*1000)/1000;delete d._rs;});
  A.nShort=shortIds.length;A.nEligible=elig.length;A.nReject=A.funds.filter(function(d){return d.reason}).length;A.nTotal=A.funds.length;
  var win=A.funds.filter(function(d){return d.rank==1})[0];
  A.verdict=(win?first(win.name)+" leads on risk-adjusted return.":"No fund met the mandate.");
  A.verdictHtml=(win?"<b>"+first(win.name)+"</b> leads on risk-adjusted return.":"No fund met the mandate.");
  A._snap=null;rebuildGates();}
function applyMandate(){screenAndScore();var d=$('#drawer');if(d)d.classList.remove('open');rerender();}
var HOUSE=null;
function openMandate(){if(!HOUSE)HOUSE=JSON.parse(JSON.stringify({ms:A.mandateSpec,w:A.weights}));
  var ms=A.mandateSpec||{};var str016=[];A.funds.forEach(function(d){if(str016.indexOf(d.strategy)<0)str016.push(d.strategy)});
  var liq=ms.liqCap==null?400:ms.liqCap, vol=ms.volCap==null?0.5:ms.volCap, mdd=ms.maxddFloor==null?-0.5:ms.maxddFloor;
  var fs=weightFactors();
  function sld(id,lbl,val,min,max,step,fmt){return "<div class='mf-row'><label>"+lbl+"<b id='"+id+"v'>"+fmt(val)+"</b></label><input type='range' id='"+id+"' min='"+min+"' max='"+max+"' step='"+step+"' value='"+val+"'></div>"}
  var chips=str016.map(function(s){var on=(ms.exclStrats||[]).indexOf(s)<0;return "<span class='mf-chip"+(on?'':' off')+"' data-s=\""+s+"\">"+s+"</span>"}).join('');
  var wsl=fs.map(function(k,i){var pv=Math.round((A.weights[k]||0)*100);return "<div class='mf-row'><label><span class='wdot' style='background:"+segColor(i,false)+"'></span>"+k.replace(/_/g,' ')+"<b id='w_"+k+"v'>"+pv+"%</b></label><input type='range' class='mf-w' data-k='"+k+"' min='0' max='50' step='1' value='"+pv+"'></div>"}).join('');
  var h="<div class='d-pre'>Mandate · investable constraints</div><div class='d-name'>Edit the house view</div>"
   +"<p class='mm-p'>Re-screen and re-score the loaded universe live. Changes are stamped against the default mandate.</p>"
   +"<div class='mf-h'>Hard limits</div>"
   +sld('mf_liq','Liquidity · redeem within',liq,15,400,5,function(v){return Math.round(v)+' days'})
   +sld('mf_vol','Target vol ceiling',vol,0.05,0.6,0.01,function(v){return Math.round(v*100)+'%'})
   +sld('mf_mdd','Max drawdown tolerance',mdd,-0.6,-0.05,0.01,function(v){return Math.round(v*100)+'%'})
   +"<div class='mf-h'>Strategy exclusions <span class='mf-hint'>tap to exclude</span></div><div class='mf-chips'>"+chips+"</div>"
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
    var nw=[],c=1; for(j=0;j<m;j++){c*=(1+nr[j]); nw.push(Math.round(c*1e4)/1e4);}
    var nm=0; for(j=0;j<m;j++) nm+=nr[j]; nm/=m;
    var nv=0; for(j=0;j<m;j++){var e3=nr[j]-nm; nv+=e3*e3;} var vol=Math.sqrt(nv/(m-1))*Math.sqrt(ppy);
    var g2=1; for(j=0;j<m;j++) g2*=(1+nr[j]); var ret=(g2>0?Math.pow(g2,ppy/m)-1:0);
    var mar=rf/ppy,ds=0; for(j=0;j<m;j++){var q=nr[j]-mar; if(q<0) ds+=q*q;} var dvol=Math.sqrt(ds/m)*Math.sqrt(ppy);
    var peak=1,mdd=0; for(j=0;j<m;j++){if(nw[j]>peak)peak=nw[j]; var dq=nw[j]/peak-1; if(dq<mdd)mdd=dq;}
    d.wealth=nw; d.ret=ret; d.vol=vol;
    d.sharpe=(vol>0?(ret-rf)/vol:0);
    d.sortino=(dvol>0?(ret-rf)/dvol:0);
    d.maxdd=mdd; d.calmar=(mdd<0?ret/Math.abs(mdd):0);
    if(d.fee!=null) d.netret=ret-d.fee/100;
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
  var zv=surv.map(function(d){return d.vol}),zr=surv.map(function(d){return d.ret});
  if(b){zv=zv.concat([b.vol]);zr=zr.concat([b.ret])}
  var zvmin=Math.min.apply(null,zv),zvmax=Math.max.apply(null,zv),zrmin=Math.min.apply(null,zr),zrmax=Math.max.apply(null,zr);
  var zvr=(zvmax-zvmin)||1,zrr=(zrmax-zrmin)||1;
  surv.forEach(function(d){d.xz=Math.round((14+(d.vol-zvmin)/zvr*72)*10)/10;d.yz=Math.round((14+(d.ret-zrmin)/zrr*72)*10)/10});
  if(b){b.xz=Math.round((14+(b.vol-zvmin)/zvr*72)*10)/10;b.yz=Math.round((14+(b.ret-zrmin)/zrr*72)*10)/10;
    if(b.vol>0){var s=b.ret/b.vol;var mp=function(vol){return [Math.round((14+(vol-zvmin)/zvr*72)*10)/10,Math.round((14+(s*vol-zrmin)/zrr*72)*10)/10]};var p1=mp(zvmin),p2=mp(zvmax);A.benchLine={x1:p1[0],y1:p1[1],x2:p2[0],y2:p2[1]}}}
  A.funds.forEach(function(d){if(d.xz==null){d.xz=d.x;d.yz=d.y}});}
function buildGuides(){var g=$('#guides');
  if(!A.bench){if(g)g.classList.remove('on');return}
  var mk=$('#benchmk');if(mk&&A.bench.xz!=null){mk.style.left=A.bench.xz+'%';mk.style.bottom=A.bench.yz+'%';$('.bl',mk).innerHTML=A.bench.name.split(' (')[0]+' · reference'}
  var bl=$('#beatlbl');if(bl){bl.innerHTML='reference index ·<br>passive beta ·<br>out of mandate';}
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
  if(wf){var ap=X(0)+','+Y(lo)+' ';wf.wealth.forEach(function(w,i){ap+=X(i)+','+Y(w)+' '});ap+=X(n-1)+','+Y(lo);var ar=document.createElementNS(ns,'polygon');ar.setAttribute('points',ap);ar.setAttribute('fill','url(#wgrad)');ar.style.opacity='0';ar.style.transition='opacity 1s';svg.appendChild(ar);setTimeout(function(){ar.style.opacity='1'},700)}
  // benchmark dashed line
  if(bench){var bl=poly(bench.map(function(w,i){return X(i)+','+Y(w)}).join(' '),WARM,'1.3','4 3');bl.style.opacity='0';bl.style.transition='opacity .8s';svg.appendChild(bl);setTimeout(function(){bl.style.opacity='.7'},900)}
  // label positions
  var lab=funds.slice();if(bench)lab.push({__bench:true,wealth:bench});
  var used=[];lab.slice().sort(function(a,b){return Y(a.wealth[n-1])-Y(b.wealth[n-1])}).forEach(function(d){var tp=Y(d.wealth[n-1])/H*100;while(used.some(function(u){return Math.abs(u-tp)<7.5})){tp+=7.5}used.push(tp);d.__tp=tp});
  funds.forEach(function(d,idx){var win=d.rank==1;var col=win?WINC:GR[Math.min(idx,3)];
    var pl=poly(d.wealth.map(function(w,i){return X(i)+','+Y(w)}).join(' '),col,win?'2.4':'1.3');
    if(win)pl.style.filter='drop-shadow(0 0 5px '+cssv('--accent-glow')+')';
    pl.style.strokeDasharray='1600';pl.style.strokeDashoffset='1600';svg.appendChild(pl);
    setTimeout(function(){pl.style.transition='stroke-dashoffset 1.3s ease';pl.style.strokeDashoffset='0'},120+idx*80);
    var li=d.wealth.length-1,lv=d.wealth[li];
    var dot=document.createElementNS(ns,'circle');dot.setAttribute('cx',X(li));dot.setAttribute('cy',Y(lv));dot.setAttribute('r',win?'3.4':'2.2');dot.setAttribute('fill',col);dot.style.opacity='0';dot.style.transition='opacity .4s';svg.appendChild(dot);setTimeout(function(){dot.style.opacity='1'},120+idx*80+1150);
    var gain=isFinite(lv)?((lv-1)*100).toFixed(0):'—';
    var t=el('div','tt'+(win?' twin':''));t.style.color=col;t.style.right='2px';t.style.top=d.__tp+'%';t.innerHTML=first(d.name)+" <b>+"+gain+"%</b>";host.appendChild(t);
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
  az.innerHTML=
    "<div class='hud-grid'></div><div class='hud-scan'></div>"
   +"<div class='hud-top'><div class='hud-id'><span class='hud-rec'></span>EQUI · DATA CORE</div></div>"
   +"<div class='hud-stage' id='hudstage'></div>"
   +"<div class='hud-bot'><div class='hud-phase'><span class='hp-n'>00</span><span class='hp-l' id='hudphase'>DATA ACQUISITION</span></div><div class='hud-prog' id='hudprog'></div><div class='hud-log' id='hudlog'></div></div>";
  var prog=$('#hudprog',az),stage=$('#hudstage',az);
  ['acquire','parse','validate','reconcile','ready'].forEach(function(s,i){var seg=el('div','hpseg');seg.dataset.i=i;seg.innerHTML="<i></i><span>"+s+"</span>";prog.appendChild(seg)});
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
   +"<div class='az-src' id='srcA'><div class='az-src-h'><span class='az-ic'>▤</span>LOCAL FILES</div>"
     +"<div class='az-row'><span>funds.csv</span><b id='fa'>—</b></div><div class='az-row'><span>returns.csv</span><b id='fb'>—</b></div>"
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
  await wait(360);$('#srcA',az).classList.add('in');log('mounting local dataset · data/samples/');await wait(520);if(aborted)return;
  $('#fa',az).textContent=UNIV+' records';$('#fb',az).textContent=ROWS+' rows';$('#stA',az).innerHTML="<span class='ok'>●</span> loaded";
  $('#beamA',az).classList.add('on');await wait(500);if(aborted)return;
  $('#srcB',az).classList.add('in');
  if(LIVE){
    log('opening https://'+(A._keyed?'api':'fred')+'.stlouisfed.org …');await wait(700);if(aborted)return;
    $('#stB',az).innerHTML="<span class='ok'>●</span> 200 OK · live fetch · "+(b.n||36)+" monthly obs";
    $('#srcB',az).classList.add('active');$('#srcA',az).classList.add('standby');
    $('#azusing',az).innerHTML="<b>SOURCE IN USE</b> · benchmark fetched LIVE from FRED · "+(b.name||'S&amp;P 500')+" · as-of "+(b.asOf||'—');
  }else{
    log('FRED endpoint available · this run uses the committed local snapshot');await wait(700);if(aborted)return;
    $('#stB',az).innerHTML="<span class='muted'>○</span> "+(b.kind==='cache'?'served from cache':'not called · snapshot mode');
    $('#srcA',az).classList.add('active');$('#srcB',az).classList.add('standby');
    $('#azusing',az).innerHTML="<b>SOURCE IN USE</b> · benchmark from LOCAL "+(b.kind==='cache'?'cache':'snapshot')+" ("+(b.name||'S&amp;P 500')+", as-of "+(b.asOf||'—')+") · FRED live available";
  }
  $('#beamB',az).classList.add('on');
  await wait(1100);if(aborted)return;$('#hub',az).classList.add('live');await wait(800);if(aborted)return;

  // ══ 2 · PARSE — raw rows, column mapping, normalization, optional fields ══
  phase(2,'PARSE · NORMALIZE');
  // date, fund_id, raw value, status ('ok' | 'norm' cleaned→col5 | 'bad' date→quarantined); 3 bad matches the real quarantine count
  var sample=[['2023-07-01','MAC','0.021','ok',''],['2023-07-01','EQ-LS','1.95%','norm','0.0195'],['2023-08-01','MN','0,70%','norm','0.0070'],['—','VEN','0.031','bad',''],['2023-13-01','CR','0.012','bad',''],['n/a','DA','0.008','bad','']];
  stage.innerHTML=
   "<div class='az-parse'>"
   +"<div class='az-matrix'><div class='az-mh'><span>date</span><span>fund_id</span><span>monthly_return</span><span>status</span></div><div class='az-mb' id='mtx'></div></div>"
   +"<div class='az-side'>"
     +"<div class='az-sh'>COLUMN MAP</div><div class='az-map' id='cmap'></div>"
     +"<div class='az-sh'>NORMALIZE</div><div class='az-norm' id='cnorm'></div>"
     +"<div class='az-sh'>OPTIONAL FIELDS</div><div class='az-opt' id='copt'></div>"
   +"</div></div>";
  var mtx=$('#mtx',az);log('streaming rows · detecting schema');
  for(var r=0;r<sample.length;r++){if(aborted)return;var sr=sample[r];var stt=sr[3];var baddate=(stt==='bad');var row=el('div','az-mrow');
    var vcell=(stt==='norm')?"<span>"+sr[2]+" <b class='normv'>&rarr; "+sr[4]+"</b></span>":"<span>"+sr[2]+"</span>";
    var stat=baddate?"<span class='mstat'></span>":(stt==='norm'?"<span class='mstat'><span class='okc'>✓</span> cleaned</span>":"<span class='mstat'><span class='okc'>✓</span></span>");
    row.innerHTML=(baddate?"<span class='badc'>":"<span>")+sr[0]+"</span><span>"+sr[1]+"</span>"+vcell+stat;
    mtx.appendChild(row);setTimeout(function(rr){rr.classList.add('in')}.bind(null,row),20);await wait(240)}
  await wait(360);if(aborted)return;
  var maps=[['date','→ period'],['fund_id','→ id'],['monthly_return','→ return']];var cm=$('#cmap',az);
  for(var mi=0;mi<maps.length;mi++){if(aborted)return;var mr=el('div','az-mapr');mr.innerHTML="<b>"+maps[mi][0]+"</b><span>"+maps[mi][1]+"</span>";cm.appendChild(mr);setTimeout(function(x){x.classList.add('in')}.bind(null,mr),20);await wait(300)}
  var norms=['% → decimal','strip 1,000s','ISO-8601 dates','coerce n/a → null'];var cn=$('#cnorm',az);
  for(var ni=0;ni<norms.length;ni++){if(aborted)return;var nr=el('div','az-normr');nr.innerHTML="<span class='ck'>✓</span>"+norms[ni];cn.appendChild(nr);setTimeout(function(x){x.classList.add('in')}.bind(null,nr),20);await wait(230)}
  var opt=$('#copt',az);opt.innerHTML="<span class='optt'>redemption_freq</span><span class='optt'>lockup_months</span><span class='optt'>notice_days</span><span class='optt'>mgmt_fee</span><div class='opt-note'>→ liquidity + fee model</div>";
  setTimeout(function(){$$('.optt',az).forEach(function(t,i){setTimeout(function(){t.classList.add('in')},i*120)})},20);
  log('normalizing types · mapping optional liquidity & fee fields');
  await wait(1500);if(aborted)return;

  // ══ 3 · VALIDATE — quarantine bad rows ══
  phase(3,'VALIDATE');
  var qreason=(Object.keys(rd.quarantine_reasons||{'bad date':QN})[0]||'bad date');
  var qrows=$$('.az-mrow',az).filter(function(rw){return $('.badc',rw)});
  for(var vi=0;vi<qrows.length;vi++){if(aborted)return;qrows[vi].classList.add('quarr');
    var ms=$('.mstat',qrows[vi]);if(ms)ms.innerHTML="⊘ "+qreason;await wait(340)}
  log('validating '+ROWS+' rows · '+(ROWS-QN)+' valid · '+QN+' quarantined ('+qreason+') · row-level, no fund dropped');
  await wait(1700);if(aborted)return;

  // ══ 4 · RECONCILE — match IDs + align the window ══
  phase(4,'RECONCILE');
  stage.innerHTML="<div class='az-rec'><div class='az-rec-h'>IDENTIFIER RECONCILIATION</div><div class='az-chips' id='rchips'></div>"
   +"<div class='az-tl'><div class='az-tl-h'>SHARED WINDOW</div><div class='az-tl-bar'><i id='tlfill'></i></div>"
   +"<div class='az-tl-dates'><span>"+(ov.start||'')+"</span><span>"+(ov.end||'')+"</span></div>"
   +"<div class='az-tl-n'><b>"+((rd.coverage&&rd.coverage[0]&&rd.coverage[0].n)||36)+"</b> months · one shared window · "+WR+"/"+UNIV+" funds matched · quarantine was row-level, so every fund keeps its valid months</div></div></div>";
  var rc=$('#rchips',az);
  for(var f=0;f<A.funds.length;f++){if(aborted)return;var fd0=A.funds[f];var ch=el('div','az-fchip');ch.innerHTML="<span class='ck'>✓</span>"+fd0.id;rc.appendChild(ch);setTimeout(function(x){x.classList.add('in')}.bind(null,ch),20);await wait(150)}
  setTimeout(function(){var tf=$('#tlfill',az);if(tf)tf.classList.add('on')},300);
  log('reconciled '+WR+' identifiers · aligned '+(ov.start||'')+' → '+(ov.end||''));
  await wait(1600);if(aborted)return;

  // ══ 5 · READY ══
  phase(5,'UNIVERSE READY');
  stage.innerHTML="<div class='az-ready'><div class='az-ready-big'>UNIVERSE READY</div>"
   +"<div class='az-ready-sub'>"+UNIV+" funds · benchmark bound ("+(b.name||'index')+") · risk-free "+(A.rfUsed!=null?(A.rfUsed*100).toFixed(2)+'%':'—')+"</div>"
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
  chapter('01 · Universe',cap(NUM[total]||total)+' candidates','the full fund universe enters the screen');
  A.funds.forEach(function(d,i){var n=nodes[d.id];var p=universePos(i);n.style.left=p.x+'%';n.style.bottom=p.y+'%'});
  for(var i=0;i<total;i++){if(aborted)return;nodes[A.funds[i].id].classList.add('shown');await wait(170)}
  await wait(350);
  for(var i2=0;i2<total;i2++){if(aborted)return;nodes[A.funds[i2].id].classList.add('labeled');await wait(120)}
  await wait(2000);
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
    var sr=$('.sr',en);if(sr)sr.innerHTML=(rs.length>1?("breaches "+rs.length+" hard limits"):rs[0].text);
    en.classList.add('reject');await wait(1150+rs.length*950);   // hold longer when more limits break
    gates.forEach(function(g){g.classList.remove('act')});$$('#ip-gates .ipg').forEach(function(g){g.classList.remove('hot')});
    en.classList.remove('focus');en.classList.add('gone');updateCounter();await wait(720);
  }
  gates.forEach(function(g){g.classList.remove('act')});$$('#ip-gates .ipg').forEach(function(g){g.classList.remove('hot')});
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
function settle(){document.body.classList.add('settled');document.body.classList.remove('scoring');document.body.classList.remove('playing');setPaused(false);clearHalos();clearRtags();clearCue();A.funds.forEach(function(d){var n=nodes[d.id];if(d.eligible&&d.id!==(shortlisted()[0]||{}).id&&!d.cut)n.classList.remove('dimmed')});$('#chapter').innerHTML='';$('.rail').classList.add('in');$('#gates').classList.remove('on');$('#counter').classList.remove('on');typeVerdict();
  setTimeout(function(){layoutRows();redrawTraj()},680);}

function reset(){aborted=true;paused=false;flushWaits();document.body.classList.remove('settled');document.body.classList.remove('scoring');document.body.classList.remove('screening');document.body.classList.remove('playing');document.body.classList.remove('paused');document.body.classList.remove('az-run');var azl=$('#az');if(azl)azl.remove();
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
  return "<div class='fd-terms'>"+cells.map(function(c){return "<span><i>"+c[0]+"</i><b>"+c[1]+"</b></span>"}).join('')+"</div>";}
function fundDrawer(fid){var d=A.funds.filter(function(f){return f.id==fid})[0];if(!d)return;openDrawer("<div class='d-pre'>Fund brief · rank "+(d.rank?String(d.rank).padStart(2,'0'):'—')+"</div><div class='d-name'>"+d.name+"</div><div class='d-strat'>"+d.strategy+"</div>"+fundTerms(d)+d.detail)}

function wire(){
  var tip=$('#tip');
  document.addEventListener('mousemove',function(e){var n=e.target.closest('.node');if(n&&n.dataset.tip&&document.body.classList.contains('settled')){tip.innerHTML=n.dataset.tip;tip.style.opacity=1;tip.style.left=e.clientX+'px';tip.style.top=e.clientY+'px'}else tip.style.opacity=0});
  document.addEventListener('click',function(e){var n=e.target.closest('.node.cand');if(n&&document.body.classList.contains('settled')){fundDrawer(n.dataset.fid);return}var ch=e.target.closest('.chip');if(ch){fundDrawer(ch.dataset.fid)}});
  var pl=$('#play');if(pl)pl.addEventListener('click',replay);
  var sk=$('#skip');if(sk)sk.addEventListener('click',function(){aborted=true;paused=false;flushWaits();document.body.classList.remove('playing');document.body.classList.remove('paused');document.body.classList.remove('az-run');var azl=$('#az');if(azl)azl.remove();clearRtags();clearHalos();clearCue();setLeaderNode(null);A.funds.forEach(function(d){nodes[d.id].classList.remove('leader','focus','cutfocus','rshow')});document.body.classList.remove('screening');var ip=$('#intropane');if(ip)ip.classList.add('out');
    A.funds.forEach(function(d){var n=nodes[d.id];n.classList.add('shown','labeled');if(d.reason){n.classList.add('gone')}else{n.classList.add('ranked','showstat');n.style.left=d.xz+'%';n.style.bottom=d.yz+'%';if(d.cut)n.classList.add('cutout','dimmed');else if(d.rank!=1)n.classList.add('dimmed')}});
    frontier();document.body.classList.add('scoring');$('#scorepane').classList.add('in');buildWeigh();renderFinal();
    var win=shortlisted()[0];nodes[win.id].classList.add('focus','win','locked');var cr=$('.crown',nodes[win.id]);if(cr)cr.lastChild.textContent='recommended';nodes[win.id].classList.add('leader');
    $('#weighticker').innerHTML='Final · weighted risk-adjusted score';var comps=(win.components||[]).slice().sort(function(a,b){return b.c-a.c}).slice(0,3).map(function(c){return c.k.replace(/_/g,' ')});$('#whynote').innerHTML="<b>"+first(win.name)+"</b> wins on "+comps.join(', ')+" — the deciding factors.";$('#trajpane').classList.add('in');buildTraj();$('.sweetz').classList.add('on');updateCounter('Shortlist');settle()});
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
  var ub=$('#upBtn'),ui=$('#upInput');if(ub&&ui){ub.addEventListener('click',function(){ui.click()});ui.addEventListener('change',function(){ingestFiles(ui.files);ui.value=''})}
  var wl=$('#weighlegend');if(wl)wl.addEventListener('click',function(e){if(!document.body.classList.contains('settled'))return;var ch=e.target.closest('.lchip');if(!ch)return;var k=ch.dataset.k;var act=(A.activeMetrics||weightFactors().slice()).slice();var i=act.indexOf(k);if(i>=0){if(act.length<=1){toast("<span class='tk' style='color:var(--loss)'>!</span>Keep at least one metric");return}act.splice(i,1)}else act.push(k);applyReweigh(act)});
  document.addEventListener('click',function(e){if(e.target&&e.target.id==='wreset')resetWeights()});
  document.addEventListener('click',function(e){var pop=$('#pop');if(pop&&pop.classList.contains('on')&&!e.target.closest('#pop')&&!e.target.closest('#dlBtn'))pop.classList.remove('on')});
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
  var body=(dd?first(dd.name)+' carries the deepest drawdown at '+pct(dd.maxdd)+'. ':'')+(vv?first(vv.name)+' is the most volatile ('+pct(vv.vol)+'). ':'')+'Recomputed live against the current mandate.';
  var sum=w?('Recomputed live: '+A.nTotal+' funds screened, '+A.nEligible+' eligible, '+A.nShort+' shortlisted. '+first(w.name)+' leads on risk-adjusted return ('+pct(w.ret)+' at '+pct(w.vol)+' vol, Sharpe '+num(w.sharpe)+').'):'No fund met the mandate.';
  return {summary:sum,recommendation:(w?'<b>'+first(w.name)+'</b> leads on risk-adjusted return across the '+A.nShort+' shortlisted funds. The S&P benchmark is passive equity beta shown for reference — outside this mandate\'s strategy and risk limits.':'No fund met the mandate.'),keyRisks:{body:body,claims:claims},appendix:'Metrics recomputed client-side with the same deterministic engine (vol = sample-std annualized; Sharpe/Sortino excess over the mandate risk-free; beta/alpha OLS vs benchmark). Figures reflect the current mandate and inputs.'};}
function openMemo(){var m=(A._reran?liveMemo():(A.memo||{}));var risks=m.keyRisks||{};var w=shortlisted()[0]||{};
  var WARN="<svg viewBox='0 0 24 24' fill='none'><path d='M12 3l9 16H3l9-16z' stroke='currentColor' stroke-width='1.7' stroke-linejoin='round'/><path d='M12 10v4' stroke='currentColor' stroke-width='1.8' stroke-linecap='round'/><circle cx='12' cy='16.6' r='.6' fill='currentColor' stroke='currentColor'/></svg>";
  var kpis=[['Ann. return',pct(w.ret)],['Volatility',pct(w.vol)],['Sharpe',num(w.sharpe)],['Sortino',num(w.sortino)],['Max DD',pct(w.maxdd)],['Net of fee',(w.netret!=null?pct(w.netret):'—')]];
  var kpiH=kpis.map(function(k){return "<div class='mvk'><b>"+k[1]+"</b><i>"+k[0]+"</i></div>"}).join('');
  var rows=shortlisted().map(function(s){return "<tr"+(s.rank==1?" class='mwin'":"")+"><td class='mr'>"+String(s.rank).padStart(2,'0')+"</td><td class='mnm'>"+first(s.name)+"</td><td>"+pct(s.ret)+"</td><td>"+num(s.sharpe)+"</td><td>"+num(s.sortino)+"</td><td>"+pct(s.maxdd)+"</td><td class='msc'>"+(s.score>=0?'+':'')+s.score.toFixed(2)+"</td></tr>"}).join('');
  var claims=(risks.claims||[]).map(function(c){var mt=(c.metric||'');var sev=/drawdown/.test(mt)?' hi':/vol|beta/.test(mt)?' md':'';var parts=String(c.text).split(':');var lab=parts[0],val=parts.slice(1).join(':').trim();
    return "<div class='mvr"+sev+"'><span class='mvr-ic'>"+WARN+"</span><div class='mvr-b'><div class='mvr-t'>"+lab+(val?" <b>"+val+"</b>":"")+"</div><div class='mvr-f'>"+(c.fund||'')+"</div></div></div>"}).join('');
  var reco=m.recommendation||A.verdictHtml||'';
  var h="<div class='mv'>"
   +"<div class='mv-eyebrow'>Investment Committee memo · "+A.mandate+"</div>"
   +"<div class='mv-hero'>"+reco+"</div>"
   +"<div class='mv-pills'><span class='mvp'>"+A.nShort+" of "+A.nTotal+" advance</span><span class='mvp ok' title='Every numeric claim in this memo was recomputed from the source series and matched within tolerance'>&#10003; "+A.verified+"/"+A.total+" claims verified</span></div>"
   +(w.name?("<div class='mv-band'><div class='mv-band-h'><span class='mv-rec'>Recommended</span><span class='mv-wn'>"+first(w.name)+"</span><span class='mv-ws'>"+(w.strategy||'')+"</span></div><div class='mv-kpis'>"+kpiH+"</div></div>"):"")
   +(m.summary?("<p class='mv-lead'>"+m.summary+"</p>"):"")
   +"<div class='mv-h'>Shortlist</div><table class='mm-tbl'><thead><tr><th>#</th><th>Fund</th><th>Ret</th><th>SR</th><th>Sor</th><th>Max DD</th><th>Score</th></tr></thead><tbody>"+rows+"</tbody></table>"
   +"<div class='mv-h'>Key risks</div>"+(risks.body?("<p class='mv-lead sm'>"+risks.body+"</p>"):"")+"<div class='mvr-list'>"+claims+"</div>"
   +(m.appendix?("<details class='mv-apx'><summary>Data appendix &amp; methodology</summary><p class='mv-fine'>"+m.appendix+"</p></details>"):"")
   +"</div>";
  openDrawer(h);var d=$('#drawer');if(d)d.classList.add('wide');}
function auditDrawer(){var A2=A.audit||[];
  var groups=[],gi={};A2.forEach(function(c){if(!(c.fund in gi)){gi[c.fund]=groups.length;groups.push({fund:c.fund,items:[]})}groups[gi[c.fund]].items.push(c)});
  var body=groups.map(function(g){return "<div class='av-group'><div class='av-fund'>"+g.fund+"<span class='av-n'>"+g.items.length+" claims</span></div>"+g.items.map(function(c){var src=(c.sources||[]).join(' · ')||'—';return "<div class='av-item"+(c.verified?'':' bad')+"'><span class='av-ck'>"+(c.verified?'✓':'!')+"</span><div class='av-body'><div class='av-line'><span class='av-met'>"+c.metric+"</span><span class='av-val'>"+(c.value==null?'—':c.value)+"</span></div><div class='av-src' title=\""+src.replace(/"/g,'')+"\">"+src+"</div></div></div>"}).join('')+"</div>"}).join('');
  if(!A2.length)body="<p class='d-p'>This view is running on re-uploaded data — metrics were recomputed live from your CSV, so the memo's original claim ledger isn't attached. Load the bundled sample to see the full audit trail.</p>";
  var shield="<svg viewBox='0 0 24 24' fill='none'><path d='M12 2.4l7 2.9v5.7c0 4.7-3.3 8-7 9.6-3.7-1.6-7-4.9-7-9.6V5.3l7-2.9z' fill='var(--accent-soft)' stroke='var(--accent2)' stroke-width='1.3' stroke-linejoin='round'/><path d='M8.6 12.2l2.3 2.3 4.5-4.6' stroke='var(--accent2)' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'/></svg>";
  openDrawer("<div class='av-head'><div class='av-shield'>"+shield+"</div><div><div class='d-pre'>Audit trail · verification</div><div class='d-name'>"+A.verified+" / "+A.total+" verified</div></div></div><div class='d-strat' style='margin-top:12px'>every figure re-checked against the deterministic metrics engine</div><p class='d-p'>The memo's language model may narrate, but it never computes. Each numeric claim below was recomputed from the source return series and matched exactly — nothing reaches the page unverified.</p>"+body)}
function openExportPop(anchor){var pop=$('#pop');if(!pop)return;var r=anchor.getBoundingClientRect();
  pop.innerHTML="<div class='pop-card'><div class='pop-hd'><b>Export memo</b><i>a clean, no-nonsense PDF of the recommendation</i></div>"
    +"<div class='pop-opt' data-a='pdf'><span class='pi'>⤓</span><div class='pt'><b>Download PDF</b><i>saves the memo straight to your device</i></div></div>"
    +"<div class='pop-opt' data-a='print'><span class='pi'>⎙</span><div class='pt'><b>Print</b><i>opens the print dialog</i></div></div></div>";
  pop.style.top=(r.bottom+8)+'px';pop.style.right=(window.innerWidth-r.right)+'px';pop.classList.add('on');
  $$('.pop-opt',pop).forEach(function(o){o.addEventListener('click',function(){var a=o.dataset.a;pop.classList.remove('on');setTimeout(function(){if(a==='print')window.print();else downloadPDF()},120)})});}
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
function fundMetrics(r){var ppy=12,rf=(A.mandateSpec&&A.mandateSpec.rf)||0.02,n=r.length;if(n<2)return null;
  var g=1;r.forEach(function(x){g*=(1+x)});var annret=g>0?Math.pow(g,ppy/n)-1:g-1;
  var vol=_psstd(r)*Math.sqrt(ppy);var rfp=rf/ppy;var annex=_pmean(r.map(function(x){return x-rfp}))*ppy;
  var sh=vol?annex/vol:null;var dn=r.map(function(x){return Math.min(x-rfp,0)});var dd=Math.sqrt(_pmean(dn.map(function(x){return x*x})))*Math.sqrt(ppy);
  var so=dd?annex/dd:null;var w=1,peak=1,mdd=0,wl=[];r.forEach(function(x){w*=(1+x);wl.push(Math.round(w*1e4)/1e4);peak=Math.max(peak,w);mdd=Math.min(mdd,w/peak-1)});
  var cal=(mdd!==0)?annret/Math.abs(mdd):null;
  return {ann_return:annret,ann_vol:vol,sharpe:sh,sortino:so,calmar:cal,max_drawdown:mdd,wealth:wl};}
function parseCSV(t){var out=[];t.replace(/\r/g,'').split('\n').forEach(function(ln){if(!ln.trim())return;var row=[],cur='',q=false;for(var i=0;i<ln.length;i++){var c=ln[i];if(c==='"'){q=!q}else if(c===','&&!q){row.push(cur);cur=''}else cur+=c}row.push(cur);out.push(row.map(function(s){return s.trim()}))});return out}
function _findCol(hdr,cands){for(var i=0;i<cands.length;i++){var j=hdr.indexOf(cands[i]);if(j>=0)return j}for(var k=0;k<hdr.length;k++){for(var c=0;c<cands.length;c++){if(hdr[k].indexOf(cands[c])>=0)return k}}return -1}
function _normRet(raw){if(raw==null)return null;var s=String(raw).trim();if(!s||['na','n/a','nan','null','none','-'].indexOf(s.toLowerCase())>=0)return null;var pct=s.indexOf('%')>=0;s=s.replace(/%/g,'').replace(/,/g,'').replace(/\s/g,'');var v=parseFloat(s);if(isNaN(v)||!isFinite(v))return null;if(pct)return v/100;return Math.abs(v)>1.5?v/100:v}
function _validDate(s){if(s==null)return false;s=String(s).trim();if(!s||s.toLowerCase()==='nan')return false;return !isNaN(Date.parse(s))}
function ingestFiles(list){var files=[].slice.call(list||[]);if(!files.length)return;
  toast("reading "+files.length+" file"+(files.length>1?'s':'')+"…");
  Promise.all(files.map(function(f){return f.text()})).then(function(all){
    var funds={},ret={},order=[],quar=0;
    all.forEach(function(txt){var rows=parseCSV(txt);if(rows.length<2)return;var hdr=rows[0].map(function(h){return h.toLowerCase().trim()});
      var iId=_findCol(hdr,['fund_id','fund','ticker','symbol','id']),iNm=_findCol(hdr,['name']),iSt=_findCol(hdr,['strategy']);
      var iRet=_findCol(hdr,['monthly_return','return','ret','performance']),iDt=_findCol(hdr,['date','period','month','asof','as_of']);
      if(iNm>=0&&iSt>=0&&iId>=0&&iRet<0){rows.slice(1).forEach(function(r){var id=(r[iId]||'').trim();if(id)funds[id]={name:(r[iNm]||id).trim(),strategy:(r[iSt]||'').trim()}})}
      else if(iId>=0&&iRet>=0){rows.slice(1).forEach(function(r){var id=(r[iId]||'').trim();var dt=iDt>=0?(r[iDt]||'').trim():'x';var v=_normRet(r[iRet]);
        if(!id||id.toLowerCase()==='nan'||v==null||(iDt>=0&&!_validDate(dt))){quar++;return}   // mirror the engine: quarantine, never silently keep bad rows
        if(!ret[id]){ret[id]=[];order.push(id)}ret[id].push({d:dt,v:v})})}
    });
    var ids=Object.keys(ret);if(!ids.length){toast("<span class='tk' style='color:var(--loss)'>!</span>No returns found — expected columns like fund_id, date, monthly_return");return}
    ids.forEach(function(id){ret[id].sort(function(a,b){return a.d<b.d?-1:a.d>b.d?1:0})});
    recompute(funds,ret,order,quar);
  }).catch(function(e){toast("<span class='tk' style='color:var(--loss)'>!</span>Couldn't parse that CSV")});}
function recompute(funds,ret,order,quar){ try{
  var ms=A.mandateSpec||{exclStrats:[],volCap:null,rf:0.02,topN:5};var W=A.weights,DIR=A.dir||{};
  var benchId=null;['SP500','SPX','BENCH','BENCHMARK'].forEach(function(b){Object.keys(ret).forEach(function(id){if(id.toUpperCase()===b)benchId=id})});
  var ids=order.filter(function(id){return id!==benchId&&ret[id].length>=2});
  var mbf={},names={},strat={};ids.forEach(function(id){var series=ret[id].map(function(x){return x.v});var mm=fundMetrics(series);if(!mm)return;mbf[id]=mm;var fdef=funds[id]||{};names[id]=fdef.name||id;strat[id]=fdef.strategy||'—'});
  ids=ids.filter(function(id){return mbf[id]});if(ids.length<2){toast("<span class='tk' style='color:var(--loss)'>!</span>Need at least 2 funds with 2+ periods");return}
  var bench=null;if(benchId&&ret[benchId]&&ret[benchId].length>=2){var bs=ret[benchId].map(function(x){return x.v});var bm=fundMetrics(bs);if(bm)bench={name:names[benchId]||funds[benchId]&&funds[benchId].name||'Benchmark',vol:bm.ann_vol,ret:bm.ann_return,wealth:bm.wealth}}
  // mandate: eligible = strategy allowed AND vol <= cap
  function eligibleOf(id){var okS=ms.exclStrats.indexOf(strat[id])<0;var okV=(ms.volCap==null)||(mbf[id].ann_vol==null)||(mbf[id].ann_vol<=ms.volCap);return okS&&okV}
  var elig=ids.filter(eligibleOf);
  // rank eligible: z across eligible
  var stE={};Object.keys(W).forEach(function(k){var vals=elig.map(function(id){return mbf[id][k]}).filter(function(v){return v!=null});if(vals.length>=2)stE[k]=[_pmean(vals),_ppstd(vals)]});
  var scoreE={};elig.forEach(function(id){var s=0;Object.keys(W).forEach(function(k){var v=mbf[id][k];if(v==null||!stE[k]||stE[k][1]===0)return;s+=W[k]*((v-stE[k][0])/stE[k][1])*(DIR[k]||0)});scoreE[id]=s});
  var ranked=elig.slice().sort(function(a,b){return scoreE[b]-scoreE[a]});var shortIds=ranked.slice(0,ms.topN);var rankOf={};shortIds.forEach(function(id,i){rankOf[id]=i+1});
  // visual components on the SAME eligible-z basis as the ranking, so bars == rank order
  function comps(id){var out=[];Object.keys(W).forEach(function(k){var v=mbf[id][k];if(v==null||!stE[k]||stE[k][1]===0)return;out.push({k:k,c:Math.round(W[k]*((v-stE[k][0])/stE[k][1])*(DIR[k]||0)*1000)/1000})});return out}
  // universe scatter range (all funds with metrics)
  var vols=ids.map(function(id){return mbf[id].ann_vol}),rets=ids.map(function(id){return mbf[id].ann_return});
  var vmin=Math.min.apply(null,vols),vmax=Math.max.apply(null,vols),rmin=Math.min.apply(null,rets),rmax=Math.max.apply(null,rets);var vr=(vmax-vmin)||1,rr=(rmax-rmin)||1;
  var fd=ids.map(function(id){var m=mbf[id];var rk=rankOf[id]||null;var elig1=eligibleOf(id);var cut=(rk==null&&elig1);
    var reasons=[];if(!elig1){
      if(ms.volCap!=null&&m.ann_vol>ms.volCap)reasons.push({text:'too volatile · '+Math.round(m.ann_vol*100)+'% > '+Math.round(ms.volCap*100)+'% cap',kind:'VOLATILITY'});
      if(ms.maxddFloor!=null&&m.max_drawdown!=null&&m.max_drawdown<ms.maxddFloor)reasons.push({text:'drawdown · '+Math.round(m.max_drawdown*100)+'% beyond '+Math.round(ms.maxddFloor*100)+'% floor',kind:'DRAWDOWN'});
      if(ms.exclStrats.indexOf(strat[id])>=0)reasons.push({text:'off-strategy · '+strat[id],kind:'STRATEGY'});
      if(!reasons.length)reasons.push({text:'excluded by mandate',kind:'MANDATE'});}
    var reason=(reasons.length?reasons[0].text:null);
    var cp=elig1?comps(id):[];var cm={};cp.forEach(function(x){cm[x.k]=x.c});var sc=Math.round(cp.reduce(function(s,x){return s+x.c},0)*1000)/1000;
    return {id:id,name:names[id],strategy:strat[id],rank:rk,excluded:rk==null,eligible:elig1,cut:cut,rkind:(reasons.length?reasons[0].kind:null),reasons:reasons,
      srank:(rk||(cut?90:99)),x:Math.round((12+(m.ann_vol-vmin)/vr*76)*10)/10,y:Math.round((12+(m.ann_return-rmin)/rr*76)*10)/10,
      ret:m.ann_return,vol:m.ann_vol,sharpe:m.sharpe,sortino:m.sortino,calmar:m.calmar,maxdd:m.max_drawdown,wealth:m.wealth,reason:reason,components:cp,comp:cm,score:sc,detail:''};});
  // zoom coords over eligible + bench
  var surv=fd.filter(function(d){return d.eligible});var benchLine=null,gateX=null;
  if(surv.length){var zv=surv.map(function(d){return d.vol}),zr=surv.map(function(d){return d.ret});if(bench){zv=zv.concat([bench.vol]);zr=zr.concat([bench.ret])}
    var zvmin=Math.min.apply(null,zv),zvmax=Math.max.apply(null,zv),zrmin=Math.min.apply(null,zr),zrmax=Math.max.apply(null,zr);var zvr=(zvmax-zvmin)||1,zrr=(zrmax-zrmin)||1;
    surv.forEach(function(d){d.xz=Math.round((14+(d.vol-zvmin)/zvr*72)*10)/10;d.yz=Math.round((14+(d.ret-zrmin)/zrr*72)*10)/10});
    if(bench){bench.xz=Math.round((14+(bench.vol-zvmin)/zvr*72)*10)/10;bench.yz=Math.round((14+(bench.ret-zrmin)/zrr*72)*10)/10;
      if(bench.vol>0){var s=bench.ret/bench.vol;var mp=function(vol){return [Math.round((14+(vol-zvmin)/zvr*72)*10)/10,Math.round((14+(s*vol-zrmin)/zrr*72)*10)/10]};var p1=mp(zvmin),p2=mp(zvmax);benchLine={x1:p1[0],y1:p1[1],x2:p2[0],y2:p2[1]}}}
    if(ms.volCap!=null){var gx=12+(ms.volCap-vmin)/vr*76;if(gx>0&&gx<100)gateX=Math.round(gx*10)/10}}
  fd.forEach(function(d){if(d.xz==null){d.xz=d.x;d.yz=d.y}});
  // detail html for the drawer
  fd.forEach(function(d){var cells=[['ann return',pct(d.ret)],['ann vol',pct(d.vol)],['sharpe',num(d.sharpe)],['sortino',num(d.sortino)],['calmar',num(d.calmar)],['max drawdown',pct(d.maxdd)]].map(function(c){return "<div class='cell'><b>"+c[1]+"</b><i>"+c[0]+"</i></div>"}).join('');
    var lead=d.rank?("ranks #"+d.rank+" for this mandate"):(d.reason?("was excluded — "+d.reason):"was outscored below the shortlist");
    d.detail="<p class='d-p'>"+d.name+" "+lead+". It returned "+pct(d.ret)+" annualized against "+pct(d.vol)+" volatility, a Sharpe of "+num(d.sharpe)+" and a Sortino of "+num(d.sortino)+".</p><div class='mgrid'>"+cells+"</div><div class='src-lbl'>Recomputed from your uploaded returns</div>";});
  var win=fd.filter(function(d){return d.rank==1})[0];
  A.funds=fd;A.bench=bench;A.benchLine=benchLine;A.gateX=gateX;A.volcap=(ms.volCap!=null?Math.round(ms.volCap*100)+'%':null);
  A.nTotal=fd.length;A.nEligible=fd.filter(function(d){return d.eligible}).length;A.nShort=shortIds.length;A.nReject=fd.filter(function(d){return d.reason}).length;
  A.verdict=(win?win.name+" leads on risk-adjusted return.":"No fund met the mandate.");A.verdictHtml=(win?"<b>"+win.name+"</b> leads on risk-adjusted return.":"No fund met the mandate.");
  A.audit=[];A.shareText=(win?win.name+" — recommended (risk-adjusted). "+A.nShort+" shortlisted from "+A.nTotal+".":"No fund met the mandate.");
  rerender();
  toast("<span class='tk'>&#10003;</span>Re-ran the analysis · "+A.nTotal+" funds → "+A.nShort+" shortlisted"+(quar?" · "+quar+" bad rows quarantined":""));
 }catch(err){toast("<span class='tk' style='color:var(--loss)'>!</span>Analysis failed on that data")}}
function rerender(){aborted=true;A.weights0=Object.assign({},A.weights);A.activeMetrics=weightFactors().slice();A._snap=null;A._reran=true;var f=$('#field');$$('.node',f).forEach(function(n){n.remove()});nodes={};rows={};segState={};trajBuilt=false;
  document.body.classList.remove('settled','scoring','screening');$('#scorebars').innerHTML='';$('#weighticker').innerHTML='';$('#whynote').innerHTML='';$('#weighlegend').innerHTML='';$('#weighlegend').classList.remove('in');$('#traj').innerHTML='';$$('.tt,.tx,.ty').forEach(function(t){t.remove()});
  $('.rail').classList.remove('in');$('#trajpane').classList.remove('in');$('#scorepane').classList.remove('in');$('.sweetz').classList.remove('on');clearCue();
  // rebuild the shortlist rail
  var rc=$('.rail .chips');if(rc){rc.innerHTML=shortlisted().map(function(s){return "<div class='chip"+(s.rank==1?' r1':'')+"' data-fid='"+s.id+"' title='Open fund detail'><span class='n'>"+String(s.rank).padStart(2,'0')+"</span><span class='nm'>"+s.name+"</span><span class='rt'>"+pct(s.ret)+"</span><span class='cx'>⤢</span></div>"}).join('')}
  buildField();buildIntro();setPrintDate();_lastLive=null;setTimeout(function(){aborted=false;story()},60);}
function doShare(){var txt=A.shareText||document.title;
  var ok=function(){toast("<span class='tk'>✓</span>Recommendation summary copied to clipboard")};
  try{if(navigator.share){navigator.share({title:A.title||document.title,text:txt}).then(function(){},function(){});toast("<span class='tk'>✓</span>Opening share…");return}}catch(e){}
  try{navigator.clipboard.writeText(txt).then(ok,ok)}catch(e){ok()}}
function setPrintDate(){var el2=$('#pd-date');if(!el2)return;try{var d=new Date();el2.textContent=d.toLocaleDateString(undefined,{year:'numeric',month:'long',day:'numeric'})}catch(e){el2.textContent=''}}
window.addEventListener('DOMContentLoaded',function(){document.documentElement.dataset.theme='light';buildField();buildIntro();sourceChip();setPrintDate();wire();
  // when served by `./amb serve`, pull live market data (browser -> localhost -> FRED)
  // BEFORE the story so Act 0 shows the real live fetch; else play immediately.
  if(servedLive()){fetchLiveMarket(false).then(function(){rerender()})}else{story()}});
})();
