# -*- coding: utf-8 -*-
"""
Genera index.html: dashboard tipo CENTRO DE MONITOREO (oscuro premium).
- Mapa con TODAS las aeronaves del padrón: en vuelo (rojo pulsante con glow) o en tierra
  (azul tenue, ubicadas en su provincia). Aeropuertos principales, rutas recientes tenues
  y efecto radar sobre Argentina.
- Cabecera de impacto + KPIs con mini-tendencias + gráfico grande con glow.
- Ticker de actividad reciente (despegues/aterrizajes/encuentros).
Datos: padron + vuelos.db + movimientos.csv. "Volando ahora" en vivo (airplanes.live).
Uso: python3 build_index.py
"""
import csv, json, os, sqlite3, datetime, collections

BASE=os.path.dirname(os.path.abspath(__file__))
DB=os.environ.get("PADRON_DB", os.path.join(BASE,"vuelos.db"))
MOV=os.path.join(BASE,"movimientos.csv")
OUT=os.path.join(BASE,"index.html")
DATASETS=[("padron_aeronaves.csv","provincial"),("charters_dirigentes.csv","privado")]

# capitales provinciales (fallback para ubicar aeronaves en tierra)
CAP={"Buenos Aires":[-34.92,-57.95],"CABA":[-34.60,-58.38],"Catamarca":[-28.47,-65.78],
"Chaco":[-27.45,-58.99],"Chubut":[-43.30,-65.10],"Córdoba":[-31.42,-64.18],
"Corrientes":[-27.47,-58.83],"Entre Ríos":[-31.73,-60.52],"Formosa":[-26.18,-58.17],
"Jujuy":[-24.19,-65.30],"La Pampa":[-36.62,-64.29],"La Rioja":[-29.41,-66.85],
"Mendoza":[-32.89,-68.84],"Misiones":[-27.37,-55.90],"Neuquén":[-38.95,-68.06],
"Río Negro":[-40.81,-63.00],"Salta":[-24.79,-65.41],"San Juan":[-31.54,-68.54],
"San Luis":[-33.30,-66.34],"Santa Cruz":[-51.62,-69.22],"Santa Fe":[-31.63,-60.70],
"Santiago del Estero":[-27.78,-64.26],"Tierra del Fuego":[-54.81,-68.31],
"Tucumán":[-26.82,-65.22]}
AEROP=[["AEP",-34.5594,-58.4155],["EZE",-34.8222,-58.5358],["COR",-31.31,-64.21],
["MDZ",-32.83,-68.79],["SLA",-24.86,-65.49],["BRC",-41.15,-71.16],["SDE",-27.77,-64.31],
["RES",-27.45,-59.06],["IGR",-25.74,-54.47],["FTE",-50.28,-72.05],["TUC",-26.84,-65.10],
["NQN",-38.95,-68.16],["PSS",-27.39,-55.97],["BHI",-38.72,-62.16]]

def fnum(x):
    try: return float(x)
    except: return None

