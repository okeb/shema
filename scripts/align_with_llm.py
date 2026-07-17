#!/usr/bin/env python3
"""
align_with_llm.py — Aligne les Strong's sur le texte BYM en utilisant un LLM (Ollama).

Pour chaque verset avec un faible taux de tags, envoie au LLM :
  - Le texte BYM
  - Les segments LSG (mot + code Strong)
  - Les substitutions connues (gloss_mapping.json)

Le LLM produit l'alignement BYM → Strong's, qui est validé puis sauvegardé
dans db/strongs/overrides.json.

Le script est reprendable : il charge les overrides existants et ne re-traite
pas les versets déjà corrigés.

Usage :
    python3 scripts/align_with_llm.py                    # tous les versets à corriger
    python3 scripts/align_with_llm.py --limit 100        # 100 versets seulement
    python3 scripts/align_with_llm.py --batch-size 5     # 5 versets par appel LLM
    python3 scripts/align_with_llm.py --model qwen2.5:14b
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
OVERRIDES_PATH = os.path.join(BASE_DIR, "db", "strongs", "overrides.json")
BYM_STRONGS_PATH = os.path.join(BASE_DIR, "db", "strongs", "bym_strongs.json")
GLOSS_MAPPING_PATH = os.path.join(BASE_DIR, "db", "strongs", "gloss_mapping.json")
THEBYM_PATH = os.path.join(BASE_DIR, "db", "thebym.json")

OLLAMA_URL = "http://localhost:11434/api/generate"

# Ordre Bible de Jérusalem (identique à build_strongs.py)
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


def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_lsg_segments_from_db(conn, book, chap, verse, is_at):
    """Récupère et parse les segments LSG depuis strong.sqlite."""
    cur = conn.cursor()
    table = "LSGSAT2" if is_at else "LSGSNT2"
    cur.execute(f"SELECT Texte FROM {table} WHERE Livre=? AND Chapitre=? AND Verset=?", (book, chap, verse))
    row = cur.fetchone()
    if not row:
        return []

    text = row[0]
    prefix = "H" if is_at else "G"
    max_code = 8674 if is_at else 5624

    if is_at:
        number_re = re.compile(r"0(\d{3,4})")
    else:
        number_re = re.compile(r"(?<=\s)(\d{1,5})(?=[\s'\-,.;:!?)\]]|$)")

    segments = []
    prev_end = 0
    for m in number_re.finditer(text):
        code_num = int(m.group(1))
        if code_num == 0 or code_num > max_code:
            continue
        raw = text[prev_end:m.start()]
        raw = re.sub(r"\(\d+\)", "", raw).strip()
        raw = raw.strip(",.;:!?()\"'[]\u00ab\u00bb \u2014\u2013-")
        segments.append({"word": raw, "strong": f"{prefix}{code_num}"})
        prev_end = m.end()

    return segments


def build_prompt(verses_data, gloss_mapping):
    """
    Construit le prompt pour le LLM.
    verses_data = [(key, bym_text, lsg_segments), ...]
    """
    prompt = """Tu es un expert en linguistique biblique. Ta tâche : aligner les codes Strong's sur le texte BYM (Bible de Yehoshoua Ha Mashiah).

Pour chaque verset, tu reçois :
1. Le texte BYM (la traduction cible)
2. Les segments de la traduction Louis Segond (LSG) avec leurs codes Strong's
3. Des substitutions connues (LSG → BYM)

Tu dois produire un alignement : découper le texte BYM en segments et assigner le code Strong's correspondant à chaque segment. Les segments avec null n'ont pas de code Strong's (mots ajoutés par la BYM, articles, etc.).

RÈGLES CRITIQUES :
- La concaténation de tous les "text" doit reproduire EXACTEMENT le texte BYM (caractère pour caractère)
- Un code Strong's peut couvrir plusieurs mots BYM (ex: "les cieux" = un seul code)
- Les marqueurs invisibles (H853, articles grecs G3588) n'ont pas de mot BYM → les ignorer
- Si un mot LSG ne correspond à aucun mot BYM, le code est perdu (ne pas forcer)

Substitutions connues (LSG → BYM) :
"""
    # Add gloss mapping
    for strong, mapping in gloss_mapping.items():
        if mapping:
            pairs = ", ".join(f'"{k}" → "{v}"' for k, v in mapping.items())
            prompt += f"  {strong}: {pairs}\n"

    prompt += "\n"

    for i, (key, bym_text, lsg_segs) in enumerate(verses_data):
        prompt += f"--- Verset {i+1}: {key} ---\n"
        prompt += f'Texte BYM: "{bym_text}"\n'
        prompt += "Segments LSG:\n"
        for seg in lsg_segs:
            if seg["word"] and seg["strong"]:
                prompt += f'  "{seg["word"]}" → {seg["strong"]}\n'
            elif seg["strong"]:
                prompt += f'  (invisible) → {seg["strong"]}\n'
        prompt += "\n"

    prompt += """Réponds UNIQUEMENT avec un JSON valide. Format :

