# -*- coding: utf-8 -*-
"""
Vigía del Observatorio: revisa que el recolector y la publicación sigan andando
y avisa por Telegram cuando algo se cae (y cuando se recupera).

Corre en el VPS cada 10 min (systemd: observatorio-vigia.timer).
Necesita TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID (en /etc/observatorio-vigia.env).

Uso:
    python3 vigia.py            # revisa y avisa solo si cambió algo
    python3 vigia.py --prueba   # manda el estado actual por Telegram aunque esté todo bien
"""
import json, os, sys, time, shutil, subprocess, urllib.request, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
VIVO = os.path.join(BASE, "vivo.json")
ESTADO = os.path.join(BASE, ".vigia_estado.json")
SITIO = "https://diegocheein.github.io/observatorio-aeronautico/"
RECORDAR_CADA = 6 * 3600     # si sigue caído, repetir el aviso cada 6 h

def chequeos():
    """Devuelve {clave: descripción} de cada problema encontrado."""
    p = {}
    ahora = time.time()

    try:
        est = subprocess.run(["systemctl", "is-active", "observatorio-poller"],
                             capture_output=True, text=True).stdout.strip()
    except OSError as e:
        est = f"desconocido ({e})"
    if est != "active":
        p["poller"] = f"El recolector (observatorio-poller) está «{est}»."

    try:
        v = json.load(open(VIVO))
        edad = ahora - v.get("ts", 0)
        if edad > 5 * 60:
            p["vivo"] = f"El recolector no escribe datos hace {int(edad // 60)} min."
        sin_ok = ahora - (v.get("ultimo_ok") or v.get("ts", 0))
        if sin_ok > 15 * 60:
            p["fuente"] = (f"Las APIs ADS-B (adsb.lol / adsb.fi) no responden hace "
                           f"{int(sin_ok // 60)} min: no se registran vuelos.")
    except Exception as e:
        p["vivo"] = f"No se puede leer vivo.json ({e})."

    try:
        ct = int(subprocess.run(["git", "-C", BASE, "log", "-1", "--format=%ct"],
                                capture_output=True, text=True).stdout.strip())
        if ahora - ct > 40 * 60:
            p["publicar"] = f"No se publica nada hace {int((ahora - ct) // 60)} min (ver publicar.log)."
    except Exception as e:
        p["publicar"] = f"No se pudo leer el último commit ({e})."

    du = shutil.disk_usage("/")
    uso = du.used / du.total * 100
    if uso > 90:
        p["disco"] = f"Disco del VPS al {uso:.0f}% (quedan {du.free / 2**30:.1f} GB)."

    try:
        req = urllib.request.Request(SITIO + "vivo.json?t=%d" % ahora,
                                     headers={"User-Agent": "observatorio-vigia"})
        w = json.load(urllib.request.urlopen(req, timeout=20))
        edad = ahora - w.get("ts", 0)
        if edad > 60 * 60:
            p["web"] = f"La web publicada tiene datos de hace {int(edad // 60)} min (¿falla GitHub Pages?)."
    except Exception as e:
        p["web"] = f"No se puede abrir la web publicada ({e})."
    return p

def telegram(texto):
    tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        print("[vigia] faltan TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID; aviso no enviado:\n" + texto)
        return
    data = urllib.parse.urlencode({"chat_id": chat, "text": texto,
                                   "disable_web_page_preview": "true"}).encode()
    urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage", data, timeout=20)

def main():
    prueba = "--prueba" in sys.argv
    problemas = chequeos()
    try:
        antes = json.load(open(ESTADO))
    except Exception:
        antes = {"problemas": {}, "avisado": 0}
    ahora = time.time()
    nuevos = [k for k in problemas if k not in antes["problemas"]]
    resueltos = [k for k in antes["problemas"] if k not in problemas]
    recordar = problemas and ahora - antes.get("avisado", 0) > RECORDAR_CADA

    msg = []
    if problemas and (nuevos or recordar or prueba):
        msg.append("🔴 Observatorio Aeronáutico: hay problemas")
        msg += ["• " + d for d in problemas.values()]
        msg.append("Entrá al VPS: ssh cheques  (logs en /opt/observatorio/publicar.log)")
    if resueltos:
        msg.append("✅ Observatorio: se resolvió\n" +
                   "\n".join("• " + antes["problemas"][k] for k in resueltos))
    if prueba and not problemas:
        msg.append("✅ Observatorio Aeronáutico: todo funcionando (mensaje de prueba del vigía).")

    avisado = antes.get("avisado", 0)
    if msg:
        telegram("\n".join(msg) + "\n" + SITIO)
        avisado = ahora if problemas else 0
    json.dump({"problemas": problemas, "avisado": avisado}, open(ESTADO, "w"), ensure_ascii=False)
    print(f"[vigia] {len(problemas)} problema(s): {', '.join(problemas) or 'ninguno'}")

if __name__ == "__main__":
    main()
