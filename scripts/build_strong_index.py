#!/usr/bin/env python3
"""
build_strong_index.py — Construit l'index inversé Strong's → versets.

Pour chaque code Strong's, liste tous les versets BYM qui le contiennent,
avec le texte du verset. Évite les doublons (un verset avec le même code
plusieurs fois n'apparaît qu'une fois).

Output : db/strongs/strong_index.json

Usage :
    python3 scripts/build_strong_index.py
"""

import argparse
import json
import os
import re
from collections import defaultdict

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
BYM_STRONGS_PATH = os.path.join(BASE_DIR, "db", "strongs", "bym_strongs.json")
BYM_PATH = os.path.join(BASE_DIR, "db", "thebym.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "db", "strongs", "strong_index.json")

# Table abréviation → nom complet du livre (pour la réponse API)
BOOK_NAMES = {
    "Ge.": "Genese", "Ex.": "Exode", "Lé.": "Levitique", "No.": "Nombres",
    "De.": "Deuteronome", "Jos.": "Josue", "Jg.": "Juges",
    "1 S.": "1 Samuel", "2 S.": "2 Samuel", "1 R.": "1 Rois", "2 R.": "2 Rois",
    "Es.": "Esaie", "Jé.": "Jeremie", "Ez.": "EzechieL",
    "Os.": "Osee", "Joë.": "JoeL", "Am.": "Amos", "Ab.": "Abdias",
    "Jon.": "Jonas", "Mi.": "Michee", "Na.": "Nahum", "Ha.": "Habakuk",
    "So.": "Sophonie", "Ag.": "Aggee", "Za.": "Zacharie", "Mal.": "Malachie",
    "Ps.": "Psaumes", "Pr.": "Proverbes", "Job": "Job", "Ca.": "Cantique",
    "Ru.": "Ruth", "La.": "Lamentations", "Ec.": "Ecclesiaste",
    "Est.": "Esther", "Da.": "Daniel", "Esd.": "Esdras", "Né.": "Nehemie",
    "1 Ch.": "1 Chroniques", "2 Ch.": "2 Chroniques",
    "Mt.": "Matthieu", "Mc.": "Marc", "Lu.": "Luc", "Jn.": "Jean",
    "Ac.": "Actes", "Ja.": "Jacques", "Ga.": "Galates",
    "1 Th.": "1 Thessaloniciens", "2 Th.": "2 Thessaloniciens",
    "1 Co.": "1 Corinthiens", "2 Co.": "2 Corinthiens", "Ro.": "Romains",
    "Ep.": "Ephesiens", "Ph.": "Philippiens", "Col.": "Colossiens",
    "Phm.": "Philemon", "1 Ti.": "1 Timothee", "Tit.": "Tite",
    "1 Pi.": "1 Pierre", "2 Pi.": "2 Pierre", "2 Ti.": "2 Timothee",
    "Jud.": "Judas", "Hé.": "Hebreux",
    "1 Jn.": "1 Jean", "2 Jn.": "2 Jean", "3 Jn.": "3 Jean", "Ap.": "Apocalypse",
}


def parse_verse_key(key):
    """Parse 'Jn. 1:1' → ('Jn.', 1, 1) ou 'Job 3:2' → ('Job', 3, 2)."""
    # Format : ABBR CHAP:VERSET (ex: "Ge. 1:1", "1 S. 1:2", "Job 3:2")
    m = re.match(r'^(.+?)\s+(\d+):(\d+)$', key)
    if not m:
        return None, None, None
    abbr = m.group(1).strip()
    chap = int(m.group(2))
    verset = int(m.group(3))
    return abbr, chap, verset


def main():
    parser = argparse.ArgumentParser(description="Index inversé Strong's → versets (par version)")
    parser.add_argument("--strongs", default=BYM_STRONGS_PATH,
                        help="Fichier de segments Strong's en entrée (défaut: bym_strongs.json)")
    parser.add_argument("--out", default=OUTPUT_PATH,
                        help="Fichier d'index en sortie (défaut: strong_index.json)")
    args = parser.parse_args()

    # Charger l'alignement
    with open(args.strongs, encoding="utf-8") as f:
        strongs = json.load(f)

    print(f"Chargé: {len(strongs)} versets alignés depuis {os.path.basename(args.strongs)}")

    # Construire l'index : code → liste de clés de versets (format "Jn. 1:1")
    # Le texte BYM est récupéré côté API depuis thebym.json (déjà chargé en mémoire)
    index = defaultdict(list)
    seen = defaultdict(set)  # Pour éviter les doublons (même verset + même code)

    for key, segments in strongs.items():
        abbr, chap, verset = parse_verse_key(key)
        if abbr is None:
            continue

        for seg in segments:
            code = seg.get("strong")
            if not code:
                continue
            # Éviter les doublons : un verset n'apparaît qu'une fois par code
            verse_id = f"{key}:{code}"
            if verse_id in seen[code]:
                continue
            seen[code].add(verse_id)

            index[code].append(key)

    # Convertir en dict ordonné (par fréquence décroissante)
    index = dict(sorted(index.items(), key=lambda x: -len(x[1])))

    # Sauvegarder
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)

    size_mb = os.path.getsize(args.out) / 1024 / 1024
    print(f"\nIndex: {len(index)} codes Strong's")
    print(f"Écrit: {args.out} ({size_mb:.1f} MB)")

    # Stats
    top5 = list(index.items())[:5]
    print(f"\nTop 5:")
    for code, verses in top5:
        print(f"  {code:7s} → {len(verses)} versets")


if __name__ == "__main__":
    main()