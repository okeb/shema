#!/usr/bin/env python3
"""
build_strongs.py — Génère db/strongs/bym_strongs.json (aligné sur le texte BYM).

Pipeline :
1. Télécharge strong.sqlite (bible-strong).
2. Parse les tables LSGSAT2 (AT) et LSGSNT2 (NT) — texte Louis Segond avec
   numéros Strong's embarqués dans le texte.
3. Pour chaque verset :
   a. Parse le texte LSG en segments (mot_français, code_strong).
   b. Applique gloss_mapping.json (substitutions conditionnées par code Strong).
   c. Aligne les segments LSG avec le texte BYM (thebym.json).
   d. Produit des segments BYM avec codes Strong's : [{text, strong}, ...]
4. Les overrides (overrides.json) prennent le pas sur l'alignement automatique.

Usage :
    python3 scripts/build_strongs.py
    python3 scripts/build_strongs.py --sqlite /path/to/strong.sqlite
"""

import argparse
import json
import os
import re
import sqlite3
import unicodedata
import urllib.request

STRONG_SQLITE_URL = "https://assets.bible-strong.app/databases/strong.sqlite"
BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
OUTPUT_PATH = os.path.join(BASE_DIR, "db", "strongs", "bym_strongs.json")
GLOSS_MAPPING_PATH = os.path.join(BASE_DIR, "db", "strongs", "gloss_mapping.json")
THEBYM_PATH = os.path.join(BASE_DIR, "db", "thebym.json")
OVERRIDES_PATH = os.path.join(BASE_DIR, "db", "strongs", "overrides.json")
STRONG_TO_BYM_PATH = os.path.join(BASE_DIR, "db", "strongs", "strong_to_bym.json")
VERSIF_OFFSETS_PATH = os.path.join(BASE_DIR, "db", "strongs", "versif_offsets.json")

# Ordre Bible de Jérusalem (vérifié contre les données réelles)
BOOK_NUM_TO_ABBR = [
    "Ge. ", "Ex. ", "Lé. ", "No. ", "De. ",
    "Jos. ", "Jg. ", "Ru. ",
    "1 S. ", "2 S. ", "1 R. ", "2 R. ",
    "1 Ch. ", "2 Ch. ", "Esd. ", "Né. ", "Est. ",
    "Job ", "Ps. ", "Pr. ", "Ec. ", "Ca. ",
    "Es. ", "Jé. ", "La. ", "Ez. ", "Da. ",
    "Os. ", "Joë. ", "Am. ", "Ab. ", "Jon. ", "Mi. ", "Na. ", "Ha. ",
    "So. ", "Ag. ", "Za. ", "Mal. ",
    "Mt. ", "Mc. ", "Lu. ", "Jn. ", "Ac. ",
    "Ro. ", "1 Co. ", "2 Co. ", "Ga. ", "Ep. ", "Ph. ", "Col. ",
    "1 Th. ", "2 Th. ", "1 Ti. ", "2 Ti. ", "Tit. ", "Phm. ",
    "Hé. ", "Ja. ", "1 Pi. ", "2 Pi. ", "1 Jn. ", "2 Jn. ", "3 Jn. ", "Jud. ", "Ap. "
]
OT_MAX_BOOK = 39
HEBREW_MAX = 8674
GREEK_MAX = 5624

# Marqueur de versification en tête de verset LSG, ex. « (7.26) ». Le texte LSG du
# sqlite annote la numérotation hébraïque/BYM réelle quand elle diffère de la sienne.
# Le point distingue ce marqueur des codes grammaticaux « (8799) » (sans point).
VERSIF_MARKER_RE = re.compile(r"^\s*\((\d+)\.(\d+)\)\s*")
# Variante non ancrée : un verset LSG peut contenir PLUSIEURS marqueurs (il s'étale alors
# sur plusieurs versets BYM — cas des « splits » de versification).
VERSIF_MARKER_ANY_RE = re.compile(r"\((\d+)\.(\d+)\)")


def split_lsg_by_markers(lsg_text, native_key, abbr):
    """Découpe un texte LSG en morceaux (clé_BYM, texte) selon les marqueurs « (C.V) ».

    Le texte avant le 1er marqueur appartient au verset natif ; chaque marqueur ouvre un
    morceau rattaché au verset BYM qu'il désigne (les frontières de versets BYM tombent
    aux marqueurs). Sans marqueur → [(native_key, texte)]. Les marqueurs eux-mêmes sont
    retirés (ils ne font pas partie du texte aligné)."""
    text = lsg_text or ""
    markers = list(VERSIF_MARKER_ANY_RE.finditer(text))
    if not markers:
        return [(native_key, text)]
    pieces = []
    head = text[: markers[0].start()]
    if head.strip():
        pieces.append((native_key, head))
    for i, mk in enumerate(markers):
        bkey = f"{abbr}{int(mk.group(1))}:{int(mk.group(2))}"
        start = mk.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        pieces.append((bkey, text[start:end]))
    return pieces


# ─── Utilitaires ─────────────────────────────────────────────────────

def download(url, dest):
    print(f"Téléchargement : {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "shema-build-lexicon/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
    print(f"  → {os.path.getsize(dest)} bytes")


def strip_accents(text):
    """Retire les accents (NFD → supprime les diacritiques)."""
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def normalize(word):
    """Normalise pour comparaison : minuscules, sans accents, sans ponctuation."""
    w = word.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    w = strip_accents(w.lower().strip(",.;:!?()\"'[]\u00ab\u00bb\u2014\u2013"))
    return w


def levenshtein(a, b):
    """Distance de Levenshtein entre deux chaînes."""
    if len(a) < len(b):
        return levenshtein(b, a)
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(
                cur[-1] + 1,
                prev[j] + 1,
                prev[j - 1] + (0 if ca == cb else 1),
            ))
        prev = cur
    return prev[-1]


# ─── Parsing LSG ─────────────────────────────────────────────────────

