#!/usr/bin/env python3
"""
build_lsg.py — Construit le texte Louis Segond 1910 + segments Strong's natifs.

Le texte LSG dans strong.sqlite contient les numéros Strong's inline :
  AT : "Au commencement 07225, Dieu 0430 créa 01254 (8804) 0853 les cieux 08064"
  NT : "Au 1722 commencement 746 était 2258 (5713) la Parole 3056"

Génère deux fichiers :
  - db/lsg.json              : texte pur (sans codes Strong's)
  - db/strongs/lsg_strongs.json : segments [{text, strong}] par verset

Usage :
    python3 scripts/build_lsg.py --sqlite /tmp/strong.sqlite
"""

import argparse
import json
import os
import re
import sqlite3
import sys

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
LSG_PATH = os.path.join(BASE_DIR, "db", "lsg.json")
LSG_STRONGS_PATH = os.path.join(BASE_DIR, "db", "strongs", "lsg_strongs.json")

# Table de correspondance numéro de livre → abréviation (même ordre que build_strongs.py)
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


def load_lsg_glosses(sqlite_path):
    """Charge les glosses LSG depuis les tables Hebreu et Grec de strong.sqlite.
    Retourne un dict: code (ex: 'H7225') → liste de glosses nets (ex: ['commencement', 'prémices', ...])
    """
    glosses = {}
    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()

    # Hébreu
    cur.execute("SELECT Code, LSG FROM Hebreu")
    for code, lsg in cur.fetchall():
        gloss_list = []
        # Format: "gloss1, gloss2 freq, gloss3, ...; total_count"
        # Séparer les glosses du compte total
        parts = lsg.split(';')[0] if ';' in lsg else lsg
        for g in parts.split(','):
            g = g.strip()
            if not g or g == '...':
                continue
            # Retirer les nombres de fréquence (ex: "Dieu 2425" → "Dieu")
            g = re.sub(r'\s+\d+$', '', g).strip()
            if g:
                gloss_list.append(g)
        if gloss_list:
            glosses[f"H{code}"] = gloss_list

    # Grec
    cur.execute("SELECT Code, LSG FROM Grec")
    for code, lsg in cur.fetchall():
        gloss_list = []
        parts = lsg.split(';')[0] if ';' in lsg else lsg
        for g in parts.split(','):
            g = g.strip()
            if not g or g == '...':
                continue
            g = re.sub(r'\s+\d+$', '', g).strip()
            if g:
                gloss_list.append(g)
        if gloss_list:
            glosses[f"G{code}"] = gloss_list

    conn.close()
    return glosses


def find_gloss_in_text(text, gloss_list):
    """Cherche le meilleur gloss dans le texte. Retourne (start, end) du match, ou None.
    Passe 1: match exact sur TOUS les glosses (priorise les plus longs).
    Passe 2: match sans parenthèses (terre(s) → terre).
    Passe 3: match par préfixe/stem — seulement si aucun match exact trouvé.
    """
    if not gloss_list:
        return None

    text_stripped = text.strip()
    text_lower_stripped = text_stripped.lower()
    leading = len(text) - len(text.lstrip())

    # Trier les glosses par longueur décroissante (privilégier les glosses les plus longs/spécifiques)
    sorted_glosses = sorted(gloss_list, key=len, reverse=True)

    # --- Passe 1: match exact (insensible à la casse) sur tous les glosses ---
    for gloss in sorted_glosses:
        gloss_lower = gloss.lower()
        idx = text_lower_stripped.find(gloss_lower)
        if idx >= 0:
            return (leading + idx, leading + idx + len(gloss))

    # --- Passe 2: match sans parenthèses: "terre(s)" → "terre" ---
    for gloss in sorted_glosses:
        gloss_lower = gloss.lower()
        gloss_no_paren = re.sub(r'\([^)]+\)', '', gloss_lower).strip()
        if gloss_no_paren and gloss_no_paren != gloss_lower:
            idx = text_lower_stripped.find(gloss_no_paren)
            if idx >= 0:
                return (leading + idx, leading + idx + len(gloss_no_paren))

    # --- Passe 3: match par préfixe/stem — seulement si aucun match exact ---
    for gloss in sorted_glosses:
        gloss_lower = gloss.lower()
        if len(gloss_lower) >= 5:
            stem = gloss_lower[:4]  # 4 premiers caractères
            idx = text_lower_stripped.find(stem)
            if idx > 0:  # > 0 pour éviter de matcher au tout début
                # Étendre le match jusqu'à la fin du mot
                end = idx + len(stem)
                while end < len(text_lower_stripped) and text_lower_stripped[end].isalpha():
                    end += 1
                # Vérifier que c'est bien un stem du gloss (pas juste un préfixe commun)
                matched_word = text_lower_stripped[idx:end]
                if gloss_lower.startswith(matched_word[:3]) and len(matched_word) > 4:
                    return (leading + idx, leading + end)

    return None


