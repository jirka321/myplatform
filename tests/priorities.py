# tests/priorities.py
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from sqlalchemy import func, or_
from models import db, LikertAnswer, DuelAnswer, ResultProfile
from .priorities_logic import (
    CATEGORIES, LIKERT_MIN, LIKERT_MAX,
    get_total_statements_count, get_statement_by_progress, get_statement_text,
    compute_likert_scores,
    rank_by_likert, select_topN_with_tiebreak,
    start_duels_for_top, duel_next_pair, duel_choose, duel_is_done, duel_get_insertion_order,
    pre_top_table, post_duel_hybrid_table,
    DuelState, TieBreakPlan,
    normalize_likert, compute_duel_strength, hybrid_score,
)

import base64, pickle

# --- Budget settings (each Likert score costs its value) ---
POOL = 280  # total points available in Likert phase
LAMBDA_HYBRID = 0.5  # váha pro hybrid (Likert kotva vs. síla duelů)

# --- Helpers pro (de)serializaci duelových stavů do session ---

def _dumps(obj) -> str:
    return base64.b64encode(pickle.dumps(obj)).decode("utf-8")


def _loads(s: str):
    return pickle.loads(base64.b64decode(s.encode("utf-8"))) if s else None


def _likert_sum(uid):
    """Sum of all Likert scores for the current user (this session-less MVP)."""
    total = (
        db.session.query(func.coalesce(func.sum(LikertAnswer.score), 0))
        .filter(or_(LikertAnswer.user_id == uid, LikertAnswer.user_id == str(uid)))
        .scalar()
    )
    return int(total or 0)


def _parse_qid(qid):
    """
    Parse composite q_id in format 'category|statement_index' (string) used by the modal.
    Returns tuple (category, statement_index) or (None, None) on failure.
    """
    if not qid or "|" not in qid:
        return (None, None)
    cat, idx = qid.split("|", 1)
    try:
        return cat, int(idx)
    except Exception:
        return (None, None)


bp = Blueprint("priorities", __name__, template_folder="../templates/priorities")


