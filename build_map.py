# -*- coding: utf-8 -*-
"""
Genera mapa_vivo.html (Mapa en vivo) con el header compartido y filtros horizontales.
- Sin barra lateral: barra de filtros arriba + mapa a pantalla completa.
- Mostrar: todas / por provincia / privadas. Aeronave individual para ver su historial.
- Al elegir una aeronave aparece un panel flotante con datos e historial (rango máx. 1 año).
- En vuelo: rojo pulsante; en tierra: azul. Rutas del historial en gris con flechas.
Uso: python3 build_map.py
"""
import csv, json, os, sqlite3, collections
from site_theme import THEME, top

BASE=os.path.dirname(os.path.abspath(__file__))
DB=os.environ.get("PADRON_DB", os.path.join(BASE,"vuelos.db"))
MOV=os.path.join(BASE,"movimientos.csv"); OUT=os.path.join(BASE,"mapa_vivo.html")
DATASETS=[("padron_aeronaves.csv","provincial"),("charters_dirigentes.csv","privado")]

def fnum(x):
    try: return float(x)
    except: return None
aircraft, meta_by_hex=[],{}
for fname,grupo in DATASETS:
    p=os.path.join(BASE,fname)
    if not os.path.exists(p): continue
    for r in csv.DictReader(open(p,encoding="utf-8")):
        hx=(r.get("hex") or "").strip().upper()
        grp="privado" if (grupo=="privado" or "charter" in (r.get("organismo","").lower())) else "provincial"
        it={"matricula":r.get("matricula",""),"hex":hx,"grupo":grp,"provincia":r.get("provincia",""),
            "tipo":r.get("tipo",""),"lat":None,"lon":None,"track":0,"flying":False}
        aircraft.append(it)
        if hx: meta_by_hex[hx]=it
if os.path.exists(DB):
    try:
        con=sqlite3.connect(DB)
        for hx,lat,lon,track in con.execute("""SELECT s.hex,s.lat,s.lon,s.track FROM snapshots s
            JOIN (SELECT hex,MAX(ts) m FROM snapshots WHERE lat IS NOT NULL GROUP BY hex) x
            ON s.hex=x.hex AND s.ts=x.m""").fetchall():
            it=meta_by_hex.get((hx or "").upper())
            if it: it.update(lat=lat,lon=lon,track=track or 0)
        con.close()
    except Exception as e: print("aviso DB:",e)
hist=collections.defaultdict(list)
if os.path.exists(MOV):
    for r in csv.DictReader(open(MOV,encoding="utf-8")):
        hist[r.get("matricula","")].append({"inicio":r.get("inicio",""),"fin":r.get("fin",""),"dur":r.get("dur_min",""),
            "origen":r.get("origen",""),"destino":r.get("destino",""),
            "olat":fnum(r.get("origen_lat")),"olon":fnum(r.get("origen_lon")),
            "dlat":fnum(r.get("destino_lat")),"dlon":fnum(r.get("destino_lon"))})
DATA=json.dumps({"aircraft":aircraft,"hist":hist,"hexes":[a["hex"] for a in aircraft if a["hex"]]}, ensure_ascii=False)

MAPCSS="""<style>
 .filters{margin:14px 20px 0;max-width:none}
 .mapwrap{position:relative;margin:14px 20px 18px}
 #map{height:82vh;min-height:560px;border:1px solid var(--bd);border-radius:12px}
 .fp{position:absolute;top:12px;right:12px;width:310px;max-height:calc(82vh - 24px);overflow:auto;
   background:rgba(14,34,56,.97);border:1px solid var(--bd);border-radius:12px;z-index:600;display:none;box-shadow:0 10px 30px #0008}
 .fp .h{padding:11px 14px;border-bottom:1px solid var(--bd);display:flex;justify-content:space-between;align-items:center}
 .fp .h b{font-size:15px} .fp .x{cursor:pointer;color:var(--mut);font-size:18px;line-height:1}
 .fp .meta{padding:10px 14px;font-size:13px;color:var(--mut);border-bottom:1px solid var(--bd)} .fp .meta b{color:var(--txt)}
 .fp .ht{padding:9px 14px 4px;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--mut)}
 .fl{padding:9px 14px;border-top:1px solid var(--bd);cursor:pointer} .fl:hover{background:#12304a}
 .fl.sel{background:#163a59;border-left:3px solid var(--rojo)}
 .fl .r{color:#fff;font-weight:600;font-size:13px} .fl .d{color:var(--mut);font-size:12px;margin-top:2px}
 .tag{display:inline-block;font-size:10px;font-weight:700;padding:1px 7px;border-radius:9px;margin:4px 3px 0 0}
 .t-int{background:rgba(168,85,247,.2);color:#c99bf5}.t-fds{background:rgba(245,158,11,.22);color:#fbd38d}.t-noc{background:rgba(56,189,248,.18);color:#9bdcf7}
 .plane{transition:transform .3s} .plane.fly{filter:drop-shadow(0 0 7px #EF4444);animation:pp 2s infinite}
 @keyframes pp{50%{opacity:.45}} .flow{stroke-dasharray:6 10;animation:flow 1.2s linear infinite}@keyframes flow{to{stroke-dashoffset:-32}}
 .btn{background:var(--azul);color:#04121f;border:none;border-radius:7px;padding:8px 13px;font-size:13px;font-weight:700;cursor:pointer}
 .btn.alt{background:var(--panel2);color:var(--txt);border:1px solid var(--bd);font-weight:400}
</style>"""