def parse_verse(text, is_at, lsg_glosses=None):
    """
    Parse un verset LSG avec Strong's inline en segments [{text, strong}].

    Format du texte : "mot 0CODE, next_mot 0CODE2 (morpho)"
    Le code Strong's est placé APRÈS le mot qu'il décrit.

    Utilise les glosses LSG (champ LSG des tables Hebreu/Grec) pour identifier
    quel(s) mot(s) correspond(ent) réellement à chaque code, et séparer les
    mots fonctionnels (articles, prépositions) en segments null.

    Produit des segments INLINE comme bym_strongs.json :
    - Segments avec code = mot(s) décrits par le code (+ ponctuation de fin)
    - Segments null = espaces, ponctuation et mots fonctionnels
    - La concaténation de tous les text = texte exact du verset
    """
    TRAILING_PUNCT = re.compile(r'^([,.;:!?…»«"\)\]]+)')

    if is_at:
        pattern = re.compile(r'(?:^|\s+)(\d{4,6})(?:\s*\(\d+\))?(?=\s|$|[^\d])')
    else:
        pattern = re.compile(r'(?:^|\s+)(\d{1,5})(?:\s*\(\d+\))?(?=\s|$|[^\d])')

    matches = list(pattern.finditer(text))
    if not matches:
        return [{"text": text, "strong": None}]

    segments = []

    for i, m in enumerate(matches):
        raw_code = m.group(1)
        if is_at:
            code = "H" + str(int(raw_code))
        else:
            code = "G" + raw_code

        # Texte avant ce code (depuis la fin du match précédent)
        if i == 0:
            before = text[:m.start()]
        else:
            before = text[matches[i - 1].end():m.start()]

        # 1. Extraire la ponctuation de tête (appartient au mot précédent)
        punct_match = TRAILING_PUNCT.match(before)
        if punct_match:
            trailing_punct = punct_match.group(1)
            rest = before[punct_match.end():]
            if segments:
                segments[-1]["text"] += trailing_punct
            else:
                segments.append({"text": trailing_punct, "strong": None})
        else:
            rest = before

        # 2. Extraire les espaces de tête → segment null
        space_match = re.match(r'^(\s+)', rest)
        if space_match:
            spaces = space_match.group(1)
            rest = rest[space_match.end():]
            segments.append({"text": spaces, "strong": None})

        # 3. Identifier le bon mot pour ce code via les glosses LSG
        word_text = rest.strip()

        if lsg_glosses and code in lsg_glosses and word_text:
            gloss_list = lsg_glosses[code]
            match_pos = find_gloss_in_text(word_text, gloss_list)
            if match_pos:
                g_start, g_end = match_pos
                # Texte avant le gloss (mots fonctionnels) → null
                before_gloss = word_text[:g_start]
                if before_gloss:
                    segments.append({"text": before_gloss, "strong": None})
                # Le gloss lui-même → tagged
                gloss_text = word_text[g_start:g_end]
                segments.append({"text": gloss_text, "strong": code})
                # Texte après le gloss → null
                after_gloss = word_text[g_end:]
                if after_gloss:
                    segments.append({"text": after_gloss, "strong": None})
            else:
                # Pas de gloss trouvé → garder tout le texte taggé (fallback)
                segments.append({"text": word_text, "strong": code})
        else:
            # Pas de glosses disponibles ou texte vide → garder tel quel
            if word_text or code:
                segments.append({"text": word_text, "strong": code})

    # Texte restant après le dernier code
    after_last = text[matches[-1].end():]
    if after_last:
        punct_match = TRAILING_PUNCT.match(after_last)
        if punct_match:
            trailing_punct = punct_match.group(1)
            rest = after_last[punct_match.end():]
            if segments:
                segments[-1]["text"] += trailing_punct
            else:
                segments.append({"text": trailing_punct, "strong": None})
        else:
            rest = after_last

        rest = rest.strip()
        if rest:
            segments.append({"text": rest, "strong": None})

    # Nettoyer : stripper les espaces en tête et en queue du texte concaténéré
    concat = ''.join(seg["text"] for seg in segments)
    stripped = concat.strip()
    if stripped != concat:
        leading = len(concat) - len(concat.lstrip())
        trailing = len(concat) - len(concat.rstrip())
        # Retirer les caractères de tête
        remaining = leading
        i = 0
        while remaining > 0 and i < len(segments):
            seg = segments[i]
            if seg["strong"] is not None and not seg["text"]:
                # Code orphelin avec texte vide → le garder, passer au suivant
                i += 1
                continue
            if len(seg["text"]) <= remaining:
                remaining -= len(seg["text"])
                segments.pop(i)
            else:
                seg["text"] = seg["text"][remaining:]
                remaining = 0
                i += 1
        # Retirer les caractères de queue
        remaining = trailing
        j = len(segments) - 1
        while remaining > 0 and j >= 0:
            seg = segments[j]
            if seg["strong"] is not None and not seg["text"]:
                j -= 1
                continue
            if len(seg["text"]) <= remaining:
                remaining -= len(seg["text"])
                segments.pop(j)
                j -= 1
            else:
                seg["text"] = seg["text"][:len(seg["text"]) - remaining] if remaining > 0 else seg["text"]
                remaining = 0
                j -= 1

    return segments


