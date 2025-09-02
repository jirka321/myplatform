# tests/priorities_logic.py
from itertools import combinations

# 20 kategorií × 5 výroků – přepiš si texty podle svého HTML, strukturu nech
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

def get_all_statements():
    out=[]
    for key, cat in CATEGORIES.items():
        for i, txt in enumerate(cat["statements"]):
            out.append({
                "category_key": key,
                "category_label": cat["label"],
                "statement_index": i,
                "text": txt
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
    scores={}
    for row in likert_rows:
        scores[row.category] = scores.get(row.category, 0) + int(row.score)
    return scores

def top_n_categories(score_map: dict, n: int = 10):
    return sorted(score_map.items(), key=lambda kv: kv[1], reverse=True)[:n]

def generate_duel_pairs_from_top(top_list):
    keys = [k for k,_ in top_list]
    return list(combinations(keys, 2))

def duel_score(duel_rows):
    wins={}
    for d in duel_rows:
        wins[d.chosen] = wins.get(d.chosen, 0) + 1
    return wins

def combine_final_ranking(likert_scores: dict, duel_wins: dict):
    rows = []
    keys = set(likert_scores.keys()) | set(duel_wins.keys())
    for k in keys:
        w = duel_wins.get(k, 0)
        l = likert_scores.get(k, 0)
        combined = w + l  # jednoduchý součet, jako v původním HTML
        rows.append((k, combined, w, l))
    rows.sort(key=lambda r: r[1], reverse=True)  # řazení podle combined
    return rows