def parse_lsg_segments(text, is_at):
    """
    Parse le texte LSG en segments (mot, code_strong).

    Format AT  : « Au commencement 07225, Dieu 0430 créa 01254 (8804) 0853 … »
    Format NT  : « Car 1063 Dieu 2316 a tant 3779 aimé 25 (5656) … »

    Retourne : [{"word": "Au commencement", "strong": "H7225"}, {"word": "", "strong": "H853"}, …]
    """
    prefix = "H" if is_at else "G"
    max_code = HEBREW_MAX if is_at else GREEK_MAX

    if is_at:
        # AT : nombres zero-padded (07225, 0430, 0853)
        number_re = re.compile(r"0(\d{3,4})")
    else:
        # NT : nombres 1-5 chiffres, précédés d'un espace
        # Suivis par : espace, apostrophe, ponctuation, parenthèse, fin
        number_re = re.compile(r"(?<=\s)(\d{1,5})(?=[\s'\-,.;:!?)\]]|$)")

    segments = []
    prev_end = 0

    for m in number_re.finditer(text):
        code_num = int(m.group(1))
        if code_num == 0 or code_num > max_code:
            continue

        raw = text[prev_end:m.start()]
        # Retirer les codes grammaticaux (8804)
        raw = re.sub(r"\(\d+\)", "", raw)
        word = raw.strip()

        segments.append({"word": word, "strong": f"{prefix}{code_num}"})
        prev_end = m.end()

    # Texte restant après le dernier code
    trailing = re.sub(r"\(\d+\)", "", text[prev_end:]).strip()
    if trailing:
        segments.append({"word": trailing, "strong": None})

    return segments


# ─── Substitution ────────────────────────────────────────────────────

def clean_word(word):
    """Nettoie un mot : retire ponctuation et espaces en début/fin."""
    # Normaliser les guillemets courbes en droits
    word = word.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    return word.strip(",.;:!?()\"'[]\u00ab\u00bb \u2014\u2013-")


# Table de conjugaison pour les verbes irréguliers français les plus fréquents
# maps infinitif → liste des racines des formes conjuguées
IRREGULAR_VERBS = {
    "faire": ["fair", "fais", "fait", "fit", "font", "fer", "fass"],
    "etre": ["suis", "est", "sont", "ete", "etai", "ser", "soit", "soy"],
    "avoir": ["avons", "avais", "avai", "aur", "ai", "as", "ont"],
    "aller": ["vais", "va", "all", "ir", "all"],
    "venir": ["vien", "vint", "ven", "viendr"],
    "dire": ["dis", "dit", "dir", "d"],
    "prendre": ["prend", "pris", "pren", "prendr"],
    "voir": ["voi", "vit", "vis", "verr"],
    "savoir": ["sai", "sait", "sav", "saur"],
    "pouvoir": ["peu", "put", "pouv", "pourr"],
    "vouloir": ["veu", "voul", "voudr", "veul"],
    "falloir": ["fau", "fall", "faudr"],
    "devoir": ["doi", "dev", "durr", "devr"],
    "mettre": ["met", "mis", "mett"],
    "sortir": ["sor", "sort", "sorti"],
}


# Termes grammaticaux hébreux/araméens (binyanim) à ignorer dans les définitions.
GRAMMAR_TERMS = {"qal", "niphal", "hiphil", "pael", "hitpael", "polel", "hithpael",
                 "piel", "hophal", "pual", "hitpolel", "nithpael", "hishtaphel",
                 "ishtaphel", "hithpeal", "hithpaal", "peal", "ithpeel",
                 "ithpaal", "aphel", "shaphel", "tiphil"}

# Mots-outils français : trop fréquents/ambigus pour servir de racine de matching
# (une définition encyclopédique en contient — « il fut le père de CEUX qui… »).
FRENCH_STOP = {
    "avec", "dans", "pour", "sans", "sous", "leur", "leurs", "cette", "cela",
    "ceux", "celui", "celle", "celles", "elle", "elles", "vous", "nous", "tout",
    "tous", "toute", "toutes", "etre", "avoir", "faire", "quelque", "quelques",
    "plus", "moins", "ainsi", "alors", "aussi", "comme", "donc", "mais", "quand",
    "selon", "entre", "chez", "vers", "contre", "lequel", "laquelle", "lesquels",
    "dont", "lorsque", "puis", "encore", "meme", "memes", "tres", "bien", " etc",
    "cest", "quil", "quelle", "quelquun", "chose", "choses", "facon", "maniere",
    "sorte", "sortes", "etat", "fait", "afin", "ceci", "voici", "voila",
    "celleci", "celuici", "ceuxci", "ainsi", "lautre", "autre", "autres",
}


def is_content_type(type_str):
    """Vrai si le type grammatical Strong's porte un sens lexical traduisible en BYM
    (verbe, nom commun, adjectif, adverbe) — exclut noms propres et mots-outils."""
    t = strip_accents((type_str or "").lower())
    if "propre" in t:  # nom propre / locatif → translittération, pas définition
        return False
    return any(kw in t for kw in ("verbe", "nom ", "adjectif", "adverbe"))


def is_proper_type(type_str):
    """Vrai si le code est un nom propre (anthroponyme ou toponyme « locatif »)."""
    return "propre" in (type_str or "").lower()


def translit_norm(word):
    """Réduit une translittération (lexique) ou un mot BYM à un squelette comparable.

    La BYM emploie des graphies hébraïsantes (Hanowk, Yitzhak, Yéshoua) proches du
    « translit » du lexique (Chanowk, Yitschaq, Yeshuwa`) mais loin du mot LSG francisé
    (Hénoc, Isaac, Josué). On normalise les divergences systématiques : ou→u, waw
    quiescent, y→i, k/c→q, doublons, et h muet (Chanowk/Hanowk, Noach/Noah)."""
    t = strip_accents(str(word).lower())
    t = re.sub(r"[^a-z]", "", t)
    t = t.replace("ou", "u").replace("w", "")
    t = t.replace("y", "i").replace("k", "q").replace("c", "q")
    t = re.sub(r"(.)\1", r"\1", t)
    t = t.replace("h", "")
    return t


