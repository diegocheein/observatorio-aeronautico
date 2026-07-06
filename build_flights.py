# -*- coding: utf-8 -*-
"""
Analizador de movimientos: convierte las posiciones crudas (snapshots) que
recolecta poller.py en VUELOS (tramos) con aeropuerto de origen y destino.

Lógica:
  - Por cada aeronave (hex), ordena los snapshots por tiempo.
  - Corta en un nuevo tramo cuando hay un hueco sin señal > GAP_MIN minutos
    (la aeronave aterrizó y volvió a despegar, o salió de cobertura).
  - Para cada tramo toma la primera y la última posición y les asigna el
    aeropuerto más cercano (< RADIO_KM). Eso da origen y destino aproximados.
  - Escribe movimientos.csv y actualiza la tabla 'vuelos' en la base.

Uso:
    python3 build_flights.py            # procesa vuelos.db -> movimientos.csv
    PADRON_DB=/ruta/vuelos.db python3 build_flights.py
Sólo usa librería estándar.
"""
import csv, sqlite3, os, math, datetime, time

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("PADRON_DB", os.path.join(BASE, "vuelos.db"))
AIRPORTS = os.path.join(BASE, "airports_ar.csv")
OUT = os.path.join(BASE, "movimientos.csv")
HISTORIAL = os.path.join(BASE, "historial_opensky.csv")   # backfill OpenSky (opcional)
GAP_MIN = 30          # minutos sin señal => nuevo tramo
RADIO_KM = 25         # radio máx. para asignar un aeropuerto
MIN_PUNTOS = 3        # tramos con menos puntos se descartan (ruido)

# --- detección de "vuelo terminado" (el avión ya aterrizó / está quieto) ---
SETTLE_SEG = 20 * 60  # sin señal nueva por 20 min => el vuelo terminó
ALT_TIERRA = 3000     # ft: por debajo se considera bajo (aproximación/tierra)
GS_TIERRA  = 80       # kt: por debajo se considera lento (tierra/taxi)
QUIETO_SEG = 5 * 60   # tiene que estar bajo+lento al menos 5 min para contarlo posado
RADIO_EST  = 200      # km: radio para ESTIMAR el aeropuerto si perdió señal en descenso
BAJANDO_FT = 3000     # ft de descenso (en ~5 min) para considerar que venía aterrizando

# Hora local de Argentina (UTC-3, sin horario de verano). El VPS corre en UTC,
# así que convertimos a -3 para que la actividad muestre la hora argentina.
AR_TZ = datetime.timezone(datetime.timedelta(hours=-3))

