#!/usr/bin/env python3
"""
build_lsg_native.py — Construit les segments Strong's LSG à partir de la
**concordance native** de strong.sqlite (position des codes), sans glosses.

Différence avec build_lsg.py :
  - build_lsg.py        : re-devine quel mot porte le code via les glosses LSG
                          (find_gloss_in_text, matching flou). Approche pensée
                          pour la BYM (qui n'a aucun alignement natif).
  - build_lsg_native.py : utilise la position brute. Dans strong.sqlite chaque
                          code est placé JUSTE APRÈS le(s) mot(s) qu'il décrit :
                            "Au commencement 07225, Dieu 0430 créa 01254 (8804) ..."
                          => le run de mots qui précède un code lui appartient.
                          C'est exact, déterministe et sans perte.

Règles du parseur « brut » :
  - chaque numéro Strong's prend le run de mots qui le précède (jusqu'au code
    précédent) ;
  - les codes morpho entre parenthèses « (8804) » sont écartés (grammaire) ;
  - un code « nu » sans mot devant (ex. 0853 = את, objet non traduit) devient un
    segment taggé à texte vide {"text": "", "strong": code} — position préservée ;
  - la ponctuation de fin (« , » « . ») se rattache au groupe de mots précédent ;
  - les espaces inter-mots sont des segments null.

Invariant garanti : concat(seg["text"]) == texte exact du verset.

Flag --refine : couche NON destructive qui sort uniquement les mots-outils en
tête de groupe (au, le, la, les, et, de…) vers un segment null, sans jamais
déplacer ni supprimer un code. Pire cas = le groupe natif entier (jamais une
erreur de mapping).

Flag --last-word : concordance stricte. Ne garde que le DERNIER mot du groupe (le
mot placé juste avant le code dans la source), tout le reste de la phrase (entre ce
code et le précédent) repassant en segment null. Englobe --refine et prime sur lui.
À utiliser pour que la concordance (et les bulles du lecteur) ne surlignent que le
mot porteur du code, pas la phrase entière. Le texte rendu et la liste des codes
restent strictement identiques (invariant préservé).

Sorties (par défaut, à CÔTÉ des fichiers de build_lsg.py — rien n'est écrasé) :
  - db/lsg.json                          (texte pur ; identique quelle que soit la méthode)
  - db/strongs/lsg_strongs_native.json   (segments natifs)

Usage :
    python3 scripts/build_lsg_native.py --sqlite /tmp/strong.sqlite
    python3 scripts/build_lsg_native.py --sqlite /tmp/strong.sqlite --refine
    python3 scripts/build_lsg_native.py --sqlite /tmp/strong.sqlite --refine \
        --out db/strongs/lsg_strongs.json --text-out db/lsg.json   # pour remplacer
"""

import argparse
import json
import os
import re
import sqlite3
import sys

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")

# Table de correspondance numéro de livre → abréviation (même ordre que build_strongs.py / build_lsg.py)
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

# Ponctuation qui se rattache au mot/groupe précédent.
TRAILING_PUNCT = re.compile(r'^([,.;:!?…»«"\)\]]+)')

# Mots-outils français pris en tête de groupe par --refine (forme minuscule, sans ponctuation).
FUNCTION_WORDS = {
    "au", "aux", "le", "la", "les", "un", "une", "des", "du",
    "de", "et", "à", "en", "dans", "par", "pour", "avec", "sur",
    "ce", "cet", "cette", "ces", "ne", "que", "se", "sa", "son", "ses",
    "ou", "or", "ni", "car", "donc", "puis", "comme",
}


def parse_verse_native(text, is_at, morph_map=None):
    """Parse un verset LSG (codes Strong's inline) en segments [{text, strong}]
    par POSITION native. Aucun gloss. Invariant : concat(text) == texte du verset.

    Si morph_map est fourni, le code grammatical « (8804) » qui suit un code Strong's
    est résolu en libellé FR et ajouté au segment sous la clé "morph"."""
    lang = "H" if is_at else "G"
    if is_at:
        # Codes AT : 4 à 6 chiffres (avec zéros de tête). Morpho « (8804) » capturé.
        pattern = re.compile(r'(?:^|\s+)(\d{4,6})(?:\s*\((\d+)\))?(?=\s|$|[^\d])')
    else:
        # Codes NT : 1 à 5 chiffres. Morpho « (5713) » capturé.
        pattern = re.compile(r'(?:^|\s+)(\d{1,5})(?:\s*\((\d+)\))?(?=\s|$|[^\d])')

    matches = list(pattern.finditer(text))
    if not matches:
        return [{"text": text, "strong": None}]

    segments = []

    for i, m in enumerate(matches):
        raw_code = m.group(1)
        code = ("H" + str(int(raw_code))) if is_at else ("G" + raw_code)

        # Texte entre la fin du code précédent et le début de ce code.
        before = text[:m.start()] if i == 0 else text[matches[i - 1].end():m.start()]

        # 1. Ponctuation de tête → appartient au groupe précédent.
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

        # 2. Espaces de tête → segment null.
        space_match = re.match(r'^(\s+)', rest)
        if space_match:
            segments.append({"text": space_match.group(1), "strong": None})
            rest = rest[space_match.end():]

        # 3. Le run de mots restant = le texte de CE code (brut, sans découpe gloss).
        word_text = rest.strip()
        seg = {"text": word_text, "strong": code}
        if morph_map and m.group(2):
            fr = morph_map.get(lang + str(int(m.group(2))))
            if fr:
                seg["morph"] = fr
        segments.append(seg)

    # Texte après le dernier code.
    after_last = text[matches[-1].end():]
    if after_last:
        punct_match = TRAILING_PUNCT.match(after_last)
        if punct_match:
            if segments:
                segments[-1]["text"] += punct_match.group(1)
            else:
                segments.append({"text": punct_match.group(1), "strong": None})
            rest = after_last[punct_match.end():]
        else:
            rest = after_last
        rest = rest.strip()
        if rest:
            segments.append({"text": rest, "strong": None})

    return _strip_edges(segments)


