# Spec — Version « Texte original » (grec / hébreu / araméen) avec Strong's

> Nouveau type de « version » servant le **texte original courant** (formes fléchies telles
> qu'elles apparaissent dans le verset, dans l'ordre des mots originaux) + codes Strong's +
> morphologie, au lieu d'une traduction française.
> Statut : **implémentée sur `feature/original-text`**. Mise à jour : 2026-08-15.

L'implémentation utilise MorphHB/OSHB pour l'AT et le jeu Scrivener 1894 accentué de
`honza/textus-receptus` pour le NT. Le décodage morphologique français est matérialisé dans
chaque segment (`morph_fr`) au build, plutôt que dans des sous-tables statiques séparées.

## 1. Objectif et périmètre

Servir une « version » `orig` du texte biblique où, à la place d'une traduction française
(BYM/LSG/Darby), l'utilisateur reçoit le **texte original mot-à-mot** :

- **AT** : hébreu massorétique (Leningrad Codex), portions araméennes incluses
  (Daniel 2:4–7:28, Esdras 4:8–6:18 + 7:12-26, Jérémie 10:11).
- **NT** : grec du **Textus Receptus** (Scrivener 1894 / Stephanus 1550) — *pas* Nestle-Aland,
  pour rester cohérent avec la base textuelle de la BYM (voir `align-strongs`).

Chaque mot porte son code Strong's, sa morphologie, et — en mode interlinéaire — une glose
française. Le lemme (forme de dictionnaire) vient du `lexicon.json` existant, inchangé.

### Hors périmètre (v1)

- Translittération phonétique d'affichage (déjà dispo via `lexicon.json.translit` si besoin).
- Vocalisation alternatives / qere-ketiv étendu au-delà du minimum (cf. §8).
- Apparat critique des variantes TR vs NA28 (peut faire l'objet d'une v2).

## 2. Pourquoi pas « l'interlinéaire par lemme » (approche rejetée)

On aurait pu, pour chaque verset, remplacer le français par `lexicon[seg.strong].lemma`. **Rejeté**
pour trois raisons :

1. Donne la **forme de dictionnaire** (γίνομαι) au lieu de la **forme du texte** (ἐγένετο).
2. **Trous** sur tout segment `strong: null` (articles, mots-outils FR) → texte incomplet.
3. **Ordre des mots = ordre français**, pas l'ordre original.

La v1 exige donc une **vraie source original + Strong's par mot** (approche B).

## 3. Sources de données

| Couche | Source recommandée | Ce qu'elle fournit | Licence / dispo |
| --- | --- | --- | --- |
| AT hébreu/araméen | **MorphHB** (OpenScriptures Hebrew Bible, WLC + Strong's + morph) | `<w lemma="H7225" morph="hcNcmsc">בְּרֵאשִׁית</w>` par mot | domaine public / CC-BY-SA |
| NT grec (TR) | **Textus Receptus + Strong's** (Scrivener 1894) — ex. jeu `tr` de BibleHub / StepBible | `<w lemma="G3588" morph="...">ὁ</w>` par mot, base TR | domaine public |
| Lemme + définition | `db/strongs/lexicon.json` **existant** | lemme original, translittération, définition, `lang` | déjà intégré |
| Morphologie FR | `db/strongs/morph_codes.json` **existant** | décodage `8799` / codes MorphHB → FR lisible | déjà intégré |

> La source MorphHB couvre **hébreu ET araméen** via les codes Strong's araméens (préfixe `H`,
> `origine: "(Araméen)"` déjà marqué dans le lexique). Pas de source araméenne séparée.

### Règle de cohérence TR (NT)

Pour chaque verset NT, la source `orig` **doit** suivre la lecture TR. Si la source TR-Strong's
récupérée diverge de la lecture TR déjà établie par la skill `align-strongs` (présence d'un
article / pronom / lexème), on privilégie la lecture TR et on journalise l'écart dans le build.
Cf. §8 (variants).

## 4. Schéma de données — `db/strongs/orig_strongs.json`

Même structure que `bym_strongs.json` (clé verset → tableau de segments) afin de réutiliser
`resolve_strongs` (`index.js:380`) avec un delta minimal.