def find_translit_match(translit, tokens, word_indices, cursor, threshold=0.70):
    """Cherche le mot BYM libre dont le squelette translittéré est le plus proche du
    « translit » du lexique (Levenshtein normalisé). Retourne l'index du token (meilleur
    score ≥ threshold) ou None. Les noms sont distinctifs → on prend l'argmax du verset."""
    # Forme primaire seule : le champ translit du lexique liste parfois des variantes
    # (« David rarement (complet) Daviyd ») dont la concaténation crée de fausses inclusions.
    primary = re.split(r"\s+ou\s+|\s+rarement\s+|\(", translit or "")[0]
    tt = translit_norm(primary)
    if len(tt) < 3:
        return None
    best_ti, best_score = None, threshold
    for wi in range(len(word_indices)):
        ti = word_indices[wi]
        if tokens[ti]["strong"] is not None:
            continue
        ww = translit_norm(tokens[ti]["text"])
        if len(ww) < 3:
            continue
        d = levenshtein(tt, ww)
        score = 1 - d / max(len(tt), len(ww))
        # Boost d'inclusion seulement si le plus court fait ≥ 4 (évite « sus » ⊂ « iesus »).
        if min(len(tt), len(ww)) >= 4 and (tt in ww or ww in tt):
            score = max(score, 0.9)
        if score >= best_score:
            best_ti, best_score = ti, score
    return best_ti


def extract_definition_stems(definition, min_len=4):
    """Extrait les racines des gloses **fiables** d'une définition Strong's.

    On ne garde QUE les portions porteuses de sens, pas la prose encyclopédique
    (qui injecte des mots-outils ⇒ faux positifs) :
      • les gloses entre guillemets (« … » ou " … ") ;
      • la tête de chaque sens numéroté (« 1) aussi, … » → « aussi ») jusqu'au
        premier séparateur (virgule, slash, point-virgule).
    Chaque mot retenu (≥ min_len, hors mots-outils/grammaire) produit une racine
    (préfixe 5 lettres) + les radicaux irréguliers connus si c'est un infinitif.
    """
    if not definition:
        return []

    # Retirer un éventuel préfixe « Lemma = » (translittération, non pertinent ici).
    body = re.sub(r'^[^=\n]{0,40}=', '', definition)

    # Tous les mots de la définition (split sur espaces ET ponctuation/chiffres), filtrés :
    # le tri se fait par mots-outils (FRENCH_STOP) + binyanim (GRAMMAR_TERMS) + longueur,
    # PAS en restreignant aux seules gloses-titres (qui sacrifiait trop de recall). C'est
    # le filtrage par stopwords + le gating par type de contenu qui assurent la précision.
    stems = set()
    for w in re.split(r'[\s,.\n;:()\[\]\d/]+', body):
        w = strip_accents(w.strip().lower()).strip("'\"- ")
        if not w or len(w) < min_len:
            continue
        if w in GRAMMAR_TERMS or w in FRENCH_STOP:
            continue
        stems.add(w[: min(5, len(w))])
        if w in IRREGULAR_VERBS:
            for sfx in IRREGULAR_VERBS[w]:
                if len(sfx) >= 3:
                    stems.add(sfx)

    return list(stems)


# Mots BYM fréquents/fonctionnels à ne JAMAIS tagger par définition (ils n'ont pas de
# sens lexical propre ; ex. « pour » capté par le radical « pourr » de pouvoir).
DEF_BYM_BLOCK = {"pour", "avec", "dans", "sans", "plus", "vers", "chez", "sous",
                 "leur", "leurs", "elle", "elles", "nous", "vous", "tout", "tous"}


def _def_word_matches(norm_bym, stems):
    """Le mot BYM (normalisé) correspond-il à l'une des racines de la définition ?"""
    if not norm_bym or len(norm_bym) < 4 or norm_bym in DEF_BYM_BLOCK:
        return False
    for stem in stems:
        if len(stem) < 4:
            continue
        # Le mot BYM commence par la racine (ex: « flûte » ⊃ « flut »)
        if norm_bym.startswith(stem):
            return True
        # La racine commence par le mot BYM (formes irrégulières : « fit » ⊂ « faire »)
        if len(norm_bym) >= 4 and stem.startswith(norm_bym):
            return True
    return False


def find_definition_match(stems, tokens, word_indices, cursor, max_lookahead=None):
    """
    Cherche un mot BYM non assigné qui correspond à une racine de la définition.
    Scanne tout le verset, au plus proche du curseur d'abord (avant puis arrière).
    La précision repose sur des gloses fiables (cf. extract_definition_stems) et le
    gating par type de contenu en amont, pas sur l'étroitesse de la fenêtre.
    """
    n = len(word_indices)
    order = list(range(cursor, n)) + list(range(cursor - 1, -1, -1))
    for wi in order:
        ti = word_indices[wi]
        if tokens[ti]["strong"] is not None:
            continue
        norm_bym = normalize(tokens[ti]["text"])
        if _def_word_matches(norm_bym, stems):
            return ti
    return None


# ─── Nombres ─────────────────────────────────────────────────────────
# La BYM écrit les nombres en CHIFFRES (« 30 », « 300 ») et conserve la décomposition
# additive de l'hébreu en tokens séparés (« 900 ans et 30 ans » → H7970 sur « 30 »), là où
# le code Strong porte un mot-nombre hébreu/grec (« trente »). L'appariement exact (mot LSG
# « trente » vs « 30 ») échoue donc toujours. On apparie par VALEUR : on extrait la/les
# valeur(s) entière(s) de la définition Strong's et on cherche un token BYM (chiffre, ou
# mot-nombre sans ambiguïté) de même valeur. Déterministe et quasi 100 % de précision.
NUM_UNITS = {"zero": 0, "un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5,
             "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12,
             "treize": 13, "quatorze": 14, "quinze": 15, "seize": 16, "dixsept": 17,
             "dixhuit": 18, "dixneuf": 19}
