# -*- coding: utf-8 -*-
# Padrón de aeronaves de gobiernos provinciales argentinos.
# Campos: provincia, organismo, matricula, tipo, categoria, estado, confianza, fuente, notas
# confianza: ALTA (matrícula confirmada en fuente reciente), MEDIA (tipo confirmado, matrícula a verificar),
#            BAJA (dato histórico 2007/2015, requiere verificación actual)

SEED = [
 # --- Buenos Aires ---
 ["Buenos Aires","Dirección de Aeronáutica (DAO)","LV-WNS","MBB/Kawasaki BK-117 C-1","helicóptero","",
  "MEDIA","Zona Militar","Helicóptero sanitario/seguridad DAO"],
 ["Buenos Aires","Dirección de Aeronáutica (DAO)","LV-WRW","MBB/Kawasaki BK-117 C-1","helicóptero","",
  "MEDIA","Zona Militar","Helicóptero DAO"],
 ["Buenos Aires","Dirección de Aeronáutica (DAO)","LV-YBT","Eurocopter EC-135 T1","helicóptero","",
  "MEDIA","Zona Militar","Helicóptero DAO"],
 ["Buenos Aires","Dirección de Aeronáutica (DAO)","LV-WEJ","Cessna 550 Citation II","avión","activo",
  "ALTA","Airliners.net (álbum)","S/N 550-0724. Jet oficial DAO"],
 ["Buenos Aires","Ministerio de Salud de la Provincia","LQ-APX","MBB BO-105 CBS","helicóptero","activo",
  "ALTA","Airliners.net (álbum)","S/N S-558. Helicóptero sanitario"],
 ["Buenos Aires","Dir. Prov. de Aeronavegación Oficial y Planif. Aeroportuaria","LV-WMI","Cessna 208B Grand Caravan","avión","activo",
  "ALTA","aporte usuario (video)","Misiones oficiales y traslados sanitarios"],
 ["Buenos Aires","Dirección de Aeronáutica (DAO)","","Cessna 208B Grand Caravan","avión","",
  "BAJA","Zona Militar 2007","unidad adicional; matrícula a verificar"],
 ["Buenos Aires","Dir. Prov. de Aeronavegación Oficial y Planif. Aeroportuaria","LV-MRU","Cessna 441 Conquest","avión","dado de baja 2013",
  "VERIF. ANAC","Res. SGG Nº42/2013 (B.O. PBA)","Cedido en 2013 a la Facultad de Ingeniería UNLP"],
 ["Buenos Aires","Dir. Prov. de Aeronavegación Oficial y Planif. Aeroportuaria","LV-MMY","Cessna 441 Conquest","avión","dado de baja 2013",
  "VERIF. ANAC","Res. SGG Nº42/2013 (B.O. PBA)","Cedido en 2013 al Centro de Formación Profesional Nº403"],
 ["Buenos Aires","Dir. Prov. de Aeronavegación Oficial y Planif. Aeroportuaria","LV-MRT","Cessna 441 Conquest","avión","dado de baja 2013",
  "VERIF. ANAC","Res. SGG Nº42/2013 (B.O. PBA)","Cedido en 2013 a la EEST Nº7 Taller Regional Quilmes"],
 ["Buenos Aires","Dir. Prov. de Aeronavegación Oficial y Planif. Aeroportuaria","LV-WHI","Eurocopter BO-105 CBS-4","helicóptero","dado de baja 2013",
  "VERIF. ANAC","Res. SGG Nº42/2013 (B.O. PBA)","Cedido en 2013 a la Facultad de Ingeniería UNLP"],
 # --- Catamarca ---
 ["Catamarca","Gobierno de Catamarca","LV-JWN","Learjet 75","avión","activo",
  "ALTA","La Nación 2024","Jet de la gobernación"],
 # --- Chaco ---
 ["Chaco","Charter usado por la gobernación","LV-CIO","Learjet 60","avión","activo",
  "MEDIA","hexdb / SoloChaco","Titular: Baires Fly (charter, NO propiedad provincial)"],
 ["Chaco","Gobierno de Chaco","LV-MDN","Rockwell 690B Turbo Commander","avión","activo",
  "ALTA","Airliners.net / Zona Militar","Transporte, logística y vuelos sanitarios"],
 # --- Chubut ---
 ["Chubut","Gobierno de Chubut","LV-CKA","Learjet 60XR","avión","activo",
  "CRUCE BD","hexdb (titular)","Titular registrado: Governor of Chubut Province"],
 ["Chubut","Gobierno de Chubut","LV-BEM","Hawker 400XP","avión","activo",
  "ALTA","Digesto Chubut / airhistory","Avión sanitario y traslados oficiales"],
 ["Chubut","Gobierno de Chubut","LV-WPB","Beechcraft King Air C90B","avión","activo",
  "ALTA","Aeromarket / jetphotos","Traslados ejecutivos y vuelos sanitarios"],
 ["Chubut","Charter usado por la gobernación","LV-FUT","Learjet 60","avión","charter",
  "CRUCE BD","lista aeronáutica / hexdb","Titular: Excel Servicios Aereos. Trasladó al gob. Mariano Arcioni (NO es propiedad provincial)"],
 # --- Córdoba ---
 ["Córdoba","Gobierno de Córdoba","LQ-HBQ","Learjet 60","avión","",
  "MEDIA","La Nación / Perfil","Avión 'sanitario'/gobernación; matrícula a confirmar"],
 ["Córdoba","Gobierno de Córdoba","LQ-BAN","Beechcraft Super King Air 350 (B300)","avión","activo",
  "ALTA","Airliners.net / TC Córdoba","Vuelos sanitarios y traslados oficiales"],
 ["Córdoba","Gobierno de Córdoba","LV-KOW","Air Tractor AT-802 (Fuego)","avión","activo",
  "ALTA","aporte usuario (pista18)","Avión hidrante; flota contra incendios forestales"],
 # --- Corrientes ---
 ["Corrientes","Dirección Provincial de Aeronáutica","LV-WJO","Cessna 550 Citation II","avión","activo",
  "ALTA","HCD Corrientes Expte 17504/2023","S/N 550-0728 (ex LV-PHN). Propiedad del Gobierno de Corrientes"],
 ["Corrientes","Dirección Provincial de Aeronáutica","LV-WYR","Cessna 208B Grand Caravan","avión","activo",
  "ALTA","ASN / hexdb / aerospotter","S/N 208B-0598 (ex LV-PMX). Incidente menor Resistencia 04/09/2009"],
 ["Corrientes","Dirección Provincial de Aeronáutica","LV-ZNU","Cessna 208B Grand Caravan","avión","activo",
  "ALTA","aerospotter 2009","S/N 208B-0718 (ex LV-POC)"],
 ["Corrientes","Dirección Provincial de Aeronáutica","LV-BDI","Bell 407","helicóptero","activo",
  "ALTA","aerospotter 2009","S/N 53649 (ex N46375)"],
 # --- Entre Ríos ---
 ["Entre Ríos","Policía de Entre Ríos","LQ-BII","Bell 427","helicóptero","activo",
  "ALTA","Airliners.net (álbum)","S/N 56060. Helicóptero policial provincial"],
 # --- Formosa ---
 ["Formosa","Gobierno de Formosa","LV-BIV","Cessna 208B Grand Caravan","avión","activo",
  "ALTA","Planespotters / hexdb","Confirmado Gobierno de Formosa (BD figura 'Government of Argentina')"],
 # --- Jujuy ---
 ["Jujuy","Coordinación Aeronáutica de Jujuy","LQ-BMH","Cessna Citation Excel","avión","activo",
  "CRUCE BD","Coord. Jujuy + hexdb","Prefijo LQ estatal. BD figura 'Banco Macro SA' (registro a actualizar)"],
 ["Jujuy","Coordinación Aeronáutica de Jujuy","LQ-KOR","Learjet 31A","avión","activo",
  "ALTA","Coord. Jujuy / FR24","Matrícula reportada en FlightRadar24; hex a resolver"],
 ["Jujuy","Coordinación Aeronáutica de Jujuy","LQ-HVN","Airbus H125","helicóptero","activo",
  "ALTA","Vía Jujuy / helis.com","Sanitario; S/N 8401 (2017). Hex no listado aún"],
 # --- La Pampa ---
 ["La Pampa","Gobierno de La Pampa","LQ-JVH","Learjet 60","avión","activo",
  "ALTA","La Nación 2024","Jet de la gobernación, comprado ~US$2M"],
 # --- La Rioja ---
 ["La Rioja","Gobierno de La Rioja","LQ-WTN","Cessna 650 Citation VII","avión","activo",
  "ALTA","Planespotters / Ley 10.722/2024","Base IRJ. Ley 2024 autoriza venta y compra de nuevo sanitario"],
 ["La Rioja","Charter usado por la gobernación","LV-YLC","Beechcraft King Air B350","avión","charter",
  "CRUCE BD","lista aeronáutica / hexdb","Titular: Aero Baires SA. Trasladó al gob. Sergio Casas (NO es propiedad provincial)"],
 # --- Mendoza ---
 ["Mendoza","Gobierno de Mendoza","","Avión sanitario (a confirmar tipo)","avión","",
  "MEDIA","Diario Textual 2020","Comprado 2020 ~US$2M para traslados sanitarios"],
 # --- Misiones ---
 ["Misiones","Policía de Misiones","","Eurocopter EC130 B4","helicóptero","",
  "MEDIA","prensa 2010","Comprado 2010 ~US$3,1M; usado por la gobernación"],
 ["Misiones","Policía de Misiones","LQ-WHT","Bell 206B JetRanger II","helicóptero","activo",
  "ALTA","Airliners.net (álbum)","S/N 4293"],
 ["Misiones","Charter usado por la gobernación","LV-BBG","Hawker 125-800XP","avión","charter",
  "CRUCE BD","lista aeronáutica / hexdb","Titular: Sullair Argentina SA. Trasladó al gob. Hugo Passalacqua (NO es propiedad provincial)"],
 # --- Neuquén ---
 ["Neuquén","Dirección Provincial de Aeronáutica","LV-AXO","Beechcraft B200 King Air","avión","activo",
  "ALTA","Foto Aeronáutica Neuquén","Flota oficial provincial"],
 ["Neuquén","Dirección Provincial de Aeronáutica","LV-BDM","Learjet 31A","avión","activo",
  "ALTA","Foto Aeronáutica Neuquén","Canje con Salta 2009"],
 ["Neuquén","Dirección Provincial de Aeronáutica","LV-CIP","Bell 429","helicóptero","activo",
  "ALTA","Foto Aeronáutica Neuquén","Helicóptero oficial"],
 ["Neuquén","Dirección Provincial de Aeronáutica","LQ-BBR","Bell 407","helicóptero","activo",
  "ALTA","Foto Aeronáutica Neuquén","Gobierno de la Provincia del Neuquén"],
 # --- Río Negro ---
 ["Río Negro","Gobierno de Río Negro","LV-KFB","Cessna Citation V Ultra","avión","vendido/subasta 2024",
  "ALTA","Aviacionline 2024","Subastado en 2024"],
 # --- Salta ---
 ["Salta","Dirección Aeron. de Aviación Civil Salta","LV-ARD","Learjet 45XR","avión","activo",
  "VERIF. ANAC","ANAC (Afectación)","S/N 232, afect. 25/04/2005. Operador comercial registrado"],
 ["Salta","Dirección Aeron. de Aviación Civil Salta","LV-BXD","Learjet 45","avión","activo",
  "VERIF. ANAC","ANAC (Afectación)","S/N 254, afect. 17/07/2012"],
 # --- San Juan ---
 ["San Juan","Gobierno de San Juan","LQ-IJK","Learjet 75","avión","activo",
  "CRUCE BD","hexdb (titular)","Titular registrado: Governor of San Juan Province"],
 ["San Juan","Gobierno de San Juan","LQ-YHC","Cessna 550 Citation II","avión","vendido 2019 (subasta)",
  "ALTA","Diario de Cuyo / aerospotter 2019","Subastado abr-2019 a Ivica y Antonio Dumandzic S.A. (ya no es provincial)"],
 ["San Juan","Dirección de Aeronáutica de San Juan","LQ-BHT","Bell 407","helicóptero","accidentado 2013",
  "ALTA","Wikipedia / JST / álbum","ex LV-BHT (S/N 53735). Accidente 11/10/2013 en Valle Fértil (gob. Gioja a bordo)"],
 # --- San Luis ---
 ["San Luis","Gobierno de San Luis","","(a relevar)","","",
  "BAJA","-","Histórico: flota provincial amplia; relevar actual"],
 # --- Santa Cruz ---
 ["Santa Cruz","Gobierno de Santa Cruz","LV-KJY","Pilatus PC-24","avión","activo",
  "ALTA","Gob. Santa Cruz 2023","Sanitario 'La Cruz del Sur', registrado 19/09/2023"],
 # --- Santa Fe ---
 ["Santa Fe","Dir. Prov. de Movilidad y Aeronáutica","LQ-BIN","Eurocopter AS350 B2","helicóptero","activo",
  "ALTA","Boletín Oficial Santa Fe","Helicóptero oficial"],
 ["Santa Fe","Dir. Prov. de Movilidad y Aeronáutica","LV-CLE","Beechcraft Baron 58P","avión","activo",
  "ALTA","Boletín Oficial Santa Fe","Avión oficial"],
 ["Santa Fe","Dir. Prov. de Movilidad y Aeronáutica","LV-FKW","Beechcraft Baron 58P","avión","activo",
  "ALTA","Boletín Oficial Santa Fe","Avión oficial"],
 ["Santa Fe","Dir. Prov. de Movilidad y Aeronáutica","","Agusta AW109","helicóptero","activo",
  "MEDIA","Gob. Santa Fe","Emergencias/patrullaje policial; matrícula a verificar"],
 ["Santa Fe","Dir. Prov. de Movilidad y Aeronáutica","","Air Tractor AT-802 Fire Boss","avión","en incorporación",
  "MEDIA","aporte usuario (pista18)","Adquirido; pendiente de traslado (certificación de pilotos en EE.UU.)"],
 # --- Santiago del Estero ---
 ["Santiago del Estero","Dirección Provincial de Aeronáutica","LQ-KKX","Beechcraft Super King Air 200","avión","activo",
  "ALTA","Zona Militar / prensa","Comprado ~US$2,95M (gob. Zamora)"],
 ["Santiago del Estero","Dirección Provincial de Aeronáutica","LQ-CPS","Learjet 45","avión","activo",
  "ALTA","avionesenezeiza 2020","Visto en Ezeiza"],
 ["Santiago del Estero","Dirección Provincial de Aeronáutica","LV-KJS","Boeing 737 Fireliner (hidrante)","avión","activo",
  "ALTA","aporte usuario","Avión hidrante contra incendios"],
 ["Santiago del Estero","Dirección Provincial de Aeronáutica","LQ-BFS","Learjet 40","avión","activo",
  "ALTA","Airliners.net / lista aeronáutica","S/N 45-2003. Trasladó al gob. Zamora (también citado como LV-BFS)"],
 ["Santiago del Estero","Dirección Provincial de Aeronáutica","LQ-ZRB","Raytheon King Air C90A","avión","activo",
  "ALTA","Airliners.net (álbum)","S/N LJ-1552"],
 ["Santiago del Estero","Dirección Provincial de Aeronáutica","LQ-BIZ","Bell 427","helicóptero","activo",
  "ALTA","Airliners.net (álbum)","S/N 56042"],
 ["Santiago del Estero","Dirección Provincial de Aeronáutica","LQ-ZNT","Bell 206B JetRanger II","helicóptero","activo",
  "ALTA","Airliners.net (álbum)","S/N 4499"],
 ["Santiago del Estero","Dirección Provincial de Aeronáutica","LV-MIS","Pilatus PC-6 Turbo Porter","avión","activo",
  "ALTA","Airliners.net (álbum)","S/N 793"],
 # --- Tierra del Fuego ---
 ["Tierra del Fuego","Dirección de Aviación de Tierra del Fuego","LV-AIT","Gates Learjet 35A","avión","activo",
  "ALTA","Airliners.net","MSN 35A-408. Sanitario/oficial"],
 ["Tierra del Fuego","Dir. Prov. de Aeronavegación Oficial","LV-MTP","IAI-201 Arava","avión","activo",
  "ALTA","Gob. Tierra del Fuego 2020","Transporte de carga sanitaria entre ciudades de la provincia"],
 # --- Tucumán ---
 ["Tucumán","Gobierno de Tucumán","LV-BEU","Cessna 550B Citation Bravo","avión","activo",
  "ALTA","MSP Tucumán 2024 / spotter","MSN 1120. Usado sanitario+protocolar; service en Paraguay 2024 (gob. Jaldo). (LV-CKA era de Chubut)"],
 # --- CABA ---
 ["CABA","Gobierno de la Ciudad","","(a relevar)","","",
  "BAJA","-","Relevar; mayormente usa charters"],
]

# ===== Charters usados por políticos / dirigentes (NO flota estatal provincial) =====
# Misma estructura de columnas: ámbito(provincia), usuario/dirigente(organismo), matrícula, tipo, ...
DIRIGENTES = [
 ["AFA / fútbol","Usado por Claudio 'Chiqui' Tapia","LV-SYG","Gulfstream G400 (GLF4)","avión","activo",
  "ALTA","Cadena3 / Nexofin","ex T7-SUE (San Marino), S/N 1522. Operado por Flyzar (Serv. y Empr. Aeronáuticos SA)"],
]

if __name__ == "__main__":
    import csv, sys
    w = csv.writer(sys.stdout)
    w.writerow(["provincia","organismo","matricula","tipo","categoria","estado","confianza","fuente","notas"])
    w.writerows(SEED)