```jsonc
{
  "Ge. 1:1": [
    { "text": "בְּרֵאשִׁית", "strong": "H7225", "morph": "R/Ncfsa", "gloss": "Au commencement" },
    { "text": "בָּרָא",      "strong": "H1254", "morph": "Vqp3ms",  "gloss": "créa" },
    { "text": "אֱלֹהִים",    "strong": "H430",  "morph": "Ncmpa",   "gloss": "Elohîm" },
    { "text": "אֵת",          "strong": "H853",  "morph": "To",      "gloss": "" },
    { "text": "הַשָּׁמַיִם", "strong": "H8064", "morph": "Td/Ncmpa", "gloss": "les cieux" },
    { "text": "וְאֵת",        "strong": "H853",  "morph": "C/To",    "gloss": "et" },
    { "text": "הָאָרֶץ",     "strong": "H776",  "morph": "Td/Ncbsa", "gloss": "la terre" }
  ],
  "Mt. 1:1": [
    { "text": "βίβλος",        "strong": "G976",  "morph": "N-NSF", "gloss": "Livre" },
    { "text": "γενέσεως",      "strong": "G1078", "morph": "N-GSF", "gloss": "de la genèse de" },
    { "text": "Ἰησοῦ",         "strong": "G2424", "morph": "N-GSM", "gloss": "Yéhoshoua" },
    { "text": "Χριστοῦ",       "strong": "G5547", "morph": "N-GSM", "gloss": "Mashiah" },
    { "text": "υἱοῦ",          "strong": "G5207", "morph": "N-GSM", "gloss": "fils" }
  ]
}
```

Conventions de segment :

- `text` : **forme fléchie** exacte du mot dans le verset (hébreu massorétique vocalisé, grec TR
  avec accents/esprits). Sens de lecture : RTL pour hébreu/araméen, LTR pour grec — géré côté
  présentation par `lang` du segment (cf. §6).
- `strong` : code Strong (`H7225` / `G976`). `null` uniquement pour la ponctuation / matière
  non lemmatisée (cf. §8).
- `morph` : code morphologique **tel quel** (format MorphHB pour AT, format Robinson/Parsing
  pour NT) — décodage FR via `morph_codes.json` existant ou une table d'extension (§5.4).
- `gloss` : glose française courte (alignée sur la BYM quand possible). Optionnel — absent en
  mode « original seul » pur, mais stocké une fois pour pouvoir servir l'interlinéaire sans
  rebuild. Mot-outils sans équivalent FR : `gloss: ""`.

### Index inversé — `db/strongs/orig_strong_index.json`

Généré par `build_strong_index.py --strongs db/strongs/orig_strongs.json --out …` (script
existant). Donne Strong's → liste de versets, comme pour BYM/Darby.

## 5. Pipeline de build — `scripts/build_original.py`

Un nouveau script, appelé par une cible `make original`.

### 5.1 Cible Makefile

```makefile
original:
	@echo "═══ Texte original : AT (WLC/MorphHB) ═══"
	python3 scripts/build_original.py --lang ot --sqlite $(SQLITE)
	@echo "═══ Texte original : NT (TR + Strong's) ═══"
	python3 scripts/build_original.py --lang nt --sqlite $(SQLITE)
	@echo "═══ Index Strong's → versets ═══"
	python3 scripts/build_strong_index.py --strongs db/strongs/orig_strongs.json --out db/strongs/orig_strong_index.json
	@echo "✅ Version 'orig' construite"
```

### 5.2 Étapes du script

1. **Ingestion source**
   - AT : parser MorphHB (OSIS/XML ou JSON) → `{ livre, chap, verset, ordre, text, strong, morph }`.
   - NT : parser la source TR-Strong's → même structure.
2. **Mapping vers clés du projet** : convertir `(livre, chap, verset)` en clé `"Ge. 1:1"` via
   la table `BOOK_NAMES` (`index.js:174`) — *extraire cette table dans un module shared* pour
   ne pas la dupliquer (cf. §7).
