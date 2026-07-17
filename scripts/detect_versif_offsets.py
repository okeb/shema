#!/usr/bin/env python3
"""
detect_versif_offsets.py — Détecte les décalages de versification LSG↔BYM **non marqués**.

La BYM suit la numérotation hébraïque, la LSG la numérotation chrétienne. Certains décalages
sont annotés dans le texte LSG par un marqueur « (C.V) » (gérés directement par build_strongs)
— mais d'autres ne le sont pas (ex. Genèse 32, Exode 22, Daniel 4…).

Comme LSG et BYM sont **deux traductions françaises**, on détecte ces décalages par recouvrement
de mots : le verset LSG c:v « matche » mieux le BYM c:(v+δ). On ne retient un δ≠0 que s'il est
nettement meilleur que δ=0, et seulement pour des **runs** de versets consécutifs (évite les faux
positifs isolés). Les versets déjà marqués « (C.V) » sont ignorés (déjà traités).

En plus des régions (décalages internes à un chapitre), on résout les **bords cross-chapitre** :
le 1er/dernier verset d'une zone décalée a sa source dans le chapitre voisin (ex. BYM Ge 32:1 =
LSG Ge 31:55 ; LSG Ex 22:1 = BYM Ex 21:37). On les détecte par recouvrement contre le chapitre
adjacent et on les émet comme paires explicites (clé_LSG -> clé_BYM).

Sortie : db/strongs/versif_offsets.json — objet
    {"regions": [{"book":"Ge.","chap":32,"from":1,"to":32,"delta":1,"overlap":0.69}, ...],
     "pairs":   [["Ge. 31:55","Ge. 32:1"], ["Ex. 22:1","Ex. 21:37"], ...]}

Usage :
    python3 scripts/detect_versif_offsets.py
"""

import json
import os
import re
import unicodedata
from collections import defaultdict

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
LSG_PATH = os.path.join(BASE_DIR, "db", "lsg.json")
BYM_PATH = os.path.join(BASE_DIR, "db", "thebym.json")
OUT_PATH = os.path.join(BASE_DIR, "db", "strongs", "versif_offsets.json")

MARKER_RE = re.compile(r"\(\d+\.\d+\)")
KEY_RE = re.compile(r"^(.+?)\s+(\d+):(\d+)$")

# Seuils de détection
MIN_OVERLAP = 0.40   # recouvrement minimal au meilleur δ pour le croire
MIN_GAIN = 0.25      # gain minimal du meilleur δ sur δ=0
MIN_RUN = 3          # longueur minimale d'un run pour être retenu
MAX_GAP = 2          # trou max (versets) toléré pour fusionner deux runs de même δ
DELTAS = (-3, -2, -1, 1, 2, 3)


def norm(t):
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def words(t):
    return {w for w in re.findall(r"[a-z]{4,}", norm(MARKER_RE.sub("", t or "")))}


def overlap(a, b):
    A, B = words(a), words(b)
    return len(A & B) / min(len(A), len(B)) if A and B else 0.0