def clean_text(segments):
    """Concatène les segments inline pour obtenir le texte pur.
    Les segments contiennent déjà les espaces et la ponctuation."""
    return ''.join(seg["text"] for seg in segments)


def main():
    parser = argparse.ArgumentParser(description="Build LSG 1910 text + Strong's segments")
    parser.add_argument("--sqlite", default="/tmp/strong.sqlite", help="Path to strong.sqlite")
    args = parser.parse_args()

    if not os.path.exists(args.sqlite):
        print(f"Erreur: {args.sqlite} non trouvé", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(args.sqlite)
    cur = conn.cursor()

    # Charger les glosses LSG pour identifier le bon mot par code
    lsg_glosses = load_lsg_glosses(args.sqlite)
    print(f"Glosses LSG: {len(lsg_glosses)} codes")

    lsg = {}          # texte pur
    lsg_strongs = {}  # segments avec Strong's

    total_versets = 0
    total_codes = 0

    for book_num in range(1, 67):
        abbr = BOOK_NUM_TO_ABBR[book_num - 1]
        is_at = book_num <= OT_MAX_BOOK
        table = "LSGSAT2" if is_at else "LSGSNT2"

        cur.execute(
            f"SELECT Chapitre, Verset, Texte FROM {table} WHERE Livre=? ORDER BY Chapitre, Verset",
            (book_num,)
        )
        rows = cur.fetchall()
        book_versets = 0

        for chap, verset, texte in rows:
            key = f"{abbr}{chap}:{verset}"
            segments = parse_verse(texte, is_at, lsg_glosses)
            clean = clean_text(segments)

            lsg[key] = clean
            lsg_strongs[key] = segments

            book_versets += 1
            total_codes += sum(1 for s in segments if s["strong"])

        total_versets += book_versets
        print(f"  {abbr.strip():>8s} : {book_versets:5d} versets")

    conn.close()

    # Sauvegarder lsg.json
    os.makedirs(os.path.dirname(LSG_PATH), exist_ok=True)
    with open(LSG_PATH, "w", encoding="utf-8") as f:
        json.dump(lsg, f, ensure_ascii=False)
    lsg_size = os.path.getsize(LSG_PATH) / 1024 / 1024

    # Sauvegarder lsg_strongs.json
    os.makedirs(os.path.dirname(LSG_STRONGS_PATH), exist_ok=True)
    with open(LSG_STRONGS_PATH, "w", encoding="utf-8") as f:
        json.dump(lsg_strongs, f, ensure_ascii=False)
    strongs_size = os.path.getsize(LSG_STRONGS_PATH) / 1024 / 1024

    print(f"\nTotal : {total_versets} versets, {total_codes} codes Strong's")
    print(f"Écrit : {LSG_PATH} ({lsg_size:.1f} MB)")
    print(f"Écrit : {LSG_STRONGS_PATH} ({strongs_size:.1f} MB)")

    # Vérification d'intégrité sur quelques versets
    print("\n=== Vérification ===")
    for key in ["Ge. 1:1", "Jn. 1:1", "Ps. 1:1"]:
        if key in lsg_strongs:
            segs = lsg_strongs[key]
            print(f"\n{key} :")
            print(f"  texte  : {lsg[key]}")
            print(f"  segments :")
            for s in segs:
                print(f"    {s['strong'] or '----':>7s}  « {s['text'][:40]} »")


if __name__ == "__main__":
    main()