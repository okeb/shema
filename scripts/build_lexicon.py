#!/usr/bin/env python3
"""
build_lexicon.py — Génère db/strongs/lexicon.json depuis strong.sqlite (bible-strong).

Télécharge strong.sqlite, lit les tables Hebreu + Grec, et produit un dictionnaire
indexé par code Strong canonique (ex: "H7225", "G2424").

Usage:
    python3 scripts/build_lexicon.py
    python3 scripts/build_lexicon.py --sqlite /path/to/strong.sqlite   # éviter le téléchargement
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import urllib.request

STRONG_SQLITE_URL = "https://assets.bible-strong.app/databases/strong.sqlite"
STRONG_SQLITE_FALLBACK = "https://storage.googleapis.com/bible-strong-app.appspot.com/databases/strong.sqlite"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "strongs", "lexicon.json")


def strip_html(text):
    """Nettoie les balises HTML et les entités courantes."""
    if not text:
        return ""
    # Remplacer <br> et <br/> par des nouvelles lignes
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    # Remplacer les balises de bloc par des nouvelles lignes
    text = re.sub(r"</?p[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"</?ol[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"</?ul[^>]*>", "\n", text, flags=re.I)
    # <li> → nouvelle ligne avec un tiret (liste à puette)
    text = re.sub(r"<li[^>]*>", "\n• ", text, flags=re.I)
    text = re.sub(r"</li>", "", text, flags=re.I)
    # Supprimer les balises img
    text = re.sub(r"<img[^>]*>", "", text, flags=re.I)
    # Supprimer toutes les autres balises restantes
    text = re.sub(r"<[^>]+>", "", text)
    # Entités HTML courantes
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&quot;", '"').replace("&#39;", "'")
    # Nettoyer les espaces et lignes vides
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]
    text = "\n".join(lines)
    return text


def download(url, dest):
    print(f"Téléchargement: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "shema-build-lexicon/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
    print(f"  → {os.path.getsize(dest)} bytes")


def build_from_hebrew(conn, lexicon):
    cur = conn.cursor()
    cur.execute("SELECT Code, Mot, Phonetique, Hebreu, Origine, Type, LSG, Definition FROM Hebreu")
    rows = cur.fetchall()
    count = 0
    for code, mot, phonetique, hebreu, origine, type_, lsg, definition in rows:
        if code == 0:
            continue
        key = f"H{code}"
        lexicon[key] = {
            "lemma": hebreu or "",
            "translit": mot or "",
            "phonetique": phonetique or "",
            "origine": strip_html(origine) if origine else "",
            "type": type_ or "",
            "definition": strip_html(definition) if definition else "",
            "lang": "hebrew",
        }
        count += 1
    print(f"  Hebreu: {count} entrées")
    return count


def build_from_greek(conn, lexicon):
    cur = conn.cursor()
    cur.execute("SELECT Code, Mot, Phonetique, Grec, Origine, Type, LSG, Definition FROM Grec")
    rows = cur.fetchall()
    count = 0
    for code, mot, phonetique, grec, origine, type_, lsg, definition in rows:
        if code == 0:
            continue
        key = f"G{code}"
        lexicon[key] = {
            "lemma": grec or "",
            "translit": mot or "",
            "phonetique": phonetique or "",
            "origine": strip_html(origine) if origine else "",
            "type": type_ or "",
            "definition": strip_html(definition) if definition else "",
            "lang": "greek",
        }
        count += 1
    print(f"  Grec: {count} entrées")
    return count


def main():
    parser = argparse.ArgumentParser(description="Génère db/strongs/lexicon.json")
    parser.add_argument("--sqlite", help="Chemin vers strong.sqlite (évite le téléchargement)")
    parser.add_argument("--output", default=OUTPUT_PATH, help="Chemin de sortie")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    if args.sqlite:
        sqlite_path = args.sqlite
    else:
        sqlite_path = "/tmp/strong.sqlite"
        if not os.path.exists(sqlite_path):
            download(STRONG_SQLITE_URL, sqlite_path)
            if os.path.getsize(sqlite_path) < 1_000_000:
                print("Premier téléchargement trop petit, essai du fallback...")
                download(STRONG_SQLITE_FALLBACK, sqlite_path)

    print(f"\nLecture: {sqlite_path}")
    conn = sqlite3.connect(sqlite_path)

    lexicon = {}
    build_from_hebrew(conn, lexicon)
    build_from_greek(conn, lexicon)
    conn.close()

    print(f"\nTotal entrées lexique: {len(lexicon)}")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(lexicon, f, ensure_ascii=False, indent=None, separators=(",", ":"))
    print(f"Écrit: {args.output} ({os.path.getsize(args.output)} bytes)")

    # Vérification rapide
    sample = lexicon.get("H7225")
    if sample:
        print(f"\nVérification H7225: lemma={sample['lemma']!r}, translit={sample['translit']!r}")
    sample = lexicon.get("G2424")
    if sample:
        print(f"Vérification G2424: lemma={sample['lemma']!r}, translit={sample['translit']!r}")


if __name__ == "__main__":
    main()