```json
[
  {
    "key": "Ge. 1:1",
    "segments": [
      {"text": "Au commencement", "strong": "H7225"},
      {"text": " ", "strong": null},
      {"text": "Elohîm", "strong": "H430"},
      ...
    ]
  }
]
```

REGLES POUR LE TEXTE :
- Chaque espace entre les mots DOIT etre un segment separe : {"text": " ", "strong": null}
- La ponctuation reste attachee au mot qui la precede
- La concatenation de tous les "text" doit reproduire EXACTEMENT le texte BYM

IMPORTANT : pas de texte avant ou apres le JSON. Uniquement le JSON."""

    return prompt


def call_ollama(model, prompt, timeout=300, retries=3):
    """Appelle l'API Ollama et retourne la réponse texte."""
    for attempt in range(retries):
        data = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 8192,
            }
        }).encode("utf-8")

        req = urllib.request.Request(
            OLLAMA_URL,
            data=data,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                response = result.get("response", "")
                if response and response.strip():
                    return response
                # Réponse vide → retry
                if attempt < retries - 1:
                    wait = (attempt + 1) * 10
                    print(f"  ⚠️ Réponse vide, retry dans {wait}s...")
                    time.sleep(wait)
                else:
                    return ""
        except Exception as e:
            if attempt < retries - 1:
                wait = (attempt + 1) * 10
                print(f"  ⚠️ Tentative {attempt+1}/{retries} échouée ({e}), retry dans {wait}s...")
                time.sleep(wait)
            else:
                print(f"  ⚠️ Erreur après {retries} tentatives: {e}")
                return None
    return None


def parse_llm_response(response):
    """Extrait le JSON de la réponse du LLM."""
    if not response:
        return None

    # 1. Essayer ```json ... ```
    json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 2. Essayer le bloc JSON brut [ ... ]
    json_match = re.search(r'\[.*\]', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # 3. Essayer { ... } (objet unique)
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            obj = json.loads(json_match.group(0))
            return [obj] if isinstance(obj, dict) else obj
        except json.JSONDecodeError:
            pass

    return None


def normalize_quotes(text):
    """Normalise les guillemets courbes en droits pour la comparaison."""
    return text.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')


def validate_alignment(segments, bym_text):
    """Valide que l'alignement reconstitue exactement le texte BYM."""
    if not segments:
        return False, "segments vides"

    reconstructed = "".join(s.get("text", "") for s in segments)
    # Normaliser les guillemets pour la comparaison
    if normalize_quotes(reconstructed) != normalize_quotes(bym_text):
        return False, f"texte ≠ BYM: {repr(reconstructed[:60])} vs {repr(bym_text[:60])}"

    # Corriger les guillemets dans les segments pour correspondre au BYM
    # (reconstruire avec le texte BYM exact)
    for s in segments:
        if "text" in s:
            s["text"] = normalize_quotes(s["text"])
    # Ajuster : remplacer le texte des segments par le texte BYM correspondant
    # si la seule difference etait les guillemets
    recon_normalized = "".join(s.get("text", "") for s in segments)
    bym_normalized = normalize_quotes(bym_text)
    if recon_normalized == bym_normalized:
        # Reconstituer avec le texte BYM exact en conservant les strong's
        cursor = 0
        for s in segments:
            seg_len = len(s.get("text", ""))
            s["text"] = bym_text[cursor:cursor + seg_len]
            cursor += seg_len

    for s in segments:
        if "text" not in s or "strong" not in s:
            return False, "segment malformé (text/strong manquant)"

    return True, "ok"


def main():
    parser = argparse.ArgumentParser(description="Alignement Strong's par LLM")
    parser.add_argument("--model", default="qwen2.5:14b", help="Modèle Ollama")
    parser.add_argument("--limit", type=int, default=0, help="Limite de versets (0 = tous)")
    parser.add_argument("--batch-size", type=int, default=3, help="Versets par appel LLM")
    parser.add_argument("--sqlite", default="/tmp/strong.sqlite", help="Chemin strong.sqlite")
    parser.add_argument("--min-rate", type=float, default=0.5, help="Traiter les versets avec taux < min-rate")
    parser.add_argument("--dry-run", action="store_true", help="Ne pas sauvegarder")
    args = parser.parse_args()

    # Charger les données
    bym = load_json(THEBYM_PATH)
    bym_strongs = load_json(BYM_STRONGS_PATH)
    gloss_mapping = load_json(GLOSS_MAPPING_PATH)
    overrides = load_json(OVERRIDES_PATH)

    print(f"BYM: {len(bym)} versets")
    print(f"Overrides existants: {len(overrides)}")

    # Identifier les versets à corriger
    to_fix = []
    for key, segs in bym_strongs.items():
        if key in overrides:
            continue  # déjà corrigé
        total = sum(1 for s in segs if s.get("text") and s["text"].strip())
        tagged = sum(1 for s in segs if s.get("strong") and s.get("text") and s["text"].strip())
        if total > 0 and tagged / total < args.min_rate:
            to_fix.append(key)

    print(f"Versets à corriger (taux < {args.min_rate*100:.0f}%): {len(to_fix)}")

    if args.limit > 0:
        to_fix = to_fix[:args.limit]
        print(f"Limité à {len(to_fix)} versets")

    if not to_fix:
        print("Rien à corriger.")
        return

    # Préparer la connexion SQLite
    # Construire l'index inverse: key → (book, chap, verse, is_at)
    key_to_db = {}
    for book in range(1, 67):
        is_at = book <= 39
        abbr = BOOK_NUM_TO_ABBR[book - 1]
        # On ne connaît pas les chap/verse par avance, on reconstruira à la volée
        key_to_db[abbr] = (book, is_at)

    conn = sqlite3.connect(args.sqlite)

    # Traiter par batches
    stats = {"total": 0, "success": 0, "failed": 0, "saved": 0}
    start_time = time.time()

    for batch_start in range(0, len(to_fix), args.batch_size):
        batch_keys = to_fix[batch_start:batch_start + args.batch_size]
        batch_data = []

        for key in batch_keys:
            bym_text = bym.get(key, "")
            if not bym_text:
                continue

            # Trouver le book/chap/verse
            # key format: "Ge. 1:1" or "1 Co. 2:3" or "Job 1:1"
            parts = key.rsplit(" ", 1)
            if len(parts) != 2:
                continue
            book_abbr = parts[0] + " "
            ref = parts[1].split(":")
            if len(ref) != 2:
                continue
            chap, verse = int(ref[0]), int(ref[1])

            # Trouver le numéro de livre
            book_num = None
            is_at = None
            for bn, abbr in enumerate(BOOK_NUM_TO_ABBR, 1):
                if abbr == book_abbr:
                    book_num = bn
                    is_at = bn <= 39
                    break

            if book_num is None:
                continue

            lsg_segs = parse_lsg_segments_from_db(conn, book_num, chap, verse, is_at)
            if not lsg_segs:
                continue

            batch_data.append((key, bym_text, lsg_segs))

        if not batch_data:
            continue

        batch_num = batch_start // args.batch_size + 1
        total_batches = (len(to_fix) + args.batch_size - 1) // args.batch_size

        # Délai entre les appels pour éviter le rate limiting
        if batch_num > 1:
            time.sleep(10)

        # Construire le prompt
        prompt = build_prompt(batch_data, gloss_mapping)

        # Appeler le LLM
        print(f"\n[{batch_num}/{total_batches}] {len(batch_data)} versets...")

        response = call_ollama(args.model, prompt)
        if not response:
            print(f"  ⚠️ Pas de réponse du LLM")
            stats["failed"] += len(batch_data)
            stats["total"] += len(batch_data)
            continue

        # Parser la réponse
        result = parse_llm_response(response)
        if not result:
            print(f"  ⚠️ Réponse non parsable")
            print(f"  Raw (100 premiers chars): {repr(response[:100])}")
            stats["failed"] += len(batch_data)
            stats["total"] += len(batch_data)
            continue

        # Valider et sauvegarder
        for item in result:
            key = item.get("key", "")
            segments = item.get("segments", [])

            bym_text = bym.get(key, "")
            if not bym_text:
                continue

            valid, msg = validate_alignment(segments, bym_text)
            stats["total"] += 1

            if valid:
                overrides[key] = segments
                stats["success"] += 1
                tagged = sum(1 for s in segments if s["strong"])
                print(f"  ✅ {key}: {tagged} tags ({msg})")
            else:
                stats["failed"] += 1
                print(f"  ❌ {key}: {msg}")
                if segments:
                    recon = "".join(s.get("text","") for s in segments)
                    print(f"     recon: {repr(recon[:80])}")
                    print(f"     bym  : {repr(bym_text[:80])}")

        # Sauvegarder périodiquement
        if not args.dry_run and (stats["success"] % 20 == 0 or batch_num % 10 == 0):
            save_json(OVERRIDES_PATH, overrides)
            stats["saved"] = len(overrides)
            elapsed = time.time() - start_time
            print(f"  💾 Sauvegardé ({len(overrides)} overrides, {elapsed:.0f}s)")

    # Sauvegarde finale
    conn.close()

    if not args.dry_run:
        save_json(OVERRIDES_PATH, overrides)

    # Rapport
    elapsed = time.time() - start_time
    print(f"\n{'='*50}")
    print(f"Rapport final:")
    print(f"  Versets traités : {stats['total']}")
    print(f"  Succès          : {stats['success']}")
    print(f"  Échecs          : {stats['failed']}")
    print(f"  Overrides total : {len(overrides)}")
    print(f"  Temps           : {elapsed:.0f}s")
    print(f"  Sauvegardé      : {OVERRIDES_PATH}")


if __name__ == "__main__":
    main()