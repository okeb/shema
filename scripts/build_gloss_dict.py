#!/usr/bin/env python3
"""
build_gloss_dict.py — Construit le dictionnaire global Strong's → gloss BYM.

Extrait les correspondances vérifiées depuis bym_strongs.json (l'auto-alignement
qui a réussi à matcher des codes Strong's avec des mots BYM).

Pour chaque code Strong's, agrège les mots BYM auxquels il a été associé et
garde le(s) plus fréquents comme gloss de référence.

Output : db/strongs/strong_to_bym.json

Usage :
    python3 scripts/build_gloss_dict.py
"""

import json
import os
import re
import unicodedata
from collections import Counter, defaultdict

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
BYM_STRONGS_PATH = os.path.join(BASE_DIR, "db", "strongs", "bym_strongs.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "db", "strongs", "strong_to_bym.json")
MANUAL_VARIANTS_PATH = os.path.join(BASE_DIR, "db", "strongs", "manual_variants.json")


def strip_accents(text):
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def clean_gloss(text):
    """Nettoie le texte BYM d'un segment pour extraire le gloss canonique."""
    # Retirer ponctuation en début/fin
    text = text.strip(",.;:!?()\"'[]\u00ab\u00bb \u2014\u2013-")
    return text


def main():
    with open(BYM_STRONGS_PATH, encoding="utf-8") as f:
        strongs = json.load(f)

    print(f"Chargé: {len(strongs)} versets alignés")

    # Extraire toutes les correspondances (code → texte BYM)
    correspondences = defaultdict(Counter)  # code → {bym_text: count}

    for key, segments in strongs.items():
        for seg in segments:
            strong = seg.get("strong")
            text = seg.get("text", "")
            if not strong or not text or not text.strip():
                continue

            gloss = clean_gloss(text)
            if gloss and len(gloss) >= 2:
                correspondences[strong][gloss] += 1

    print(f"Codes Strong's avec correspondances: {len(correspondences)}")

    # Construire le dictionnaire
    dictionary = {}
    for code, counts in correspondences.items():
        # Prendre le gloss le plus fréquent
        best_gloss, best_count = counts.most_common(1)[0]
        total = sum(counts.values())

        # Garder les variantes significatives (>10% du total, min 3 occurrences)
        variants = []
        for gloss, count in counts.most_common(10):
            if count >= max(3, total * 0.1):
                variants.append(gloss)

        dictionary[code] = {
            "gloss": best_gloss,
            "count": total,
            "confidence": round(best_count / total, 2),
            "variants": variants[:5],
        }

    # Trier par fréquence décroissante
    dictionary = dict(sorted(dictionary.items(), key=lambda x: -x[1]["count"]))

    # Fusionner les variantes manuelles. Elles vont dans un champ DÉDIÉ « manual »
    # (jamais écrasé par la régénération auto) que build_strongs essaie AVANT la glose
    # auto : une expression curée par un humain prime sur la glose statistique, qui est
    # souvent un mot-outil court (« une », « pour », « pays ») capturant gloutonnement
    # un article au lieu de laisser la vraie expression multi-mots matcher.
    if os.path.exists(MANUAL_VARIANTS_PATH):
        with open(MANUAL_VARIANTS_PATH, encoding="utf-8") as f:
            manual = json.load(f)
        added = 0
        for code, variants in manual.items():
            if code not in dictionary:
                dictionary[code] = {
                    "gloss": variants[0],
                    "count": 0,
                    "confidence": 0,
                    "variants": [],
                    "manual": list(variants),
                }
            else:
                dictionary[code]["manual"] = list(variants)
            added += len(variants)
        print(f"\nVariantes manuelles: {added} entrées (champ « manual », prioritaire)")

    # Sauvegarder
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dictionary, f, ensure_ascii=False, indent=2)

    print(f"\nDictionnaire: {len(dictionary)} codes Strong's")
    print(f"Écrit: {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH)} bytes)")

    # Statistiques
    high_conf = sum(1 for v in dictionary.values() if v["confidence"] >= 0.8)
    mid_conf = sum(1 for v in dictionary.values() if 0.5 <= v["confidence"] < 0.8)
    low_conf = sum(1 for v in dictionary.values() if v["confidence"] < 0.5)

    print(f"\nConfiance:")
    print(f"  Haute (≥80%): {high_conf} codes")
    print(f"  Moyenne (50-80%): {mid_conf} codes")
    print(f"  Basse (<50%): {low_conf} codes")

    # Top 20
    print(f"\nTop 20 correspondances:")
    for code, info in list(dictionary.items())[:20]:
        print(f"  {code:7s} → \"{info['gloss']}\" ({info['count']}x, {info['confidence']*100:.0f}%)")


if __name__ == "__main__":
    main()