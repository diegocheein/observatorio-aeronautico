# -*- coding: utf-8 -*-
"""Resuelve el código ICAO24 (hex) de cada matrícula del padrón usando hexdb.io.
Escribe padron_aeronaves.csv con la columna hex completada."""
import csv, time, urllib.request
from padron_seed import SEED
try:
    from padron_seed import DIRIGENTES
except Exception:
    DIRIGENTES = []

import json, os
UA = {"User-Agent":"Mozilla/5.0 (padron-aeronaves-provinciales)"}
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".hex_cache.json")
try:
    CACHE = json.load(open(CACHE_FILE, encoding="utf-8"))
except Exception:
    CACHE = {}

def _get(url):
    if url in CACHE:
        return CACHE[url]
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=8) as r:
        val = r.read().decode().strip()
    CACHE[url] = val
    try:
        json.dump(CACHE, open(CACHE_FILE,"w",encoding="utf-8"))
    except Exception:
        pass
    return val

def reg_to_hex(reg):
    reg = reg.strip()
    if not reg or any(c in reg for c in " /,"):  # vacío o celda con varias matrículas
        return ""
    try:
        val = _get(f"https://hexdb.io/reg-hex?reg={reg}")
        return "" if val.lower() in ("n/a","","none") else val.upper()
    except Exception:
        return ""   # no figura en la base hex (se completa al verla volar)

def hex_to_owner(hexcode):
    """Devuelve (titular_registrado, tipo_db) desde la base de aviación hexdb."""
    if not hexcode or hexcode.startswith("ERR"):
        return "", ""
    try:
        d = json.loads(_get(f"https://hexdb.io/api/v1/aircraft/{hexcode}"))
        return d.get("RegisteredOwners","") or "", d.get("Type","") or ""
    except Exception:
        return "", ""

cols = ["provincia","organismo","matricula","tipo","categoria","estado","confianza","fuente","notas"]
out_cols = ["provincia","organismo","matricula","hex","tipo","categoria","estado",
            "confianza","titular_registrado","fuente","notas"]
BASE = os.path.dirname(os.path.abspath(__file__))

def procesar(seed, outfile):
    rows = []
    for r in seed:
        d = dict(zip(cols, r))
        d["hex"] = reg_to_hex(d["matricula"])
        d["titular_registrado"], d["tipo_db"] = hex_to_owner(d["hex"])
        if d["matricula"]:
            print(f'{d["matricula"]:>8}  ->  {d["hex"] or "(sin hex)":8}  {d["titular_registrado"]}')
        rows.append(d)
        time.sleep(0.05)
    with open(os.path.join(BASE, outfile),"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        for d in rows:
            w.writerow({k:d.get(k,"") for k in out_cols})
    con_hex = sum(1 for d in rows if d["hex"])
    print(f"{outfile}: {len(rows)} filas | con hex {con_hex}")
    return rows

def guardar_cache():
    try:
        json.dump(CACHE, open(CACHE_FILE,"w",encoding="utf-8"))
    except Exception:
        pass

if __name__ == "__main__":
    procesar(SEED, "padron_aeronaves.csv")
    procesar(DIRIGENTES, "charters_dirigentes.csv")
    guardar_cache()
    print("DONE")
