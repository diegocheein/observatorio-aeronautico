# -*- coding: utf-8 -*-
"""
Backfill de historial de vuelos desde OpenSky Network.

Toma los hex (ICAO24) del padrón y consulta el endpoint /flights/aircraft de
OpenSky, que devuelve los vuelos REALES de cada aeronave (despegue, aterrizaje y
aeropuertos estimados) en un rango de hasta 30 días. Resuelve los códigos de
aeropuerto a ciudad/coordenadas usando airports_ar.csv (cobertura global) y
escribe 'historial_opensky.csv' con EXACTAMENTE las mismas columnas que
movimientos.csv. Luego build_flights.py lo fusiona, así el historial queda en la
página de entrada y persiste en cada regeneración del sitio.

Autenticación (OpenSky migró a OAuth2 client-credentials):
    export OPENSKY_CLIENT_ID="tu_client_id"
    export OPENSKY_CLIENT_SECRET="tu_client_secret"
  (se obtienen creando una cuenta gratis en https://opensky-network.org y un
   "API client" en el perfil de la cuenta).
  Compatibilidad: si tenés cuenta vieja, también acepta:
    export OPENSKY_USER="usuario"; export OPENSKY_PASS="clave"
  Sin credenciales funciona en modo anónimo pero con límites muy bajos.

Uso:
    python3 backfill_opensky.py            # últimos 30 días
    python3 backfill_opensky.py --dias 7   # últimos 7 días
    python3 backfill_opensky.py --dias 90  # se parte en ventanas de 30 días
Sólo usa la librería estándar de Python 3.
"""
import csv, json, os, time, argparse, urllib.request, urllib.parse, urllib.error, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
PADRON = os.path.join(BASE, "padron_aeronaves.csv")
AIRPORTS = os.path.join(BASE, "airports_ar.csv")
OUT = os.path.join(BASE, "historial_opensky.csv")
API = "https://opensky-network.org/api"
TOKEN_URL = ("https://auth.opensky-network.org/auth/realms/opensky-network/"
             "protocol/openid-connect/token")
UA = {"User-Agent": "padron-aeronaves-provinciales/1.0 (proyecto periodistico)"}
MAX_VENTANA = 30 * 24 * 3600   # 30 días: tope por consulta de OpenSky

# columnas idénticas a movimientos.csv (para que la fusión sea directa)
COLS = ["matricula", "provincia", "hex", "inicio", "fin", "dur_min", "origen", "destino",
        "origen_code", "destino_code", "origen_lat", "origen_lon", "destino_lat",
        "destino_lon", "alt_max_ft", "puntos"]