NUM_TENS = {"vingt": 20, "trente": 30, "quarante": 40, "cinquante": 50, "soixante": 60}
NUM_SCALE = {"cent": 100, "cents": 100, "mille": 1000, "millier": 1000, "milliers": 1000}
NUM_ORD = {"premier": 1, "premiere": 1, "deuxieme": 2, "second": 2, "seconde": 2,
           "troisieme": 3, "quatrieme": 4, "cinquieme": 5, "sixieme": 6, "septieme": 7,
           "huitieme": 8, "neuvieme": 9, "dixieme": 10, "onzieme": 11, "douzieme": 12,
           "vingtieme": 20, "trentieme": 30, "centaine": 100, "centaines": 100,
           "vingtaine": 20, "dizaine": 10, "douzaine": 12}
NUMBER_WORDS = set(NUM_UNITS) | set(NUM_TENS) | set(NUM_SCALE) | set(NUM_ORD)
# Mots-nombres à NE JAMAIS matcher côté BYM : « un/une » est massivement l'article indéfini
# (« un homme »), « premier/première » un ordinal isolé ⇒ faux positifs. La valeur 1 n'est
# donc récupérable que via un token chiffre « 1 » littéral (cf. bannissement dans extract).
NUM_WORD_BLOCK = {"un", "une", "premier", "premiere"}
ENUM_MARKER_RE = re.compile(r"\b\d+[a-z]?\)")  # « 1) », « 1a) », « 2) » : numérotation des sens


def eval_number_run(toks):
    """Évalue une suite de mots-nombres français en entier (« soixante dix » → 70)."""
    total, cur, got = 0, 0, False
    for w in toks:
        if w in NUM_UNITS:
            cur += NUM_UNITS[w]; got = True
        elif w in NUM_TENS:
            cur += NUM_TENS[w]; got = True
        elif w in NUM_SCALE:
            cur = (cur or 1) * NUM_SCALE[w]; total += cur; cur = 0; got = True
        elif w in NUM_ORD:
            cur += NUM_ORD[w]; got = True
    return total + cur if got else None


def is_numeric_definition(definition):
    """Vrai si la définition Strong's décrit essentiellement un nombre (≥ moitié de mots-nombres)."""
    d = strip_accents((definition or "").lower())
    words = [w for w in re.split(r"[^a-z]+", d) if len(w) >= 2]
    if not words:
        return False
    nums = sum(1 for w in words if w in NUMBER_WORDS)
    return nums >= 1 and nums / len(words) >= 0.5


def extract_number_values(definition):
    """Ensemble des valeurs entières exprimées par la définition (mots français + chiffres).

    Retire d'abord la numérotation des sens « 1) / 1a) » et les renvois Strong « (06240) »
    (sinon le « 1 » d'« 1) » injecte une fausse valeur 1). Pour les mots français on n'évalue
    que le PREMIER sens (avant la 1ʳᵉ virgule/point-virgule) : c'est la glose canonique. Évaluer
    les sens suivants fusionnerait des gloses distinctes (« trente, trentième » → 60) ou des
    idiomes (« trois vingtaines » → 23). Les chiffres isolés du texte (3, 300) restent fiables et
    sont tous pris. La valeur 1 est bannie (piège de l'article — cf. NUM_WORD_BLOCK)."""
    d = strip_accents((definition or "").lower())
    d = ENUM_MARKER_RE.sub(" ", d)
    d = re.sub(r"\(\d+\)", " ", d)
    vals = set()
    for m in re.findall(r"\d+", d):
        vals.add(int(m))
    # Premier sens uniquement, joints par espace/trait d'union (« soixante-dix », « deux cents »).
    first_sense = re.split(r"[,.;:/]", d, 1)[0]
    run = [w for w in re.split(r"[^a-z]+", first_sense) if w]
    if run and all(w in NUMBER_WORDS for w in run):
        v = eval_number_run(run)
        if v:
            vals.add(v)
    return {v for v in vals if v and v != 1}


def token_number_value(text):
    """Valeur numérique d'un token BYM : chiffre pur, ou mot-nombre non ambigu. Sinon None."""
    n = normalize(text)
    if n.isdigit():
        return int(n)
    if n in NUMBER_WORDS and n not in NUM_WORD_BLOCK:
        return eval_number_run([n])
    return None


def find_number_match(values, tokens, word_indices, cursor):
    """Cherche un token BYM libre dont la valeur numérique ∈ values, au plus proche du curseur."""
    n = len(word_indices)
    order = list(range(cursor, n)) + list(range(cursor - 1, -1, -1))
    for wi in order:
        ti = word_indices[wi]
        if tokens[ti]["strong"] is not None:
            continue
        if token_number_value(tokens[ti]["text"]) in values:
            return ti
    return None


def apply_substitution(word, strong_code, gloss_mapping):
    """
    Applique gloss_mapping[strong_code] en vérifiant chaque sous-mot.
    Gère les phrases multi-mots comme « de Jésus » -> « de Yéhoshoua ».
    Retourne (mot_substitué, a_été_substitué).
    """
    entry = gloss_mapping.get(strong_code)
    if not entry:
        return word, False
    
    sub_words = word.split()
    result_words = []
    any_substituted = False
    
    for sw in sub_words:
        cleaned = clean_word(sw).lower()
        bym_word = entry.get(cleaned)
        if not bym_word:
            bym_word = entry.get(strip_accents(cleaned))
        if bym_word:
            result_words.append(bym_word)
            any_substituted = True
        else:
            result_words.append(sw)
    
    return " ".join(result_words), any_substituted


# ─── Alignement LSG → BYM ─────────────────────────────────────────────

