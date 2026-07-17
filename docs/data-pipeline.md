# Pipeline de données — shema (API BJC)

> Doc de référence sur **d'où vient le texte servi** et **comment il est régénéré**.
> But : éviter de re-explorer le code à chaque fois. Mise à jour : 2026-06-22.

## Source de vérité

**GitLab `gitlab.com/anjc/bjc-source`** est la **source de vérité** du texte
biblique (66 fichiers markdown `NN-Nom.md`, format OSIS-like). Tout le contenu
servi par l'API en dérive ; rien n'est édité à la main dans `db/`.

Format d'un verset dans le markdown source :

```
1:1	<w lemma="strong:H07225">Au commencement</w><!--commentaire--> <w lemma="strong:H0430">Elohîm</w> ...
```

- `chap:verset` + TAB + texte.
- `<!-- ... -->` = notes (supprimées au nettoyage).
- `<w lemma="strong:...">` = tag Strong's (voir section dédiée — quasi inexistant).

## Fichiers de données (`db/`)

| Fichier | Rôle | Généré par |
| --- | --- | --- |
| `db/thebym.json` | **Master plat servi par l'API** `{ "Ge. 1:1": "texte" }`, 66 livres (~31 169 versets) | ETL (`update_from_gitlab.py`) |
| `db/books/bym.json` | Sous-ensemble **livres 06+** (~25 317 v.), conservé pour compat | ETL |
| `db/books/bym_info.json` | Infos des 66 livres (titre, auteur, sections, paragraphes…) | ETL |
| `db/books/{ge,ex,lé,no,de}.json` | **OBSOLÈTES** — anciens fichiers 01–05 figés (oct. 2022). Ne feed plus `thebym.json`. | legacy (manuel) |
| `db/books/ge_next.json` | Legacy, format différent (8 clés), inutilisé | legacy |

`index.js` ne charge que **`db/thebym.json`** et **`db/books/bym_info.json`** au
démarrage (`require`, une fois). Les clés de verset suivent le format
`"<Abbrev> <chap>:<verset>"` (ex. `"Ge. 1:1"`, `"Job 1:1"` — Job sans point).

## ETL — `scripts/update_from_gitlab.py`

1. Clone/pull `bjc-source` (`--clone-dir`, défaut `/tmp/bjc-source`).
2. `process_markdown()` parse chaque fichier → versets nettoyés
   (`clean_verse_text` : retire `<!-- -->`, `<w>`, normalise les espaces) + infos.
3. Écrit **les 66 livres** dans `thebym.json` (master), le sous-ensemble 06+ dans
   `bym.json`, et `bym_info.json`.
4. Affiche un **rapport de diff** vs le `thebym.json` précédent
   (versets ajoutés / supprimés / modifiés).

> ⚠️ Historique : avant 2026-06-22, l'ETL ne régénérait que `bym.json` (06+) ;
> `thebym.json` et les livres 01–05 étaient assemblés **à la main** et n'étaient
> jamais re-synchronisés → ~3 130 versets avaient divergé de GitLab (dont ~50 %
> des livres 01–05). Corrigé : l'ETL régénère désormais tout depuis GitLab.

## Automatisation

`.github/workflows/update-bible.yml` (`workflow_dispatch`, déclenché par cron
Vercel) : lance l'ETL puis commit `db/thebym.json`, `db/books/bym.json`,
`db/books/bym_info.json`. ⇒ le texte reste synchronisé sur GitLab à chaque run.

## Strong's — état réel de la couverture amont

⚠️ **La source BJC ne contient quasiment aucun tag Strong's.**

- **6 balises `<w>` au total dans toute la Bible**, **toutes dans Genèse 1:1**
  (codes `H7225, H430, H853, H1254, H8064, H776`). Échantillon de démo.
- Les 65 autres livres (y compris le reste de la Genèse et tout le NT) : **0 tag**.

⇒ « préserver les `<w>` à l'import » ne donne des Strong's que pour **1 verset**.
Une vraie couverture nécessite une **source d'alignement externe** (interlinéaire
hébreu/grec ↔ Strong's), p. ex. `interlineaire.sqlite` + `strong.sqlite` du projet
`bible-strong` (CDN `assets.bible-strong.app/databases/`), **non aligné** sur le
texte français BYM (mapping mot↔français = problème ouvert). Décision en attente.

## Vérifs rapides

```bash
# Re-synchroniser le contenu depuis GitLab
python3 scripts/update_from_gitlab.py --clone-dir /tmp/bjc-source

# Valider le master sans démarrer le serveur
node -e "console.log(Object.keys(require('./db/thebym.json')).length)"

# Couverture des tags Strong's dans la source
grep -roh 'strong:[HG][0-9]*' /tmp/bjc-source/*.md | wc -l
```
