#!/usr/bin/env python3
"""
Mise à jour de thebym.json, bym.json et bym_info.json depuis le dépôt GitLab BJC.
GitLab est la source de vérité : les 66 livres sont régénérés à chaque exécution.
Usage :
    python3 scripts/update_from_gitlab.py [--clone-dir /tmp/bjc-source]

Le dépôt est cloné automatiquement si --clone-dir n'existe pas déjà.
"""

import re
import json
import os
import glob
import argparse
import subprocess
import sys

GITLAB_URL = "https://gitlab.com/anjc/bjc-source.git"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
BYM_JSON     = os.path.join(PROJECT_DIR, "db", "books", "bym.json")
BYM_INFO_JSON = os.path.join(PROJECT_DIR, "db", "books", "bym_info.json")
THEBYM_JSON  = os.path.join(PROJECT_DIR, "db", "thebym.json")  # master servi par l'API


# ---------------------------------------------------------------------------
# Utilitaires de parsing
# ---------------------------------------------------------------------------

def clean_verse_text(text):
    """Supprime les commentaires <!-- --> et les balises <w>, nettoie les espaces."""
    text = re.sub(r'<!--.*?-->', '', text)
    text = re.sub(r'<w[^>]*>(.*?)</w>', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def parse_book_abbreviation(header_line):
    """Extrait la dernière abréviation entre parenthèses d'une ligne de titre."""
    m = re.search(r'\(([^)]+)\)\s*$', header_line.strip())
    return m.group(1) if m else None


def format_verse_key(abbrev, chapter, verse):
    """Construit la clé JSON d'un verset (ex: 'Jos. 1:1' ou 'Job 1:1')."""
    # Job n'a pas de point dans les clés bym.json
    if abbrev == 'Job.':
        return f'Job {chapter}:{verse}'
    return f'{abbrev} {chapter}:{verse}'


def parse_h_block(block_text):
    """Parse le bloc <h>...</h> en champs structurés."""
    fields = {}
    extras = []
    for line in (l.strip() for l in block_text.strip().split('\n') if l.strip()):
        if line.startswith('Signification :'):
            fields['signification'] = line[len('Signification :'):].strip()
        elif re.match(r'Auteurs?\s*:', line):
            fields['auteur'] = line.split(':', 1)[1].strip()
        elif line.startswith('Thème :'):
            fields['theme'] = line[len('Thème :'):].strip()
        elif line.startswith('Date de rédaction :'):
            fields['date'] = line[len('Date de rédaction :'):].strip()
        elif line.startswith('('):
            extras.append(line)
    if extras:
        fields['notes'] = ' '.join(extras)
    return fields


def parse_intro(content, h_end_pos):
    """Extrait le texte d'introduction entre </h> et le premier chapitre/verset."""
    after_h = content[h_end_pos:].strip()
    m = re.match(r'^(.+?)(?=\n## |\n\d+:\d+)', after_h, re.DOTALL)
    if not m:
        return ''
    intro = re.sub(r'<[^>]+>', '', m.group(1))
    return re.sub(r'\s+', ' ', intro).strip()


# ---------------------------------------------------------------------------
# Traitement d'un fichier markdown
# ---------------------------------------------------------------------------

def process_markdown(filepath):
    """
    Retourne (abbrev, verses_dict, info_dict) depuis un fichier markdown.
    verses_dict : { "Abbrev. chap:verset": "texte" }
    info_dict   : { titre, abreviation, signification, auteur, theme, date,
                    introduction?, notes?, sections?, paragraphes? }
      sections   : [{"titre": "...", "debut": "Abbrev. chap:verset"}, ...]
      paragraphes: ["Abbrev. chap:verset", ...]  — versets ouvrant un nouveau paragraphe
    """
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')

    # --- Abréviation & titre ---
    abbrev = None
    titre_clean = ''
    for line in lines:
        if line.startswith('# '):
            abbrev = parse_book_abbreviation(line)
            titre_clean = re.sub(r'\s*\([^)]+\)\s*$', '', line[2:]).strip()
            break
    if not abbrev:
        return None, {}, {}

    # --- Versets, sections et paragraphes ---
    verses = {}
    sections = []      # titres de section avec leur verset de début
    paragraphes = []   # versets qui ouvrent un nouveau paragraphe (ligne vide précédente)

    pending_section = None   # titre ## en attente du prochain verset
    last_verse_key = None
    blank_since_last_verse = False

    for line in lines:
        stripped = line.strip()

        # Titre de chapitre (## ...) ou titre de section (### ...)
        # Les ### écrasent le ## précédent : on garde le titre le plus précis
        if stripped.startswith('### '):
            pending_section = re.sub(r'<!--.*?-->', '', stripped[4:]).strip()
            continue
        if stripped.startswith('## '):
            pending_section = re.sub(r'<!--.*?-->', '', stripped[3:]).strip()
            continue

        # Ligne de verset (chapitre:verset\ttexte)
        m = re.match(r'^(\d+):(\d+)\t(.+)$', line)
        if m:
            chapter, verse, text = m.group(1), m.group(2), m.group(3)
            cleaned = clean_verse_text(text)
            if cleaned:
                key = format_verse_key(abbrev, chapter, verse)
                verses[key] = cleaned

                if pending_section is not None:
                    sections.append({"titre": pending_section, "debut": key})
                    pending_section = None

                if blank_since_last_verse and last_verse_key is not None:
                    paragraphes.append(key)

                last_verse_key = key
                blank_since_last_verse = False
            continue

        # Ligne vide après un verset → potentiel saut de paragraphe
        if not stripped and last_verse_key is not None:
            blank_since_last_verse = True

    # --- Bloc <h> ---
    h_m = re.search(r'<h>\n(.*?)\n</h>', content, re.DOTALL)
    info = {}
    if h_m:
        info = parse_h_block(h_m.group(1))
        intro = parse_intro(content, h_m.end())
        if intro:
            info['introduction'] = intro

    info['titre'] = titre_clean
    info['abreviation'] = abbrev
    if sections:
        info['sections'] = sections
    if paragraphes:
        info['paragraphes'] = paragraphes

    return abbrev, verses, info


# ---------------------------------------------------------------------------
# Clonage du dépôt
# ---------------------------------------------------------------------------

def ensure_clone(clone_dir):
    if os.path.isdir(os.path.join(clone_dir, '.git')):
        print(f"[git] Mise à jour du dépôt dans {clone_dir} ...")
        subprocess.run(['git', '-C', clone_dir, 'pull', '--depth=1'], check=True)
    else:
        print(f"[git] Clonage de {GITLAB_URL} dans {clone_dir} ...")
        subprocess.run(
            ['git', 'clone', '--depth=1', GITLAB_URL, clone_dir],
            check=True
        )


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Régénère thebym.json, bym.json et bym_info.json depuis GitLab (source de vérité).")
    parser.add_argument('--clone-dir', default='/tmp/bjc-source',
                        help="Répertoire local du dépôt cloné (défaut: /tmp/bjc-source)")
    args = parser.parse_args()

    ensure_clone(args.clone_dir)

    all_md = sorted(glob.glob(os.path.join(args.clone_dir, '[0-9][0-9]-*.md')))
    if not all_md:
        print(f"Aucun fichier markdown trouvé dans {args.clone_dir}", file=sys.stderr)
        sys.exit(1)

    # GitLab = source de vérité : on régénère TOUS les livres (01-66).
    #   - new_master → db/thebym.json     (master plat, servi par index.js)
    #   - new_bym    → db/books/bym.json   (sous-ensemble 06+, conservé pour compat)
    #   - new_info   → db/books/bym_info.json (infos des 66 livres)
    new_master = {}   # tous les livres 01-66
    new_bym    = {}   # livres 06+ uniquement
    new_info   = {}

    print("Traitement des fichiers markdown…")
    for filepath in all_md:
        num = int(os.path.basename(filepath)[:2])
        abbrev, verses, info = process_markdown(filepath)
        if not abbrev:
            print(f"  AVERTISSEMENT : pas d'abréviation dans {filepath}")
            continue

        new_master.update(verses)      # tous les livres
        if num >= 6:
            new_bym.update(verses)     # sous-ensemble historique 06+

        # Infos pour tous les livres
        info_key = 'Job.' if abbrev == 'Job.' else abbrev
        new_info[info_key] = info

        print(f"  {os.path.basename(filepath):30s} → {abbrev:8s} | {len(verses):4d} versets")

    # S'assurer que les dossiers de sortie existent (utile en CI / clone vierge)
    os.makedirs(os.path.dirname(THEBYM_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(BYM_JSON), exist_ok=True)

    # --- Rapport de différences vs thebym.json précédent ---
    if os.path.exists(THEBYM_JSON):
        with open(THEBYM_JSON, encoding='utf-8') as f:
            old_master = json.load(f)
        old_keys, new_keys = set(old_master), set(new_master)
        added   = new_keys - old_keys
        removed = old_keys - new_keys
        changed = sum(1 for k in (old_keys & new_keys) if old_master[k] != new_master[k])
        print("\n--- Synchronisation depuis GitLab (source de vérité) ---")
        print(f"  versets ajoutés   : {len(added)}")
        print(f"  versets supprimés : {len(removed)}")
        print(f"  versets modifiés  : {changed}")
        if removed:
            print(f"  ⚠️  exemples supprimés : {sorted(removed)[:5]}")

    # Écriture thebym.json (master servi par l'API)
    with open(THEBYM_JSON, 'w', encoding='utf-8') as f:
        json.dump(new_master, f, ensure_ascii=False, indent=4)
    print(f"\n[OK] thebym.json  : {len(new_master)} versets → {THEBYM_JSON}")

    # Écriture bym.json (sous-ensemble 06+, conservé pour compat)
    with open(BYM_JSON, 'w', encoding='utf-8') as f:
        json.dump(new_bym, f, ensure_ascii=False, indent=4)
    print(f"[OK] bym.json     : {len(new_bym)} versets → {BYM_JSON}")

    # Écriture bym_info.json
    with open(BYM_INFO_JSON, 'w', encoding='utf-8') as f:
        json.dump(new_info, f, ensure_ascii=False, indent=4)
    print(f"[OK] bym_info.json: {len(new_info)} livres  → {BYM_INFO_JSON}")


if __name__ == '__main__':
    main()