def tokenize_bym(text):
    """
    Tokenise le texte BYM en tokens (mot / séparateur).
    Retourne : [{"text": "Au", "is_word": True, "strong": None}, {"text": " ", "is_word": False, "strong": None}, …]
    """
    tokens = []
    for m in re.finditer(r"\S+|\s+", text):
        tok = m.group()
        tokens.append({
            "text": tok,
            "is_word": not tok[0].isspace(),
            "strong": None,
        })
    return tokens


def find_match(lsg_sub_words, bym_tokens, cursor, max_lookahead=5):
    """
    Cherche une position où les sous-mots LSG correspondent aux mots BYM.
    Retourne (start, end) ou (None, None).
    """
    n = len(lsg_sub_words)
    if n == 0:
        return None, None

    max_start = min(cursor + max_lookahead, len(bym_tokens) - n + 1)

    for start in range(cursor, max_start):
        if not bym_tokens[start]["is_word"]:
            continue
        match = True
        for j in range(n):
            idx = start + j * 2  # skip separators between words
            if idx >= len(bym_tokens) or not bym_tokens[idx]["is_word"]:
                match = False
                break
            if normalize(lsg_sub_words[j]) != normalize(bym_tokens[idx]["text"]):
                match = False
                break
        if match:
            # Return the range of word indices (not token indices)
            return start, start + (n - 1) * 2

    return None, None


def find_fuzzy_match(lsg_word, bym_tokens, cursor, max_lookahead=5, max_dist=2):
    """
    Cherche un match flou (Levenshtein) sur le dernier sous-mot.
    Retourne l'index du token BYM ou None.
    """
    norm_lsg = normalize(lsg_word)
    if not norm_lsg:
        return None

    for i in range(cursor, min(cursor + max_lookahead, len(bym_tokens))):
        if not bym_tokens[i]["is_word"]:
            continue
        if bym_tokens[i]["strong"] is not None:
            continue  # déjà assigné
        norm_bym = normalize(bym_tokens[i]["text"])
        if not norm_bym:
            continue
        if levenshtein(norm_lsg, norm_bym) <= max_dist:
            return i
    return None