# ===================== ENTRY =====================
@bp.route("/", methods=["GET"])
def entry():
    """Jedna šablona, která zobrazí to, co ji pošleme (stage=auth/likert/duel/result)."""
    uid = session.get("user_id")
    if not uid:
        return render_template("test.html", stage="auth")

    # Pokud už máme hotové výsledky a lock na result, rovnou renderuj
    if session.get("force_stage") == "result" and session.get("result_rows"):
        return render_template("test.html", stage="result", rows=session["result_rows"])

    # ========== FÁZE 1: Likert ==========
    total = get_total_statements_count()
    answered = LikertAnswer.query.filter(or_(LikertAnswer.user_id == uid, LikertAnswer.user_id == str(uid))).count()
    if answered < total:
        stmt = get_statement_by_progress(answered)
        return render_template(
            "test.html",
            stage="likert",
            progress={"index": answered + 1, "total": total},
            data={
                "category_key": stmt["category_key"],
                "category_label": stmt["category_label"],
                "statement_index": stmt["statement_index"],
                "text": stmt["text"],
                "likert_min": LIKERT_MIN,
                "likert_max": LIKERT_MAX,
            },
        )

    # ========== Výpočty po Likertu ==========
    likert_rows = LikertAnswer.query.filter(or_(LikertAnswer.user_id == uid, LikertAnswer.user_id == str(uid))).all()
    score_map = compute_likert_scores(likert_rows)

    # 1) TIE-BREAK do TOP10 (duely jen v tie bandu, BEZ gated)
    # pokud ještě nemáme uložené top10_ids a neběží tie-break engine
    top10_ids = session.get("top10_ids")
    tb_state_s = session.get("tb_state")
    tb_slots = session.get("tb_slots")
    tb_guaranteed = session.get("tb_guaranteed")

    # Pokud už běží tie-break engine v session, pokračuj z něj
    if tb_state_s and not top10_ids:
        engine: DuelState = _loads(tb_state_s)
        if duel_is_done(engine):
            tb_slots = int(session.get("tb_slots", 0) or 0)
            tb_guaranteed = session.get("tb_guaranteed") or []
            ordered = duel_get_insertion_order(engine)
            winners = ordered[:tb_slots]
            session["top10_ids"] = tb_guaranteed + winners
            session.pop("tb_state", None)
            session.pop("tb_slots", None)
            session.pop("tb_guaranteed", None)
            return redirect(url_for("priorities.entry"))
        else:
            pair = duel_next_pair(engine)
            if not pair:
                return redirect(url_for("priorities.entry"))
            a, b = pair
            # DŮLEŽITÉ: uložit engine se `cur` po next_pair
            session["tb_state"] = _dumps(engine)
            return render_template(
                "test.html",
                stage="duel",
                progress={"index": engine.comparisons + 1, "total": engine.comparisons + 6},
                data={
                    "substage": "tiebreak",
                    "a": {"key": a, "label": CATEGORIES[a]["label"]},
                    "b": {"key": b, "label": CATEGORIES[b]["label"]},
                },
            )

    if not top10_ids:
        # žádný hotový TOP10 → zkus vybrat nebo rozjet tie-break
        # (bez voleb; volby poběží interaktivně přes /answer-duel)
        res_ids, plan = select_topN_with_tiebreak(score_map, CATEGORIES, top_n=10, tb_choices=None)
        if plan is None:
            # máme kompletní TOP10 hned
            session["top10_ids"] = res_ids
            top10_ids = res_ids
        else:
            # ulož tie-break engine do session a zobraz duelový pár z tie bandu
            session["tb_state"] = _dumps(plan.engine)
            session["tb_slots"] = plan.slots
            session["tb_guaranteed"] = plan.guaranteed_ids

            engine: DuelState = plan.engine
            pair = duel_next_pair(engine)
            if not pair:
                # nemělo by nastat, ale fallback: vrať se na GET
                return redirect(url_for("priorities.entry"))
            a, b = pair
            # uložit engine s nastaveným `cur`
            session["tb_state"] = _dumps(engine)
            return render_template(
                "test.html",
                stage="duel",
                progress={"index": engine.comparisons + 1, "total": engine.comparisons + 6},
                data={
                    "substage": "tiebreak",
                    "a": {"key": a, "label": CATEGORIES[a]["label"]},
                    "b": {"key": b, "label": CATEGORIES[b]["label"]},
                },
            )

    # 2) TOP10 DUELY s gated swapem
    top_duel_state_s = session.get("top_duel_state")
    if top10_ids and not top_duel_state_s:
        # inicializuj duely pro TOP10
        engine = start_duels_for_top(top10_ids, CATEGORIES)
        session["top_duel_state"] = _dumps(engine)
        top_duel_state_s = session["top_duel_state"]

    if top_duel_state_s:
        engine: DuelState = _loads(top_duel_state_s)
        if not duel_is_done(engine):
            pair = duel_next_pair(engine)
            if not pair:
                return redirect(url_for("priorities.entry"))
            a, b = pair
            # uložit engine s nastaveným `cur`
            session["top_duel_state"] = _dumps(engine)
            return render_template(
                "test.html",
                stage="duel",
                progress={"index": engine.comparisons + 1, "total": engine.comparisons + 12},
                data={
                    "substage": "top10",
                    "a": {"key": a, "label": CATEGORIES[a]["label"]},
                    "b": {"key": b, "label": CATEGORIES[b]["label"]},
                },
            )

        # duely dokončeny → výsledky: poskládej VŠECH 20 (TOP10 má duely, ostatní jen Likert)
        all_ids = list(CATEGORIES.keys())
        # normalizovaný Likert pro všechny
        l_norm_all = normalize_likert({k: score_map.get(k, 0) for k in all_ids})
        # duel strength: co nebylo v TOP10 duelech, má 0/0 (hladké dělení 0.5)
        d_stats = engine.duel_stats
        d_strength_all = {}
        for cid in all_ids:
            st = d_stats.get(cid, {"wins": 0, "comparisons": 0})
            d_strength_all[cid] = (st.get("wins", 0) + 0.5) / (st.get("comparisons", 0) + 1)
        s_all = hybrid_score(l_norm_all, d_strength_all, lam=LAMBDA_HYBRID)

        full_rows = []
        for cid in all_ids:
            full_rows.append({
                "rank": 0,
                "id": cid,
                "name": CATEGORIES[cid]["label"],
                "likert": int(score_map.get(cid, 0)),
                "wins": int(d_stats.get(cid, {}).get("wins", 0)),
                "hybrid": float(s_all.get(cid, 0.5)),
            })
        full_rows.sort(key=lambda r: (-r["hybrid"], r["name"]))
        for i, r in enumerate(full_rows, start=1):
            r["rank"] = i

        _persist_results(uid, full_rows)
        session["result_rows"] = [{
            "rank": r["rank"],
            "category_label": r["name"],
            "category_key": r["id"],
            "wins": r["wins"],
            "likert": r["likert"],
        } for r in full_rows]
        session["force_stage"] = "result"

        # uklid flow klíčů
        session.pop("top_duel_state", None)
        session.pop("tb_state", None)
        session.pop("tb_slots", None)
        session.pop("tb_guaranteed", None)

        return render_template("test.html", stage="result", rows=session["result_rows"])

    # Bezpečný fallback: ukaž všech 20 podle Likertu (bez duelů), a zamkni result
    all_ids = list(CATEGORIES.keys())
    l_norm_all = normalize_likert({k: score_map.get(k, 0) for k in all_ids})
    full_rows = []
    for cid in all_ids:
        full_rows.append({
            "rank": 0,
            "id": cid,
            "name": CATEGORIES[cid]["label"],
            "likert": int(score_map.get(cid, 0)),
            "wins": 0,
            "hybrid": float(l_norm_all.get(cid, 0.5)),
        })
    full_rows.sort(key=lambda r: (-r["hybrid"], r["name"]))
    for i, r in enumerate(full_rows, start=1):
        r["rank"] = i

    _persist_results(uid, full_rows)
    session["result_rows"] = [{
        "rank": r["rank"],
        "category_label": r["name"],
        "category_key": r["id"],
        "wins": r["wins"],
        "likert": r["likert"],
    } for r in full_rows]
    session["force_stage"] = "result"

    return render_template("test.html", stage="result", rows=session["result_rows"])


