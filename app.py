# app.py
# Add dotenv and database URL loading
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from models import db, init_db, User
from models import ResultProfile, LikertAnswer, DuelAnswer
from tests.priorities import bp as priorities_bp

app = Flask(__name__)
app.secret_key = "change_this_in_production_super_secret_key"
init_db(app)

# ---------- rozcestník ----------
@app.route("/")
def home():
    return """
    <h1>MyPlatform</h1>
    <p>Server běží.</p>
    <p><a href='/auth'>Přihlásit / Registrovat</a></p>
    <p><a href='/priorities/'>Priorities test</a> (vyžaduje přihlášení)</p>
    """

# ---------- AUTH PAGE ----------
@app.route("/auth", methods=["GET"])
def auth_page():
    return """
<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Přihlášení / Registrace</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@500;700&family=Work+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root{
      --text:#0f1a24;
      --muted:#4b6b88;
      --border:rgba(0,0,0,.08);
      --accent-a:#0090ff;
      --accent-b:#26b0ff;
    }

    html,body{height:100%}
    body{ margin:0; background:#ffffff; color:var(--text); font-family:"Work Sans", system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Arial; overflow-x:hidden; }

    .bg{ position:fixed; inset:-20vh -20vw -20vh -20vw; pointer-events:none; z-index:0; overflow:hidden; }
    .bg::before{ content:""; position:absolute; width:82vmin; height:82vmin; left:50%; top:46%; transform:translate(-50%,-50%); background:radial-gradient(circle at 50% 50%, rgba(0,185,255,.44) 0%, rgba(92,122,255,.40) 33%, rgba(255,120,200,.30) 58%, rgba(0,0,0,0) 72%); filter: blur(120px); opacity:.92; }
    .bg::after{ content:""; position:absolute; width:48vmin; height:48vmin; left:50%; top:46%; transform:translate(-50%,-50%); background:radial-gradient(circle at 50% 50%, rgba(255,255,255,.80) 0%, rgba(255,255,255,.0) 60%); filter: blur(30px); opacity:.9; }

    .wrap{ position:relative; z-index:1; min-height:100%; display:flex; align-items:center; justify-content:center; padding:6vh 4vw; }
    .glass{ width:min(560px, 100%); border-radius:20px; background: transparent; border: none; box-shadow: none; backdrop-filter: none; -webkit-backdrop-filter: none; }
    .card{ padding:18px 20px; border:1px solid rgba(0,0,0,.06); border-radius:18px; background:rgba(255,255,255,.65); box-shadow:0 8px 22px rgba(15,27,36,.07); backdrop-filter: blur(16px) saturate(140%); -webkit-backdrop-filter: blur(16px) saturate(140%); }

    header{ display:flex; align-items:center; justify-content:space-between; gap:16px; padding:18px 22px; border-bottom:1px solid var(--border) }
    .brand{ display:flex; align-items:center; gap:10px; font-family:'Quicksand', sans-serif; font-weight:800; letter-spacing:.4px; }
    .pill{ border:1px solid rgba(0,120,255,.18); background:rgba(0,120,255,.08); border-radius:999px; padding:6px 12px; font-size:12px; color:#0f3555; }

    main{ padding:22px 22px 26px }
    h1{ font-family:'Quicksand', sans-serif; margin:0 0 8px; font-size:28px }
    .kicker{ color:var(--muted); font-size:14px; margin-bottom:16px }

    .row{ margin:10px 0 }
    input{
      width: calc(100% - 20px);
      max-width: 500px;
      padding: 12px 14px;
      border-radius: 12px;
      border: 1px solid rgba(15,27,36,.10);
      background: #fff;
      color: #0f1a24;
      outline: none;
      display: block;
      margin: 0 auto;
      box-shadow:0 1px 0 rgba(15,27,36,.04);
    }
    input::placeholder{ color:#5d7b96 }

    .controls{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin-top:16px }
    .btn{ border:none; padding:12px 18px; border-radius:999px; font-family:'Quicksand', sans-serif; font-weight:800; cursor:pointer; }
    .btn.primary{ color:#00150b; background:linear-gradient(90deg, var(--accent-a), var(--accent-b)); }
    .btn.secondary{ background:#fff; border:1px solid rgba(15,27,36,.12); color:#0f1a24 }
    .msg{ font-size:13px; color:#b04a2a; min-height:18px }

    .page-logo { position: fixed; top: 20px; left: 24px; font-family: 'Quicksand', sans-serif; font-weight: 700; font-size: 23px; letter-spacing: 1px; color: #0f1a24; text-transform: uppercase; z-index: 10; }
  </style>
</head>
<body>
  <div class="page-logo">PROTOKOL</div>
  <div class="bg"></div>
  <div class="wrap">
    <div class="glass">
      <div class="card">
        <header>
          <div class="brand"><span class="pill">UX</span><span class="pill">UI</span><span>&nbsp;AUTH</span></div>
          <div><a href="/" style="color:#0f3555;text-decoration:none;font-size:14px">Domů</a></div>
        </header>
        <main>
          <h1>Přihlášení / Registrace</h1>
          <div class="kicker">Po úspěchu tě hned pošlu na Priorities test.</div>

          <div class="row"><input id="email" type="email" placeholder="Email"></div>
          <div class="row"><input id="password" type="password" placeholder="Heslo"></div>

          <div class="controls">
            <button class="btn secondary" id="btn-login">Přihlásit</button>
            <button class="btn primary" id="btn-register">Registrovat</button>
          </div>

          <div class="row msg" id="msg"></div>
          <div class="kicker">Nebo pokračuj na <a href="/priorities/" style="color:#0f3555">/priorities/</a> pokud už máš session.</div>
        </main>
      </div>
    </div>
  </div>

  <script>
    const $ = s => document.querySelector(s);
    async function call(url, body) {
      try {
        const r = await fetch(url, { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(body) });
        const j = await r.json();
        if (j.message) { location.href = "/priorities/"; }
        else { $("#msg").textContent = j.error || "Chyba"; }
      } catch(e) {
        $("#msg").textContent = "Server nedostupný";
      }
    }
    $("#btn-login").onclick = () => call("/login", { email: $("#email").value.trim(), password: $("#password").value.trim() });
    $("#btn-register").onclick = () => call("/register", { email: $("#email").value.trim(), password: $("#password").value.trim() });
  </script>
</body>
</html>
"""