def _strip_edges(segments):
    """Retire les espaces de tête/queue du texte concaténé, sans perdre de code."""
    concat = ''.join(s["text"] for s in segments)
    stripped = concat.strip()
    if stripped == concat:
        return segments

    leading = len(concat) - len(concat.lstrip())
    trailing = len(concat) - len(concat.rstrip())

    # Tête
    remaining, i = leading, 0
    while remaining > 0 and i < len(segments):
        seg = segments[i]
        if seg["strong"] is not None and not seg["text"]:
            i += 1
            continue
        if len(seg["text"]) <= remaining:
            remaining -= len(seg["text"])
            segments.pop(i)
        else:
            seg["text"] = seg["text"][remaining:]
            remaining = 0
            i += 1
    # Queue
    remaining, j = trailing, len(segments) - 1
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
            seg["text"] = seg["text"][:len(seg["text"]) - remaining]
            remaining = 0
            j -= 1
    return segments


def _norm_word(token):
    """Minuscule + retrait de la ponctuation pour tester l'appartenance à FUNCTION_WORDS."""
    return re.sub(r"[^0-9a-zàâäéèêëîïôöùûüçœ'\-]", "", token.lower())


def refine_segment(seg):
    """Sort les mots-outils en tête d'un groupe taggé vers un segment null.
    Ne touche jamais au code (ni à son champ morph) ; garde toujours ≥ 1 mot de
    contenu taggé. Préserve l'invariant : concat des sorties == seg["text"]."""
    text = seg["text"]
    content_seg = {k: v for k, v in seg.items()}  # copie (garde strong + morph)
    if not text.strip():
        return [content_seg]

    # Tokens = « mot + espaces qui suivent », pour préserver l'espacement exact.
    tokens = re.findall(r'\S+\s*', text)
    if len(tokens) <= 1:
        return [content_seg]

    lead, i = "", 0
    # On s'arrête à l'avant-dernier token pour garantir un contenu non vide.
    while i < len(tokens) - 1 and _norm_word(tokens[i].strip()) in FUNCTION_WORDS:
        lead += tokens[i]
        i += 1

    if not lead:
        return [content_seg]

    content_seg["text"] = "".join(tokens[i:])
    return [{"text": lead, "strong": None}, content_seg]


def apply_refine(segments):
    refined = []
    for seg in segments:
        if seg["strong"] and seg["text"].strip():
            refined.extend(refine_segment(seg))
        else:
            refined.append(seg)
    return refined


def lastword_segment(seg):
    """Réduit un groupe taggé à son DERNIER mot — celui placé juste avant le code
    Strong's dans la concordance native. Toute la portion de phrase comprise entre ce
    code et le code précédent (mots-outils + mots ajoutés par la traduction) repasse
    dans un segment null. C'est la règle « concordance = le seul mot avant le code »,
    plus stricte que --refine (qui ne sortait que les mots-outils connus).

    Garde toujours ≥ 1 mot de contenu taggé, préserve strong + morph, et l'invariant :
    concat des sorties == seg["text"]."""
    text = seg["text"]
    content_seg = {k: v for k, v in seg.items()}  # copie (garde strong + morph)
    if not text.strip():
        return [content_seg]

    # Tokens = « mot + espaces qui suivent », pour préserver l'espacement exact.
    tokens = re.findall(r'\S+\s*', text)
    if len(tokens) <= 1:
        return [content_seg]

    lead = "".join(tokens[:-1])
    content_seg["text"] = tokens[-1]
    return [{"text": lead, "strong": None}, content_seg]


def apply_lastword(segments):
    out = []
    for seg in segments:
        if seg["strong"] and seg["text"].strip():
            out.extend(lastword_segment(seg))
        else:
            out.append(seg)
    return out


