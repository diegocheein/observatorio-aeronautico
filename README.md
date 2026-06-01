# Registro de aeronaves de gobiernos provinciales — Argentina

Proyecto periodístico/de investigación para **registrar por dónde se mueven las
aeronaves de los gobiernos provinciales argentinos**, a partir de datos públicos
ADS-B. Inspirado en el "Apocalypse Early Warning System" de Kyle McDonald, pero
enfocado en la flota oficial provincial.

## Cómo funciona (resumen)

1. Se arma un **padrón** de aeronaves provinciales (matrícula → código hex ICAO).
2. Un **recolector** consulta en vivo la red ADS-B (airplanes.live) por esos hex y
   guarda cada posición.
3. Un **analizador** agrupa las posiciones en vuelos (tramos) y les asigna
   aeropuerto de origen y destino.
4. Se generan **reportes**: planilla, reporte de movimientos y un mapa vivo.

```
padron_seed.py ──► resolve_hex.py ──► padron_aeronaves.csv  ──► build_xlsx.py ──► Padron_aeronaves_provinciales.xlsx
                                          │                                        (planilla, 5 pestañas)
                                          ▼
                       poller.py ──► vuelos.db ──► build_flights.py ──► movimientos.csv
                                                         │                    │
                                                         ▼                    ▼
                                                 build_report.py        build_map.py
                                                 reporte_movimientos.html   mapa_vivo.html
```

## Archivos

| Archivo | Qué es |
|---|---|
| `padron_seed.py` | Padrón fuente (lista `SEED` provincial + `DIRIGENTES` charters de políticos). Editá acá para sumar aeronaves. |
| `resolve_hex.py` | Resuelve el hex ICAO de cada matrícula y el titular registrado (vía hexdb.io). Genera `padron_aeronaves.csv` y `charters_dirigentes.csv`. Tiene caché (`.hex_cache.json`). |
| `padron_aeronaves.csv` | Padrón resuelto (matrícula, hex, tipo, provincia, confianza, titular registrado). |
| `build_xlsx.py` | Genera la planilla Excel con pestañas: Padrón completo, Flota propia, Charter o contratado, Charter políticos-dirigentes, Guía. |
| `Padron_aeronaves_provinciales.xlsx` | Planilla final (deliverable principal del padrón). |
| `airports_ar.csv` | Base de aeropuertos (Argentina + limítrofes, de OurAirports) con coordenadas. |
| `poller.py` | **Recolector**: consulta airplanes.live por los hex del padrón y guarda posiciones en `vuelos.db`. |
| `build_flights.py` | **Analizador**: convierte las posiciones en vuelos con origen/destino. Genera `movimientos.csv`. |
| `build_report.py` | Reporte visual de movimientos (`reporte_movimientos.html`): mapa de rutas + tablas + banderas. |
| `build_stats.py` | **Estadísticas** (`estadisticas.html`): aviones más activos, provincias, fin de semana, exterior y **encuentros** de aeronaves (alerta si 3+ en el mismo lugar y día). |
| `build_map.py` | **Mapa vivo** (`mapa_vivo.html`): aviones en su ubicación, rojo si vuelan, hover con datos, selección + historial por avión. |
| `admin.py` | **Panel web con contraseña** (Flask) para listar, agregar, editar y borrar aeronaves (flota provincial y charters de dirigentes), con resolución automática de hex/titular y botón para regenerar planilla/mapa/reporte. |

## Requisitos

- Python 3 (sólo librería estándar para poller/flights/report/map).
- `openpyxl` para la planilla: `pip install openpyxl`.
- Conexión a internet (airplanes.live para posiciones; hexdb.io para resolver hex).

## Uso

### Actualizar el padrón
1. Editá `padron_seed.py` (sumá filas a `SEED` o `DIRIGENTES`).
2. `python3 resolve_hex.py`  → completa hex y titular.
3. `python3 build_xlsx.py`   → regenera la planilla.

### Recolectar movimientos (correr de forma continua)
```bash
python3 poller.py            # loop continuo (consulta cada 60 s)
python3 poller.py --once     # una sola pasada (para cron)
```
> El recolector debe correr 24/7: ADS-B sólo da la posición *en el momento*; si no
> estás escuchando, ese vuelo no queda registrado. Recomendado: un VPS chico.

### Generar reportes
```bash
python3 build_flights.py     # vuelos.db -> movimientos.csv
python3 build_report.py      # -> reporte_movimientos.html
python3 build_map.py         # -> mapa_vivo.html
```

### Automatizar (ejemplo cron en el VPS)
```cron
# recolector como servicio (systemd) o:
*/1 * * * *  cd /ruta && python3 poller.py --once
# reportes cada mañana
0 7 * * *    cd /ruta && python3 build_flights.py && python3 build_report.py && python3 build_map.py
```

