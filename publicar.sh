#!/usr/bin/env bash
# Publicador del Observatorio Aeronautico (corre en el VPS).
# Reconstruye el sitio desde la base local (vuelos.db) y empuja al repo.
# El workflow de GitHub Pages publica el HTML resultante.
set -u
cd /opt/observatorio || exit 1
export PADRON_DB=/opt/observatorio/vuelos.db
export LC_ALL=C.UTF-8 LANG=C.UTF-8

LOG="/opt/observatorio/publicar.log"
echo "==== $(date '+%Y-%m-%d %H:%M:%S') publicar.sh ====" >> "$LOG"

# 1) Reconstruir vuelos + todas las paginas
python3 build_flights.py >> "$LOG" 2>&1
python3 build_xlsx.py    >> "$LOG" 2>&1
python3 build_index.py   >> "$LOG" 2>&1
python3 build_map.py     >> "$LOG" 2>&1
python3 build_report.py  >> "$LOG" 2>&1
python3 build_stats.py   >> "$LOG" 2>&1
python3 build_ayuda.py   >> "$LOG" 2>&1

# 2) Commitear datos + HTML si cambiaron
git add vuelos.db movimientos.csv *.html Padron_aeronaves_provinciales.xlsx 2>/dev/null
if git diff --cached --quiet; then
    echo "  sin cambios, no se commitea" >> "$LOG"
    exit 0
fi
git commit -m "Datos ADS-B $(date '+%Y-%m-%d %H:%M') (VPS)" >> "$LOG" 2>&1

# 3) Push, con reintento rebase favoreciendo los datos del VPS
if ! git push origin main >> "$LOG" 2>&1; then
    echo "  push rechazado, rebase -X theirs y reintento" >> "$LOG"
    git pull --rebase -X theirs origin main >> "$LOG" 2>&1
    git push origin main >> "$LOG" 2>&1
fi
echo "  publicado OK" >> "$LOG"