# ---------- helpers ----------

def get_current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)

def require_admin_or_403():
    u = get_current_user()
    if not u or not getattr(u, "is_admin", False):
        # minimal 403 page
        return ("<h1>403</h1><p>Přístup pouze pro administrátora.</p>", 403)
    return None

# ---------- AUTH JSON ----------
@app.route("/register", methods=["POST"])
def register_api():
    data = request.get_json(force=True)
    email = data.get("email"); password = data.get("password")
    if not email or not password:
        return jsonify({"error":"Email a heslo jsou povinné"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error":"Email už existuje"}), 400
    u = User(email=email, password=password)
    db.session.add(u); db.session.commit()
    session["user_id"] = u.id
    return jsonify({"message":"Registrace OK", "user_id":u.id})

@app.route("/login", methods=["POST"])
def login_api():
    data = request.get_json(force=True)
    email = data.get("email"); password = data.get("password")
    u = User.query.filter_by(email=email).first()
    if u and u.password == password:
        session["user_id"] = u.id
        return jsonify({"message":"Login OK", "user_id":u.id})
    return jsonify({"error":"Špatný email nebo heslo"}), 401

# Alias routes for old/new frontend paths
@app.route("/api/register", methods=["POST"])
def api_register_alias():
    return register_api()

@app.route("/api/login", methods=["POST"])
def api_login_alias():
    return login_api()

@app.route("/logout", methods=["POST"])
def logout_api():
    session.clear()
    return jsonify({"message":"Odhlášeno"})

# ---------- ADMIN PREHLED (chráněný) ----------
@app.route("/admin")
def admin_index():
    guard = require_admin_or_403()
    if guard: return guard
    users = User.query.order_by(User.id.asc()).all()
    rows = "".join([
        f"<tr><td>{u.id}</td><td>{u.email}</td><td>{'✔️' if getattr(u,'is_admin',False) else ''}</td>"
        f"<td><a href='/admin/user/{u.id}'>detail</a></td></tr>" for u in users
    ])
    return f"""
    <style>
      body{{font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; padding:24px;}}
      table{{border-collapse: collapse; width: 100%; max-width: 900px}}
      th,td{{border:1px solid #ddd; padding:8px; text-align:left}}
      th{{background:#f7f7f7}}
      a{{text-decoration:none}}
    </style>
    <h1>Uživatelé</h1>
    <table>
      <thead><tr><th>ID</th><th>Email</th><th>Admin</th><th>Akce</th></tr></thead>
      <tbody>{rows or "<tr><td colspan='4'>Žádní uživatelé</td></tr>"}</tbody>
    </table>
    """

@app.route("/admin/user/<int:user_id>")
def admin_user_detail(user_id):
    guard = require_admin_or_403()
    if guard: return guard
    u = User.query.get_or_404(user_id)

    results = ResultProfile.query.filter_by(user_id=user_id).order_by(ResultProfile.rank.asc()).all()
    likerts = LikertAnswer.query.filter_by(user_id=user_id).order_by(LikertAnswer.category.asc(), LikertAnswer.statement_index.asc()).all()
    duels   = DuelAnswer.query.filter_by(user_id=user_id).all()

    res_rows = "".join([
        f"<tr><td>{r.rank}</td><td>{r.category}</td><td>{int(r.score) if r.score is not None else ''}</td></tr>" for r in results
    ])
    lik_rows = "".join([
        f"<tr><td>{la.category}</td><td>{la.statement_index}</td><td>{la.score}</td></tr>" for la in likerts
    ])
    duel_rows = "".join([
        f"<tr><td>{d.option_a}</td><td>{d.option_b}</td><td><b>{d.chosen}</b></td></tr>" for d in duels
    ])

    return f"""
    <style>
      body{{font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; padding:24px; max-width:1100px}}
      h1,h2{{margin:0 0 8px}}
      .muted{{color:#666; margin-bottom:16px}}
      section{{margin:22px 0}}
      table{{border-collapse: collapse; width: 100%}}
      th,td{{border:1px solid #ddd; padding:8px; text-align:left; vertical-align: top}}
      th{{background:#f7f7f7}}
      .back{{margin-bottom:12px; display:inline-block}}
    </style>
    <a class="back" href="/admin">← zpět na seznam</a>
    <h1>Uživatel #{u.id}</h1>
    <div class="muted">{u.email}</div>

    <section>
      <h2>Seřazené priority (výstup)</h2>
      <table>
        <thead><tr><th>#</th><th>Kategorie</th><th>Kombinované skóre</th></tr></thead>
        <tbody>{res_rows or "<tr><td colspan='3'>Zatím nic</td></tr>"}</tbody>
      </table>
    </section>

    <section>
      <h2>Likert odpovědi</h2>
      <table>
        <thead><tr><th>Kategorie (klíč)</th><th>Index výroku</th><th>Hodnota</th></tr></thead>
        <tbody>{lik_rows or "<tr><td colspan='3'>Zatím nic</td></tr>"}</tbody>
      </table>
    </section>

    <section>
      <h2>Duely</h2>
      <table>
        <thead><tr><th>Možnost A</th><th>Možnost B</th><th>Zvoleno</th></tr></thead>
        <tbody>{duel_rows or "<tr><td colspan='3'>Zatím nic</td></tr>"}</tbody>
      </table>
    </section>
    """

# ---------- zaregistruj test jako modul ----------
app.register_blueprint(priorities_bp, url_prefix="/priorities")

if __name__ == "__main__":
    app.run(debug=True)
