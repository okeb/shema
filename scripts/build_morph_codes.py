#!/usr/bin/env python3
"""
build_morph_codes.py — Génère db/strongs/morph_codes.json : table de résolution
des codes grammaticaux Strong's (« Online Bible » / TVM) en libellés français.

Ces codes (hébreu 8673–8819, grec 5612–5928) apparaissent entre parenthèses
dans le texte LSG inline de strong.sqlite, ex. « créa 01254 (8804) ». Ils ne
sont PAS dans strong.sqlite ni dans bible-strong → la table est dérivée de
studybible.info (qui décompose chaque code) :
  - Hébreu : Stem (binyan) + Mood (aspect)   ex. H8804 = Qal + Perfect
  - Grec   : Tense + Voice + Mood             ex. G5713 = Imperfect + (no voice) + Indicative

Provenance : studybible.info/strongs/<CODE> (champ « Strong's: … »).
La table est figée (la grammaire ne change pas) → à committer comme donnée de
référence ; ce script ne sert qu'à la (re)générer.

Usage :
    # à partir du dump déjà récupéré (recommandé, pas de re-scraping)
    python3 scripts/build_morph_codes.py --raw /tmp/morph_raw.json
    # ou en re-scrapant studybible.info pour les codes présents dans le sqlite
    python3 scripts/build_morph_codes.py --sqlite /tmp/strong.sqlite
"""
import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
OUT_PATH = os.path.join(BASE_DIR, "db", "strongs", "morph_codes.json")

# --- Traductions FR ---------------------------------------------------------
# Stems (binyanim) : translittérations standard, conservées telles quelles.
STEM_FR = {}  # identité ; on normalise juste « Or » → « ou »

MOOD_FR = {
    "Perfect": "accompli", "Imperfect": "inaccompli", "Imperative": "impératif",
    "Infinitive": "infinitif", "Participle": "participe",
    "Participle Active": "participe actif", "Participle Passive": "participe passif",
    "Participle Peil": "participe Peil",
    "Indicative": "indicatif", "Subjunctive": "subjonctif", "Optative": "optatif",
    "Impersonal": "impersonnel",
}
TENSE_FR = {
    "Aorist": "aoriste", "Second Aorist": "aoriste second",
    "Future": "futur", "Second Future": "futur second",
    "Imperfect": "imparfait", "Perfect": "parfait", "Second Perfect": "parfait second",
    "Pluperfect": "plus-que-parfait", "Second Pluperfect": "plus-que-parfait second",
    "Present": "présent", "No Tense Stated": None,
}
VOICE_FR = {
    "Active": "actif", "Middle": "moyen", "Passive": "passif",
    "Middle Deponent": "moyen déponent", "Passive Deponent": "passif déponent",
    "Middle or Passive Deponent": "moyen/passif déponent",
    "Either Middle or Passive": "moyen ou passif", "No Voice Stated": None,
}

# Codes « méta » (variantes de lecture / double analyse) : pas de stem/mood.
VARIANTS = {
    "H8675": "double analyse (Kethiv/Qeré)",
    "H8676": "deux numéros Strong (analyse alternative)",
    "H8677": "deux numéros Strong + grammaire",
    "H8678": "variante (deux analyses)",
    "G5625": "deux numéros Strong (variante)",
}


def stem_fr(s):
    return STEM_FR.get(s, s.replace(" Or ", " ou "))


def label(code, parsed):
    """Construit l'entrée résolue {fr, type, ...} à partir des champs studybible."""
    if code in VARIANTS:
        return {"fr": VARIANTS[code], "type": "variant", "variant": True}

    if "Stem" in parsed:  # Hébreu : Stem + Mood(aspect)
        stem = stem_fr(parsed["Stem"])
        aspect = MOOD_FR.get(parsed.get("Mood", ""), parsed.get("Mood", ""))
        fr = f"{stem} {aspect}".strip()
        return {"fr": fr, "type": "hebrew", "stem": stem, "aspect": aspect}

    # Grec : Tense + Voice + Mood
    tense = TENSE_FR.get(parsed.get("Tense", ""), parsed.get("Tense"))
    voice = VOICE_FR.get(parsed.get("Voice", ""), parsed.get("Voice"))
    mood = MOOD_FR.get(parsed.get("Mood", ""), parsed.get("Mood"))
    parts = [p for p in (tense, voice, mood) if p]
    out = {"fr": " ".join(parts), "type": "greek"}
    if tense:
        out["tense"] = tense
    if voice:
        out["voice"] = voice
    if mood:
        out["mood"] = mood
    return out


# --- Scraping (optionnel) ---------------------------------------------------
def scrape(codes):
    def fetch(code):
        url = f"https://studybible.info/strongs/{code}"
        for _ in range(3):
            try:
                html = subprocess.run(["curl", "-fsSL", url], capture_output=True,
                                      timeout=40).stdout.decode("utf-8", "replace")
                head = html.split("<details>")[0]
                txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", head))
                parsed = {}
                for field in ("Stem", "Tense", "Voice", "Mood"):
                    m = re.search(field + r"\s*-\s*(.*?)\s*See\s*\{", txt)
                    if m:
                        parsed[field] = m.group(1).strip()
                return code, {"parsed": parsed}
            except Exception:
                continue
        return code, {"parsed": {}}

    out = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for code, data in ex.map(fetch, codes):
            out[code] = data
    return out


def codes_from_sqlite(path):
    import sqlite3
    c = sqlite3.connect(path); cur = c.cursor()
    heb, grc = set(), set()
    for (t,) in cur.execute("SELECT Texte FROM LSGSAT2"):
        heb.update(re.findall(r"\((\d+)\)", t))
    for (t,) in cur.execute("SELECT Texte FROM LSGSNT2"):
        grc.update(re.findall(r"\((\d+)\)", t))
    return [f"H{x}" for x in heb] + [f"G{x}" for x in grc]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", help="Dump JSON déjà récupéré (code -> {parsed})")
    ap.add_argument("--sqlite", default="/tmp/strong.sqlite")
    args = ap.parse_args()

    if args.raw and os.path.exists(args.raw):
        raw = json.load(open(args.raw, encoding="utf-8"))
    else:
        if not os.path.exists(args.sqlite):
            print("Ni --raw ni --sqlite disponible", file=sys.stderr); sys.exit(1)
        raw = scrape(codes_from_sqlite(args.sqlite))

    table, unresolved = {}, []
    for code, data in raw.items():
        parsed = data.get("parsed", {})
        if not parsed and code not in VARIANTS:
            unresolved.append(code)
            continue
        table[code] = label(code, parsed)

    table = dict(sorted(table.items(), key=lambda kv: (kv[0][0], int(kv[0][1:]))))
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    json.dump(table, open(OUT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"Codes résolus : {len(table)}")
    if unresolved:
        print(f"⚠️  Non résolus ({len(unresolved)}): {unresolved}", file=sys.stderr)
    print(f"Écrit : {OUT_PATH}")
    for c in ["H8804", "H8799", "H8762", "G5713", "G5719", "G5656"]:
        if c in table:
            print(f"  {c}: {table[c]['fr']}")


if __name__ == "__main__":
    main()