# ===================== ANSWERS =====================
@bp.route("/answer-likert", methods=["POST"])
def answer_likert():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("priorities.entry"))

    cat = request.form.get("category_key")
    # Safe parse: if fields are missing (e.g., all radios disabled), just re-render
    try:
        idx_raw = request.form.get("statement_index")
        score_raw = request.form.get("score")
        if idx_raw is None or score_raw is None:
            return redirect(url_for("priorities.entry"))
        idx = int(idx_raw)
        score = int(score_raw)
    except (TypeError, ValueError):
        return redirect(url_for("priorities.entry"))
    score = max(LIKERT_MIN, min(LIKERT_MAX, score))

    # Budget validation: sum of all other answers + new score must be <= POOL
    spent_without_this = (
        db.session.query(func.coalesce(func.sum(LikertAnswer.score), 0))
        .filter(LikertAnswer.user_id == uid)
        .filter(~((LikertAnswer.category == cat) & (LikertAnswer.statement_index == idx)))
        .scalar()
        or 0
    )
    if int(spent_without_this) + int(score) > POOL:
        # If over budget, just re-render current page without saving
        return redirect(url_for("priorities.entry"))

    # Upsert: update existing answer for this (category, statement_index), otherwise insert
    existing = LikertAnswer.query.filter_by(user_id=uid, category=cat, statement_index=idx).first()
    if existing:
        existing.score = score
    else:
        db.session.add(LikertAnswer(user_id=uid, category=cat, statement_index=idx, score=score))
    db.session.commit()
    return redirect(url_for("priorities.entry"))


