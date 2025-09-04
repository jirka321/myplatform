# tests/priorities_logic.py
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# 20 kategorií × 5 výroků – ponecháme strukturu a texty
CATEGORIES = {
    "c1": {"label":"Přínos druhým / smysl práce","statements":[
        "Moje práce má pozitivní dopad na životy jiných lidí.",
        "Cítím se nejlépe, když můžu někomu pomoct.",
        "Je pro mě důležité vidět, že má činnost konkrétní výsledky pro druhé.",
        "Úspěch mě těší hlavně tehdy, když prospívá i jiným.",
        "Cítím odpovědnost přispívat k lepšímu světu."
    ]},
    "c2": {"label":"Finance a majetek","statements":[
        "Peníze jsou pro mě důležitým měřítkem úspěchu.",
        "Mám rád/a pocit finanční jistoty a stability.",
        "Usiluji o zvyšování svého příjmu.",
        "Materiální zabezpečení mi dává svobodu volby.",
        "Rád/a investuji do věcí, které zvyšují moji hodnotu."
    ]},
    "c3": {"label":"Cestování a poznávání","statements":[
        "Cestování je pro mě zdroj energie a inspirace.",
        "Láká mě objevovat nové kultury a prostředí.",
        "Když dlouho necestuji, cítím, že mi něco chybí.",
        "Preferuji utrácení za zážitky před hmotnými věcmi.",
        "Rád/a poznávám lidi z různých koutů světa."
    ]},
    "c4": {"label":"Osobní rozvoj a vzdělávání","statements":[
        "Neustále se snažím zlepšovat své dovednosti.",
        "Rád/a se učím nové věci, i když nejsou přímo k práci.",
        "Vzdělávání je pro mě dlouhodobá životní hodnota.",
        "Baví mě překonávat své limity v učení.",
        "Cítím radost, když se mi podaří osvojit novou dovednost."
    ]},
    "c5": {"label":"Partnerské vztahy","statements":[
        "Partnerský vztah je pro mě klíčovým zdrojem štěstí.",
        "Potřebuji mít po boku blízkého člověka.",
        "Kvalita mého vztahu ovlivňuje můj celkový životní pocit.",
        "Jsem ochoten/ochotna obětovat jiné věci pro udržení vztahu.",
        "Sdílení života s partnerem je pro mě prioritou."
    ]},
    "c6": {"label":"Rodina a děti","statements":[
        "Rodina je pro mě na prvním místě.",
        "Rád/a trávím čas s rodinou, i když je to na úkor práce.",
        "Chci vytvářet dobré podmínky pro život svých blízkých.",
        "Rodinné tradice jsou pro mě důležité.",
        "Cítím odpovědnost za podporu své rodiny."
    ]},
    "c7": {"label":"Zdraví a fyzická kondice","statements":[
        "Pečuji o své fyzické zdraví.",
        "Pohyb je pro mě důležitou součástí života.",
        "Vyhýbám se návykům, které škodí zdraví.",
        "Dobrý zdravotní stav považuji za základ spokojenosti.",
        "Sleduji svůj životní styl a snažím se ho zlepšovat."
    ]},
    "c8": {"label":"Duševní pohoda / vnitřní klid","statements":[
        "Hledám způsoby, jak zůstat vnitřně vyrovnaný/á.",
        "Potřebuji mít dostatek času na odpočinek.",
        "Umím si vytvořit prostor pro sebe.",
        "Vyhýbám se zbytečnému stresu.",
        "Klid a harmonie jsou pro mě zásadní."
    ]},
    "c9": {"label":"Kariérní úspěch","statements":[
        "Chci dosáhnout vysoké pozice ve svém oboru.",
        "Toužím po uznání v profesní komunitě.",
        "Cíleně pracuji na své kariérní dráze.",
        "Úspěch v práci mi přináší pocit hrdosti.",
        "Měřím svůj pokrok podle profesních úspěchů."
    ]},
    "c10": {"label":"Prestiž a společenské postavení","statements":[
        "Záleží mi na tom, jak mě vnímají ostatní.",
        "Prestižní status je pro mě motivací.",
        "Rád/a jsem spojován/a s úspěšnými lidmi.",
        "Společenské uznání mě povzbuzuje.",
        "Značky a symboly úspěchu pro mě mají význam."
    ]},
    "c11": {"label":"Kreativita a sebevyjádření","statements":[
        "Potřebuji prostor pro svou tvořivost.",
        "Vytváření nových věcí mě naplňuje.",
        "Baví mě hledat originální řešení.",
        "Umělecké nebo kreativní činnosti jsou pro mě důležité.",
        "Kreativní proces mi dává pocit svobody."
    ]},
    "c12": {"label":"Dobré mezilidské vztahy","statements":[
        "Mám rád/a přátelské pracovní prostředí.",
        "Oceňuji, když mě lidé respektují a podporují.",
        "Snažím se být dobrým kolegou/kamarádem.",
        "Spokojenost ve vztazích zvyšuje moji životní pohodu.",
        "Dobrá atmosféra je pro mě důležitější než výše platu."
    ]},
    "c13": {"label":"Volný čas a koníčky","statements":[
        "Potřebuji mít čas na své koníčky.",
        "Záliby jsou pro mě zdrojem radosti.",
        "Práce by mi neměla brát všechen volný čas.",
        "Trávím čas aktivitami, které mě baví.",
        "Vyhrazený čas pro koníčky považuji za nutnost."
    ]},
    "c14": {"label":"Spiritualita / víra","statements":[
        "Duchovní život je pro mě důležitý.",
        "Víra mi pomáhá zvládat těžké situace.",
        "Potřebuji mít prostor pro duchovní praktiky.",
        "Hledám smysl svého života.",
        "Spirituální hodnoty mě ovlivňují při rozhodování."
    ]},
    "c15": {"label":"Stabilita a jistota","statements":[
        "Mám rád/a, když vím, co mě čeká.",
        "Vyhýbám se zbytečným rizikům.",
        "Stabilní prostředí mi dodává klid.",
        "Nerad/a měním zaběhnuté pořádky.",
        "Jistota zaměstnání je pro mě klíčová."
    ]},
    "c16": {"label":"Dobrodružství a nové zkušenosti","statements":[
        "Vyhledávám nové a neznámé situace.",
        "Baví mě zkoušet věci, které jsem ještě nedělal/a.",
        "Adrenalinové zážitky mi přinášejí radost.",
        "Rutina mě rychle unaví.",
        "Život má být plný překvapení a změn."
    ]},
    "c17": {"label":"Svoboda a nezávislost","statements":[
        "Potřebuji možnost rozhodovat o svém čase.",
        "Nemám rád/a, když mě někdo příliš kontroluje.",
        "Svoboda volby je pro mě důležitější než vysoký plat.",
        "Chci mít možnost dělat věci po svém.",
        "Oceňuji flexibilitu v práci i osobním životě."
    ]},
    "c18": {"label":"Pomoc komunitě / dobrovolnictví","statements":[
        "Chci být prospěšný/á své komunitě.",
        "Dobrovolnická práce mě naplňuje.",
        "Baví mě organizovat akce pro ostatní.",
        "Pomoc lidem v nouzi považuji za svou povinnost.",
        "Rád/a se zapojuji do projektů, které zlepšují okolí."
    ]},
    "c19": {"label":"Pohodlný životní standard","statements":[
        "Oceňuji komfortní bydlení a prostředí.",
        "Mám rád/a kvalitní vybavení a služby.",
        "Pohodlí pro mě znamená vyšší kvalitu života.",
        "Jsem ochoten/ochotna investovat do pohodlí.",
        "Příjemné prostředí zlepšuje moji náladu."
    ]},
    "c20": {"label":"Vliv a možnost rozhodovat","statements":[
        "Rád/a ovlivňuji důležitá rozhodnutí.",
        "Chci mít slovo v tom, jak se věci dělají.",
        "Líbí se mi vést lidi nebo projekty.",
        "Mám rád/a, když druzí naslouchají mému názoru.",
        "Možnost rozhodovat mi dává pocit odpovědnosti a síly."
    ]},
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
                "text": txt,
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