3. **Correction de versification** : appliquer `versif_offsets.json` existant si la source
   originale décale vs la BYM (rare pour l'original, mais à vérifier sur Esdras/Néhémie et
   AT Apocryphes exclus). Journaliser les versets sans correspondance.
4. **Enrichissement lexique** : pour chaque `strong`, vérifier l'existence dans `lexicon.json`.
   - Si absent → avertir ( Strong's orphelin) et marquer `strong` suspect dans un rapport.
5. **Gloses** : tenter un alignement `gloss` sur les segments BYM du même verset
   (`bym_strongs.json`) quand les codes Strong coïncident — sinon `gloss: ""`.
6. **Écriture** : `db/strongs/orig_strongs.json` (merge AT + NT, trié par clé).

### 5.3 Idempotence & re-build partiel

Le script accepte `--lang ot|nt` pour reconstruire une couche seule (le NT évolue peu, l'AT
est figé). Merge deterministe : clés triées, segments dans l'ordre source.

### 5.4 Décodage morphologique FR

`morph_codes.json` actuel décode les codes `8799` du format LSG-sqlite. MorphHB (AT) et
Robinson (NT) utilisent des codes différents (`Vqp3ms`, `N-NSF`). Deux options :

- **(recommandé)** Ajouter deux sous-tables `morph_at` et `morph_nt` dans `morph_codes.json`,
  le décodage `resolve_strongs` garde le format brut dans `morph` et ajoute `morph_fr` décodé.
- Ou : convertir les codes MorphHB/Robinson vers le format `8799` au build. *Rejeté* : perte
  d'information et mapping non bijectif.

## 6. Intégration API (`index.js`)

### 6.1 Registre `VERSIONS` (delta)

```js
const orig_strongs = loadOptional("./db/strongs/orig_strongs.json", "Strong's ORIG");
const origStrongIndex = loadOptional("./db/strongs/orig_strong_index.json", "Strong's index ORIG");

const VERSIONS = {
  bym:   { /* inchangé */ },
  lsg:   { /* inchangé */ },
  darby: { /* inchangé */ },
  orig: {
    data: bym,                 // texte « plan » = la BYM (fallback lecture humaine)
    strongsData: orig_strongs, // le texte original est dans les segments Strong's
    strongIndex: origStrongIndex,
    name: "Texte original (Hébreu / Araméen / Grec TR)",
    strongs: true,
    isOriginal: true,          // nouveau flag
  },
};
```

> Particularité : pour `orig`, le « texte » affiché par défaut n'est **pas** `data[key]` (français)
> mais **la concaténation des `seg.text` originaux**. Le flag `isOriginal` signale ce mode.

### 6.2 Endpoint

`GET /orig/jean/3/16` → verset dans la version originale.

Paramètres de requête :

| Param | Valeurs | Effet |
| --- | --- | --- |
| `strongs=1` | (existant) | Attache les segments `strongs` au verset. **Pour `orig`, renvoie les segments originaux même sans ce flag** (le segment *est* le texte). |
| `mode` | `orig` (défaut) \| `interlinear` | `orig` : texte original seul (+ Strong au survol). `interlinear` : chaque mot original + glose FR en regard. |
| `translit=1` | booléen | Ajoute `translit` et `phonetique` par segment (depuis `lexicon.json`). |

### 6.3 Delta `resolve_strongs` (`index.js:380`)

Pour `orig`, ajouter `lang` par segment (dérivé du préfixe Strong `H`/`G` ou d'un champ
`lang` stocké au build) + `morph_fr` décodé + `gloss` (déjà présent). Le chemin existant
renvoie déjà `lemma`, `translit`, `definition` — inchangé.

### 6.4 Sens de lecture (RTL)

Côté API : aucun. Côté présentation (si le consumer rend du HTML) : `dir="rtl"` pour les
segments `lang ∈ {hebrew, aramaic}`, `dir="ltr"` pour `greek`. L'API expose `lang` par segment
pour que le client décide. *Ne pas réordonner* les segments (l'ordre source est l'ordre de
lecture).

## 7. Refactor partagé (prérequis propre)

La table `BOOK_NAMES` / `BOOK_ALIASES` vit dans `index.js` et est aussi nécessaire au build
Python. **Extraire** ces tables dans `db/books_meta.json` (ou `db/book_aliases.json`) chargé
par `index.js` et par `scripts/build_original.py`. Évite la dérive entre Node et Python.

## 8. Cas limites

| Cas | Décision v1 |
| --- | --- |
| **Araméen** (Da 2:4–7:28, Esd 4:8–6:18, Esd 7:12-26, Jé 10:11) | Couvert par MorphHB + codes H araméens. `lang: "aramaic"` marqué au build (préfixe H + `lexicon.origine` contient « Araméen »). |
| **Qere / Ketiv** | Conserver le **Ketiv** (écrit) dans `text` ; si MorphHB fournit le Qere, l'ajouter dans un champ optionnel `qere` (v1 : ignorer sauf si trivial). |
| **Mots sans Strong** (matère, accents seuls, maqqef, etc.) | `strong: null`, `text` conservé pour fidélité du flux (ex. le `-` maqqef). Pas de `gloss`. |
| **Articles G3588 / pronoms G846** | **Tous présents** dans la source TR — à la différence de la LSG qui les omet. C'est précisément l'intérêt de `orig`. Ne pas filtrer. |
| **Variantes TR vs NA28** (lexème substitué, ex. Mt 15:4 ἐνετείλατο vs εἶπεν) | Source `orig` suit le TR. Si la source récupérée porte NA28, lever une alerte build par verset et (option) surcharger via un futur `orig_variants.json` — v1 : alerter seulement. |
| **Versification différente** | Appliquer `versif_offsets.json` ; journaliser les versets orphelins (original sans verset BYM) et les versets BYM sans original (ex. additions NA28 absentes du TR). |
| **Ponctuation massorétique / grecque** | Conservée dans des segments `strong: null` ou rattachée au mot précédent selon la source. Choix à figer au build (préférer : rattachée au mot, `punct` séparé si la source l'expose). |
| **Noms propres translittérés** (ex. Ἰησοῦ) | `text` = forme grecque fléchie ; `gloss` = forme BYM (« Yéhoshoua »). Le lemme `lexicon.json` donne déjà la forme de dictionnaire. |

## 9. Plan de livraison

1. **Prérefactor** : extraire `BOOK_NAMES`/`BOOK_ALIASES` dans `db/books_meta.json` (§7). ~1 h.
2. **Spike source AT** : récupérer MorphHB, parser 1 livre (Genèse), valider le schéma. ~2 h.
3. **Build AT** : `build_original.py --lang ot` complet + index. ~3 h.
4. **Spike source NT** : récupérer TR-Strong's, parser Jean, valider cohérence TR vs `align-strongs`. ~2 h.
5. **Build NT** : `build_original.py --lang nt` + index. ~3 h.
6. **Intégration API** : delta `VERSIONS`, `resolve_strongs`, `mode`/`translit`, flag `isOriginal`. ~2 h.
7. **Morph FR** : sous-tables `morph_at`/`morph_nt`. ~2 h.
8. **Tests** : versets pivot (Ge 1:1, Da 2:4 araméen, Jn 3:16, Mt 15:4 variante TR) + cohérence Strong's avec `bym_strongs.json`. ~2 h.
9. **Doc** : MAJ `data-pipeline.md` + mention `orig` sur la home. ~1 h.

## 10. Critères d'acceptation

- `GET /orig/genèse/1/1` renvoie Gen 1:1 en hébreu massorétique, 7 segments, chacun avec
  `strong` + `morph` + `lang: "hebrew"`.
- `GET /orig/daniel/2/4?mode=interlinear` renvoie l'araméen avec glose FR et `lang: "aramaic"`.
- `GET /orig/jean/3/16?strongs=1&translit=1` renvoie le grec TR + `translit` + `definition`.
- `GET /orig/matthieu/15/4` : le Strong sur « commandé » est **G1781** (TR), pas G2036 (NA28).
- `db/strongs/orig_strong_index.json` : `H7225` contient bien `Ge. 1:1`.
- Aucune divergence silencieuse TR/NA28 : tout verset NT à risque est journalisé au build.
- `make align` (BYM) et `make original` sont indépendants — l'un n'altère pas les données de l'autre.
