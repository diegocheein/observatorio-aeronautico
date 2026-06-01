# -*- coding: utf-8 -*-
"""Genera reporte_movimientos.html (Reporte histórico) con el tema oscuro compartido."""
import csv, json, os
from site_theme import THEME, top

BASE=os.path.dirname(os.path.abspath(__file__))
MOV=os.path.join(BASE,"movimientos.csv"); OUT=os.path.join(BASE,"reporte_movimientos.html")

def fnum(x):
    try: return float(x)
    except: return None
rows=list(csv.DictReader(open(MOV,encoding="utf-8"))) if os.path.exists(MOV) else []
flights=[{"matricula":r.get("matricula",""),"provincia":r.get("provincia",""),
          "inicio":r.get("inicio",""),"dur":r.get("dur_min",""),
          "origen":r.get("origen",""),"destino":r.get("destino",""),"dcode":r.get("destino_code",""),
          "olat":fnum(r.get("origen_lat")),"olon":fnum(r.get("origen_lon")),
          "dlat":fnum(r.get("destino_lat")),"dlon":fnum(r.get("destino_lon"))} for r in rows]
DATA=json.dumps(flights, ensure_ascii=False)

BODY = """
<div class="wrap">
 <h1 class="htitle">Reporte histórico</h1>
 <p class="hsub">Movimientos detectados por aeronave, fecha y provincia.</p>
 <div class="filters">
   <div><label>Aeronave</label><select id="fAero"><option value="">Todas</option></select></div>
   <div><label>Provincia</label><select id="fProv"><option value="">Todas</option></select></div>
   <span class="info" id="info"></span>
 </div>
 <div class="kpis">
   <div class="kpi"><div class="bar"></div><div class="v" id="k-tot">0</div><div class="l">Vuelos registrados</div></div>
   <div class="kpi amar"><div class="bar"></div><div class="v" id="k-fds">0</div><div class="l">Fin de semana</div></div>
   <div class="kpi"><div class="bar"></div><div class="v" id="k-noc">0</div><div class="l">Nocturnos</div></div>
   <div class="kpi fly"><div class="bar"></div><div class="v" id="k-int">0</div><div class="l">Internacionales</div></div>
 </div>
 <div class="panel"><div class="ph">Rutas detectadas</div><div id="map"></div></div>
 <p class="note">Las líneas muestran rutas detectadas. Los colores indican tipo de vuelo.</p>
 <div class="panel"><div class="ph">Vuelos</div><div class="scroll">
   <table id="t"><thead><tr><th>Fecha</th><th>Matrícula</th><th>Provincia</th><th>Origen</th><th>Destino</th><th>Dur</th><th>Señales</th></tr></thead><tbody></tbody></table>
 </div></div>
 <div class="two">
  <div class="panel"><div class="ph">Por aeronave</div><div class="scroll"><table id="ta"><thead><tr><th>Matrícula</th><th>Provincia</th><th>Vuelos</th></tr></thead><tbody></tbody></table></div></div>
  <div class="panel"><div class="ph">Por provincia</div><div class="scroll"><table id="tp"><thead><tr><th>Provincia</th><th>Vuelos</th><th>Aeronaves</th></tr></thead><tbody></tbody></table></div></div>
 </div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const FL=__DATA__; let fAero='',fProv='';
const fecha=s=>(s||'').slice(0,10);
const dt=s=>new Date((s||'').replace(' ','T'));
const esFds=s=>{const d=dt(s);return !isNaN(d)&&(d.getDay()===0||d.getDay()===6);};
const esNoc=s=>{const d=dt(s);return !isNaN(d)&&(d.getHours()>=22||d.getHours()<6);};
const esInt=c=>!!c&&!c.startsWith('SA');
const map=L.map('map',{attributionControl:false}).setView([-40,-63],4);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',{maxZoom:11}).addTo(map);
let layers=[];
function fillSel(){const sa=document.getElementById('fAero'),sp=document.getElementById('fProv');
  [...new Set(FL.map(f=>f.matricula).filter(Boolean))].sort().forEach(m=>{const o=document.createElement('option');o.value=m;o.textContent=m;sa.appendChild(o);});
  [...new Set(FL.map(f=>f.provincia).filter(Boolean))].sort().forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=p;sp.appendChild(o);});}
function flags(f){let h='';
  if(esInt(f.dcode))h+='<span class="badge b-int">internacional</span>';
  if(esFds(f.inicio))h+='<span class="badge b-fds">fin de semana</span>';
  if(esNoc(f.inicio))h+='<span class="badge b-noc">nocturno</span>';return h;}
function render(){
  const fl=FL.filter(f=>(!fAero||f.matricula===fAero)&&(!fProv||f.provincia===fProv));
  const S=(id,v)=>document.getElementById(id).textContent=v;
  S('k-tot',fl.length);S('k-fds',fl.filter(f=>esFds(f.inicio)).length);
  S('k-noc',fl.filter(f=>esNoc(f.inicio)).length);S('k-int',fl.filter(f=>esInt(f.dcode)).length);
  layers.forEach(l=>map.removeLayer(l));layers=[];const pts=[];
  fl.forEach(f=>{ if(f.olat==null||f.dlat==null)return;
    const col=esInt(f.dcode)?'#EF4444':(esFds(f.inicio)?'#F59E0B':'#38BDF8');
    layers.push(L.polyline([[f.olat,f.olon],[f.dlat,f.dlon]],{color:col,weight:2,opacity:.7}).addTo(map)
      .bindTooltip(`${f.matricula}: ${f.origen} → ${f.destino}`));
    pts.push([f.olat,f.olon],[f.dlat,f.dlon]);});
  if(pts.length)map.fitBounds(pts,{padding:[40,40]});
  const tb=document.querySelector('#t tbody');tb.innerHTML='';
  fl.slice().sort((a,b)=>a.inicio<b.inicio?1:-1).forEach(f=>tb.insertAdjacentHTML('beforeend',
    `<tr><td>${f.inicio} ${flags(f)}</td><td><b>${f.matricula}</b></td><td>${f.provincia}</td><td>${f.origen}</td><td>${f.destino}</td><td>${f.dur}</td><td></td></tr>`));
  const ca={},cp={},cpa={};
  fl.forEach(f=>{ca[f.matricula]=(ca[f.matricula]||0)+1;cp[f.provincia]=(cp[f.provincia]||0)+1;(cpa[f.provincia]=cpa[f.provincia]||new Set()).add(f.matricula);});
  const ta=document.querySelector('#ta tbody');ta.innerHTML='';
  Object.entries(ca).sort((a,b)=>b[1]-a[1]).forEach(([k,v])=>ta.insertAdjacentHTML('beforeend',`<tr><td><b>${k}</b></td><td>${(FL.find(f=>f.matricula===k)||{}).provincia||''}</td><td>${v}</td></tr>`));
  const tp=document.querySelector('#tp tbody');tp.innerHTML='';
  Object.entries(cp).sort((a,b)=>b[1]-a[1]).forEach(([k,v])=>tp.insertAdjacentHTML('beforeend',`<tr><td>${k}</td><td>${v}</td><td>${cpa[k].size}</td></tr>`));
  document.getElementById('info').textContent=`${fl.length} vuelos${fProv?' · '+fProv:''}${fAero?' · '+fAero:''}`;
}
document.getElementById('fAero').onchange=e=>{fAero=e.target.value;render();};
document.getElementById('fProv').onchange=e=>{fProv=e.target.value;render();};
fillSel(); render();
</script></body></html>"""

HTML=("<!doctype html><html lang=es><head><meta charset=utf-8>"
 "<meta name=viewport content='width=device-width, initial-scale=1'>"
 "<title>Reporte histórico — Observatorio Aeronáutico</title>"
 "<link rel='stylesheet' href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'/>"
 +THEME+"</head><body>"+top("reporte_movimientos.html")+BODY)
open(OUT,"w",encoding="utf-8").write(HTML.replace("__DATA__",DATA))
print(f"Reporte: reporte_movimientos.html | vuelos {len(flights)}")