def haversine(la1, lo1, la2, lo2):
    R = 6371.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp = math.radians(la2-la1); dl = math.radians(lo2-lo1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def cargar_aeropuertos():
    aps = []
    with open(AIRPORTS, encoding="utf-8") as f:
        for a in csv.DictReader(f):
            try:
                aps.append((a["icao"], a["iata"], a["ciudad"] or a["nombre"],
                            float(a["lat"]), float(a["lon"])))
            except ValueError:
                continue
    return aps

def aeropuerto_cercano(lat, lon, aps, solo_reales=False, radio=RADIO_KM):
    """Aeropuerto más cercano dentro de 'radio' km.
    solo_reales=True considera únicamente aeropuertos con código IATA
    (descarta campos/estancias chicos) — útil para *estimar* dónde aterrizó."""
    best, bestd = None, 1e9
    for icao, iata, ciudad, la, lo in aps:
        if solo_reales and not (iata or "").strip():
            continue
        d = haversine(lat, lon, la, lo)
        if d < bestd:
            best, bestd = (icao, iata, ciudad, la, lo), d
    if best and bestd <= radio:
        icao, iata, ciudad, la, lo = best
        etq = iata or icao
        return {"label": f"{etq} ({ciudad})", "code": icao, "lat": la, "lon": lo}
    return {"label": "(en ruta / sin aeropuerto cercano)", "code": "", "lat": lat, "lon": lon}

def fmt(ts):
    return datetime.datetime.fromtimestamp(ts, AR_TZ).strftime("%Y-%m-%d %H:%M")

def main():
    aps = cargar_aeropuertos()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=10000")   # esperar si el poller está escribiendo
    # snapshots puede no existir todavía (si el poller nunca corrió): la creamos vacía
    # para poder generar igual el historial de OpenSky sin datos en vivo.
    con.execute("""CREATE TABLE IF NOT EXISTS snapshots(
        ts INTEGER, hex TEXT, matricula TEXT, provincia TEXT,
        lat REAL, lon REAL, alt_baro INTEGER, gs REAL, track REAL, flight TEXT)""")
    # La tabla 'vuelos' la "posee" este script. El poller puede haber creado una
    # versión vieja sin columnas origen/destino: la recreamos siempre para
    # garantizar el esquema correcto (en vez de DELETE, que no migra columnas).
    con.execute("DROP TABLE IF EXISTS vuelos")
    con.execute("""CREATE TABLE vuelos(
        id INTEGER PRIMARY KEY AUTOINCREMENT, hex TEXT, matricula TEXT, provincia TEXT,
        inicio INTEGER, fin INTEGER, origen TEXT, destino TEXT,
        dur_min INTEGER, alt_max INTEGER, puntos INTEGER)""")
    ahora = int(time.time())
    hexes = [r[0] for r in con.execute("SELECT DISTINCT hex FROM snapshots").fetchall()]
    movimientos = []
    for h in hexes:
        snaps = con.execute(
            "SELECT ts,matricula,provincia,lat,lon,alt_baro,gs FROM snapshots "
            "WHERE hex=? AND lat IS NOT NULL ORDER BY ts", (h,)).fetchall()
        if not snaps:
            continue
        # segmentar por huecos
        tramos, actual = [], [snaps[0]]
        for prev, cur in zip(snaps, snaps[1:]):
            if (cur[0]-prev[0]) > GAP_MIN*60:
                tramos.append(actual); actual=[cur]
            else:
                actual.append(cur)
        tramos.append(actual)
        for t in tramos:
            if len(t) < MIN_PUNTOS:
                continue
            ini, fin = t[0], t[-1]
            matric, prov = ini[1], ini[2]
            alt_max = max((s[5] or 0) for s in t)

            # ¿el vuelo terminó? Dos formas de saberlo:
            #  (a) hace SETTLE_SEG que no recibimos señal => aterrizó / salió de cobertura.
            #  (b) viene bajo y lento (posado) de forma sostenida al final del tramo.
            sin_senal = (ahora - fin[0]) >= SETTLE_SEG
            # buscar la cola "en tierra": puntos finales bajos y lentos.
            posado = ini      # punto donde tocó tierra (touchdown aprox.)
            for s in reversed(t):
                if (s[5] or 0) <= ALT_TIERRA and (s[6] or 0) <= GS_TIERRA:
                    posado = s
                else:
                    break
            quieto_seg = fin[0] - posado[0]
            en_tierra = (posado is not ini) and quieto_seg >= QUIETO_SEG
            finalizado = sin_senal or en_tierra

            # --- ORIGEN ---
            # Si lo captamos bajo y lento, realmente despegó cerca: aeropuerto cercano.
            # Si apareció alto/en crucero, NO es el despegue real (sólo entró a cobertura):
            # estimamos el aeropuerto REAL (con IATA) más cercano al primer punto.
            en_despegue = (ini[5] or 0) <= ALT_TIERRA and (ini[6] or 0) <= GS_TIERRA
            if en_despegue:
                o = aeropuerto_cercano(ini[3], ini[4], aps)
            else:
                o = aeropuerto_cercano(ini[3], ini[4], aps, solo_reales=True, radio=RADIO_EST)
                if o["code"]:
                    o = dict(o); o["label"] = o["label"] + " · estimado"
                else:
                    o = {"label": "(fuera de cobertura)", "code": "", "lat": ini[3], "lon": ini[4]}
            if not finalizado:
                # sigue en el aire: no inventamos un aterrizaje.
                d = {"label": "(en vuelo)", "code": "", "lat": fin[3], "lon": fin[4]}
                fin_ts = fin[0]
            elif en_tierra:
                # tocó tierra: destino = aeropuerto cercano al punto de toque.
                d = aeropuerto_cercano(posado[3], posado[4], aps)
                fin_ts = posado[0]
            else:
                # sin señal: el avión desapareció del radar. Si venía BAJANDO (aproximación)
                # o ya estaba bajo, suponemos que aterrizó en el aeropuerto REAL más cercano
                # (p.ej. su cabecera). Si estaba alto y nivelado, sólo salió de cobertura.
                alt_fin = fin[5]
                alt_prev = next((s[5] for s in reversed(t)
                                 if fin[0]-s[0] >= 300 and s[5] is not None), None)
                bajando = (alt_fin is not None and alt_prev is not None
                           and (alt_prev - alt_fin) >= BAJANDO_FT)
                bajo = (alt_fin is not None and alt_fin <= 8000)
                if bajando or bajo:
                    d = aeropuerto_cercano(fin[3], fin[4], aps, solo_reales=True, radio=RADIO_EST)
                    if d["code"]:
                        d = dict(d); d["label"] = d["label"] + " · estimado"
                    else:
                        d = {"label": "(fuera de cobertura)", "code": "", "lat": fin[3], "lon": fin[4]}
                else:
                    d = {"label": "(fuera de cobertura)", "code": "", "lat": fin[3], "lon": fin[4]}
                fin_ts = fin[0]

            dur = round((fin_ts-ini[0])/60)
            con.execute("INSERT INTO vuelos(hex,matricula,provincia,inicio,fin,origen,destino,dur_min,alt_max,puntos) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (h, matric, prov, ini[0], fin_ts, o["label"], d["label"], dur, alt_max, len(t)))
            movimientos.append([matric, prov, h, fmt(ini[0]), fmt(fin_ts), dur,
                                o["label"], d["label"], o["code"], d["code"],
                                o["lat"], o["lon"], d["lat"], d["lon"], alt_max, len(t)])
    con.commit()

    COLS = ["matricula","provincia","hex","inicio","fin","dur_min","origen","destino",
            "origen_code","destino_code","origen_lat","origen_lon","destino_lat","destino_lon",
            "alt_max_ft","puntos"]

    # --- fusionar historial de OpenSky (backfill), si existe ---
    # Clave de deduplicación: (hex, inicio) — evita duplicar un vuelo ya detectado en vivo.
    claves = {(str(m[2]).upper(), str(m[3])) for m in movimientos}
    extra = 0
    if os.path.exists(HISTORIAL):
        for r in csv.DictReader(open(HISTORIAL, encoding="utf-8")):
            k = ((r.get("hex") or "").upper(), r.get("inicio") or "")
            if k in claves or not k[0]:
                continue
            claves.add(k)
            movimientos.append([r.get(c, "") for c in COLS])
            extra += 1

    movimientos.sort(key=lambda x: x[3])
    with open(OUT,"w",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        w.writerows(movimientos)
    suf = f" (incluye {extra} de OpenSky)" if extra else ""
    print(f"Vuelos detectados: {len(movimientos)}{suf} -> {os.path.basename(OUT)}")
    for m in movimientos[:20]:
        print(f"  {m[3]}  {m[0]:8} {m[1]:16} {m[6]:28} -> {m[7]}")

if __name__ == "__main__":
    main()