@bp.route("/answer-duel", methods=["POST"])
def answer_duel():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("priorities.entry"))

    a = request.form.get("a_key")
    b = request.form.get("b_key")
    chosen = request.form.get("chosen_key")
    if chosen not in (a, b):
        return redirect(url_for("priorities.entry"))

    # Volitelné: logovat do DB (audit trail)
    db.session.add(DuelAnswer(user_id=uid, option_a=a, option_b=b, chosen=chosen))
    db.session.commit()

    # TIE-BREAK fáze?
    tb_state_s = session.get("tb_state")
    if tb_state_s:
        engine: DuelState = _loads(tb_state_s)
        # v tie-breaku je gating vypnutý
        loser = a if chosen == b else b
        duel_choose(engine, chosen, loser, gated=False)
        if duel_is_done(engine):
            # hotovo → doplň vítěze do top10 a přepni na TOP10 duely
            tb_slots = int(session.get("tb_slots", 0) or 0)
            tb_guaranteed = session.get("tb_guaranteed") or []
            ordered = duel_get_insertion_order(engine)
            winners = ordered[:tb_slots]
            top10_ids = tb_guaranteed + winners
            session["top10_ids"] = top10_ids
            session.pop("tb_state", None)
            session.pop("tb_slots", None)
            session.pop("tb_guaranteed", None)
            # inicializace TOP10 duelů proběhne v GET /
            return redirect(url_for("priorities.entry"))
        else:
            # pokračujeme v tie-breaku
            session["tb_state"] = _dumps(engine)
            return redirect(url_for("priorities.entry"))

    # TOP10 fáze (gated)
    top_state_s = session.get("top_duel_state")
    if top_state_s:
        engine: DuelState = _loads(top_state_s)
        loser = a if chosen == b else b
        duel_choose(engine, chosen, loser, gated=True)
        session["top_duel_state"] = _dumps(engine)
        return redirect(url_for("priorities.entry"))

    # Fallback
    return redirect(url_for("priorities.entry"))


