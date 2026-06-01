# -*- coding: utf-8 -*-
"""Estilo visual compartido por todas las páginas (tema oscuro del observatorio)."""

THEME = """<style>
 :root{--bg:#071827;--panel:#0E2238;--panel2:#102A43;--bd:#1E3A56;--txt:#F8FAFC;--mut:#94A3B8;
   --azul:#38BDF8;--verde:#22C55E;--rojo:#EF4444;--amar:#F59E0B}
 *{box-sizing:border-box}
 body{margin:0;background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,Arial,sans-serif;
   background-image:radial-gradient(circle at 50% -5%,rgba(56,189,248,.07),transparent 45%)}
 a{color:var(--azul);text-decoration:none}
 .top{display:flex;align-items:center;justify-content:space-between;padding:11px 20px;border-bottom:1px solid var(--bd);
   background:#081d30;position:sticky;top:0;z-index:1000}
 .brand{display:flex;align-items:center;gap:11px}
 .brand .logo{width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,#38BDF8,#0b6aa3);
   display:flex;align-items:center;justify-content:center;box-shadow:0 0 16px #38bdf844}
 .brand b{font-size:14px;letter-spacing:1.5px;display:block} .brand small{font-size:9.5px;color:var(--mut);letter-spacing:2px}
 .nav a{font-size:13px;margin-left:15px;color:#bcd3ec} .nav a:hover{color:#fff}
 .nav a.act{color:#fff;border-bottom:2px solid var(--azul);padding-bottom:4px}
 .wrap{max-width:1280px;margin:0 auto;padding:18px 20px}
 .htitle{font-size:21px;font-weight:800;margin:0;letter-spacing:.3px}
 .hsub{color:var(--mut);font-size:13px;margin:4px 0 16px}
 .panel{background:var(--panel);border:1px solid var(--bd);border-radius:12px;overflow:hidden;margin-bottom:16px}
 .ph{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--mut);padding:11px 14px;border-bottom:1px solid var(--bd)}
 .pb{padding:14px}
 .filters{display:flex;gap:14px;align-items:flex-end;flex-wrap:wrap;background:var(--panel);border:1px solid var(--bd);
   border-radius:12px;padding:12px 14px;margin-bottom:16px}
 .filters label{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--mut);display:block;margin-bottom:4px}
 .filters select,.filters input{background:var(--panel2);border:1px solid var(--bd);color:var(--txt);border-radius:7px;
   padding:7px 9px;font-size:13px;min-width:175px}
 .seg{display:flex;border:1px solid var(--bd);border-radius:7px;overflow:hidden}
 .seg button{background:var(--panel2);border:none;color:var(--mut);padding:7px 13px;cursor:pointer;font-size:13px;border-right:1px solid var(--bd)}
 .seg button:last-child{border-right:none} .seg button.act{background:var(--azul);color:#04121f;font-weight:700}
 .info{color:var(--mut);font-size:12px}
 .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}
 @media(max-width:760px){.kpis{grid-template-columns:repeat(2,1fr)}}
 .kpi{background:var(--panel);border:1px solid var(--bd);border-radius:10px;padding:10px 14px;position:relative;overflow:hidden}
 .kpi .v{font-size:25px;font-weight:800;line-height:1} .kpi .l{font-size:10.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.08em;margin-top:3px}
 .kpi .bar{position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--azul)}
 .kpi.fly .v{color:var(--rojo)} .kpi.fly .bar{background:var(--rojo)}
 .kpi.amar .v{color:var(--amar)} .kpi.amar .bar{background:var(--amar)}
 .kpi.verde .v{color:var(--verde)} .kpi.verde .bar{background:var(--verde)}
 .two{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:820px){.two{grid-template-columns:1fr}}
 table{border-collapse:collapse;width:100%;font-size:13px}
 th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--bd)}
 th{background:var(--panel2);color:#cfe0f0;font-size:11px;text-transform:uppercase;letter-spacing:.05em;position:sticky;top:0}
 tbody tr:nth-child(even){background:#0c2034}
 tr.al td{color:var(--amar);font-weight:600}
 .badge{display:inline-block;font-size:10.5px;font-weight:700;padding:1px 8px;border-radius:20px;margin:2px 3px 0 0}
 .b-int{background:rgba(168,85,247,.18);color:#c99bf5}.b-fds{background:rgba(245,158,11,.2);color:#fbd38d}
 .b-noc{background:rgba(56,189,248,.16);color:#9bdcf7}.b-pri{background:rgba(239,68,68,.18);color:#f5a3a3}
 .pill{display:inline-block;background:rgba(245,158,11,.2);color:#fbd38d;font-weight:700;font-size:10.5px;padding:1px 8px;border-radius:20px}
 .scroll{max-height:420px;overflow:auto}
 #map{height:440px} .leaflet-container{background:#06121f} .leaflet-tooltip{font-size:12px}
 .note{color:var(--mut);font-size:12px;margin-top:8px} .muted{color:var(--mut);font-size:12px}
 canvas{max-height:300px}
</style>"""

_LOGO = ('<svg width="17" height="17" viewBox="0 0 24 24"><path d="M12 2 L14 11 L22 15 L22 17 L14 14.5 '
         'L13.5 20 L16 21.5 L16 23 L12 22 L8 23 L8 21.5 L10.5 20 L10 14.5 L2 17 L2 15 L10 11 Z" fill="#04121f"/></svg>')

_NAV = [("index.html","Inicio"),("mapa_vivo.html","Mapa en vivo"),
        ("reporte_movimientos.html","Reporte histórico"),
        ("estadisticas.html","Estadísticas y alertas"),("ayuda.html","Metodología")]

def top(active=""):
    links = "".join(f'<a href="{h}" class="{"act" if h==active else ""}">{t}</a>' for h,t in _NAV)
    return ('<div class="top"><div class="brand"><div class="logo">'+_LOGO+'</div>'
            '<div><b>OBSERVATORIO AERONÁUTICO</b><small>AERONAVES OFICIALES · ARGENTINA</small></div></div>'
            f'<div class="nav">{links}</div></div>')
