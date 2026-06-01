# -*- coding: utf-8 -*-
"""
Recolector ADS-B de aeronaves provinciales argentinas.
- Lee el padrón (padron_aeronaves.csv), toma los códigos hex.
- Consulta airplanes.live cada N segundos.
- Guarda cada posición en una base SQLite (snapshots) y arma "vuelos" (tramos)
  agrupando posiciones contiguas de una misma aeronave.

Uso:
    python3 poller.py            # corre en loop continuo (Ctrl+C para frenar)
    python3 poller.py --once     # una sola pasada (ideal para cron)
Requiere solo la librería estándar de Python 3.
"""
import csv, json, sqlite3, time, argparse, urllib.request, datetime, os

BASE = os.path.dirname(os.path.abspath(__file__))
PADRON = os.path.join(BASE, "padron_aeronaves.csv")
DB = os.environ.get("PADRON_DB", os.path.join(BASE, "vuelos.db"))
INTERVALO = 60          # segundos entre consultas
GAP_VUELO = 30*60       # corte entre tramos: 30 min sin señal => nuevo vuelo
UA = {"User-Agent": "padron-aeronaves-provinciales/1.0 (proyecto periodistico)"}

def cargar_padron():
    reg = {}
    with open(PADRON, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            h = (row.get("hex") or "").strip().upper()
            if h and not h.startswith("ERR"):
                reg[h] = row
    return reg

def init_db():
    c = sqlite3.connect(DB)
    c.execute("PRAGMA busy_timeout=10000")   # esperar hasta 10s si la base está ocupada
    c.executescript("""
    CREATE TABLE IF NOT EXISTS snapshots(
        ts INTEGER, hex TEXT, matricula TEXT, provincia TEXT,
        lat REAL, lon REAL, alt_baro INTEGER, gs REAL, track REAL, flight TEXT);
    CREATE INDEX IF NOT EXISTS idx_snap_hex_ts ON snapshots(hex, ts);
    CREATE TABLE IF NOT EXISTS vuelos(
        id INTEGER PRIMARY KEY AUTOINCREMENT, hex TEXT, matricula TEXT, provincia TEXT,
        inicio INTEGER, fin INTEGER, lat_ini REAL, lon_ini REAL, lat_fin REAL, lon_fin REAL,
        alt_max INTEGER, puntos INTEGER);
    """)
    c.commit()
    return c

def consultar(hexes):
    """Consulta airplanes.live por lista de hex (en bloques)."""
    out = []
    for i in range(0, len(hexes), 100):
        bloque = ",".join(hexes[i:i+100])
        url = f"https://api.airplanes.live/v2/hex/{bloque}"
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode())
            out += data.get("ac", [])
        except Exception as e:
            print(f"  [aviso] error consultando bloque: {e}")
        time.sleep(1)
    return out

def guardar(con, reg, aviones, ts):
    cur = con.cursor()
    activos = 0
    for ac in aviones:
        h = (ac.get("hex") or "").upper()
        meta = reg.get(h, {})
        lat, lon = ac.get("lat"), ac.get("lon")
        if lat is None:   # sin posición => en tierra o señal parcial; lo ignoramos
            continue
        activos += 1
        cur.execute("INSERT INTO snapshots VALUES (?,?,?,?,?,?,?,?,?,?)", (
            ts, h, meta.get("matricula",""), meta.get("provincia",""),
            lat, lon, ac.get("alt_baro") if isinstance(ac.get("alt_baro"),int) else None,
            ac.get("gs"), ac.get("track"), (ac.get("flight") or "").strip()))
    con.commit()
    return activos

def pasada(con, reg):
    ts = int(time.time())
    hexes = list(reg.keys())
    aviones = consultar(hexes)
    n = guardar(con, reg, aviones, ts)
    hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if n:
        vistos = ", ".join(sorted({reg[a.get("hex","").upper()]["matricula"]
                    for a in aviones if a.get("hex","").upper() in reg and a.get("lat") is not None}))
        print(f"[{hora}] {n} aeronave(s) provincial(es) en vuelo: {vistos}")
    else:
        print(f"[{hora}] sin aeronaves provinciales en el aire")
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="una sola pasada y salir")
    args = ap.parse_args()
    reg = cargar_padron()
    print(f"Padrón cargado: {len(reg)} aeronaves con hex rastreable")
    con = init_db()
    if args.once:
        pasada(con, reg); return
    print(f"Recolectando cada {INTERVALO}s. Ctrl+C para frenar.")
    try:
        while True:
            pasada(con, reg)
            time.sleep(INTERVALO)
    except KeyboardInterrupt:
        print("\nDetenido.")

if __name__ == "__main__":
    main()