## Panel de administración (`admin.py`)

Para cargar/editar aeronaves sin tocar código.

```bash
pip install flask openpyxl
export ADMIN_PASSWORD="tu-clave-fuerte"   # ¡cambiá la default 'cambiar123'!
python3 admin.py                          # abrir http://127.0.0.1:5000
```

- Ingreso con contraseña (variable `ADMIN_PASSWORD`).
- Dos solapas: **Flota provincial** y **Charters políticos/dirigentes**.
- Agregar / editar / borrar aeronaves. Al guardar, resuelve **hex** y **titular
  registrado** automáticamente desde la matrícula (tildando la casilla).
- Botón **"Regenerar salidas"**: corre `build_xlsx.py`, `build_map.py` y `build_report.py`.
- Edita directamente los CSV (`padron_aeronaves.csv`, `charters_dirigentes.csv`), que
  pasan a ser la fuente viva. `padron_seed.py` queda como semilla inicial.
- **Seguridad**: es una herramienta local. Correrla en localhost o detrás del firewall
  del VPS; no exponerla a internet sin HTTPS y contraseña fuerte.

## El mapa vivo (`mapa_vivo.html`)

- Cada aeronave se dibuja con un **ícono de avión** rotado según el rumbo.
- **Rojo + pulso** = volando ahora (botón "Actualizar posiciones en vivo" consulta airplanes.live);
  **azul** = última posición conocida. La referencia de colores está sobre el mapa (abajo a la izq.).
- **Hover** sobre un avión → matrícula, provincia/ámbito, tipo y estado en vivo.
- **Dos selectores**: aeronaves **provinciales** y aeronaves **privadas / dirigentes**.
- **Historial filtrable por rango de fechas** (máx. 1 año). Cada vuelo muestra **advertencias**:
  `internacional`, `fin de semana`, `nocturno`, `uso privado presunto` (destino turístico/de ocio).
- Al elegir un vuelo del historial se dibuja la **ruta en gris con flechas de dirección**
  (origen → destino). Sin selección, el mapa sólo muestra los aviones en su ubicación.
- Nota: la actualización en vivo se hace desde el navegador; si airplanes.live bloquea
  por CORS, conviene servir el HTML desde el mismo servidor o usar un proxy simple.

## Despliegue en GitHub (Pages + Actions)

El proyecto incluye `requirements.txt`, `.gitignore`, `index.html` (portada) y un workflow
en `.github/workflows/deploy.yml`.

1. Crear un repo y subir todo: `git init && git add . && git commit -m "init" && git push`.
2. En el repo: **Settings → Pages → Source: GitHub Actions**.
3. El workflow corre cada ~15 min (y manualmente desde la pestaña *Actions*):
   recolecta una muestra en vivo, reconstruye `movimientos.csv`, el mapa y el reporte,
   commitea los datos y publica el sitio en Pages (portada con mapa y reporte).
4. La web queda en `https://<usuario>.github.io/<repo>/`.

Límite: GitHub Actions no corre exactamente al minuto (cron real ~5-15 min), así que la
captura es **parcial**. Para un historial 24/7 confiable, correr `poller.py` en un VPS
(o sumar ambos: VPS para recolectar + Pages para publicar). El **admin** (`admin.py`) se
usa localmente o en el VPS, no en Pages (Pages es estático).

## Niveles de confianza del padrón

- **VERIF. ANAC** — confirmado en consulta oficial de ANAC.
- **CRUCE BD** — titular confirmado en base de aviación (hexdb).
- **ALTA** — matrícula confirmada en fuente periodística / spotting.
- **MEDIA** — tipo confirmado, matrícula a verificar.
- **BAJA** — dato histórico, requiere verificación actual.

La columna **"Titular registrado (BD)"** permite detectar casos donde la matrícula
NO está a nombre de la provincia (banco, empresa, leasing, charter): el segundo
nivel de la investigación.

## Metodología y límites

- Origen/destino se infieren por **cercanía** al aeropuerto más próximo al
  despegue/aterrizaje (radio 25 km). Los helipuertos no siempre figuran.
- Las **banderas** del reporte (fin de semana, nocturno, internacional) son
  disparadores, no conclusiones: hay que cruzar con la agenda oficial del funcionario.
- Este registro es un **punto de partida**, no un padrón oficial cerrado. Toda
  publicación debería verificarse contra el Registro Nacional de Aeronaves (ANAC)
  y fuentes oficiales.

## Fuentes principales

- ADS-B en vivo: airplanes.live · Resolución hex/titular: hexdb.io
- Aeropuertos: OurAirports · Registro: ANAC (cad.anac.gob.ar)
- Prensa y spotting: La Nación, Gaceta Aeronáutica, Zona Militar, Airliners.net,
  Planespotters, boletines oficiales provinciales.