def align_segments(lsg_segments, bym_text, gloss_mapping, strong_to_bym=None, lexicon=None):
    """
    Aligne les segments LSG avec le texte BYM.
    Produit une liste de segments : [{"text": "Au commencement", "strong": "H7225"}, …]
    """
    tokens = tokenize_bym(bym_text)
    word_indices = [i for i, t in enumerate(tokens) if t["is_word"]]
    cursor = 0  # index dans word_indices
    unmatched = []  # Strong's non alignés au texte BYM

    for seg in lsg_segments:
        strong = seg["strong"]
        lsg_word = clean_word(seg["word"])

        # Skip : pas de code, ou mot vide (marqueur invisible)
        if not strong or not lsg_word:
            continue

        # 1. Appliquer la substitution
        expected_word, was_substituted = apply_substitution(lsg_word, strong, gloss_mapping)
        sub_words = expected_word.split()
        matched = False

        # 1bis. Variantes manuelles MULTI-MOTS : la BYM rend ce code par une expression
        # curée (« pays lointain », « mit autour ») plus large que le mot LSG (« pays »,
        # « entoura »). Sans ça, l'étape mono-mot LSG ci-dessous attrape le mot isolé et le
        # mot BYM voisin reste orphelin. On essaie donc ces variantes AVANT le match LSG.
        # On exige >= 2 mots, match strictement consécutif ⇒ haute précision ; les mono-mots
        # restent au dico (étape 5).
        if strong_to_bym:
            mv_entry = strong_to_bym.get(strong)
            for mv in (mv_entry.get("manual", []) if mv_entry else []):
                mv_words = mv.split()
                if len(mv_words) < 2:
                    continue
                # Recherche AVANT uniquement (l'expression BYM est près du curseur) :
                # un fallback global ferait sauter le curseur loin et orphalinerait les
                # codes intermédiaires. L'étape 5 (dico) garde le repli global.
                start_wi, end_wi = find_match_in_words(mv_words, tokens, word_indices, cursor, max_lookahead=10)
                if start_wi is not None:
                    for wi in range(start_wi, end_wi + 1):
                        tokens[word_indices[wi]]["strong"] = strong
                    cursor = max(cursor, end_wi + 1)
                    matched = True
                    break

        # 2. Essayer le match exact (mot substitué) — progressif par suffixe
        # Du dernier mot (celui que le Strong's décrit) vers le mot complet
        for n in range(1, len(sub_words) + 1):
            suffix = sub_words[-n:]
            # Sauter si le dernier mot est trop court (mot fonctionnel)
            if n == 1 and len(suffix[0]) < 3:
                continue
            start_wi, end_wi = find_match_in_words(suffix, tokens, word_indices, cursor)
            if start_wi is not None:
                for wi in range(start_wi, end_wi + 1):
                    ti = word_indices[wi]
                    tokens[ti]["strong"] = strong
                cursor = end_wi + 1
                matched = True
                break

        if not matched:
            # 3. Fallback : mot LSG original — progressif par suffixe aussi
            orig_sub_words = lsg_word.split()
            for n in range(1, len(orig_sub_words) + 1):
                suffix = orig_sub_words[-n:]
                if n == 1 and len(suffix[0]) < 3:
                    continue
                start_wi, end_wi = find_match_in_words(suffix, tokens, word_indices, cursor)
                if start_wi is not None:
                    for wi in range(start_wi, end_wi + 1):
                        ti = word_indices[wi]
                        tokens[ti]["strong"] = strong
                    cursor = end_wi + 1
                    matched = True
                    break

        if not matched and sub_words:
            # 4. Fuzzy match sur le dernier sous-mot
            last_word = sub_words[-1]
            fuzzy_ti = find_fuzzy_match_token(last_word, tokens, word_indices, cursor)
            if fuzzy_ti is not None:
                tokens[fuzzy_ti]["strong"] = strong
                cursor = word_indices.index(fuzzy_ti) + 1
                matched = True

        # Nom propre : la BYM translittère l'hébreu (Hanowk, Yitzhak, Yéshoua) au lieu de
        # franciser (Hénoc, Isaac, Josué). Le « translit » du lexique est alors bien plus
        # proche du mot BYM que le mot LSG ⇒ on apparie par squelette translittéré, AVANT le
        # dico appris (peu fiable pour les noms : il capte des voisins « qui »/« père »). Le
        # dico reste en repli pour les noms dont la graphie BYM diverge trop de la translit.
        if not matched and lexicon and is_proper_type(lexicon.get(strong, {}).get("type", "")):
            tr_ti = find_translit_match(lexicon[strong].get("translit", ""), tokens, word_indices, cursor)
            if tr_ti is not None:
                tokens[tr_ti]["strong"] = strong
                cursor = max(cursor, word_indices.index(tr_ti) + 1)
                matched = True

        if not matched and strong_to_bym:
            # 5. Dictionnaire global : chercher le gloss BYM connu pour ce code
            # Cherche dans TOUT le texte (pas seulement apres le curseur)
            # pour trouver les mots BYM non encore assignes
            # Priorite 1 : le mot substitue (s'il y a eu substitution)
            # Priorite 2 : le gloss du dictionnaire, puis les variantes
            entry = strong_to_bym.get(strong)
            candidates = []
            if was_substituted and expected_word:
                candidates.append(expected_word)
            if entry:
                # Les variantes MANUELLES (curées) priment sur la glose auto : une
                # expression multi-mots humaine (« mit autour », « laissa en location »)
                # doit l'emporter sur la glose statistique courte (« une », « pour »)
                # qui sinon capture gloutonnement un article.
                manual = entry.get("manual", [])
                dict_gloss = entry.get("gloss", "")
                variants = entry.get("variants", [])
                for v in manual + [dict_gloss] + variants:
                    if v and v not in candidates:
                        candidates.append(v)
            # Pour un nom propre, le dico appris contient des voisins parasites en
            # minuscule (« qui »/« père »/« lui »). En repli (la translit a échoué), on
            # ne garde que les candidats capitalisés — un vrai nom l'est toujours.
            if lexicon and is_proper_type(lexicon.get(strong, {}).get("type", "")):
                candidates = [c for c in candidates if c[:1].isupper()]
            for candidate in candidates:
                if not candidate or len(candidate) < 2:
                    continue
                dict_sub_words = candidate.split()
                # D'abord chercher apres le curseur
                start_wi, end_wi = find_match_in_words(dict_sub_words, tokens, word_indices, cursor, max_lookahead=7)
                if start_wi is None:
                    # Sinon chercher depuis le debut (mots non assignes avant le curseur)
                    start_wi, end_wi = find_match_in_words(dict_sub_words, tokens, word_indices, 0, max_lookahead=999)
                if start_wi is not None:
                    for wi in range(start_wi, end_wi + 1):
                        ti = word_indices[wi]
                        tokens[ti]["strong"] = strong
                    cursor = max(cursor, end_wi + 1)
                    matched = True
                    break

        if not matched and lexicon:
            # 6. Définition du Strong's : la BYM traduit le SENS hébreu (suit la définition
            # du lexique, contrairement à la LSG qui paraphrase). On cherche un mot BYM libre
            # qui correspond à une glose fiable de la définition — UNIQUEMENT pour les types
            # de contenu (verbe/nom commun/adjectif/adverbe). Les noms propres relèvent de la
            # translittération, et les mots-outils (pronom/préposition/conjonction/particule)
            # sont le plancher non récupérable (faux positifs « ceux/plus/contre »).
            entry = lexicon.get(strong)
            if entry and is_content_type(entry.get("type", "")):
                stems = extract_definition_stems(entry.get("definition", ""))
                if stems:
                    def_ti = find_definition_match(stems, tokens, word_indices, cursor)
                    if def_ti is not None:
                        tokens[def_ti]["strong"] = strong
                        cursor = max(cursor, word_indices.index(def_ti) + 1)
                        matched = True

        if not matched and lexicon:
            # 7. Nombres : la BYM écrit les nombres en chiffres (« 30 », « 300 ») et garde la
            # décomposition additive hébraïque en tokens séparés, là où le code Strong porte un
            # mot-nombre — les étapes mot-à-mot échouent donc toujours. On apparie par valeur.
            entry = lexicon.get(strong)
            definition = entry.get("definition", "") if entry else ""
            if definition and is_numeric_definition(definition):
                values = extract_number_values(definition)
                if values:
                    num_ti = find_number_match(values, tokens, word_indices, cursor)
                    if num_ti is not None:
                        tokens[num_ti]["strong"] = strong
                        cursor = max(cursor, word_indices.index(num_ti) + 1)
                        matched = True

        # Si toujours pas de match → ajouter comme segment non aligné
        if not matched:
            unmatched.append({"text": None, "strong": strong, "gloss": lsg_word})

    # Fusionner les tokens en segments
    aligned = merge_tokens(tokens)
    
    # Ajouter les unmatched à la fin
    return aligned + unmatched


def find_match_in_words(lsg_sub_words, tokens, word_indices, cursor, max_lookahead=5):
    """
    Cherche une position dans word_indices où les sous-mots LSG correspondent
    aux mots BYM consécutifs. Retourne (start_wi, end_wi) ou (None, None).
    """
    n = len(lsg_sub_words)
    if n == 0:
        return None, None

    max_start = min(cursor + max_lookahead, len(word_indices) - n + 1)

    for start in range(cursor, max_start):
        match = True
        for j in range(n):
            wi = start + j
            if wi >= len(word_indices):
                match = False
                break
            ti = word_indices[wi]
            if tokens[ti]["strong"] is not None:
                match = False  # déjà assigné
                break
            norm_lsg = normalize(lsg_sub_words[j])
            norm_bym = normalize(tokens[ti]["text"])
            if norm_lsg != norm_bym:
                # Match par inclusion (gère les articles : "Elohîm" dans "l'Elohîm")
                if len(norm_lsg) >= 4 and len(norm_bym) >= 4:
                    if norm_lsg in norm_bym or norm_bym in norm_lsg:
                        continue
                match = False
                break
        if match:
            return start, start + n - 1

    return None, None


