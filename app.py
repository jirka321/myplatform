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
    # Landing page is now a standalone template
    return render_template("lp.html")

# ---------- AUTH PAGE ----------
@app.route("/auth", methods=["GET"])
def auth_page():
    # Legacy path kept for backward compatibility
    return redirect(url_for("login_page"))

@app.route("/login", methods=["GET"])
def login_page():
    # Render the standalone login template
    return render_template("login.html", show_home=True)

# ---------- helpers ----------

# Clear all Priorities-related session keys (flow state)
def clear_priorities_session():
    for k in (
        "top10_ids",
        "tb_state",
        "tb_slots",
        "tb_guaranteed",
        "top_duel_state",
        "priorities_progress",
        "priorities_stage",
        # keys used by priorities blueprint to lock Result screen
        "result_rows",
        "force_stage",
    ):
        session.pop(k, None)

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
    clear_priorities_session()
    session["user_id"] = u.id
    return jsonify({"message":"Registrace OK", "user_id":u.id})

@app.route("/login", methods=["POST"])
def login_api():
    data = request.get_json(force=True)
    email = data.get("email"); password = data.get("password")
    u = User.query.filter_by(email=email).first()
    if u and u.password == password:
        clear_priorities_session()
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
def logout():
    session.clear()
    clear_priorities_session()
    return redirect(url_for("login_page"))

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

# ---------- pretty URL for standalone results ----------
@app.route('/results', methods=['GET'])
def results_redirect():
    # Redirect to the blueprint's results page
    return redirect(url_for('priorities.standalone_results'))
# ---------- zaregistruj test jako modul ----------
app.register_blueprint(priorities_bp, url_prefix="/priorities")

if __name__ == "__main__":
    app.run(debug=True)