# ---------- padrón y aeropuertos ----------
def cargar_padron():
    reg = {}
    with open(PADRON, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            h = (row.get("hex") or "").strip().upper()
            if h and not h.startswith("ERR"):
                reg[h] = row
    return reg


def cargar_aeropuertos():
    aps = {}
    with open(AIRPORTS, encoding="utf-8") as f:
        for a in csv.DictReader(f):
            icao = (a.get("icao") or "").strip().upper()
            if not icao:
                continue
            try:
                lat, lon = float(a["lat"]), float(a["lon"])
            except (ValueError, KeyError):
                continue
            etq = (a.get("iata") or "").strip() or icao
            ciudad = (a.get("ciudad") or a.get("nombre") or "").strip()
            aps[icao] = {"label": f"{etq} ({ciudad})" if ciudad else etq,
                         "code": icao, "lat": lat, "lon": lon}
    return aps


def resolver(icao, aps):
    if not icao:
        return {"label": "(desconocido)", "code": "", "lat": "", "lon": ""}
    a = aps.get(icao.strip().upper())
    if a:
        return a
    return {"label": f"({icao})", "code": icao, "lat": "", "lon": ""}


# ---------- autenticación OpenSky ----------
def obtener_token():
    cid = os.environ.get("OPENSKY_CLIENT_ID")
    csec = os.environ.get("OPENSKY_CLIENT_SECRET")
    if not (cid and csec):
        return None
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": cid,
        "client_secret": csec,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        tok = json.loads(r.read().decode())
    return tok.get("access_token")


_TOK = {"hdr": {}, "ts": 0, "modo": "anonimo"}
_TOKEN_TTL = 25 * 60   # refrescar el token OAuth2 antes de los 30 min de vida

def _calcular_auth():
    """Construye los headers de auth frescos según las credenciales disponibles."""
    try:
        token = obtener_token()
    except Exception as e:
        print(f"  [aviso] no se pudo obtener token OAuth2: {e}")
        token = None
    if token:
        return ({"Authorization": f"Bearer {token}"}, "oauth2")
    user = os.environ.get("OPENSKY_USER")
    pwd = os.environ.get("OPENSKY_PASS")
    if user and pwd:
        import base64
        cred = base64.b64encode(f"{user}:{pwd}".encode()).decode()
        return ({"Authorization": f"Basic {cred}"}, "basic")
    return ({}, "anonimo")

def auth_headers(force=False):
    """Devuelve headers de auth válidos, refrescando el token OAuth2 si venció."""
    if force or not _TOK["hdr"] or (time.time() - _TOK["ts"]) > _TOKEN_TTL:
        hdr, modo = _calcular_auth()
        _TOK.update(hdr=hdr, ts=time.time(), modo=modo)
    return _TOK["hdr"], _TOK["modo"]


# ---------- consulta de vuelos ----------
def consultar_vuelos(hex_lower, begin, end, _refresco=False):
    url = f"{API}/flights/aircraft?" + urllib.parse.urlencode({
        "icao24": hex_lower, "begin": begin, "end": end})
    hdr, _ = auth_headers()
    headers = dict(UA); headers.update(hdr)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []          # sin vuelos en el intervalo
        if e.code == 401 and not _refresco:
            auth_headers(force=True)   # token vencido: refrescar y reintentar una vez
            return consultar_vuelos(hex_lower, begin, end, _refresco=True)
        if e.code == 429:
            print("  [aviso] límite de tasa (429); espero 10s…")
            time.sleep(10)
            return None        # señal de reintento
        print(f"  [aviso] HTTP {e.code} para {hex_lower}")
        return []
    except Exception as e:
        print(f"  [aviso] error consultando {hex_lower}: {e}")
        return []


def ventanas(dias):
    """OpenSky permite consultar a lo sumo 2 particiones (días UTC) por request.
    Generamos ventanas alineadas a medianoche UTC, de 2 días, + el día de hoy."""
    DIA = 24 * 3600
    now = int(time.time())
    hoy_mid = now - (now % DIA)           # medianoche UTC de hoy (epoch es múltiplo de 86400)
    inicio = hoy_mid - dias * DIA
    bordes = []
    a = inicio
    while a < hoy_mid:
        b = min(a + 2 * DIA, hoy_mid)     # 2 días => exactamente 2 particiones
        bordes.append((a, b))
        a = b
    bordes.append((hoy_mid, now))         # día de hoy (1 partición)
    return bordes


def fmt(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=30, help="días hacia atrás (default 30)")
    args = ap.parse_args()

    reg = cargar_padron()
    aps = cargar_aeropuertos()
    _, modo = auth_headers()
    print(f"Padrón: {len(reg)} aeronaves rastreables | aeropuertos: {len(aps)} | auth: {modo}")
    if modo == "anonimo":
        print("  [aviso] Sin credenciales OpenSky: modo anónimo con límites bajos.")
        print("          Definí OPENSKY_CLIENT_ID y OPENSKY_CLIENT_SECRET para mejores resultados.")

    bordes = ventanas(args.dias)
    filas, vistos = [], set()
    for h, meta in reg.items():
        hl = h.lower()
        total_h = 0
        for (b0, b1) in bordes:
            vuelos = None
            for intento in range(3):
                vuelos = consultar_vuelos(hl, b0, b1)
                if vuelos is not None:
                    break
            vuelos = vuelos or []
            for v in vuelos:
                fs, ls = v.get("firstSeen"), v.get("lastSeen")
                if not fs or not ls:
                    continue
                clave = (h, fs)
                if clave in vistos:
                    continue
                vistos.add(clave)
                o = resolver(v.get("estDepartureAirport"), aps)
                d = resolver(v.get("estArrivalAirport"), aps)
                dur = round((ls - fs) / 60)
                filas.append({
                    "matricula": meta.get("matricula", ""),
                    "provincia": meta.get("provincia", ""),
                    "hex": h,
                    "inicio": fmt(fs), "fin": fmt(ls), "dur_min": dur,
                    "origen": o["label"], "destino": d["label"],
                    "origen_code": o["code"], "destino_code": d["code"],
                    "origen_lat": o["lat"], "origen_lon": o["lon"],
                    "destino_lat": d["lat"], "destino_lon": d["lon"],
                    "alt_max_ft": "", "puntos": "",
                })
                total_h += 1
            time.sleep(0.4)    # cortesía con la API
        if total_h:
            print(f"  {meta.get('matricula','?'):10} {h}: {total_h} vuelo(s)")

    filas.sort(key=lambda r: r["inicio"])
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(filas)
    print(f"\nHistorial OpenSky: {len(filas)} vuelos -> {os.path.basename(OUT)}")
    print("Ahora corré:  python3 build_flights.py  (fusiona el historial en movimientos.csv)")
    print("y luego regenerá las páginas (build_index/build_report/build_stats).")


if __name__ == "__main__":
    main()
