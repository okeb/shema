#!/usr/bin/env python3
"""
build_darby.py — Construit le texte de la Bible Darby (J.N. Darby, 1885).

Source : midvash/bible-data (public domain), slug `darby-fr`.
  https://raw.githubusercontent.com/midvash/bible-data/main/versions/fr/darby-fr/darby-fr.json

Schéma source : { version, name, books: [ { book (OSIS), bookId, chapters: [
{ chapter, verses: [ { number, text } ] } ] } ] }

Sortie : db/darby.json  →  { "Ge. 1:1": "Au commencement Dieu créa les cieux et la terre." }
Même schéma de clés que db/thebym.json et db/lsg.json (abbr projet + " chap:verse").

La versification Darby = protestante canonique 66 livres, identique à Segond/LSG.
Pas de Strong's natifs → version servie texte seul (strongs: false côté API).

Usage :
    python3 scripts/build_darby.py
"""

import json
import os
import re
import sys
import urllib.request

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DARBY_PATH = os.path.join(BASE_DIR, "db", "darby.json")

SOURCE_URL = (
    "https://raw.githubusercontent.com/midvash/bible-data/main/"
    "versions/fr/darby-fr/darby-fr.json"
)
CACHE = "/tmp/darby-fr.json"

# OSIS / variantes → abréviation projet (ordre des 66 livres, cf. build_lsg.py).
# On tolère plusieurs codes source possibles par livre (robustesse).
OSIS_TO_ABBR = {
    "Gen": "Ge.", "Gen": "Ge.",
    "Exod": "Ex.", "Ex": "Ex.",
    "Lev": "Lé.", "Lev": "Lé.",
    "Num": "No.", "Num": "No.",
    "Deut": "De.", "Deut": "De.",
    "Josh": "Jos.", "Josh": "Jos.",
    "Judg": "Jg.", "Judg": "Jg.",
    "Ruth": "Ru.", "Ruth": "Ru.",
    "1Sam": "1 S.", "1Sam": "1 S.",
    "2Sam": "2 S.", "2Sam": "2 S.",
    "1Kgs": "1 R.", "1Kgs": "1 R.",
    "2Kgs": "2 R.", "2Kgs": "2 R.",
    "1Chr": "1 Ch.", "1Chr": "1 Ch.",
    "2Chr": "2 Ch.", "2Chr": "2 Ch.",
    "Ezra": "Esd.", "Ezra": "Esd.",
    "Neh": "Né.", "Neh": "Né.",
    "Esth": "Est.", "Esth": "Est.",
    "Job": "Job",
    "Ps": "Ps.", "Pss": "Ps.", "Psalm": "Ps.",
    "Prov": "Pr.", "Prov": "Pr.",
    "Eccl": "Ec.", "Eccl": "Ec.", "Eccles": "Ec.",
    "Song": "Ca.", "Song": "Ca.", "Cant": "Ca.", "SongOfSol": "Ca.", "SongOfSongs": "Ca.",
    "Isa": "Es.", "Isa": "Es.", "Isai": "Es.",
    "Jer": "Jé.", "Jer": "Jé.", "Jerem": "Jé.",
    "Lam": "La.", "Lam": "La.",
    "Ezek": "Ez.", "Ezek": "Ez.", "Ezek": "Ez.",
    "Dan": "Da.", "Dan": "Da.",
    "Hos": "Os.", "Hos": "Os.",
    "Joel": "Joë.", "Joel": "Joë.",
    "Amos": "Am.", "Amos": "Am.",
    "Obad": "Ab.", "Obad": "Ab.", "Obadiah": "Ab.",
    "Jonah": "Jon.", "Jonah": "Jon.",
    "Mic": "Mi.", "Mic": "Mi.", "Micah": "Mi.",
    "Nah": "Na.", "Nah": "Na.", "Nahum": "Na.",
    "Hab": "Ha.", "Hab": "Ha.", "Habakkuk": "Ha.",
    "Zeph": "So.", "Zeph": "So.", "Zeph": "So.",
    "Hag": "Ag.", "Hag": "Ag.", "Haggai": "Ag.",
    "Zech": "Za.", "Zech": "Za.", "Zech": "Za.",
    "Mal": "Mal.", "Mal": "Mal.", "Malachi": "Mal.",
    "Matt": "Mt.", "Matt": "Mt.", "Matthew": "Mt.",
    "Mark": "Mc.", "Mark": "Mc.",
    "Luke": "Lu.", "Luke": "Lu.",
    "John": "Jn.", "John": "Jn.",
    "Acts": "Ac.", "Acts": "Ac.",
    "Rom": "Ro.", "Rom": "Ro.", "Romans": "Ro.",
    "1Cor": "1 Co.", "1Cor": "1 Co.",
    "2Cor": "2 Co.", "2Cor": "2 Co.",
    "Gal": "Ga.", "Gal": "Ga.", "Galatians": "Ga.",
    "Eph": "Ep.", "Eph": "Ep.", "Ephesians": "Ep.",
    "Phil": "Ph.", "Phil": "Ph.", "Philippians": "Ph.",
    "Col": "Col.", "Col": "Col.", "Colossians": "Col.",
    "1Thess": "1 Th.", "1Thess": "1 Th.",
    "2Thess": "2 Th.", "2Thess": "2 Th.",
    "1Tim": "1 Ti.", "1Tim": "1 Ti.",
    "2Tim": "2 Ti.", "2Tim": "2 Ti.",
    "Titus": "Tit.", "Titus": "Tit.",
    "Phlm": "Phm.", "Phlm": "Phm.", "Philemon": "Phm.",
    "Heb": "Hé.", "Heb": "Hé.", "Hebrews": "Hé.",
    "Jas": "Ja.", "Jas": "Ja.", "James": "Ja.",
    "1Pet": "1 Pi.", "1Pet": "1 Pi.", "1Peter": "1 Pi.",
    "2Pet": "2 Pi.", "2Pet": "2 Pi.", "2Peter": "2 Pi.",
    "1John": "1 Jn.", "1John": "1 Jn.",
    "2John": "2 Jn.", "2John": "2 Jn.",
    "3John": "3 Jn.", "3John": "3 Jn.",
    "Jude": "Jud.", "Jude": "Jud.",
    "Rev": "Ap.", "Rev": "Ap.", "Revelation": "Ap.",
}