def find_fuzzy_match_token(lsg_word, tokens, word_indices, cursor, max_lookahead=5, max_dist=2):
    """Cherche un match flou parmi les word_indices à partir de cursor."""
    norm_lsg = normalize(lsg_word)
    if not norm_lsg or len(norm_lsg) < 4:
        return None

    max_wi = min(cursor + max_lookahead, len(word_indices))
    for wi in range(cursor, max_wi):
        ti = word_indices[wi]
        if tokens[ti]["strong"] is not None:
            continue
        norm_bym = normalize(tokens[ti]["text"])
        if not norm_bym or len(norm_bym) < 4:
            continue
        # Exiger un préfixe commun d'au moins 3 caractères
        common_prefix = 0
        for a, b in zip(norm_lsg, norm_bym):
            if a == b:
                common_prefix += 1
            else:
                break
        if common_prefix < 3:
            continue
        if levenshtein(norm_lsg, norm_bym) <= max_dist:
            return ti
    return None


def merge_tokens(tokens):
    """
    Fusionne les tokens en segments, en regroupant les mots consécutifs
    qui partagent le même code Strong's (en incluant les séparateurs entre eux).
    """
    segments = []
    i = 0

    while i < len(tokens):
        tok = tokens[i]

        if tok["strong"] is not None:
            # Mot avec Strong's → chercher les mots suivants avec le même code
            text = tok["text"]
            strong = tok["strong"]
            j = i + 1
            while j < len(tokens) - 1:
                # Le token j doit être un séparateur et j+1 un mot avec le même strong
                if (not tokens[j]["is_word"] and
                        tokens[j + 1]["is_word"] and
                        tokens[j + 1]["strong"] == strong):
                    text += tokens[j]["text"] + tokens[j + 1]["text"]
                    j += 2
                else:
                    break
            segments.append({"text": text, "strong": strong})
            i = j
        elif not tok["is_word"]:
            # Séparateur → segment null
            # Fusionner avec les séparateurs suivants
            text = tok["text"]
            j = i + 1
            while j < len(tokens) and not tokens[j]["is_word"] and tokens[j]["strong"] is None:
                text += tokens[j]["text"]
                j += 1
            # Fusionner aussi avec un mot null adjacent
            if j < len(tokens) and tokens[j]["is_word"] and tokens[j]["strong"] is None:
                text += tokens[j]["text"]
                j += 1
                # Continuer à fusionner les séparateurs et mots null suivants
                while j < len(tokens):
                    if not tokens[j]["is_word"]:
                        if j + 1 < len(tokens) and tokens[j + 1]["is_word"] and tokens[j + 1]["strong"] is None:
                            text += tokens[j]["text"] + tokens[j + 1]["text"]
                            j += 2
                        else:
                            break
                    elif tokens[j]["is_word"] and tokens[j]["strong"] is None:
                        text += tokens[j]["text"]
                        j += 1
                    else:
                        break
            segments.append({"text": text, "strong": None})
            i = j
        else:
            # Mot sans Strong's → segment null
            segments.append({"text": tok["text"], "strong": None})
            i += 1

    return segments


