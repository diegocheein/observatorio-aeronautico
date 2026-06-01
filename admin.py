# -*- coding: utf-8 -*-
"""
Panel de administración (con contraseña) del padrón de aeronaves provinciales.
Permite listar, agregar, editar y borrar aeronaves, resolviendo hex y titular
automáticamente, y regenerar la planilla / mapa / reporte.

Requisitos:  pip install flask openpyxl
Contraseña:  variable de entorno ADMIN_PASSWORD (por defecto 'cambiar123' — ¡cambiala!)
Uso:         python3 admin.py     y abrir http://127.0.0.1:5000

Seguridad: es una herramienta local. Corrértela en localhost o detrás del firewall
del VPS; no exponerla a internet sin HTTPS y una contraseña fuerte.
"""
import os, csv, subprocess, functools
from flask import Flask, request, redirect, url_for, session, render_template_string, flash
from resolve_hex import reg_to_hex, hex_to_owner, guardar_cache

BASE = os.path.dirname(os.path.abspath(__file__))
PASSWORD = os.environ.get("ADMIN_PASSWORD", "cambiar123")
COLS = ["provincia","organismo","matricula","hex","tipo","categoria","estado",
        "confianza","titular_registrado","fuente","notas"]
DATASETS = {"provincial": "padron_aeronaves.csv", "dirigentes": "charters_dirigentes.csv"}
CONF_OPTS = ["VERIF. ANAC","CRUCE BD","ALTA","MEDIA","BAJA"]

app = Flask(__name__)
app.secret_key = os.environ.get("ADMIN_SECRET", os.urandom(24).hex())

# ---------- almacenamiento CSV ----------
def path(ds): return os.path.join(BASE, DATASETS.get(ds, DATASETS["provincial"]))
def load(ds):
    p = path(ds)
    if not os.path.exists(p): return []
    return list(csv.DictReader(open(p, encoding="utf-8")))