def fetch():
    if os.path.exists(CACHE):
        print(f"Cache: {CACHE}")
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    print(f"Téléchargement: {SOURCE_URL}")
    # urllib échoue parfois en vérif SSL sur macOS (certificats système absents).
    # On tente urllib d'abord, puis repli sur curl si échec.
    try:
        import ssl
        ctx = ssl.create_default_context()
        urllib.request.urlretrieve(SOURCE_URL, CACHE)
    except Exception as e:
        print(f"urllib a échoué ({e}); repli sur curl…")
        import subprocess
        r = subprocess.run(["curl", "-sSf", "-o", CACHE, SOURCE_URL])
        if r.returncode != 0:
            sys.exit("Échec du téléchargement (urllib + curl).")
    with open(CACHE, encoding="utf-8") as f:
        return json.load(f)


def main():
    data = fetch()
    name = data.get("name", "?")
    license_ = data.get("license", "?")
    print(f"Source: {name} — licence: {license_}")

    out = {}
    seen_abbr = set()
    unmapped = []
    for book in data.get("books", []):
        osis = book.get("book") or book.get("bookId")
        abbr = OSIS_TO_ABBR.get(osis)
        if not abbr:
            unmapped.append(osis)
            continue
        seen_abbr.add(abbr)
        for ch in book.get("chapters", []):
            chap = ch.get("chapter")
            for v in ch.get("verses", []):
                num = v.get("number")
                text = (v.get("text") or "").strip()
                # La source midvash utilise DEUX caractères étoile distincts :
                #  • '*' (U+002A) — marque de début de paragraphe, en tête de verset
                #    (*Et, *La, **Et…) ou entre deux mots sans espace (« Éternel*Dieu »).
                #    On remplace par une espace puis on collapse pour ne pas coller
                #    les mots.
                #  • '✶' (U+2736, 375 occurrences) — marqueur de révérence devant le
                #    nom divin : « ✶Seigneur », « ✶Dieu » (toujours collé au mot qui
                #    suit, précédé d'une espace). On le supprime simplement (il y a
                #    déjà une espace devant) : « le ✶Seigneur » → « le Seigneur ».
                text = re.sub(r"\*+", " ", text)
                text = text.replace("✶", "")
                # Défaut source : le composé « Éternel Dieu » (YHWH Elohim) apparaît
                # collé sans espace « ÉternelDieu » (38 occurrences, ex. Ge.2:4, Ge.3:1).
                # On rétablit l'espace avant la consolidation des espaces.
                text = text.replace("ÉternelDieu", "Éternel Dieu")
                text = re.sub(r"\s{2,}", " ", text).strip()
                key = f"{abbr} {chap}:{num}"
                out[key] = text

    # Rapport
    expected_abbr = set(OSIS_TO_ABBR.values())
    missing = sorted(expected_abbr - seen_abbr)
    print(f"\nVersets écrits : {len(out)}")
    print(f"Livres reconnus : {len(seen_abbr)}/66")
    if missing:
        print(f"⚠️  Livres manquants : {missing}")
    if unmapped:
        print(f"⚠️  Codes OSIS non mappés : {sorted(set(unmapped))}")

    # Contrôle cohérence vs LSG (même versification protestante)
    lsg_path = os.path.join(BASE_DIR, "db", "lsg.json")
    if os.path.exists(lsg_path):
        lsg = json.load(open(lsg_path, encoding="utf-8"))
        only_lsg = set(lsg) - set(out)
        only_darby = set(out) - set(lsg)
        print(f"\nComparaison LSG ({len(lsg)} vs Darby {len(out)} versets):")
        print(f"  Versets dans LSG absents de Darby : {len(only_lsg)}")
        print(f"  Versets dans Darby absents de LSG  : {len(only_darby)}")
        if only_lsg:
            print(f"  ex LSG-only : {sorted(only_lsg)[:5]}")
        if only_darby:
            print(f"  ex Darby-only : {sorted(only_darby)[:5]}")

    with open(DARBY_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nÉcrit : {DARBY_PATH} ({os.path.getsize(DARBY_PATH)} bytes)")
    print("\nSpot-check :")
    for k in ("Ge. 1:1", "Jn. 3:16", "Ge. 1:2", "Ap. 22:21"):
        print(f"  {k}: {out.get(k, '<<manquant>>')!r}")


if __name__ == "__main__":
    main()