def main():
    lsg = json.load(open(LSG_PATH, encoding="utf-8"))
    bym = json.load(open(BYM_PATH, encoding="utf-8"))

    # (abbr, chap) -> ensemble des versets LSG
    chapters = defaultdict(set)
    for k in lsg:
        m = KEY_RE.match(k)
        if m:
            chapters[(m.group(1), int(m.group(2)))].add(int(m.group(3)))

    def best_delta(abbr, c, v):
        """Retourne (delta, overlap) du meilleur appariement ; (0, s0) si pas de décalage net."""
        key = f"{abbr} {c}:{v}"
        if MARKER_RE.search(lsg.get(key, "")):
            return None  # déjà géré par marqueur
        s0 = overlap(lsg[key], bym.get(key, ""))
        best = (0, s0)
        for d in DELTAS:
            bk = f"{abbr} {c}:{v + d}"
            if bk in bym:
                s = overlap(lsg[key], bym[bk])
                if s > best[1]:
                    best = (d, s)
        d, sb = best
        if d != 0 and sb >= MIN_OVERLAP and sb - s0 >= MIN_GAIN:
            return (d, sb)
        return (0, s0)

    # 1. δ par verset
    per_verse = {}  # (abbr,c) -> {v: (delta, overlap)}
    for (abbr, c), vs in chapters.items():
        per_verse[(abbr, c)] = {v: best_delta(abbr, c, v) for v in vs}

    # 2. Runs de même δ≠0 (longueur >= MIN_RUN)
    raw_regions = []
    for (abbr, c), vmap in per_verse.items():
        seq = sorted(vmap)
        run = []

        def flush(run):
            if len(run) >= MIN_RUN:
                d = run[0][1]
                raw_regions.append([abbr, c, run[0][0], run[-1][0], d,
                                    round(sum(r[2] for r in run) / len(run), 2)])

        cur_d = None
        for v in seq:
            r = vmap[v]
            if r is None or r[0] == 0:
                flush(run); run = []; cur_d = None
                continue
            d, s = r
            if cur_d == d:
                run.append((v, d, s))
            else:
                flush(run); run = [(v, d, s)]; cur_d = d
        flush(run)

    # 3. Fusion des runs de même (livre, chap, δ) séparés par un petit trou,
    #    en étendant le δ aux versets du trou (qui appartiennent au même bloc décalé).
    raw_regions.sort()
    merged = []
    for reg in raw_regions:
        abbr, c, a, b, d, ov = reg
        if merged:
            m = merged[-1]
            if m[0] == abbr and m[1] == c and m[4] == d and a - m[3] - 1 <= MAX_GAP:
                m[3] = b
                m[5] = round((m[5] + ov) / 2, 2)
                continue
        merged.append(reg)

    regions = [{"book": r[0], "chap": r[1], "from": r[2], "to": r[3],
                "delta": r[4], "overlap": r[5]} for r in merged]

    # 4. Bords cross-chapitre : le 1er (δ>0) ou les |δ| premiers (δ<0) versets d'une zone
    #    décalée ont leur source dans le chapitre voisin. On apparie par recouvrement contre
    #    les derniers versets du chapitre adjacent.
    def chap_verses(d, abbr, c):
        out = []
        for k in d:
            m = re.match(rf"^{re.escape(abbr)} {c}:(\d+)$", k)
            if m:
                out.append(int(m.group(1)))
        return sorted(out)

    pairs = {}  # clé_LSG -> (clé_BYM, overlap)
    for r in merged:
        abbr, c, F, L, d, _ = r
        if d > 0:
            # BYM c:1..d  <-  meilleur verset LSG de la fin du chapitre c-1
            for bv in range(1, 1 + d):
                bk = f"{abbr} {c}:{bv}"
                if bk not in bym:
                    continue
                best = None
                for lv in chap_verses(lsg, abbr, c - 1)[-4:]:
                    lk = f"{abbr} {c - 1}:{lv}"
                    s = overlap(lsg.get(lk, ""), bym[bk])
                    if best is None or s > best[1]:
                        best = (lk, s)
                if best and best[1] >= MIN_OVERLAP:
                    pairs[best[0]] = (bk, round(best[1], 2))
        else:
            # LSG c:1..|δ| déplacés  ->  meilleur verset BYM de la fin du chapitre c-1
            for lv in range(1, 1 - d):
                lk = f"{abbr} {c}:{lv}"
                if lk not in lsg:
                    continue
                best = None
                for bv in chap_verses(bym, abbr, c - 1)[-4:]:
                    bk = f"{abbr} {c - 1}:{bv}"
                    s = overlap(lsg[lk], bym.get(bk, ""))
                    if best is None or s > best[1]:
                        best = (bk, s)
                if best and best[1] >= MIN_OVERLAP:
                    pairs[lk] = (best[0], round(best[1], 2))

    pair_list = [[lk, bk] for lk, (bk, _) in sorted(pairs.items())]

    out = {"regions": regions, "pairs": pair_list}
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    total_verses = sum(r["to"] - r["from"] + 1 for r in regions)
    print(f"Régions de décalage non marqué détectées : {len(regions)} "
          f"({total_verses} versets)")
    for r in sorted(regions, key=lambda x: (x["book"], x["chap"], x["from"])):
        print(f"  {r['book']} {r['chap']}:{r['from']}-{r['to']}  "
              f"δ={r['delta']:+d}  (overlap≈{r['overlap']})")
    print(f"\nBords cross-chapitre appariés : {len(pair_list)}")
    for lk, bk in pair_list:
        print(f"  LSG {lk}  ->  BYM {bk}")
    print(f"\nÉcrit : {OUT_PATH}")


if __name__ == "__main__":
    main()