def save(ds, rows):
    with open(path(ds),"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader()
        for r in rows: w.writerow({k:r.get(k,"") for k in COLS})

# ---------- auth ----------
def login_required(f):
    @functools.wraps(f)
    def w(*a, **k):
        if not session.get("auth"): return redirect(url_for("login"))
        return f(*a, **k)
    return w

# ---------- plantillas ----------
BASEHTML = """<!doctype html><html lang=es><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Admin · Padrón aeronaves</title>
<style>
 :root{--azul:#1F4E79}*{box-sizing:border-box}body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#eef2f6;color:#1c2733}
 header{background:var(--azul);color:#fff;padding:12px 20px;display:flex;justify-content:space-between;align-items:center}
 header a{color:#cfe0f0;text-decoration:none;font-size:13px;margin-left:14px}
 .wrap{max-width:1150px;margin:18px auto;padding:0 16px}
 .card{background:#fff;border:1px solid #dde3ea;border-radius:10px;padding:16px;margin-bottom:16px}
 table{border-collapse:collapse;width:100%;font-size:13px}th,td{border:1px solid #e1e6ec;padding:6px 8px;text-align:left}
 th{background:var(--azul);color:#fff}tr:nth-child(even){background:#fafbfc}
 input,select,textarea{width:100%;padding:7px;border:1px solid #c8d2dd;border-radius:6px;font-size:13px}
 .grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
 label{font-size:11px;color:#5a6675;text-transform:uppercase}
 .btn{display:inline-block;background:var(--azul);color:#fff;border:none;border-radius:6px;padding:8px 14px;font-size:13px;cursor:pointer;text-decoration:none}
 .btn.alt{background:#fff;color:var(--azul);border:1px solid var(--azul)}
 .btn.red{background:#c0392b}.btn.sm{padding:4px 9px;font-size:12px}
 .flash{background:#fff7d6;border:1px solid #f0d97a;padding:8px 12px;border-radius:6px;margin-bottom:12px;font-size:13px}
 .tag{font-size:10px;font-weight:bold;padding:1px 7px;border-radius:9px}
 .tabs a{margin-right:10px;font-size:13px;text-decoration:none;color:var(--azul);font-weight:bold}
 .tabs a.act{border-bottom:3px solid var(--azul);padding-bottom:3px}
 .muted{color:#5a6675;font-size:12px}
</style></head><body>
<header><div><b>✈ Admin — Padrón aeronaves provinciales</b></div>
<div>{% if session.auth %}<a href="{{url_for('index',ds=ds)}}">Listado</a>
<a href="{{url_for('regen',ds=ds)}}" onclick="return confirm('¿Regenerar planilla, mapa y reporte?')">Regenerar salidas</a>
<a href="{{url_for('logout')}}">Salir</a>{% endif %}</div></header>
<div class=wrap>
{% with msgs=get_flashed_messages() %}{% if msgs %}{% for m in msgs %}<div class=flash>{{m}}</div>{% endfor %}{% endif %}{% endwith %}
{{ body|safe }}</div></body></html>"""

LOGIN = """
<div class=card style="max-width:360px;margin:60px auto">
 <h3>Ingresar</h3>
 <form method=post><label>Contraseña</label>
 <input type=password name=password autofocus>
 <p><button class=btn type=submit>Entrar</button></p></form>
 <p class=muted>Definí la contraseña con la variable ADMIN_PASSWORD.</p>
</div>"""

LIST = """
<div class=tabs style="margin-bottom:10px">
 <a href="{{url_for('index',ds='provincial')}}" class="{{'act' if ds=='provincial'}}">Flota provincial ({{n_prov}})</a>
 <a href="{{url_for('index',ds='dirigentes')}}" class="{{'act' if ds=='dirigentes'}}">Charters políticos/dirigentes ({{n_dir}})</a>
</div>
<div class=card>
 <a class=btn href="{{url_for('add',ds=ds)}}">+ Agregar aeronave</a>
 <span class=muted>&nbsp; {{rows|length}} aeronaves en este conjunto</span>
 <table style="margin-top:12px"><tr><th>Matrícula</th><th>Hex</th><th>Provincia/Ámbito</th><th>Tipo</th><th>Confianza</th><th>Titular (BD)</th><th></th></tr>
 {% for r in rows %}<tr>
   <td><b>{{r.matricula}}</b></td><td>{{r.hex}}</td><td>{{r.provincia}}</td><td>{{r.tipo}}</td>
   <td>{{r.confianza}}</td><td>{{r.titular_registrado}}</td>
   <td style=white-space:nowrap>
     <a class="btn alt sm" href="{{url_for('edit',ds=ds,i=loop.index0)}}">Editar</a>
     <form method=post action="{{url_for('delete',ds=ds,i=loop.index0)}}" style=display:inline onsubmit="return confirm('¿Borrar {{r.matricula}}?')">
       <button class="btn red sm" type=submit>Borrar</button></form>
   </td></tr>{% endfor %}
 </table>
</div>"""

FORM = """
<div class=card>
 <h3>{{'Editar' if editing else 'Agregar'}} aeronave — {{'flota provincial' if ds=='provincial' else 'charter dirigente'}}</h3>
 <form method=post>
  <div class=grid>
   <div><label>{{'Provincia' if ds=='provincial' else 'Ámbito / sector'}}</label><input name=provincia value="{{r.provincia}}"></div>
   <div><label>{{'Organismo / titular' if ds=='provincial' else 'Usuario (político/dirigente)'}}</label><input name=organismo value="{{r.organismo}}"></div>
   <div><label>Matrícula</label><input name=matricula value="{{r.matricula}}" placeholder="LV-XXX / LQ-XXX"></div>
   <div><label>Tipo de aeronave</label><input name=tipo value="{{r.tipo}}"></div>
   <div><label>Categoría</label><input name=categoria value="{{r.categoria}}" placeholder="avión / helicóptero"></div>
   <div><label>Estado</label><input name=estado value="{{r.estado}}" placeholder="activo / vendido / baja..."></div>
   <div><label>Confianza</label><select name=confianza>
     {% for c in conf %}<option value="{{c}}" {{'selected' if r.confianza==c}}>{{c}}</option>{% endfor %}</select></div>
   <div><label>Fuente</label><input name=fuente value="{{r.fuente}}"></div>
  </div>
  <p><label>Notas</label><textarea name=notas rows=2>{{r.notas}}</textarea></p>
  <label><input type=checkbox name=resolver value=1 checked style=width:auto> Resolver hex y titular automáticamente desde la matrícula</label>
  <p style=margin-top:14px><button class=btn type=submit>Guardar</button>
     <a class="btn alt" href="{{url_for('index',ds=ds)}}">Cancelar</a></p>
  {% if editing and r.hex %}<p class=muted>Hex actual: {{r.hex}} · Titular BD: {{r.titular_registrado or '—'}}</p>{% endif %}
 </form>
</div>"""

def render(tpl, **kw):
    inner = render_template_string(tpl, conf=CONF_OPTS, **kw)
    return render_template_string(BASEHTML, body=inner, **kw)

# ---------- rutas ----------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        if request.form.get("password")==PASSWORD:
            session["auth"]=True; return redirect(url_for("index", ds="provincial"))
        flash("Contraseña incorrecta.")
    return render(LOGIN, ds="provincial")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/")
@app.route("/<ds>")
@login_required
def index(ds="provincial"):
    if ds not in DATASETS: ds="provincial"
    return render(LIST, ds=ds, rows=load(ds),
                  n_prov=len(load("provincial")), n_dir=len(load("dirigentes")))

@app.route("/<ds>/add", methods=["GET","POST"])
@login_required
def add(ds):
    if request.method=="POST":
        rows=load(ds); rows.append(_from_form()); save(ds, rows)
        flash("Aeronave agregada."); return redirect(url_for("index", ds=ds))
    return render(FORM, ds=ds, editing=False, r={k:"" for k in COLS})

@app.route("/<ds>/edit/<int:i>", methods=["GET","POST"])
@login_required
def edit(ds, i):
    rows=load(ds)
    if i>=len(rows): flash("No existe."); return redirect(url_for("index", ds=ds))
    if request.method=="POST":
        rows[i]=_from_form(rows[i]); save(ds, rows)
        flash("Cambios guardados."); return redirect(url_for("index", ds=ds))
    return render(FORM, ds=ds, editing=True, r=rows[i])

@app.route("/<ds>/delete/<int:i>", methods=["POST"])
@login_required
def delete(ds, i):
    rows=load(ds)
    if i<len(rows):
        m=rows[i].get("matricula",""); rows.pop(i); save(ds, rows); flash(f"Borrada {m}.")
    return redirect(url_for("index", ds=ds))

@app.route("/<ds>/regen")
@login_required
def regen(ds):
    out=[]
    for script in ("build_xlsx.py","build_map.py","build_report.py"):
        try:
            r=subprocess.run(["python3", os.path.join(BASE,script)], capture_output=True, text=True, timeout=120)
            out.append(f"{script}: {'OK' if r.returncode==0 else 'ERROR '+r.stderr[-200:]}")
        except Exception as e:
            out.append(f"{script}: {e}")
    flash(" · ".join(out)); return redirect(url_for("index", ds=ds))

def _from_form(base=None):
    r = dict(base) if base else {k:"" for k in COLS}
    for f in ("provincia","organismo","matricula","tipo","categoria","estado","confianza","fuente","notas"):
        r[f]=request.form.get(f,"").strip()
    if request.form.get("resolver") and r["matricula"]:
        r["hex"]=reg_to_hex(r["matricula"])
        r["titular_registrado"],_=hex_to_owner(r["hex"]); guardar_cache()
    return r

if __name__=="__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
