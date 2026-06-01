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
import csv, sqlite3, os, math, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("PADRON_DB", os.path.join(BASE, "vuelos.db"))
AIRPORTS = os.path.join(BASE, "airports_ar.csv")
OUT = os.path.join(BASE, "movimientos.csv")
HISTORIAL = os.path.join(BASE, "historial_opensky.csv")   # backfill OpenSky (opcional)
GAP_MIN = 30          # minutos sin señal => nuevo tramo
RADIO_KM = 25         # radio máx. para asignar un aeropuerto
MIN_PUNTOS = 3        # tramos con menos puntos se descartan (ruido)

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

def aeropuerto_cercano(lat, lon, aps):
    best, bestd = None, 1e9
    for icao, iata, ciudad, la, lo in aps:
        d = haversine(lat, lon, la, lo)
        if d < bestd:
            best, bestd = (icao, iata, ciudad, la, lo), d
    if best and bestd <= RADIO_KM:
        icao, iata, ciudad, la, lo = best
        etq = iata or icao
        return {"label": f"{etq} ({ciudad})", "code": icao, "lat": la, "lon": lo}
    return {"label": "(en ruta / sin aeropuerto cercano)", "code": "", "lat": lat, "lon": lon}

def fmt(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

def main():
    aps = cargar_aeropuertos()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=10000")   # esperar si el poller está escribiendo
    # snapshots puede no existir todavía (si el poller nunca corrió): la creamos vacía
    # para poder generar igual el historial de OpenSky sin datos en vivo.
    con.execute("""CREATE TABLE IF NOT EXISTS snapshots(
        ts INTEGER, hex TEXT, matricula TEXT, provincia TEXT,
        lat REAL, lon REAL, alt_baro INTEGER, gs REAL, track REAL, flight TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS vuelos(
        id INTEGER PRIMARY KEY AUTOINCREMENT, hex TEXT, matricula TEXT, provincia TEXT,
        inicio INTEGER, fin INTEGER, origen TEXT, destino TEXT,
        dur_min INTEGER, alt_max INTEGER, puntos INTEGER)""")
    con.execute("DELETE FROM vuelos")
    hexes = [r[0] for r in con.execute("SELECT DISTINCT hex FROM snapshots").fetchall()]
    movimientos = []
    for h in hexes:
        snaps = con.execute(
            "SELECT ts,matricula,provincia,lat,lon,alt_baro FROM snapshots "
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
            o = aeropuerto_cercano(ini[3], ini[4], aps)
            d = aeropuerto_cercano(fin[3], fin[4], aps)
            alt_max = max((s[5] or 0) for s in t)
            dur = round((fin[0]-ini[0])/60)
            con.execute("INSERT INTO vuelos(hex,matricula,provincia,inicio,fin,origen,destino,dur_min,alt_max,puntos) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (h, matric, prov, ini[0], fin[0], o["label"], d["label"], dur, alt_max, len(t)))
            movimientos.append([matric, prov, h, fmt(ini[0]), fmt(fin[0]), dur,
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
