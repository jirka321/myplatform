# tests/priorities_logic.py
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

CATEGORIES = {
  "family": {
    "label": "Rodina a děti",
    "statements": [
      "Trávit pravidelný čas s rodinou každý týden",
      "Být dostupný/dostupná, když mě rodina potřebuje",
      "Plánovat společné zážitky (výlet, víkend)",
      "Podporovat vzdělání a rozvoj dětí",
      "Udržovat rodinné rituály a tradice"
    ]
  },
  "relationship": {
    "label": "Partnerství",
    "statements": [
      "Mít s partnerem kvalitní společný čas bez rušivých vlivů",
      "Otevřeně mluvit o důležitých tématech",
      "Pracovat na společných cílech",
      "Udržovat intimitu a blízkost",
      "Společně plánovat budoucnost"
    ]
  },
  "friends": {
    "label": "Přátelé",
    "statements": [
      "Pravidelné setkání s blízkými přáteli",
      "Budovat nové smysluplné vztahy",
      "Být oporou, když přátelé něco řeší",
      "Udržovat kontakt i na dálku",
      "Mít přátele s podobnými hodnotami"
    ]
  },
  "health": {
    "label": "Zdraví",
    "statements": [
      "Pravidelné preventivní prohlídky",
      "Kvalitní spánek a režim",
      "Vyvážená strava ve většině dní",
      "Sledovat a řídit stres",
      "Denní pohyb alespoň v lehké intenzitě"
    ]
  },
  "fitness": {
    "label": "Fyzická kondice",
    "statements": [
      "Tréninkový plán a jeho dodržování",
      "Zvyšovat fyzickou výkonnost (síla/vytrvalost)",
      "Aktivní víkendy (turistika, kolo, sport)",
      "Regenerace a flexibilita (střetch, masáže)",
      "Mít jasný cíl (závod, počet tréninků)"
    ]
  },
  "mind": {
    "label": "Mentální pohoda",
    "statements": [
      "Pravidelná relaxace/meditace",
      "Mít vyvážený kalendář (nepřetěžovat se)",
      "Hranice vůči práci a lidem",
      "Vědomá práce s emocemi",
      "Čas jen pro sebe každý týden"
    ]
  },
  "career": {
    "label": "Kariéra",
    "statements": [
      "Posun na zodpovědnější roli",
      "Práce, která dává smysl",
      "Učit se dovednosti pro další krok",
      "Viditelnost výsledků (prezentace, networking)",
      "Mentor/mentoring v práci"
    ]
  },
  "business": {
    "label": "Podnikání",
    "statements": [
      "Jasný produkt/nabídka a její zlepšování",
      "Stálý přísun nových klientů/leadů",
      "Finanční plán a cashflow",
      "Automatizace a škálovatelnost",
      "Značka a marketing, který funguje"
    ]
  },
  "finance": {
    "label": "Finance",
    "statements": [
      "Tvořit rezervu (3–6 měsíců výdajů)",
      "Pravidelně investovat",
      "Mít pod kontrolou měsíční rozpočet",
      "Snižovat zbytečné výdaje",
      "Plán větších nákladů (dovolená, rekonstrukce)"
    ]
  },
  "learning": {
    "label": "Učení a nové dovednosti",
    "statements": [
      "Každý týden řízené učení (kurz/knížka)",
      "Procvičování a projekty místo pasivního čtení",
      "Sledovat pokrok a cíle učení",
      "Zpětná vazba od někoho zkušenějšího",
      "Učení, které zlepší práci/byznys"
    ]
  },
  "creativity": {
    "label": "Kreativita",
    "statements": [
      "Pravidelný prostor na tvoření",
      "Dokončovat malé kreativní projekty",
      "Sdílet tvorbu s publikem",
      "Zkoušet nové formy/techniky",
      "Mít dlouhodobý kreativní cíl"
    ]
  },
  "freedom": {
    "label": "Svoboda a cestování",
    "statements": [
      "Možnost pracovat odkudkoli",
      "Plánovat delší cesty/expedice",
      "Rozpočet na cestování",
      "Žít jednoduše (málo věcí, flexibilita)",
      "Mít čas neplánovat a improvizovat"
    ]
  },
  "home": {
    "label": "Domov a prostředí",
    "statements": [
      "Mít doma klidný a hezký prostor",
      "Udržovat pořádek bez námahy (systémy)",
      "Vybavení, které šetří čas",
      "Domácí rituály (vaření, snídaně)",
      "Mít pracovní zónu oddělenou od odpočinku"
    ]
  },
  "order": {
    "label": "Organizace a pořádek",
    "statements": [
      "Jasné priority týdne",
      "Systém úkolů, který dodržuju",
      "Timeboxing a hluboká práce",
      "Pravidelný týdenní/denní review",
      "Minimalizovat kontext-switching"
    ]
  },
  "impact": {
    "label": "Dopad a smysl",
    "statements": [
      "Dělat práci, která někomu reálně pomáhá",
      "Dobrovolnictví/charitativní přínos",
      "Tvořit věci, které přetrvají",
      "Využít své silné stránky pro druhé",
      "Žít v souladu s vlastními hodnotami"
    ]
  },
  "community": {
    "label": "Komunita a sítě",
    "statements": [
      "Být součástí aktivní komunity",
      "Přispívat zkušenostmi/znalostmi",
      "Chodit na akce a potkávat nové lidi",
      "Budovat kvalitní profesní síť",
      "Spolupráce na projektech s ostatními"
    ]
  },
  "leisure": {
    "label": "Zábava a volný čas",
    "statements": [
      "Mít v týdnu lehkost a spontánnost",
      "Pravidelně se bavit (hry, kultura, sport)",
      "Vypnout hlavu bez výčitek",
      "Výlety a mikro-dobrodružství",
      "Hobby, které mě nabíjí"
    ]
  },
  "spirituality": {
    "label": "Spiritualita / přesah",
    "statements": [
      "Mít čas na vnitřní reflexi",
      "Rituály, které mi dávají smysl",
      "Číst/učit se o filozofii, spiritualitě",
      "Být v kontaktu s přírodou",
      "Dělat věci, které podporují vděčnost"
    ]
  },
  "growth": {
    "label": "Osobní růst",
    "statements": [
      "Pracovat na slepých místech a zvycích",
      "Stanovovat a plnit osobní cíle",
      "Pravidelný coaching/terapie/mentoring",
      "Reflexe týdne a učení z chyb",
      "Překračovat komfortní zónu"
    ]
  },
  "productivity": {
    "label": "Produktivita a výsledky",
    "statements": [
      "Každý den udělat to nejdůležitější",
      "Měřit dopad, ne jen činnost",
      "Automatizovat opakované věci",
      "Eliminovat rušiče a hluk",
      "Dodržovat závazky včas"
    ]
  }
}