BODY="""
<div class="filters">
  <div><label>Mostrar</label><select id="scope"><option value="">Todas las aeronaves</option></select></div>
  <div><label>Aeronave</label><select id="plane"><option value="">— elegí una —</option></select></div>
  <div><label>Historial desde</label><input type="date" id="desde"></div>
  <div><label>Hasta</label><input type="date" id="hasta"></div>
  <button class="btn" id="btnLive">Actualizar en vivo</button>
  <button class="btn alt" id="btnReset">Limpiar</button>
  <span class="info" id="info" style="margin-left:auto"></span>
</div>
<div class="mapwrap">
  <div id="map"></div>
  <div class="fp" id="fp">
    <div class="h"><b id="fp-m"></b><span class="x" id="fp-x">×</span></div>
    <div class="meta" id="fp-meta"></div>
    <div class="ht">Historial de vuelos</div>
    <div id="fp-fl"></div>
  </div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const D=__DATA__; const byReg={}; D.aircraft.forEach(a=>byReg[a.matricula]=a);
const map=L.map('map',{attributionControl:false}).setView([-40,-63],4);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',{maxZoom:11}).addTo(map);
const ley=L.control({position:'bottomleft'});
ley.onAdd=function(){const d=L.DomUtil.create('div');
  d.style.cssText='background:rgba(8,29,48,.9);color:#e8eef5;padding:8px 11px;border-radius:9px;font:12px Arial;line-height:1.5;border:1px solid #1E3A56';
  d.innerHTML='<b>En vivo</b><br><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#EF4444;margin-right:6px"></span>volando ahora<br><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#38BDF8;margin-right:6px"></span>última posición';
  return d;};
ley.addTo(map);
function planeIcon(c,t,f){const s=`<svg class="plane${f?' fly':''}" width="${f?26:20}" height="${f?26:20}" viewBox="0 0 24 24" style="transform:rotate(${t||0}deg);opacity:${f?1:.7}">
 <path d="M12 2 L14 11 L22 15 L22 17 L14 14.5 L13.5 20 L16 21.5 L16 23 L12 22 L8 23 L8 21.5 L10.5 20 L10 14.5 L2 17 L2 15 L10 11 Z" fill="${c}" stroke="#06121f" stroke-width="0.6"/></svg>`;
 return L.divIcon({html:s,className:'',iconSize:[26,26],iconAnchor:[13,13]});}
function bearing(a,b){const r=Math.PI/180,y=Math.sin((b[1]-a[1])*r)*Math.cos(b[0]*r);
 const x=Math.cos(a[0]*r)*Math.sin(b[0]*r)-Math.sin(a[0]*r)*Math.cos(b[0]*r)*Math.cos((b[1]-a[1])*r);return (Math.atan2(y,x)*180/Math.PI+360)%360;}
function arrowIcon(d){const s=`<svg width="20" height="20" viewBox="0 0 24 24" style="transform:rotate(${d}deg)"><path d="M12 3 L19 18 L12 14 L5 18 Z" fill="#7e93a8" stroke="#06121f" stroke-width="0.8"/></svg>`;
 return L.divIcon({html:s,className:'',iconSize:[20,20],iconAnchor:[10,10]});}
let markers={},routeLayers=[],SCOPE="",curReg=null;
function inScope(a){if(!SCOPE)return true;if(SCOPE==="G:privado")return a.grupo==="privado";
 if(SCOPE.startsWith("P:"))return a.grupo!=="privado"&&a.provincia===SCOPE.slice(2);return true;}
function draw(){Object.values(markers).forEach(m=>map.removeLayer(m));markers={};
 D.aircraft.forEach(a=>{if(a.lat==null||!inScope(a))return;const col=a.flying?'#EF4444':'#38BDF8';
  const m=L.marker([a.lat,a.lon],{icon:planeIcon(col,a.track,a.flying),zIndexOffset:a.flying?1000:0}).addTo(map);
  m.on('click',()=>selectAircraft(a.matricula,true));
  m.bindTooltip(`<b>${a.matricula}</b> · ${a.provincia}<br>${a.tipo}<br>${a.flying?'<b style="color:#EF4444">EN VUELO</b>':'en tierra (últ. posición)'}`,{direction:'top',offset:[0,-8]});
  markers[a.matricula]=m;});}
function clearRoute(){routeLayers.forEach(l=>map.removeLayer(l));routeLayers=[];}
function drawRoute(o,d){const ln=L.polyline([o,d],{color:'#7e93a8',weight:3,opacity:.9}).addTo(map);routeLayers.push(ln);
 const b=bearing(o,d);[0.3,0.55,0.8].forEach(fr=>routeLayers.push(L.marker([o[0]+(d[0]-o[0])*fr,o[1]+(d[1]-o[1])*fr],{icon:arrowIcon(b),interactive:false}).addTo(map)));
 routeLayers.push(L.circleMarker(o,{radius:4,color:'#22C55E',fillColor:'#22C55E',fillOpacity:1}).addTo(map).bindTooltip('Origen'));
 routeLayers.push(L.circleMarker(d,{radius:4,color:'#EF4444',fillColor:'#EF4444',fillOpacity:1}).addTo(map).bindTooltip('Destino'));
 map.fitBounds(ln.getBounds(),{padding:[60,60]});}
function fillScope(){const s=document.getElementById('scope');
 [...new Set(D.aircraft.filter(a=>a.grupo!=='privado'&&a.provincia).map(a=>a.provincia))].sort()
   .forEach(p=>{const o=document.createElement('option');o.value='P:'+p;o.textContent='Provincia: '+p;s.appendChild(o);});
 if(D.aircraft.some(a=>a.grupo==='privado')){const o=document.createElement('option');o.value='G:privado';o.textContent='Privadas / rentadas';s.appendChild(o);}}
function fillPlanes(){const sel=document.getElementById('plane');sel.innerHTML='<option value="">— elegí una —</option>';
 D.aircraft.filter(a=>a.matricula&&inScope(a)).sort((x,y)=>x.provincia.localeCompare(y.provincia)||x.matricula.localeCompare(y.matricula))
  .forEach(a=>{const o=document.createElement('option');o.value=a.matricula;o.textContent=`${a.matricula} — ${a.provincia}`;sel.appendChild(o);});}
function dr(){return [document.getElementById('desde').value,document.getElementById('hasta').value];}
function enforceYear(){let[a,b]=dr();if(!a||!b)return;const da=new Date(a),db=new Date(b);
 if(db<da){document.getElementById('desde').value=b;return;}
 if((db-da)/86400000>366){const na=new Date(db);na.setFullYear(na.getFullYear()-1);
  document.getElementById('desde').value=na.toISOString().slice(0,10);alert('El historial admite como máximo 1 año. Ajusté la fecha "desde".');}}
function flags(f){const out=[];const d=new Date((f.inicio||'').replace(' ','T'));
 if(!isNaN(d)){const w=d.getDay();if(w===0||w===6)out.push(['t-fds','fin de semana']);const h=d.getHours();if(h>=22||h<6)out.push(['t-noc','nocturno']);}
 return out;}
function showFlights(reg){const box=document.getElementById('fp-fl');box.innerHTML='';
 const[a,b]=dr();let hs=(D.hist[reg]||[]);if(a)hs=hs.filter(f=>(f.inicio||'').slice(0,10)>=a);if(b)hs=hs.filter(f=>(f.inicio||'').slice(0,10)<=b);
 if(!hs.length){box.innerHTML='<div class="fl d" style="color:var(--mut)">Sin vuelos en el período.</div>';return;}
 hs.forEach(f=>{const el=document.createElement('div');el.className='fl';
  const tg=flags(f).map(([c,t])=>`<span class="tag ${c}">${t}</span>`).join('');
  el.innerHTML=`<div class="r">${f.origen} → ${f.destino}</div><div class="d">${f.inicio} · ${f.dur} min</div>${tg}`;
  el.onclick=()=>{document.querySelectorAll('.fl').forEach(x=>x.classList.remove('sel'));el.classList.add('sel');clearRoute();if(f.olat&&f.dlat)drawRoute([f.olat,f.olon],[f.dlat,f.dlon]);};
  box.appendChild(el);});}
function selectAircraft(reg,fromMap){const a=byReg[reg];if(!a)return;curReg=reg;
 document.getElementById('plane').value=reg;
 document.getElementById('fp-m').textContent=a.matricula;
 document.getElementById('fp-meta').innerHTML=`<span class="tag" style="background:#12304a;color:#cfe0f0">${a.grupo==='privado'?'privada/rentada':'provincial'}</span><br>${a.grupo==='privado'?'Ámbito':'Provincia'}: <b>${a.provincia}</b><br>Tipo: <b>${a.tipo}</b><br>Hex: ${a.hex||'—'}`;
 showFlights(reg);clearRoute();document.getElementById('fp').style.display='block';
 if(a.lat!=null){if(!fromMap)map.setView([a.lat,a.lon],7);if(markers[reg])markers[reg].openTooltip();}}
function fitScope(){const pts=D.aircraft.filter(a=>a.lat!=null&&inScope(a)).map(a=>[a.lat,a.lon]);if(pts.length)map.fitBounds(pts,{padding:[40,40]});else map.setView([-40,-63],4);}
function closePanel(){document.getElementById('fp').style.display='none';clearRoute();curReg=null;document.getElementById('plane').value='';}
function resetView(){closePanel();SCOPE='';document.getElementById('scope').value='';fillPlanes();draw();fitScope();
 document.getElementById('info').textContent='';}
document.getElementById('fp-x').onclick=closePanel;
document.getElementById('scope').onchange=e=>{SCOPE=e.target.value;closePanel();fillPlanes();draw();fitScope();
 document.getElementById('info').textContent=D.aircraft.filter(a=>inScope(a)&&a.lat!=null).length+' en el mapa';};
document.getElementById('plane').onchange=e=>{if(e.target.value)selectAircraft(e.target.value);else closePanel();};
document.getElementById('btnReset').onclick=resetView;
['desde','hasta'].forEach(id=>document.getElementById(id).onchange=()=>{enforceYear();if(curReg)showFlights(curReg);});
async function live(){const btn=document.getElementById('btnLive');btn.textContent='Consultando…';let ok=0;
 try{for(let i=0;i<D.hexes.length;i+=100){const res=await fetch('https://api.airplanes.live/v2/hex/'+D.hexes.slice(i,i+100).join(','));
  const j=await res.json();(j.ac||[]).forEach(ac=>{const hx=(ac.hex||'').toUpperCase();const a=D.aircraft.find(x=>x.hex===hx);
   if(a&&ac.lat!=null){a.lat=ac.lat;a.lon=ac.lon;a.track=ac.track||0;a.flying=true;ok++;}});}
  draw();btn.textContent=`En vivo: ${ok} volando`;}catch(e){btn.textContent='Sin conexión · reintentar';}}
document.getElementById('btnLive').onclick=live;
(function(){const h=new Date(),d=new Date();d.setFullYear(d.getFullYear()-1);
 document.getElementById('hasta').value=h.toISOString().slice(0,10);document.getElementById('desde').value=d.toISOString().slice(0,10);})();
fillScope();fillPlanes();draw();fitScope();
</script></body></html>"""

HTML=("<!doctype html><html lang=es><head><meta charset=utf-8>"
 "<meta name=viewport content='width=device-width, initial-scale=1'>"
 "<title>Mapa en vivo — Observatorio Aeronáutico</title>"
 "<link rel='stylesheet' href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'/>"
 +THEME+MAPCSS+"</head><body>"+top("mapa_vivo.html")+BODY)
open(OUT,"w",encoding="utf-8").write(HTML.replace("__DATA__",DATA))
print(f"Mapa: mapa_vivo.html | aeronaves {len(aircraft)} | con posición {sum(1 for a in aircraft if a['lat'] is not None)} | hex {len([a for a in aircraft if a['hex']])}")