aircraft, meta_by_hex=[],{}
for fname,grupo in DATASETS:
    p=os.path.join(BASE,fname)
    if not os.path.exists(p): continue
    for i,r in enumerate(csv.DictReader(open(p,encoding="utf-8"))):
        hx=(r.get("hex") or "").strip().upper()
        grp="privado" if (grupo=="privado" or "charter" in (r.get("organismo","").lower())) else "provincial"
        prov=r.get("provincia","")
        base=CAP.get(prov, CAP["CABA"])
        # jitter determinístico para separar aeronaves de la misma provincia
        jx=((i%5)-2)*0.13; jy=(((i//5)%5)-2)*0.13
        it={"matricula":r.get("matricula",""),"hex":hx,"grupo":grp,"provincia":prov,
            "tipo":r.get("tipo",""),"lat":base[0]+jx,"lon":base[1]+jy,"track":0,
            "flying":False,"ground":True}
        aircraft.append(it)
        if hx: meta_by_hex[hx]=it

# última posición conocida (reemplaza el fallback)
if os.path.exists(DB):
    try:
        con=sqlite3.connect(DB)
        for hx,lat,lon,track in con.execute("""SELECT s.hex,s.lat,s.lon,s.track FROM snapshots s
            JOIN (SELECT hex,MAX(ts) m FROM snapshots WHERE lat IS NOT NULL GROUP BY hex) x
            ON s.hex=x.hex AND s.ts=x.m""").fetchall():
            it=meta_by_hex.get((hx or "").upper())
            if it: it.update(lat=lat,lon=lon,track=track or 0,ground=False)
        con.close()
    except Exception as e: print("aviso DB:",e)

flights, routes=[],[]
if os.path.exists(MOV):
    for r in csv.DictReader(open(MOV,encoding="utf-8")):
        flights.append({"matricula":r.get("matricula",""),"provincia":r.get("provincia",""),
                        "inicio":r.get("inicio",""),"fin":r.get("fin",""),
                        "origen":r.get("origen",""),"destino":r.get("destino",""),
                        "dcode":r.get("destino_code","")})
        o=(fnum(r.get("origen_lat")),fnum(r.get("origen_lon")))
        d=(fnum(r.get("destino_lat")),fnum(r.get("destino_lon")))
        if None not in o and None not in d: routes.append({"o":[o[0],o[1]],"d":[d[0],d[1]],"t":r.get("inicio","")})
routes=sorted(routes,key=lambda x:x["t"],reverse=True)[:16]

# ticker de actividad (eventos recientes)
def corto(lbl): return lbl.split(" (")[0] if lbl else lbl
ev=[]
for f in flights:
    if f["fin"]: ev.append((f["fin"], f'{f["fin"][11:16]}  {f["matricula"]} aterrizó en {corto(f["destino"])}'))
    if f["inicio"]: ev.append((f["inicio"], f'{f["inicio"][11:16]}  {f["matricula"]} despegó de {corto(f["origen"])}'))
g=collections.defaultdict(lambda:{"a":set(),"lbl":"","f":""})
for f in flights:
    fch=(f["fin"] or f["inicio"] or "")[:10]; dst=f["destino"]
    if not fch or not dst or "sin aeropuerto" in dst: continue
    k=(fch,dst); g[k]["a"].add(f["matricula"]); g[k]["lbl"]=dst; g[k]["f"]=fch
for (fch,dst),x in g.items():
    if len(x["a"])>=3: ev.append((fch+" 23:59", f'Coincidencia · {len(x["a"])} aeronaves en {corto(dst)} · {fch}'))
ev=[t for _,t in sorted(ev,key=lambda e:e[0],reverse=True)[:20]]

prov_count=len({a["provincia"] for a in aircraft if a["grupo"]!="privado" and a["provincia"]})
DATA=json.dumps({"aircraft":aircraft,"hexes":[a["hex"] for a in aircraft if a["hex"]],
                 "registradas":len(aircraft),"provincias":prov_count,
                 "flights":flights,"routes":routes,"airports":AEROP,"eventos":ev}, ensure_ascii=False)

HTML=r"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Observatorio de Aeronaves Oficiales — Argentina</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
 :root{--bg:#071827;--panel:#0E2238;--azul:#38BDF8;--fly:#ff4d4d;--alert:#fbbf24;--ext:#a855f7;--enc:#fb7185;--verde:#22C55E;--txt:#e6f0fb;--mut:#7e98b4;--line:#173049}
 *{box-sizing:border-box}
 body{margin:0;background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,Arial,sans-serif;position:relative;min-height:100vh}
 body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
   background:radial-gradient(circle at 50% 0%,rgba(56,189,248,.12),transparent 42%),
     linear-gradient(rgba(255,255,255,.015) 1px,transparent 1px),
     linear-gradient(90deg,rgba(255,255,255,.015) 1px,transparent 1px);
   background-size:100% 100%,40px 40px,40px 40px}
 .top,.wrap{position:relative;z-index:1}
 a{color:var(--azul);text-decoration:none}
 .top{display:flex;align-items:center;justify-content:space-between;padding:14px 24px;border-bottom:1px solid var(--line)}
 .brand{display:flex;align-items:center;gap:12px}
 .brand .logo{width:36px;height:36px;border-radius:9px;background:radial-gradient(circle at 30% 30%,#38BDF8,#0b6aa3);display:flex;align-items:center;justify-content:center;font-size:19px;box-shadow:0 0 22px #38bdf855}
 .brand h1{font-size:15px;margin:0;letter-spacing:2px;font-weight:800}
 .brand small{display:block;font-size:10px;color:var(--mut);letter-spacing:2px}
 .nav a{font-size:13px;margin-left:18px;color:#bcd3ec} .nav a:hover{color:#fff}
 .live{display:inline-flex;align-items:center;font-size:11px;color:var(--verde);font-weight:700;letter-spacing:1px;margin-right:12px}
 .live i{width:9px;height:9px;border-radius:50%;background:var(--verde);margin-right:6px;animation:glow 1.6s infinite}
 @keyframes glow{0%,100%{box-shadow:0 0 4px var(--verde);opacity:1}50%{box-shadow:0 0 14px var(--verde);opacity:.55}}
 .wrap{padding:12px 16px;max-width:1680px;margin:0 auto}
 .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:0 0 12px}
 @media(max-width:900px){.kpis{grid-template-columns:repeat(2,1fr)}}
 .kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:8px 14px;position:relative;overflow:hidden;transition:.15s;display:flex;align-items:baseline;gap:10px}
 .kpi:hover{border-color:#2a567f}
 .kpi .lab{font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;color:var(--mut);flex:1;order:2}
 .kpi .val{font-size:26px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums;order:1}
 .kpi .tr{display:none} .kpi .bar{position:absolute;left:0;top:0;bottom:0;width:3px}
 .k1 .val{color:var(--azul)} .k1 .bar{background:var(--azul)}
 .k2 .val{color:var(--fly)} .k2 .bar{background:var(--fly)} .k2{box-shadow:inset 0 0 30px rgba(255,77,77,.06)}
 .k3 .val{color:var(--verde)} .k3 .bar{background:var(--verde)}
 .k4 .val{color:var(--alert)} .k4 .bar{background:var(--alert)}
 .grid{display:grid;grid-template-columns:2.2fr 1fr;gap:16px}@media(max-width:1000px){.grid{grid-template-columns:1fr}}
 .card{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}
 .card h3{font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:var(--mut);margin:0;padding:13px 16px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between}
 #map{height:74vh;min-height:540px} .card.map{padding:0;position:relative}
 .chartbox{padding:12px 14px}
 .ticker{max-height:250px;overflow:hidden}
 .ev{padding:9px 16px;border-bottom:1px solid var(--line);font-size:12.5px;font-family:'Consolas',monospace;color:#bcd3ec;white-space:nowrap;animation:fadein .5s}
 .ev.al{color:var(--alert)} @keyframes fadein{from{opacity:0;transform:translateY(-6px)}to{opacity:1}}
 .links{display:flex;flex-direction:column}
 .links a{padding:13px 16px;border-bottom:1px solid var(--line);display:flex;gap:11px;color:var(--txt);transition:.15s}
 .links a:hover{background:#12304a;padding-left:20px} .links a small{display:block;color:var(--mut);font-size:12px}
 .leaflet-tooltip{font-size:12px} .leaflet-container{background:#06121f}
 .pulse{filter:drop-shadow(0 0 7px #ff4d4d);animation:pp 2s infinite} @keyframes pp{50%{opacity:.45}}
 .flow{stroke-dasharray:6 10;animation:flow 1.2s linear infinite} @keyframes flow{to{stroke-dashoffset:-32}}
 .foot{color:var(--mut);font-size:12px;margin-top:16px;text-align:center}
</style></head><body>
<div class="top">
  <div class="brand"><div class="logo"><svg width="19" height="19" viewBox="0 0 24 24"><path d="M12 2 L14 11 L22 15 L22 17 L14 14.5 L13.5 20 L16 21.5 L16 23 L12 22 L8 23 L8 21.5 L10.5 20 L10 14.5 L2 17 L2 15 L10 11 Z" fill="#04121f"/></svg></div>
   <div><h1>OBSERVATORIO AERONÁUTICO</h1><small>AERONAVES OFICIALES · ARGENTINA</small></div></div>
  <div class="nav"><span class="live"><i></i>EN VIVO</span><span id="clock" style="font-size:12px;color:var(--mut)"></span>
   <a href="mapa_vivo.html">Mapa en vivo</a><a href="reporte_movimientos.html">Reporte histórico</a>
   <a href="estadisticas.html">Estadísticas y alertas</a><a href="ayuda.html">Metodología</a></div>
</div>
<div class="wrap">
 <div class="kpis">
  <div class="kpi k1"><div class="bar"></div><div class="val" id="k-reg">0</div><div class="lab">Aeronaves registradas</div></div>
  <div class="kpi k2"><div class="bar"></div><div class="val" id="k-fly">—</div><div class="lab">Volando ahora</div></div>
  <div class="kpi k3"><div class="bar"></div><div class="val" id="k-mov">0</div><div class="lab">Movimientos · 12 meses</div></div>
  <div class="kpi k4"><div class="bar"></div><div class="val" id="k-al">0</div><div class="lab">Alertas 3+ · 30 días</div></div>
 </div>
 <div class="grid">
  <div class="card map"><h3>Monitoreo en tiempo real <span style="color:var(--mut)">Argentina</span></h3>
    <div id="map"></div></div>
  <div style="display:flex;flex-direction:column;gap:16px">
   <div class="card"><h3>Actividad — últimos 30 días</h3><div class="chartbox"><canvas id="chart" height="110"></canvas></div></div>
   <div class="card"><h3>Actividad reciente</h3><div class="ticker" id="ticker"></div></div>
   <div class="card"><h3>Secciones</h3><div class="links">
     <a href="mapa_vivo.html"><div>Mapa en vivo<small>Rastreo en tiempo real</small></div></a>
     <a href="estadisticas.html"><div>Estadísticas y alertas<small>Coincidencias, rankings y patrones</small></div></a>
     <a href="reporte_movimientos.html"><div>Reporte histórico<small>Todos los vuelos detectados</small></div></a>
     <a href="ayuda.html"><div>Metodología<small>Fuentes y criterios</small></div></a>
   </div></div>
  </div>
 </div>
 <div class="foot">Datos públicos ADS-B · airplanes.live · hexdb.io · OurAirports — Las alertas son indicios para investigar.</div>
</div>
<script>
const D=__DATA__;
document.getElementById('k-reg').textContent=D.registradas;
function tick(){document.getElementById('clock').textContent=new Date().toLocaleString('es-AR');}
tick();setInterval(tick,1000);
// movimientos (12m) y alertas (30d) — cliente
const today=new Date(); const lim12=new Date(today); lim12.setFullYear(today.getFullYear()-1);
const lim30=new Date(today); lim30.setDate(today.getDate()-30);
const mov12=D.flights.filter(f=>{const d=new Date((f.inicio||'').slice(0,10)+'T12:00');return !isNaN(d)&&d>=lim12;}).length;
document.getElementById('k-mov').textContent=mov12.toLocaleString('es-AR');
const g={};
D.flights.forEach(f=>{const fch=(f.fin||f.inicio||'').slice(0,10),dst=f.destino;
  if(!fch||!dst||dst.indexOf('sin aeropuerto')>=0)return;const k=fch+'|'+dst;(g[k]=g[k]||{a:new Set(),f:fch});g[k].a.add(f.matricula);});
const al30=Object.values(g).filter(x=>x.a.size>=3 && new Date(x.f+'T12:00')>=lim30).length;
document.getElementById('k-al').textContent=al30;
// mapa
const map=L.map('map',{zoomControl:true,attributionControl:false}).setView([-40,-63],4);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',{maxZoom:11}).addTo(map);
// aeropuertos
D.airports.forEach(a=>L.circleMarker([a[1],a[2]],{radius:2.5,color:'#3a5e80',fillColor:'#3a5e80',fillOpacity:.9})
  .addTo(map).bindTooltip(a[0],{direction:'top'}));
// rutas recientes tenues con travelling
D.routes.forEach(r=>L.polyline([r.o,r.d],{color:'#38BDF8',weight:1.5,opacity:.35,className:'flow'}).addTo(map));
function icon(col,track,flying){const svg=`<svg class="${flying?'pulse':''}" width="${flying?24:18}" height="${flying?24:18}" viewBox="0 0 24 24" style="transform:rotate(${track||0}deg);opacity:${flying?1:.55}">
  <path d="M12 2 L14 11 L22 15 L22 17 L14 14.5 L13.5 20 L16 21.5 L16 23 L12 22 L8 23 L8 21.5 L10.5 20 L10 14.5 L2 17 L2 15 L10 11 Z" fill="${col}" stroke="#06121f" stroke-width="0.6"/></svg>`;
  return L.divIcon({html:svg,className:'',iconSize:[24,24],iconAnchor:[12,12]});}
let markers=[];
function drawA(){ markers.forEach(m=>map.removeLayer(m));markers=[];
  D.aircraft.forEach(a=>{ if(a.lat==null)return; const col=a.flying?'#ff4d4d':'#38BDF8';
    const m=L.marker([a.lat,a.lon],{icon:icon(col,a.track,a.flying),zIndexOffset:a.flying?1000:0}).addTo(map);
    m.bindTooltip(`<b>${a.matricula}</b> · ${a.provincia}<br>${a.tipo}<br>${a.flying?'<b style="color:#ff4d4d">EN VUELO</b>':'en tierra (últ. posición)'}`,{direction:'top',offset:[0,-8]});
    markers.push(m);});}
drawA();
// gráfico 30 días con glow
const days=[],counts=[];
for(let i=29;i>=0;i--){const d=new Date();d.setDate(d.getDate()-i);const k=d.toISOString().slice(0,10);
  days.push(k.slice(5));counts.push(D.flights.filter(f=>(f.inicio||'').slice(0,10)===k).length);}
const glow={id:'glow',beforeDatasetsDraw(c){const x=c.ctx;x.save();x.shadowColor='rgba(34,197,94,.7)';x.shadowBlur=12;},
  afterDatasetsDraw(c){c.ctx.restore();}};
new Chart(document.getElementById('chart'),{type:'line',plugins:[glow],
  data:{labels:days,datasets:[{data:counts,borderColor:'#22C55E',backgroundColor:'rgba(34,197,94,.18)',fill:true,tension:.4,borderWidth:2.5,
    pointRadius:days.map((_,i)=>i===days.length-1?4:0),pointBackgroundColor:'#22C55E'}]},
  options:{plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#7e98b4',maxTicksLimit:7,font:{size:10}},grid:{display:false}},
    y:{beginAtZero:true,ticks:{color:'#7e98b4',precision:0},grid:{color:'#12283f'}}}}});
// ticker animado
const tk=document.getElementById('ticker'); let ei=0;
function renderTicker(){ tk.innerHTML='';
  for(let i=0;i<8;i++){const t=D.eventos[(ei+i)%D.eventos.length]; if(!t)break;
    const d=document.createElement('div');d.className='ev'+(t.indexOf('Coincidencia')>=0?' al':'');d.textContent=t;tk.appendChild(d);} }
if(D.eventos.length){renderTicker(); setInterval(()=>{ei=(ei+1)%D.eventos.length;renderTicker();},2600);}
else tk.innerHTML='<div class="ev">Sin actividad registrada todavía.</div>';
// volando ahora (live)
async function live(){let ok=0;
  try{for(let i=0;i<D.hexes.length;i+=100){
    const res=await fetch('https://api.airplanes.live/v2/hex/'+D.hexes.slice(i,i+100).join(','));
    const j=await res.json();(j.ac||[]).forEach(ac=>{const hx=(ac.hex||'').toUpperCase();const a=D.aircraft.find(x=>x.hex===hx);
      if(a&&ac.lat!=null){a.lat=ac.lat;a.lon=ac.lon;a.track=ac.track||0;a.flying=true;ok++;}});}
    document.getElementById('k-fly').textContent=ok;drawA();
  }catch(e){document.getElementById('k-fly').textContent='s/d';}}
live(); setInterval(live,60000);
</script></body></html>"""

open(OUT,"w",encoding="utf-8").write(HTML.replace("__DATA__",DATA))
print(f"Portada: index.html | aeronaves {len(aircraft)} | en mapa {sum(1 for a in aircraft if a['lat'] is not None)} | rutas {len(routes)} | eventos {len(ev)}")