LIKERT_MIN, LIKERT_MAX = 1, 4

# ===== Likert: seřazení a normalizace =====

def get_all_statements():
    out = []
    for key, cat in CATEGORIES.items():
        for i, txt in enumerate(cat["statements"]):
            out.append({
                "category_key": key,
                "category_label": cat["label"],
                "statement_index": i + 1,
                "text": f"{txt} – je aktuálně:",
            })
    return out


def get_total_statements_count():
    return sum(len(cat["statements"]) for cat in CATEGORIES.values())


def get_statement_by_progress(progress_index: int):
    all_stmts = get_all_statements()
    if 0 <= progress_index < len(all_stmts):
        return all_stmts[progress_index]
    return None


def compute_likert_scores(likert_rows):
    scores = {}
    for row in likert_rows:
        scores[row.category] = scores.get(row.category, 0) + int(row.score)
    return scores


def rank_by_likert(likert_scores: Dict[str, int], category_map: Dict[str, dict]) -> List[dict]:
    rows = [{"id": cid, "name": category_map[cid]["label"], "score": int(likert_scores.get(cid, 0))}
            for cid in category_map.keys()]
    rows.sort(key=lambda x: (-x["score"], x["name"]))
    return rows


def normalize_likert(scores: Dict[str, int]) -> Dict[str, float]:
    if not scores:
        return {}
    vals = list(scores.values())
    mn, mx = min(vals), max(vals)
    if mx == mn:
        return {k: 0.5 for k in scores}
    return {k: (v - mn) / (mx - mn) for k, v in scores.items()}


