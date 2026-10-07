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
# (de a uno: si falta un archivo, un solo "git add" con todos no agrega ninguno)
for f in vuelos.db movimientos.csv vivo.json *.html Padron_aeronaves_provinciales.xlsx; do
    [ -e "$f" ] && git add "$f"
done
if git diff --cached --quiet; then
    echo "  sin cambios, no se commitea" >> "$LOG"
    exit 0
fi
git commit -m "Datos ADS-B $(date '+%Y-%m-%d %H:%M') (VPS)" >> "$LOG" 2>&1

# 3) Push, con reintento rebase favoreciendo los datos del VPS
if ! git push origin main >> "$LOG" 2>&1; then
    echo "  push rechazado, rebase -X theirs y reintento" >> "$LOG"
    git pull --rebase --autostash -X theirs origin main >> "$LOG" 2>&1
    git push origin main >> "$LOG" 2>&1
fi
echo "  publicado OK" >> "$LOG"

# 4) Cada publicacion suma una copia de vuelos.db al historial: si .git pasa de
#    500 MB, dejar solo el ultimo commit (GitHub conserva el historial completo).
#    En sep-2026 el historial llego a 2,9 GB y lleno el disco del VPS.
if [ "$(du -sm .git | cut -f1)" -gt 500 ]; then
    echo "  .git > 500 MB, recortando historial local" >> "$LOG"
    git fetch -q --depth=1 origin main >> "$LOG" 2>&1 && \
    git reflog expire --expire=now --all && git gc -q --prune=now >> "$LOG" 2>&1
fi