def main():
    parser = argparse.ArgumentParser(description="Build LSG Strong's segments (native positional)")
    parser.add_argument("--sqlite", default="/tmp/strong.sqlite", help="Chemin vers strong.sqlite")
    parser.add_argument("--refine", action="store_true", help="Sortir les mots-outils en tête de groupe")
    parser.add_argument("--last-word", action="store_true", dest="last_word",
                        help="Concordance stricte : ne garder que le dernier mot avant chaque code "
                             "(le reste du groupe repasse en segment null). Prime sur --refine.")
    parser.add_argument("--morph", action="store_true",
                        help="Résoudre le code grammatical (8804…) en libellé FR (clé 'morph')")
    parser.add_argument("--morph-table", default=os.path.join(BASE_DIR, "db", "strongs", "morph_codes.json"),
                        help="Table de résolution des codes grammaticaux")
    parser.add_argument("--out", default=os.path.join(BASE_DIR, "db", "strongs", "lsg_strongs_native.json"),
                        help="Fichier de sortie des segments")
    parser.add_argument("--text-out", default=os.path.join(BASE_DIR, "db", "lsg.json"),
                        help="Fichier de sortie du texte pur")
    parser.add_argument("--no-text", action="store_true", help="Ne pas (re)générer le texte pur")
    args = parser.parse_args()

    if not os.path.exists(args.sqlite):
        print(f"Erreur: {args.sqlite} non trouvé", file=sys.stderr)
        sys.exit(1)

    morph_map = None
    if args.morph:
        if not os.path.exists(args.morph_table):
            print(f"Erreur: table morph {args.morph_table} absente "
                  f"(lancer build_morph_codes.py)", file=sys.stderr)
            sys.exit(1)
        raw = json.load(open(args.morph_table, encoding="utf-8"))
        morph_map = {k: v["fr"] for k, v in raw.items()}
        print(f"Table morph : {len(morph_map)} codes")

    conn = sqlite3.connect(args.sqlite)
    cur = conn.cursor()

    lsg = {}          # texte pur
    lsg_strongs = {}  # segments

    total_versets = total_codes = total_bad = total_morph = 0

    for book_num in range(1, 67):
        abbr = BOOK_NUM_TO_ABBR[book_num - 1]
        is_at = book_num <= OT_MAX_BOOK
        table = "LSGSAT2" if is_at else "LSGSNT2"

        cur.execute(
            f"SELECT Chapitre, Verset, Texte FROM {table} WHERE Livre=? ORDER BY Chapitre, Verset",
            (book_num,),
        )
        rows = cur.fetchall()

        for chap, verset, texte in rows:
            key = f"{abbr}{chap}:{verset}"
            segments = parse_verse_native(texte, is_at, morph_map)
            clean = ''.join(s["text"] for s in segments)

            if args.last_word:
                # Concordance stricte : un seul mot par code. Englobe (et donc prime sur)
                # le travail de --refine, qui ne sortait que les mots-outils connus.
                segments = apply_lastword(segments)
                if ''.join(s["text"] for s in segments) != clean:
                    total_bad += 1
                    print(f"  !! invariant cassé (last-word) : {key}", file=sys.stderr)
            elif args.refine:
                segments = apply_refine(segments)
                # Invariant : le refine ne change jamais le texte rendu.
                if ''.join(s["text"] for s in segments) != clean:
                    total_bad += 1
                    print(f"  !! invariant cassé (refine) : {key}", file=sys.stderr)

            lsg[key] = clean
            lsg_strongs[key] = segments
            total_versets += 1
            total_codes += sum(1 for s in segments if s["strong"])
            total_morph += sum(1 for s in segments if s.get("morph"))

        print(f"  {abbr.strip():>8s} : {len(rows):5d} versets")

    conn.close()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(lsg_strongs, f, ensure_ascii=False)
    out_mb = os.path.getsize(args.out) / 1024 / 1024

    if not args.no_text:
        os.makedirs(os.path.dirname(args.text_out), exist_ok=True)
        with open(args.text_out, "w", encoding="utf-8") as f:
            json.dump(lsg, f, ensure_ascii=False)

    print(f"\nTotal : {total_versets} versets, {total_codes} codes Strong's"
          f"{f', {total_morph} morph résolus' if args.morph else ''}"
          f"{' (last-word)' if args.last_word else ' (refine)' if args.refine else ''}")
    if total_bad:
        print(f"⚠️  {total_bad} versets avec invariant cassé — à investiguer", file=sys.stderr)
    print(f"Écrit : {args.out} ({out_mb:.1f} MB)")
    if not args.no_text:
        print(f"Écrit : {args.text_out}")

    # Vérif d'intégrité + affichage de quelques versets.
    print("\n=== Vérification (concat == texte) ===")
    for key in ["Ge. 1:1", "Jn. 1:1", "Ps. 1:1"]:
        if key in lsg_strongs:
            segs = lsg_strongs[key]
            ok = ''.join(s["text"] for s in segs) == lsg[key]
            print(f"\n{key} : {'OK' if ok else 'KO'}")
            print(f"  texte : {lsg[key]}")
            for s in segs:
                morph = f"  [{s['morph']}]" if s.get("morph") else ""
                print(f"    {s['strong'] or '----':>7s}  « {s['text']} »{morph}")


if __name__ == "__main__":
    main()