# ===== Duelový sorter (insertion + binary search) s "gated swap" (double win) =====

@dataclass
class DuelState:
    names: Dict[str, str]                 # id -> label
    order: List[str]                      # aktuálně seřazené položky
    todo: List[str]                       # čekající k vložení
    cur: Optional[dict]                   # {"id","low","high","mid"}
    comparisons: int                      # počítadlo porovnání
    duel_stats: Dict[str, Dict[str, int]] # {"id": {"wins":int,"comparisons":int}}
    streak: Dict[Tuple[str, str], int]    # (attacker, defender) -> consecutive wins


def duel_sorter_init(items: List[Tuple[str, str]]) -> DuelState:
    names = {i: n for i, n in items}
    todo = [i for i, _ in items]
    order: List[str] = []
    duel_stats = {i: {"wins": 0, "comparisons": 0} for i, _ in items}
    streak = {}
    if todo:
        first = todo.pop(0)
        order.append(first)
    return DuelState(names, order, todo, None, 0, duel_stats, streak)


def duel_sorter_next_pair(st: DuelState) -> Optional[Tuple[str, str]]:
    if st.cur is None:
        if not st.todo:
            return None
        cid = st.todo[0]
        st.cur = {"id": cid, "low": 0, "high": len(st.order) - 1}
    mid = (st.cur["low"] + st.cur["high"]) // 2
    st.cur["mid"] = mid
    return st.cur["id"], st.order[mid]


def _bump_stats(st: DuelState, winner: str, loser: str) -> None:
    st.duel_stats[winner]["wins"] += 1
    st.duel_stats[winner]["comparisons"] += 1
    st.duel_stats[loser]["comparisons"] += 1


def duel_sorter_choose(st: DuelState, winner_id: str, loser_id: str, gated: bool = True) -> None:
    if st.cur is None:
        return
    st.comparisons += 1
    _bump_stats(st, winner_id, loser_id)

    if (not gated) or (winner_id != st.cur["id"]):
        # standardní binární vkládání
        if winner_id == st.cur["id"]:
            st.cur["high"] = st.cur["mid"] - 1
        else:
            st.cur["low"] = st.cur["mid"] + 1
    else:
        # GATED: nový prvek musí vyhrát 2× po sobě nad aktuálním soupeřem
        key = (st.cur["id"], loser_id)
        st.streak[key] = st.streak.get(key, 0) + 1
        if st.streak[key] >= 2:
            st.cur["high"] = st.cur["mid"] - 1
            st.streak[key] = 0
        else:
            # první výhra nestačí → dalším porovnáním hned výš
            st.cur["mid"] = max(st.cur["mid"] - 1, st.cur["low"])

    if st.cur["low"] > st.cur["high"]:
        st.order.insert(st.cur["low"], st.cur["id"])
        st.todo.pop(0)
        st.cur = None


def duel_sorter_done(st: DuelState) -> bool:
    return not st.todo and st.cur is None


def duel_sorter_get_order(st: DuelState) -> List[str]:
    return st.order[:]


def compute_duel_strength(duel_stats: Dict[str, Dict[str, int]]) -> Dict[str, float]:
    out = {}
    for k, s in duel_stats.items():
        w = s.get("wins", 0)
        c = s.get("comparisons", 0)
        out[k] = (w + 0.5) / (c + 1)  # Laplace smoothing
    return out


def hybrid_score(l_norm: Dict[str, float], d_strength: Dict[str, float], lam: float = 0.5) -> Dict[str, float]:
    keys = set(l_norm) | set(d_strength)
    return {k: (1 - lam) * l_norm.get(k, 0.5) + lam * d_strength.get(k, 0.5) for k in keys}


# ===== Tie-break pro cutoff TOP N (duely jen v tie bandu, bez gated) =====

@dataclass
class TieBreakPlan:
    guaranteed_ids: List[str]
    pool_ids: List[str]
    slots: int
    engine: DuelState