# ===================== REORDER TOP5 =====================
@bp.route("/reorder", methods=["POST"])
def reorder_top5():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Nejste přihlášen"}), 401

    payload = request.get_json(silent=True) or {}
    order = payload.get("order")
    if not isinstance(order, list) or len(order) != 5 or not all(isinstance(k, str) for k in order):
        return jsonify({"error": "Očekávám list 5 kategorií (keys)"}), 400

    # Nacti aktualni TOP5 z ResultProfile pro daneho usera
    top5 = (
        ResultProfile.query
        .filter(or_(ResultProfile.user_id == uid, ResultProfile.user_id == str(uid)))
        .filter(ResultProfile.rank <= 5)
        .all()
    )
    if len(top5) != 5:
        # Fallback 1: vezmi prvních 5 podle rank ASC, i kdyby ranky měly díry
        top5_any = (
            ResultProfile.query
            .filter(or_(ResultProfile.user_id == uid, ResultProfile.user_id == str(uid)))
            .order_by(ResultProfile.rank.asc())
            .limit(5)
            .all()
        )
        if len(top5_any) == 5:
            top5 = top5_any
        else:
            # Fallback 2: zkus vyrobit TOP5 ze session result_rows, pokud existují
            rows_sess = session.get("result_rows") or []
            if len(rows_sess) >= 5:
                # mapování key->label
                key_to_label = {r.get("category_key"): r.get("category_label") for r in rows_sess if r.get("category_key")}
                # doplň přes CATEGORIES
                for k in order:
                    if k not in key_to_label and k in CATEGORIES:
                        key_to_label[k] = CATEGORIES[k]["label"]
                # smaž existující prvních 5 a vlož nové podle požadovaného order
                ResultProfile.query.filter(or_(ResultProfile.user_id == uid, ResultProfile.user_id == str(uid))).filter(ResultProfile.rank <= 5).delete(synchronize_session=False)
                for idx, key in enumerate(order[:5], start=1):
                    lbl = key_to_label.get(key) or CATEGORIES.get(key, {}).get("label") or key
                    db.session.add(ResultProfile(user_id=uid, rank=idx, category=lbl, score=0.0))
                db.session.commit()
                top5 = (
                    ResultProfile.query
                    .filter(or_(ResultProfile.user_id == uid, ResultProfile.user_id == str(uid)))
                    .filter(ResultProfile.rank <= 5)
                    .order_by(ResultProfile.rank.asc())
                    .all()
                )
            else:
                return jsonify({"error": "TOP5 výsledků není připraveno"}), 400

    # Preved poradi keys -> labels podle CATEGORIES
    try:
        labels_in_order = [CATEGORIES[k]["label"] for k in order]
    except KeyError:
        return jsonify({"error": "Neznámý klíč kategorie v order"}), 400

    # Over, ze sada se shoduje s aktualnimi top5 labely
    current_labels = {r.category for r in top5}
    if set(labels_in_order) != current_labels:
        return jsonify({"error": "Sada kategorií nesouhlasí s aktuální TOP5"}), 400

    by_label = {r.category: r for r in top5}
    # 1) dočasně posuň ranky, aby nedošlo ke kolizi unique(user_id, rank)
    for idx, label in enumerate(labels_in_order, start=1):
        by_label[label].rank = 100 + idx
    db.session.flush()
    # 2) nastav finální ranky 1..5 v novém pořadí
    for idx, label in enumerate(labels_in_order, start=1):
        by_label[label].rank = idx

    db.session.commit()

    # Aktualizuj i session["result_rows"], jinak se UI po refreshi nehne
    rows = session.get("result_rows") or []
    if rows:
        # mapuj podle category_key
        key_to_row = {r.get("category_key"): r for r in rows}
        # nové TOP5 podle zadaného order
        new_top5 = [key_to_row[k] for k in order if k in key_to_row]
        # zbytek v původním pořadí
        rest = [r for r in rows if r.get("category_key") not in set(order)]
        new_rows = new_top5 + rest
        # přepočítej ranky 1..N
        for i, r in enumerate(new_rows, start=1):
            r["rank"] = i
        session["result_rows"] = new_rows

    session["force_stage"] = "result"
    return jsonify({"message": "Pořadí bylo uloženo"})


# ===================== REVIEW & ADJUST =====================
@bp.get("/review")
def review_answers():
    """
    Return remaining budget and the list of answered Likert items for the current user.
    Supports ?costly=1 to filter scores >= 3 (on 1–4 scale).
    """
    uid = session.get("user_id")
    if not uid:
        return jsonify({"remaining": POOL, "items": []})

    costly = request.args.get("costly") in ("1", "true", "yes")
    q = LikertAnswer.query.filter(or_(LikertAnswer.user_id == uid, LikertAnswer.user_id == str(uid)))
    if costly:
        q = q.filter(LikertAnswer.score >= 3)

    # Order: high score first, then by statement_index desc (proxy for recency)
    rows = q.order_by(LikertAnswer.score.desc(), LikertAnswer.statement_index.desc()).all()

    # Build items for modal; q_id is "category|statement_index"
    items = []
    for r in rows:
        text = get_statement_text(r.category, int(r.statement_index))
        items.append({
            "q_id": f"{r.category}|{r.statement_index}",
            "text": text,
            "value": int(r.score),
        })

    remaining = POOL - _likert_sum(uid)
    return jsonify({"remaining": max(0, int(remaining)), "items": items})