# ─── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Génère db/strongs/bym_strongs.json (aligné)")
    parser.add_argument("--sqlite", help="Chemin vers strong.sqlite (évite le téléchargement)")
    parser.add_argument("--output", default=OUTPUT_PATH)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # 1. Charger les données
    if args.sqlite:
        sqlite_path = args.sqlite
    else:
        sqlite_path = "/tmp/strong.sqlite"
        if not os.path.exists(sqlite_path):
            download(STRONG_SQLITE_URL, sqlite_path)

    print(f"\nLecture : {sqlite_path}")
    conn = sqlite3.connect(sqlite_path)

    with open(THEBYM_PATH, encoding="utf-8") as f:
        bym = json.load(f)
    print(f"BYM : {len(bym)} versets")

    with open(GLOSS_MAPPING_PATH, encoding="utf-8") as f:
        gloss_mapping = json.load(f)
    print(f"Gloss mapping : {len(gloss_mapping)} codes Strong")

    strong_to_bym = {}
    if os.path.exists(STRONG_TO_BYM_PATH):
        with open(STRONG_TO_BYM_PATH, encoding="utf-8") as f:
            strong_to_bym = json.load(f)
        print(f"Dictionnaire Strong→BYM : {len(strong_to_bym)} codes")

    lexicon = {}
    lexicon_path = os.path.join(BASE_DIR, "db", "strongs", "lexicon.json")
    if os.path.exists(lexicon_path):
        with open(lexicon_path, encoding="utf-8") as f:
            lexicon = json.load(f)
        print(f"Lexique : {len(lexicon)} entrées")

    overrides = {}
    if os.path.exists(OVERRIDES_PATH):
        with open(OVERRIDES_PATH, encoding="utf-8") as f:
            overrides = json.load(f)
        print(f"Overrides : {len(overrides)} versets")

    # 2. Parser LSG et aligner
    strongs = {}
    stats = {"total": 0, "aligned": 0, "override": 0, "skipped": 0}

    # Décalages de versification NON marqués (détectés par detect_versif_offsets.py).
    #   • versif : (abbr_sans_espace, chap, verset_LSG) -> delta (BYM cible = verset_LSG + delta)
    #   • versif_pairs : clé_LSG complète -> clé_BYM (bords cross-chapitre, ex. Ge 31:55 -> Ge 32:1)
    versif = {}
    versif_pairs = {}
    if os.path.exists(VERSIF_OFFSETS_PATH):
        vo = json.load(open(VERSIF_OFFSETS_PATH, encoding="utf-8"))
        for r in vo.get("regions", []):
            for v in range(r["from"], r["to"] + 1):
                versif[(r["book"], r["chap"], v)] = r["delta"]
        for lk, bk in vo.get("pairs", []):
            versif_pairs[lk] = bk
        print(f"Décalages versification : {len(versif)} versets + {len(versif_pairs)} bords cross-chapitre")

    # ── Phase 1 : collecte des morceaux de texte LSG, regroupés par verset BYM ──
    # La numérotation LSG diffère parfois de la BYM (versification hébraïque). Deux mécanismes
    # rattachent un verset LSG au bon verset BYM :
    #   • marqueurs « (C.V) » dans le texte LSG (frontières explicites, gèrent les splits) ;
    #   • décalages détectés (versif_offsets.json) pour les zones NON marquées (ex. Genèse 32).
    # Chaque morceau porte une priorité (marqueur > offset > natif) pour arbitrer les collisions
    # de bord (le verset natif juste avant une zone à δ<0 viserait le même verset BYM que le 1er
    # verset décalé) : on garde alors le morceau décalé, pas le natif déplacé.
    PRIO = {"marker": 3, "offset": 2, "native": 1}
    bym_pieces = {}  # clé BYM -> {"is_at": bool, "pieces": [(prio, ordre, texte)]}
    order = 0
    for book in range(1, 67):
        is_at = book <= OT_MAX_BOOK
        table = "LSGSAT2" if is_at else "LSGSNT2"
        abbr = BOOK_NUM_TO_ABBR[book - 1]

        cur = conn.cursor()
        cur.execute(f"SELECT Chapitre, Verset, Texte FROM {table} WHERE Livre=? ORDER BY Chapitre, Verset", (book,))

        for chap, verse, lsg_text in cur.fetchall():
            stats["total"] += 1
            native_key = f"{abbr}{chap}:{verse}"
            text = lsg_text or ""

            if VERSIF_MARKER_ANY_RE.search(text):
                tagged = [(bkey, piece, "marker")
                          for bkey, piece in split_lsg_by_markers(text, native_key, abbr)]
            elif native_key in versif_pairs:
                # bord cross-chapitre : cible BYM explicite (prime sur offset/natif)
                tagged = [(versif_pairs[native_key], text, "offset")]
            else:
                d = versif.get((abbr.strip(), chap, verse))
                if d:
                    tagged = [(f"{abbr}{chap}:{verse + d}", text, "offset")]
                else:
                    tagged = [(native_key, text, "native")]

            for bkey, piece, prio in tagged:
                order += 1
                entry = bym_pieces.setdefault(bkey, {"is_at": is_at, "pieces": []})
                entry["pieces"].append((PRIO[prio], order, piece))

    conn.close()

    # ── Phase 2 : alignement de chaque verset BYM contre son texte propre ──
    for bkey, data in bym_pieces.items():
        # Override ?
        if bkey in overrides:
            strongs[bkey] = overrides[bkey]
            stats["override"] += 1
            continue

        pieces = data["pieces"]
        prios = {p[0] for p in pieces}
        if PRIO["marker"] in prios:
            chosen = pieces  # un marqueur est présent → accumulation intentionnelle (split/merge)
        elif PRIO["offset"] in prios and PRIO["native"] in prios:
            chosen = [p for p in pieces if p[0] == PRIO["offset"]]  # offset prime sur natif déplacé
        else:
            chosen = pieces
        combined = "".join(p[2] for p in sorted(chosen, key=lambda p: p[1]))

        bym_text = bym.get(bkey)
        if not bym_text or not combined.strip():
            stats["skipped"] += 1
            continue

        lsg_segments = parse_lsg_segments(combined, data["is_at"])
        aligned = align_segments(lsg_segments, bym_text, gloss_mapping, strong_to_bym, lexicon)
        strongs[bkey] = aligned
        stats["aligned"] += 1

    # ── Phase 3 : comblement — tout verset BYM resté sans entrée reçoit son texte en
    # segment null (texte complet préservé, simplement non tagué). Évite les trous laissés
    # par les merges/splits et garantit que chaque verset BYM existe dans la sortie.
    for bkey, text in bym.items():
        if bkey not in strongs:
            strongs[bkey] = [{"text": text, "strong": None}]
            stats["filled"] = stats.get("filled", 0) + 1

    # 3. Rapport
    print(f"\n=== Rapport ===")
    print(f"  Total versets LSG : {stats['total']}")
    print(f"  Alignés           : {stats['aligned']}")
    print(f"  Overrides         : {stats['override']}")
    print(f"  Ignorés (pas BYM) : {stats['skipped']}")
    print(f"  Comblés (null)    : {stats.get('filled', 0)}")

    # Statistiques de couverture Strong's
    total_segs = 0
    tagged_segs = 0
    for key, segs in strongs.items():
        for s in segs:
            total_segs += 1
            if s["strong"]:
                tagged_segs += 1
    print(f"  Segments totaux   : {total_segs}")
    print(f"  Segments tagués   : {tagged_segs} ({100*tagged_segs/max(total_segs,1):.1f}%)")

    # 4. Écrire
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(strongs, f, ensure_ascii=False, indent=None, separators=(",", ":"))
    print(f"\nÉcrit : {args.output} ({os.path.getsize(args.output)} bytes)")

    # Vérifications
    print("\n=== Vérifications ===")
    for key in ["Ge. 1:1", "Jn. 3:16", "Ro. 1:1"]:
        segs = strongs.get(key, [])
        text = "".join(s.get("text") or "" for s in segs)
        bym_text = bym.get(key, "")
        match = "✅" if text == bym_text else "❌"
        tagged = sum(1 for s in segs if s["strong"])
        print(f"  {key}: {len(segs)} segments, {tagged} tagués, texte {match}")
        if text != bym_text:
            print(f"    BYM : {repr(bym_text[:80])}")
            print(f"    OUT : {repr(text[:80])}")


if __name__ == "__main__":
    main()