def select_topN_with_tiebreak(likert_scores: Dict[str, int],
                              category_map: Dict[str, dict],
                              top_n: int = 10,
                              tb_choices: Optional[List[Tuple[str, str]]] = None) -> Tuple[List[str], Optional[TieBreakPlan]]:
    rows = rank_by_likert(likert_scores, category_map)
    if not rows:
        return [], None

    top = rows[:top_n]
    cutoff = top[-1]["score"]
    guaranteed = [r["id"] for r in rows if r["score"] > cutoff]
    tied_band = [r for r in rows if r["score"] == cutoff]
    slots = top_n - len(guaranteed)

    if len(tied_band) <= slots:
        return guaranteed + [r["id"] for r in tied_band], None

    items = [(r["id"], r["name"]) for r in tied_band]
    engine = duel_sorter_init(items)

    if tb_choices:
        for w, l in tb_choices:
            pair = duel_sorter_next_pair(engine)
            if pair is None:
                break
            a, b = pair
            if {w, l} != {a, b}:
                continue
            duel_sorter_choose(engine, w, l, gated=False)

    if duel_sorter_done(engine):
        ordered = duel_sorter_get_order(engine)
        winners = ordered[:slots]
        return guaranteed + winners, None

    plan = TieBreakPlan(
        guaranteed_ids=guaranteed,
        pool_ids=[r["id"] for r in tied_band],
        slots=slots,
        engine=engine,
    )
    return [], plan


# ===== Fáze TOP: duely s gated swapem =====

def start_duels_for_top(top_ids: List[str], category_map: Dict[str, dict]) -> DuelState:
    items = [(cid, category_map[cid]["label"]) for cid in top_ids]
    return duel_sorter_init(items)


def duel_next_pair(state: DuelState) -> Optional[Tuple[str, str]]:
    return duel_sorter_next_pair(state)


def duel_choose(state: DuelState, winner_id: str, loser_id: str, gated: bool = True) -> None:
    duel_sorter_choose(state, winner_id, loser_id, gated=gated)


def duel_is_done(state: DuelState) -> bool:
    return duel_sorter_done(state)


def duel_get_insertion_order(state: DuelState) -> List[str]:
    return duel_sorter_get_order(state)


# ===== Výstupy =====

def pre_top_table(likert_scores: Dict[str, int], category_map: Dict[str, dict], resolved_top_ids: List[str]) -> List[dict]:
    rows = [{"id": cid, "name": category_map[cid]["label"], "score": int(likert_scores.get(cid, 0))}
            for cid in resolved_top_ids]
    rows.sort(key=lambda x: (-x["score"], x["name"]))
    return [{"rank": i + 1, **r} for i, r in enumerate(rows)]


def post_duel_hybrid_table(likert_scores: Dict[str, int],
                           category_map: Dict[str, dict],
                           top_ids: List[str],
                           duel_state: DuelState,
                           lam: float = 0.5) -> List[dict]:
    l_norm = normalize_likert({k: likert_scores.get(k, 0) for k in top_ids})
    d_strength = compute_duel_strength({k: duel_state.duel_stats.get(k, {"wins": 0, "comparisons": 0}) for k in top_ids})
    s = hybrid_score(l_norm, d_strength, lam=lam)

    out = []
    for cid in top_ids:
        out.append({
            "id": cid,
            "name": category_map[cid]["label"],
            "likert": int(likert_scores.get(cid, 0)),
            "wins": duel_state.duel_stats.get(cid, {}).get("wins", 0),
            "comparisons": duel_state.duel_stats.get(cid, {}).get("comparisons", 0),
            "hybrid": float(s.get(cid, 0.5)),
        })
    out.sort(key=lambda r: (-r["hybrid"], r["name"]))
    return [{"rank": i + 1, **r} for i, r in enumerate(out)]


# --- Helper: původní text výroku podle kategorie a indexu (1-based) ---

def get_statement_text(category_key: str, statement_index: int) -> str:
    try:
        cat = CATEGORIES.get(category_key)
        if isinstance(cat, dict):
            stmts = cat.get("statements")
            if isinstance(stmts, (list, tuple)):
                if 1 <= statement_index <= len(stmts):
                    return str(stmts[statement_index - 1])
            label = cat.get("label")
            if label:
                return f"{label} · {statement_index}"
        return f"{category_key} · {statement_index}"
    except Exception:
        return f"{category_key} · {statement_index}"
