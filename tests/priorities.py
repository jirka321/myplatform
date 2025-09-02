# tests/priorities.py
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models import db, LikertAnswer, DuelAnswer, ResultProfile
from .priorities_logic import (
    CATEGORIES, LIKERT_MIN, LIKERT_MAX,
    get_total_statements_count, get_statement_by_progress,
    compute_likert_scores, top_n_categories, generate_duel_pairs_from_top,
    duel_score, combine_final_ranking
)

bp = Blueprint("priorities", __name__, template_folder="../templates/priorities")

@bp.route("/", methods=["GET"])
def entry():
    """Jedna šablona, která zobrazí to, co ji pošleme (stage=auth/likert/duel/result)."""
    uid = session.get("user_id")
    if not uid:
        return render_template("test.html", stage="auth")

    # Likert fáze
    total = get_total_statements_count()
    answered = LikertAnswer.query.filter_by(user_id=uid).count()
    if answered < total:
        stmt = get_statement_by_progress(answered)
        return render_template("test.html", stage="likert",
                               progress={"index": answered+1, "total": total},
                               data={
                                   "category_key": stmt["category_key"],
                                   "category_label": stmt["category_label"],
                                   "statement_index": stmt["statement_index"],
                                   "text": stmt["text"],
                                   "likert_min": LIKERT_MIN,
                                   "likert_max": LIKERT_MAX
                               })

    # Duely
    likert_rows = LikertAnswer.query.filter_by(user_id=uid).all()
    score_map = compute_likert_scores(likert_rows)
    top10 = top_n_categories(score_map, n=10)
    pairs = generate_duel_pairs_from_top(top10)
    d_done = DuelAnswer.query.filter_by(user_id=uid).count()

    if d_done < len(pairs):
        a, b = pairs[d_done]
        return render_template("test.html", stage="duel",
                               progress={"index": d_done+1, "total": len(pairs)},
                               data={
                                   "a": {"key": a, "label": CATEGORIES[a]["label"]},
                                   "b": {"key": b, "label": CATEGORIES[b]["label"]}
                               })

    # Výsledek
    duel_rows = DuelAnswer.query.filter_by(user_id=uid).all()
    wins     = duel_score(duel_rows)                          # dict: key -> wins
    combined = combine_final_ranking(score_map, wins)         # list[(key, combined_score, win_count, likert_score)]

    # pomocné mapy z "combined"
    by_key_score  = {k: float(cs) for k, cs, w, l in combined}
    by_key_wins   = {k: int(w) for k, cs, w, l in combined}
    by_key_likert = {k: int(l) for k, cs, w, l in combined}

    # reverzní mapa label -> key (ResultProfile aktuálně ukládá label)
    label_to_key = {v["label"]: k for k, v in CATEGORIES.items()}

    # Načti případné existující výsledky. Pokud neexistují, založ je podle výpočtu.
    existing = ResultProfile.query.filter_by(user_id=uid).order_by(ResultProfile.rank.asc()).all()

    if not existing:
        # první dokončení testu – naplň tabulku i s ranky ze spočítaného pořadí
        for i, (cat_key, combined_score, win_count, likert_score) in enumerate(combined, start=1):
            db.session.add(ResultProfile(
                user_id=uid,
                rank=i,
                category=CATEGORIES[cat_key]["label"],
                score=float(combined_score),
            ))
        db.session.commit()
        existing = ResultProfile.query.filter_by(user_id=uid).order_by(ResultProfile.rank.asc()).all()
    else:
        # existuje už ruční pořadí – pouze aktualizuj skóre, rank NEMĚŇ
        for rp in existing:
            key = label_to_key.get(rp.category)
            if key is not None and key in by_key_score:
                rp.score = by_key_score[key]
        db.session.commit()

    # Vykreslení: vycházej z ResultProfile (rank je pravda), wins/likert jen připoj pro zobrazení
    rows = []
    for rp in existing:
        key = label_to_key.get(rp.category)
        rows.append({
            "rank": rp.rank,
            "category_label": rp.category,
            "category_key": key or "",
            "wins": (by_key_wins.get(key, 0) if key else 0),
            "likert": (by_key_likert.get(key, 0) if key else 0),
        })

    return render_template("test.html", stage="result", rows=rows)

@bp.route("/answer-likert", methods=["POST"])
def answer_likert():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("priorities.entry"))

    cat = request.form.get("category_key")
    idx = int(request.form.get("statement_index"))
    score = int(request.form.get("score"))
    score = max(LIKERT_MIN, min(LIKERT_MAX, score))

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

    db.session.add(DuelAnswer(user_id=uid, option_a=a, option_b=b, chosen=chosen))
    db.session.commit()
    return redirect(url_for("priorities.entry"))


# Route to save reordered TOP5
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
        .filter_by(user_id=uid)
        .filter(ResultProfile.rank <= 5)
        .all()
    )
    if len(top5) != 5:
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
    for idx, label in enumerate(labels_in_order, start=1):
        by_label[label].rank = idx

    db.session.commit()
    return jsonify({"message": "Pořadí bylo uloženo"})