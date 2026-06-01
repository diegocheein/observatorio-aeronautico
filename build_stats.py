# -*- coding: utf-8 -*-
"""Genera estadisticas.html (Estadísticas y alertas) con el tema oscuro compartido."""
import csv, json, os
from site_theme import THEME, top

BASE=os.path.dirname(os.path.abspath(__file__))
MOV=os.path.join(BASE,"movimientos.csv"); OUT=os.path.join(BASE,"estadisticas.html")
rows=list(csv.DictReader(open(MOV,encoding="utf-8"))) if os.path.exists(MOV) else []
flights=[{"matricula":r.get("matricula",""),"provincia":r.get("provincia",""),
          "inicio":r.get("inicio",""),"fin":r.get("fin",""),
          "origen":r.get("origen",""),"destino":r.get("destino",""),"dcode":r.get("destino_code","")} for r in rows]
DATA=json.dumps(flights, ensure_ascii=False)

BODY = """
<div class="wrap">
 <h1 class="htitle">Estadísticas y alertas</h1>
 <p class="hsub">Patrones de uso, actividad por aeronave y posibles coincidencias.</p>
 <div class="filters">
   <div><label>Aeronave</label><select id="fAero"><option value="">Todas</option></select></div>
   <div><label>Provincia</label><select id="fProv"><option value="">Todas</option></select></div>
   <div><label>Período</label><div class="seg" id="periodo">
     <button data-p="30d">30 días</button><button data-p="6m">6 meses</button>
     <button data-p="1y">1 año</button><button data-p="all" class="act">Histórico</button></div></div>
   <span class="info" id="info"></span>
 </div>
 <div class="kpis">
   <div class="kpi"><div class="bar"></div><div class="v" id="k-tot">0</div><div class="l">Vuelos</div></div>
   <div class="kpi amar"><div class="bar"></div><div class="v" id="k-fds">0</div><div class="l">Fin de semana</div></div>
   <div class="kpi"><div class="bar"></div><div class="v" id="k-int">0</div><div class="l">Internacionales</div></div>
   <div class="kpi amar"><div class="bar"></div><div class="v" id="k-al">0</div><div class="l">Coincidencias 3+</div></div>
 </div>
 <div class="panel"><div class="ph">Ranking de aeronaves más activas</div><div class="pb"><canvas id="cRank"></canvas></div></div>
 <div class="panel"><div class="ph">Coincidencia de 3 o más aeronaves</div>
   <div class="pb" style="padding-bottom:6px"><span class="muted">Mismo lugar y día. Indicio para revisión, no conclusión.</span></div>
   <div class="scroll"><table id="t-al"><thead><tr><th>Fecha</th><th>Lugar</th><th>Aeronaves</th><th>Provincias</th><th>N</th></tr></thead><tbody></tbody></table></div>
 </div>
 <div class="two">
  <div class="panel"><div class="ph">Vuelo internacional</div><div class="scroll"><table id="t-int"><thead><tr><th>Fecha</th><th>Matrícula</th><th>Provincia</th><th>Destino</th></tr></thead><tbody></tbody></table></div></div>
  <div class="panel"><div class="ph">Actividad de fin de semana</div><div class="scroll"><table id="t-fds"><thead><tr><th>Fecha</th><th>Matrícula</th><th>Provincia</th><th>Ruta</th></tr></thead><tbody></tbody></table></div></div>
 </div>
 <div class="panel"><div class="ph">Actividad por provincia</div><div class="pb"><canvas id="cProv"></canvas></div></div>
</div>
<script>
const FL=__DATA__; let period='all',fAero='',fProv='';
const dt=s=>new Date((s||'').slice(0,10)+'T12:00');
const esFds=s=>{const d=new Date((s||'').replace(' ','T'));return !isNaN(d)&&(d.getDay()===0||d.getDay()===6);};
const esInt=c=>!!c&&!c.startsWith('SA');
let chR=null,chP=null;
const valLabels={id:'vl',afterDatasetsDraw(c){const x=c.ctx;x.save();x.fillStyle='#cfe0f0';x.font='bold 11px Arial';x.textBaseline='middle';
  c.data.datasets[0].data.forEach((v,i)=>{const b=c.getDatasetMeta(0).data[i];if(b)x.fillText(v,b.x+6,b.y);});x.restore();}};
function bar(prev,id,labels,data){if(prev)prev.destroy();
  return new Chart(document.getElementById(id),{type:'bar',plugins:[valLabels],
    data:{labels,datasets:[{data,backgroundColor:'#38BDF8',borderRadius:6,barThickness:14}]},
    options:{indexAxis:'y',layout:{padding:{right:26}},plugins:{legend:{display:false}},
      scales:{x:{beginAtZero:true,ticks:{color:'#94A3B8',precision:0},grid:{color:'#15324c'}},
        y:{ticks:{color:'#cfe0f0',font:{size:11}},grid:{display:false}}}}});}
function inPeriod(f){if(period==='all')return true;const days={'30d':30,'6m':183,'1y':366}[period];
  const lim=new Date();lim.setHours(0,0,0,0);lim.setDate(lim.getDate()-days);return dt(f.inicio)>=lim;}
function fillSel(){const sa=document.getElementById('fAero'),sp=document.getElementById('fProv');
  [...new Set(FL.map(f=>f.matricula).filter(Boolean))].sort().forEach(m=>{const o=document.createElement('option');o.value=m;o.textContent=m;sa.appendChild(o);});
  [...new Set(FL.map(f=>f.provincia).filter(Boolean))].sort().forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=p;sp.appendChild(o);});}
function recompute(){
  const base=FL.filter(f=>inPeriod(f)&&(!fProv||f.provincia===fProv));
  const set=base.filter(f=>!fAero||f.matricula===fAero);
  const S=(id,v)=>document.getElementById(id).textContent=v;
  const g={};
  base.forEach(f=>{const fch=(f.fin||f.inicio||'').slice(0,10),dst=f.destino;
    if(!fch||!dst||dst.charAt(0)==='(')return;const k=fch+'|'+dst;(g[k]=g[k]||{a:new Set(),p:new Set(),fch,dst});g[k].a.add(f.matricula);if(f.provincia)g[k].p.add(f.provincia);});
  let enc=Object.values(g).filter(x=>x.a.size>=3).map(x=>({fch:x.fch,dst:x.dst,a:[...x.a].sort(),p:[...x.p].sort(),n:x.a.size}));
  if(fAero)enc=enc.filter(e=>e.a.includes(fAero));
  enc.sort((x,y)=>y.n-x.n||(x.fch<y.fch?1:-1));
  S('k-tot',set.length);S('k-fds',set.filter(f=>esFds(f.inicio)).length);
  S('k-int',set.filter(f=>esInt(f.dcode)).length);S('k-al',enc.length);
  const ca={},cp={};base.forEach(f=>{ca[f.matricula]=(ca[f.matricula]||0)+1;cp[f.provincia]=(cp[f.provincia]||0)+1;});
  const topA=Object.entries(ca).sort((a,b)=>b[1]-a[1]).slice(0,12);
  const topP=Object.entries(cp).sort((a,b)=>b[1]-a[1]).slice(0,12);
  chR=bar(chR,'cRank',topA.map(([k])=>k),topA.map(([,v])=>v));
  chP=bar(chP,'cProv',topP.map(([k])=>k),topP.map(([,v])=>v));
  const ta=document.querySelector('#t-al tbody');ta.innerHTML='';
  if(!enc.length)ta.innerHTML='<tr><td colspan=5 class=muted>Sin coincidencias en este filtro.</td></tr>';
  enc.forEach(e=>ta.insertAdjacentHTML('beforeend',`<tr class=al><td>${e.fch}</td><td>${e.dst}</td><td>${e.a.join(', ')}</td><td>${e.p.join(', ')}</td><td>${e.n} <span class=pill>revisar</span></td></tr>`));
  const ti=document.querySelector('#t-int tbody');ti.innerHTML='';
  const inter=set.filter(f=>esInt(f.dcode)).sort((a,b)=>a.inicio<b.inicio?1:-1);
  if(!inter.length)ti.innerHTML='<tr><td colspan=4 class=muted>Sin vuelos internacionales.</td></tr>';
  inter.forEach(f=>ti.insertAdjacentHTML('beforeend',`<tr><td>${f.inicio}</td><td><b>${f.matricula}</b></td><td>${f.provincia}</td><td>${f.destino}</td></tr>`));
  const tf=document.querySelector('#t-fds tbody');tf.innerHTML='';
  const fds=set.filter(f=>esFds(f.inicio)).sort((a,b)=>a.inicio<b.inicio?1:-1);
  if(!fds.length)tf.innerHTML='<tr><td colspan=4 class=muted>Sin actividad de fin de semana.</td></tr>';
  fds.forEach(f=>tf.insertAdjacentHTML('beforeend',`<tr><td>${f.inicio}</td><td><b>${f.matricula}</b></td><td>${f.provincia}</td><td>${f.origen} → ${f.destino}</td></tr>`));
  const lbl={'30d':'últimos 30 días','6m':'últimos 6 meses','1y':'último año','all':'histórico'}[period];
  document.getElementById('info').textContent=`${set.length} vuelos · ${lbl}${fProv?' · '+fProv:''}${fAero?' · '+fAero:''}`;
}
document.querySelectorAll('#periodo button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#periodo button').forEach(x=>x.classList.remove('act'));b.classList.add('act');period=b.dataset.p;recompute();});
document.getElementById('fAero').onchange=e=>{fAero=e.target.value;recompute();};
document.getElementById('fProv').onchange=e=>{fProv=e.target.value;recompute();};
fillSel(); recompute();
</script></body></html>"""

HTML=("<!doctype html><html lang=es><head><meta charset=utf-8>"
 "<meta name=viewport content='width=device-width, initial-scale=1'>"
 "<title>Estadísticas y alertas — Observatorio Aeronáutico</title>"
 "<script src='https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js'></script>"
 +THEME+"</head><body>"+top("estadisticas.html")+BODY)
open(OUT,"w",encoding="utf-8").write(HTML.replace("__DATA__",DATA))
print(f"Estadísticas: estadisticas.html | vuelos {len(flights)}")
