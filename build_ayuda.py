# -*- coding: utf-8 -*-
"""Genera ayuda.html (Metodología) con el tema oscuro compartido."""
import os
from site_theme import THEME, top
BASE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(BASE,"ayuda.html")

FAQ=[
 ("Qué es este sitio",
  "Este sitio registra movimientos de aeronaves vinculadas a gobiernos provinciales argentinos. "
  "Usa datos públicos de seguimiento aéreo y los organiza para consulta periodística."),
 ("Fuentes",
  "Las posiciones provienen de redes ADS-B públicas. La identificación de aeronaves se cruza con "
  "matrículas, registros aeronáuticos y fuentes abiertas."),
 ("Limitaciones",
  "Un vuelo puede no aparecer si el transponder está apagado, si no hay cobertura ADS-B o si la señal "
  "no fue detectada. Por eso los datos deben leerse como indicios, no como conclusiones."),
 ("Alertas",
  "Las alertas marcan patrones que pueden requerir revisión: vuelos nocturnos, internacionales, de fin "
  "de semana o coincidencias entre varias aeronaves."),
 ("Criterio editorial",
  "El sistema ordena datos públicos. No afirma irregularidades ni responsabilidades."),
]

cards="".join(f'<div class="panel"><div class="ph">{t}</div><div class="pb" style="font-size:14px;line-height:1.6">{c}</div></div>' for t,c in FAQ)

HTML=("<!doctype html><html lang=es><head><meta charset=utf-8>"
 "<meta name=viewport content='width=device-width, initial-scale=1'>"
 "<title>Metodología — Observatorio Aeronáutico</title>"+THEME+"</head><body>"
 +top("ayuda.html")+
 "<div class=wrap><h1 class=htitle>Metodología</h1>"
 "<p class=hsub>Cómo se recopilan, procesan y presentan los datos.</p>"
 +cards+
 "</div></body></html>")
open(OUT,"w",encoding="utf-8").write(HTML)
print("ayuda.html (Metodología) OK")