@bp.post("/adjust")
def adjust_answer():
    """
    Adjust a previously answered Likert item to a new score, respecting the POOL.
    Expects JSON: { "q_id": "category|statement_index", "new_value": <int> }
    """
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Nejste přihlášen"}), 401

    data = request.get_json(silent=True) or {}
    qid = data.get("q_id")
    new_value = data.get("new_value")

    cat, idx = _parse_qid(qid)
    if not cat or not isinstance(new_value, int):
        return jsonify({"error": "Neplatný vstup"}), 400

    # Clamp to allowed range
    new_value = max(LIKERT_MIN, min(LIKERT_MAX, int(new_value)))

    # Sum of all except this item
    spent_wo = (
        db.session.query(func.coalesce(func.sum(LikertAnswer.score), 0))
        .filter(or_(LikertAnswer.user_id == uid, LikertAnswer.user_id == str(uid)))
        .filter(~((LikertAnswer.category == cat) & (LikertAnswer.statement_index == idx)))
        .scalar()
        or 0
    )

    if int(spent_wo) + int(new_value) > POOL:
        remaining = POOL - int(spent_wo)
        return jsonify({"error": "Nedostatek bodů", "remaining": max(0, remaining)}), 400

    # Upsert the answer
    existing = (LikertAnswer.query
                .filter(or_(LikertAnswer.user_id == uid, LikertAnswer.user_id == str(uid)))
                .filter(LikertAnswer.category == cat, LikertAnswer.statement_index == idx)
                .first())
    if existing:
        existing.score = new_value
    else:
        db.session.add(LikertAnswer(user_id=uid, category=cat, statement_index=idx, score=new_value))
    db.session.commit()

    remaining = POOL - _likert_sum(uid)
    return jsonify({"ok": True, "remaining": max(0, int(remaining))})


# ===================== RESTART =====================
@bp.route("/restart", methods=["POST", "GET"])  # allow both for simplicity
def restart_priorities():
    uid = session.get("user_id")
    # Always clear session flow keys regardless of login state (except user_id)
    for k in ("top10_ids", "tb_state", "tb_slots", "tb_guaranteed", "top_duel_state", "result_rows", "force_stage"):
        session.pop(k, None)
    session.modified = True

    if not uid:
        # Not logged in → just go to entry which will show auth stage
        return redirect(url_for("priorities.entry"))

    # Wipe user data for a clean start
    try:
        LikertAnswer.query.filter(or_(LikertAnswer.user_id == uid, LikertAnswer.user_id == str(uid))).delete(synchronize_session=False)
        DuelAnswer.query.filter(or_(DuelAnswer.user_id == uid, DuelAnswer.user_id == str(uid))).delete(synchronize_session=False)
        ResultProfile.query.filter(or_(ResultProfile.user_id == uid, ResultProfile.user_id == str(uid))).delete(synchronize_session=False)
        db.session.commit()
    except Exception:
        db.session.rollback()

    return redirect(url_for("priorities.entry"))

# ===================== INTERNAL: persist results =====================

def _persist_results(uid: int, rows: list[dict]):
    """Zapiš/aktualizuj ResultProfile pro daného uživatele podle `rows`.
    Očekává položky obsahující alespoň: rank, id (category_key) nebo name (label).
    """
    # reverzní mapa label -> key (ResultProfile historicky ukládá label)
    label_to_key = {v["label"]: k for k, v in CATEGORIES.items()}

    existing = (ResultProfile.query
                .filter(or_(ResultProfile.user_id == uid, ResultProfile.user_id == str(uid)))
                .order_by(ResultProfile.rank.asc())
                .all())
    if not existing:
        # poprvé: založ podle dodaného pořadí
        for r in rows:
            cid = r.get("id")
            name = r.get("name") or (CATEGORIES[cid]["label"] if cid in CATEGORIES else None)
            if not name:
                continue
            db.session.add(ResultProfile(
                user_id=uid,
                rank=int(r.get("rank", 0) or 0),
                category=name,
                score=float(r.get("hybrid", r.get("likert", 0)) or 0.0),
            ))
        db.session.commit()
    else:
        # update skóre, rank zachovat pokud již existuje ruční pořadí
        by_rank = {rp.rank: rp for rp in existing}
        for r in rows:
            rank = int(r.get("rank", 0) or 0)
            cid = r.get("id")
            name = r.get("name") or (CATEGORIES[cid]["label"] if cid in CATEGORIES else None)
            if rank in by_rank and name:
                by_rank[rank].category = name
                by_rank[rank].score = float(r.get("hybrid", r.get("likert", 0)) or 0.0)
        db.session.commit()
