# Plan — Ajouter les numéros Strong's à l'API shema

> Statut : **prémisse centrale invalidée** (voir ⚠️ ci-dessous). Décision en attente.
> Périmètre : **API uniquement** (exposer les Strong's). Le rendu dans le lecteur
> `/bym/read` (front Next.js) est **hors périmètre** ici.

---

## ⚠️ MISE À JOUR 2026-06-22 — vérification de la source

**1. Couverture Strong's amont = quasi nulle.** La source BJC contient **6 balises
`<w>` au total, toutes dans Genèse 1:1**. Les 65 autres livres (reste de la Genèse
inclus, tout le NT) n'ont **aucun tag**. ⇒ L'approche « préserver les `<w>` »
(étape 2) ne produit des Strong's que pour **1 verset**. La « simplification
décisive » du plan (pas besoin d'alignement mot-à-mot) **tombe**. Voir
`docs/data-pipeline.md`.

**2. Contenu re-synchronisé depuis GitLab (fait).** En vérifiant, on a constaté que
le texte servi (livres 01–05 + assemblage `thebym.json`) avait **divergé de GitLab**
(~3 130 versets). GitLab étant la source de vérité, l'ETL a été étendu pour
régénérer les 66 livres et écrire `thebym.json` directement (+ workflow corrigé pour
le committer). **Cette partie est livrée**, indépendamment des Strong's.

**3. Décision en attente** pour la vraie couverture Strong's : il faut une **source
d'alignement externe** (interlinéaire), pas la source BJC. Options à trancher avec
l'utilisateur (voir fin du document).

---

---

## Contexte

L'utilisateur veut exposer les **numéros Strong's** (références de concordance
hébreu/grec) par verset. Constat de départ : « ils n'existent pas dans la BD ».

L'exploration a révélé un point décisif qui simplifie radicalement la tâche :

- Les Strong's **existent déjà** dans la source amont
  (`gitlab.com/anjc/bjc-source`, dépôt BJC). Chaque mot/groupe de mots tagué est
  encodé en OSIS :

  ```
  1:1 <w lemma="strong:H07225">Au commencement</w> ...
  ```

- Le script d'import les **jette explicitement** dans
  `scripts/update_from_gitlab.py`, fonction `clean_verse_text()` :

  ```python
  text = re.sub(r'<w[^>]*>(.*?)</w>', r'\1', text)
  ```

**Conséquence : pas besoin d'alignement mot-à-mot** (l'écueil classique sur une
traduction française). Il suffit de **préserver** ces balises à l'import, de les
**stocker**, puis de les **servir** via l'API.

Niveau d'enrichissement choisi : **lexique complet** (numéro + mot original +
translittération + définition), ce qui implique d'intégrer en plus un
dictionnaire Strong, car la source ne fournit que le numéro nu.

---

## Limites de couverture (vérifiées)

- **Genèse** : taguée (Strong's hébreux `strong:H#####`).
- **Jean** : aucune balise `<w>` → le **NT n'est pas tagué** dans cette source.
- La couverture réelle est donc **partielle** (vraisemblablement l'AT) et **par
  groupes de mots** (un Strong's peut couvrir « Au commencement »). On ne peut
  exposer que ce qui existe.
- ➜ L'implémentation devra **mesurer et reporter la couverture par livre**.

---

## Pipeline de données actuel (état réel du code, vérifié)

- `index.js` charge `db/thebym.json` (master plat `{ "Ge. 1:1": "texte" }`) au
  démarrage (`index.js:24`).
- `scripts/update_from_gitlab.py` ne génère que :
  - `db/books/bym.json` — **versets des livres 06+ uniquement**.
  - `db/books/bym_info.json` — **infos de tous les livres** (01–66).
- Les **versets des livres 01–05** (dont la Genèse, justement taguée) sont gérés
  **à part**, dans des fichiers séparés : `db/books/ge.json`, `ge_next.json`,
  `ex.json`, `lé.json`, `no.json`, `de.json`.
- **`db/thebym.json` n'est assemblé par aucun script présent dans le repo** —
  l'étape d'assemblage final (fusion des livres 01–05 + `bym.json` 06+) est à
  localiser/reconstituer. Elle devra être alignée pour que les segments Strong's
  couvrent les 66 livres **de la même façon que le texte**.

---

## Principe directeur

**Rétro-compatibilité totale** : les réponses actuelles de l'API ne changent
pas. Les données Strong's vivent **en parallèle** et sont servies **à la
demande** (opt-in).

---

## Étapes

### 1. Modèle de données — 2 nouveaux fichiers statiques

**`db/strongs/bym_strongs.json`** — segments ordonnés par verset, alignés sur le
texte :

```json
{
  "Ge. 1:1": [
    { "t": "Au commencement", "s": "H7225" },
    { "t": " Elohîm créa ",   "s": null },
    { "t": "les cieux",       "s": "H8064" }
  ]
}
```

- **Invariant testable** : la concaténation des `t` doit reproduire
  **exactement** le texte de `thebym.json` (garantit l'intégrité, zéro caractère
  perdu/ajouté).
- `s` = code Strong canonique, ou `null` pour le texte non tagué.
- Multi-lemmes possibles (`strong:H1 strong:H2`) → `s` peut être un tableau.

**`db/strongs/lexicon.json`** — dictionnaire indexé par code :

```json
{
  "H7225": {
    "lemma": "רֵאשִׁית",
    "translit": "reshith",
    "definition": "commencement, premier, principal",
    "lang": "hebrew"
  }
}
```

### 2. ETL — préserver les `<w>` (`scripts/update_from_gitlab.py`)

- Ajouter `segment_verse_text(text)` qui, **avant** le nettoyage actuel, parse le
  texte en segments `[{t, s}]` en capturant `lemma="strong:..."`. Réutiliser la
  **même source de vérité** que `clean_verse_text` pour garantir
  `"".join(seg.t) == clean_verse_text(text)`.
- **Normaliser** le code : `strong:H07225` → `H7225` (retirer le zéro-padding,
  garder la lettre de langue).
- Écrire `db/strongs/bym_strongs.json` en plus des sorties existantes.
- **Étendre le traitement aux livres 01–05** (la Genèse est taguée) — aligner sur
  le périmètre de `thebym.json`, pas seulement `bym.json` (06+). ➜ implique de
  réconcilier l'assemblage de `thebym.json` (voir pipeline ci-dessus).
- Afficher un **rapport de couverture** : nb de versets tagués / total, par livre.

### 3. Lexique — nouveau script `scripts/build_lexicon.py`

Construit `db/strongs/lexicon.json`. **Étape ponctuelle**, fichier statique
commité, **pas dans le cron** (le lexique ne change pas).

> **✅ DÉCIDÉ : source = `strong.sqlite` (bible-strong).** Définitions FR natives,
> meilleure qualité, couvre hébreu + grec. **Risque licence assumé** par le
> propriétaire du projet (données = assets externes, licence non explicitée). Le
> repli OpenScriptures ci-dessous reste documenté comme plan B si besoin de
> repasser sur une licence 100 % propre.
>
> ➜ `build_lexicon.py` : télécharger `strong.sqlite` (URL ci-dessous), ouvrir la
> base avec le module `sqlite3` standard, extraire `code → {lemma, translit,
> definition, lang}` et écrire `lexicon.json`. Schéma exact de la table à
> inspecter au runtime (`.tables` / `PRAGMA table_info`).

**Source française retenue (identifiée et vérifiée accessible) :**

L'appli `smontlouis/bible-strong` télécharge ses données depuis un CDN public.
Trois bases SQLite confirmées téléchargeables (HTTP 200) :

| Base            | URL                                                  | Taille | Contenu                                    |
| --------------- | ---------------------------------------------------- | ------ | ------------------------------------------ |
| Strong FR       | `https://assets.bible-strong.app/databases/strong.sqlite` | ~35 Mo | Concordance Strong **française** (héb. + grec) |
| Dictionnaire FR | `https://assets.bible-strong.app/databases/dictionnaire.sqlite` | ~24 Mo | Dictionnaire Westphal (français)           |
| Interlinéaire   | `https://assets.bible-strong.app/databases/interlineaire.sqlite` | ~21 Mo | Interlinéaire mot→Strong                   |

- Fallback CDN : `https://storage.googleapis.com/bible-strong-app.appspot.com/databases/strong.sqlite`
- `strong.sqlite` fournit de **vraies définitions Strong en français** + mot
  original + translittération → alimente directement `lexicon.json`.

**⚠️ Licence des données `strong.sqlite` : non explicitée** (code de l'appli en
GPL-3.0, mais les bases sont des assets externes). **À clarifier avant
intégration commitée.**

**Repli domaine public (licence propre, si besoin) :**

1. Backbone = **OpenScriptures** (`openscriptures/strongs` +
   `openscriptures/HebrewLexicon`, domaine public) pour mot original +
   translittération + prononciation (hébreu et grec).
2. Définition FR = **traduction des glosses anglais** (domaine public) via une
   passe LLM → gloss FR librement utilisable. Qualité « suffisante pour
   l'étude », raffinable ensuite.

> Aucune autre API/lexique Strong **français clairement libre** prêt à l'emploi
> n'a été trouvé (bolls.life = API JSON mais dictionnaires EN/RU ; lueur.org,
> emcitv, bible.audio, concordance.bible = sites copyrightés sans API libre →
> scraping écarté).

Comme la source BJC ne tague (à ce stade) que de l'hébreu, un **lexique hébreu
suffit en v1**.

### 4. API (`index.js`)

- Charger `bym_strongs.json` et `lexicon.json` au démarrage (comme `thebym.json`).
- **Opt-in** via query param `?strongs=1` sur les endpoints verset/chapitre
  existants : ajoute un champ
  `strongs: [{ text, strong, lemma, translit, definition, lang }]` (segments
  résolus contre le lexique). **Sans le param → réponse identique à aujourd'hui.**
- **✅ DÉCIDÉ : segments complets.** Le champ `strongs` renvoie **tous** les
  segments du verset (tagués + non tagués avec `strong:null`), pas seulement les
  segments tagués → la concaténation des `text` reproduit le verset exact, ce qui
  autorise un surlignage inline mot-à-mot ultérieur dans le lecteur.
- Nouvel endpoint **`GET /strong/:code`** → entrée du lexique pour un code
  (ex. `/strong/H7225`).
- Helper `attach_strongs(verseKey)` réutilisé par les routes
  verset/chapitre/sélection.

### 5. Automatisation

- Le cron hebdo (`.github/workflows/update-bible.yml`) régénère déjà via l'ETL :
  la modif de l'étape 2 fait que `bym_strongs.json` est mis à jour
  automatiquement.
- `build_lexicon.py` reste **manuel/occasionnel** (le lexique ne change pas).

---

## Fichiers concernés

- `scripts/update_from_gitlab.py` — préserver les `<w>`, émettre
  `bym_strongs.json`, couvrir 01–66, rapport de couverture.
- `scripts/build_lexicon.py` *(nouveau)* — générer `db/strongs/lexicon.json`.
- `db/strongs/bym_strongs.json` *(nouveau, généré)*.
- `db/strongs/lexicon.json` *(nouveau, généré)*.
- `index.js` — chargement au démarrage, `?strongs=1`, route `GET /strong/:code`,
  helper `attach_strongs`.
- *(À localiser)* l'étape qui assemble `db/thebym.json` à partir des fichiers par
  livre — à aligner pour produire la version segmentée sur les 66 livres.

---

## Vérification (bout en bout)

1. **ETL** : lancer `python3 scripts/update_from_gitlab.py` sur un clone ;
   vérifier que `bym_strongs.json` est généré et lire le rapport de couverture
   par livre.
2. **Invariant d'intégrité** : pour un échantillon de versets, asserter que
   `"".join(seg.t) == thebym.json[verseKey]` (aucun caractère perdu/ajouté).
3. **Lexique** : `python3 scripts/build_lexicon.py` puis vérifier
   `lexicon.json["H7225"]` (lemma + translit + définition présents).
4. **API** : démarrer le serveur, puis
   - `curl '/bym/genese/1/1?strongs=1'` → le verset contient `strongs[]` avec
     segments + champs lexique.
   - `curl '/bym/genese/1/1'` (sans param) → réponse **inchangée** (pas de champ
     `strongs`).
   - `curl '/strong/H7225'` → entrée du lexique.
   - `curl '/bym/jean/3/16?strongs=1'` → segments présents mais tous
     `strong:null` (NT non tagué) → confirme la **dégradation propre**.

---

## Décisions verrouillées (2026-06-22)

- ✅ **Source lexique FR** = `strong.sqlite` (bible-strong), risque licence
  assumé. Repli OpenScriptures documenté en plan B.
- ✅ **Forme du champ `strongs`** = segments complets (tagués + non tagués).

## 🔀 Décision requise — pivot Strong's (la source BJC ne suffit pas)

Puisque l'amont n'a qu'1 verset tagué, exposer des Strong's réels impose une
**source d'alignement externe**. Options :

- **A — Strong's par verset, niveau langue originale (recommandé).** Pour chaque
  verset, servir la liste **ordonnée des mots hébreu/grec** avec leur Strong's +
  lexique, **sans** les aligner mot-à-mot sur le français BYM. Source : interlinéaire
  (`interlineaire.sqlite` de bible-strong, ou domaine public OpenScriptures morphhb +
  GNT tagué). **Couverture ~100 % (AT+NT)**, licence gérable. Ne mappe pas sur les
  mots français.
- **B — Alignement mot→français BYM.** Le « vrai » interlinéaire français. Nécessite
  un alignement automatique lossy ; aucune source prête pour la traduction BYM.
  Coûteux, qualité incertaine. Non recommandé en v1.
- **C — Ne rien faire de plus** (servir seulement Ge 1:1 depuis la source). Inutile.

➜ Reco : **Option A**. Elle délivre la demande (« l'API fournit les Strong's ») sur
toute la Bible, avec `strong.sqlite` (lexique FR) déjà identifié.

## Décisions verrouillées (2026-06-22)

- ✅ **Source lexique FR** = `strong.sqlite` (bible-strong), risque licence
  assumé. Repli OpenScriptures documenté en plan B.
- ✅ **Forme du champ `strongs`** = segments complets (si Option B). Pour l'Option A,
  forme = liste de tokens langue-originale par verset.
- ✅ **Contenu re-synchronisé depuis GitLab** (ETL étendu aux 66 livres + workflow).

---

## Implémentation effective (2025) — Alignement LSG → BYM

L'alignement mot-à-mot a été réalisé via la **translittération LSG** (Louis Segond
avec Strong's embarqués dans `strong.sqlite`) alignée sur le texte BYM.

### Pipeline actuel

1. **`scripts/build_lexicon.py`** → `db/strongs/lexicon.json` (14 627 entrées,
   hébreu + grec, depuis `strong.sqlite`).
2. **`scripts/build_gloss_dict.py`** → `db/strongs/strong_to_bym.json` (dictionnaire
   global code → gloss BYM, construit depuis l'alignement + fusion des variantes
   manuelles de `db/strongs/manual_variants.json`).
3. **`scripts/build_strongs.py`** → `db/strongs/bym_strongs.json` (alignement
   segment par segment, 6 étapes : suffixe progressif court→long, fallback,
   fuzzy, dictionnaire, définition, non-aligné).
4. **`db/strongs/occurrences.json`** — nombre d'occurrences par code.
5. **`index.js`** — paramètre `?strongs=1` sur toutes les routes verset/chapitre,
   route `GET /strong/:code` (lexique + occurrences).

### Fichiers clés

| Fichier | Rôle |
|---|---|
| `scripts/build_strongs.py` | Moteur d'alignement (6 étapes) |
| `scripts/build_gloss_dict.py` | Construit le dictionnaire + fusion manuelles |
| `scripts/build_lexicon.py` | Construit le lexique depuis `strong.sqlite` |
| `scripts/align_with_llm.py` | Alignement LLM (correctif, arrière-plan) |
| `db/strongs/bym_strongs.json` | Alignement par verset (27 MB) |
| `db/strongs/strong_to_bym.json` | Dictionnaire code → gloss BYM (auto + manuel) |
| `db/strongs/manual_variants.json` | **Variantes manuelles** (jamais écrasé) |
| `db/strongs/gloss_mapping.json` | Substitutions conditionnées par code (noms propres) |
| `db/strongs/overrides.json` | Corrections manuelles par verset |
| `db/strongs/lexicon.json` | Lexique Strong's (lemma, translit, définition) |
| `db/strongs/occurrences.json` | Compteur d'occurrences par code |
| `Makefile` | Commandes : `make align`, `make deploy`, `make all` |

### Workflow de modification

1. Éditer `db/strongs/manual_variants.json` (variantes BYM par code)
2. `make align && make deploy`

### Algorithme d'alignement (6 étapes dans `align_segments()`)

1. **Suffixe progressif (mot substitué, court→long)** : essaie le dernier mot
   d'abord, puis expand. Les articles/conjonctions restent `null`.
2. **Suffixe progressif (mot LSG original, court→long)** : idem avec le texte LSG.
3. **Fuzzy match** : Levenshtein + préfixe commun ≥ 3 caractères.
4. **Dictionnaire** : gloss + variantes (priorité substitution > gloss > variantes).
5. **Définition** : extraction de stems depuis la définition du lexique +
   table de verbes irréguliers français.
6. **Non-aligné** : `text: null` + gloss LSG + infos lexique (aucun code perdu).

---

## 📋 Audit qualité des alignements (2026-07) — en cours

L'alignement auto produit deux classes de défauts systématiques, traités par
audit de workflow d'agents + curation conservatrice → `manual_variants.json`
(classe B) ou `overrides.json` (classe A). Pattern d'audit : scout Python
(`/tmp/scout_codes.py`) → workflow d'agents verify → curation conservatrice →
`make align` → vérif invariant texte + spot-check → `make deploy` (nécessite
autorisation explicite per-instance).

**Mémoire projet** : `strongs-alignment-curation.md` (mécanisme, garde-fous,
sémantique de matching `find_match_in_words` : inclusion sous-chaîne seulement
si variante ET token ≥ 4 caractères, sinon égalité exacte → variantes courtes
sûres).

### Classes de défauts

- **Classe A** — codes LSG marqués sur du **texte vide** (mot LSG non rendu en
  BYM, ex. article/pronon accolé) → l'aligneur les droppait. ~13 089 occ,
  6 870 légitimes, **6 219 vrais défauts sur ~5 237 versets**.
  👉 **Correction** : overrides par verset (`db/strongs/overrides.json`, scission
  de segments). **Non encore traité** — voir « Reste à faire ».

- **Classe B** — gloss auto = **mot-outil capturant un voisin** (cas H518 « si »
  collé sur « pas »). ~462 candidats.

### Avancement

| Lot | Candidats | Codes appliqués | Statut |
|---|---|---|---|
| Lot 1 (classe B) | 70 vérifiés | 45 | ✅ déployé |
| Numériques (Ge 25:7) | H7657/H3967/H2568 | 3 | ✅ déployé (+ exception `isdigit()` dans `build_strongs.py`) |
| H8141 « ans » (Ge 25:7) | override | 1 | ✅ déployé |
| **Lot 2 (classe B, 2 runs)** | **462 audités (100%)** | **99** (57+42) | ✅ déployé 2026-07-24 |

`manual_variants.json` : 136 → **283 codes**. `overrides.json` : 13 versets.

### Reste à faire (plus tard)

1. **Classe A — overrides par verset** (~5 200 versets). Détecter les codes LSG
   sur texte vide qui sont de vrais défauts (6 219 occ / 5 237 versets), générer
   des overrides scindant les segments pour taguer le mot BYM correct. Workflow
   d'agents : un agent par verset candidat (ou par lot) propose la scission →
   curation → `overrides.json` → `make align` → vérif + deploy. **Choix
   utilisateur verrouillé** : overrides par verset (précis) plutôt que
   forçage global. ⚠️ Volume ~5 200 versets ⇒ workflow potentiellement long ;
   reprendre par lots pour éviter la limite de débit (429) vue sur le lot 2.

2. **Résidus classe B** : sur les versets où la variante manuelle n'est pas
   adjacente, le gloss auto mot-outil persiste (ex. H2572 « avec » 12x, H3559
   « pour » 17x, H5704 « pour » 29x). Pas une régression ; traitable au cas par
   cas via overrides si besoin.

3. **Codes polymorphes skippés** : H7761/H7760 (suwm « mettre/poser » ~600x),
   H7761 intentionnellement non forcé (dégraderait l'alignement global). À
   revisiter seulement avec une approche par verset.

---

## ✅ Endpoint `/bym/strong/:num` — Index Strong's → versets — TERMINÉ

### Objectif

Nouvel endpoint API permettant de rechercher tous les versets contenant un code
Strong's donné, avec pagination.

### Réponse attendue

```
GET /bym/strong/G2316?page=1&size=20
```

```json
{
  "code": "G2316",
  "total": 1318,
  "page": 1,
  "size": 20,
  "lexicon": {
    "translit": "theos",
    "definition": "Dieu..."
  },
  "items": [
    {
      "livre": "Jean",
      "chapitre": 1,
      "verset": 1,
      "ecrit": "Au commencement était le Logos..."
    }
  ]
}
```

### Étapes de mise en œuvre — TOUTES TERMINÉES

#### Étape 1 — Script `scripts/build_strong_index.py` ✅

Génère un **index inversé** précalculé : code Strong's → liste de versets avec
texte BYM.

**Fichier de sortie** : `db/strongs/strong_index.json`

```json
{
  "H3068": [
    { "livre": "Genese", "chapitre": 1, "verset": 2, "ecrit": "La Terre devint..." }
  ],
  "G2316": [
    { "livre": "Jean", "chapitre": 1, "verset": 1, "ecrit": "Au commencement..." }
  ]
}
```

**Pourquoi un fichier précalculé** : `bym_strongs.json` fait 27 MB. Parcourir
31 169 versets à chaque requête serait trop lent. L'index permet une réponse
instantanée (lookup direct + `slice()`).

**Logique du script** :
1. Charge `db/strongs/bym_strongs.json` (l'alignement)
2. Charge `db/thebym.json` (le texte BYM)
3. Pour chaque verset, parcourt les segments ; pour chaque segment avec un code
   Strong's non-null, ajoute le verset à l'index du code
4. Parse la clé `Jn. 1:1` → `livre`, `chapitre`, `verset` (via la table de
   correspondance abréviations → noms de livres déjà existante dans `index.js`)
5. Évite les doublons (un verset peut avoir le même code plusieurs fois →
   n'apparaît qu'une fois dans l'index)
6. Sauvegarde `db/strongs/strong_index.json`

**Taille estimée** : ~15-20 MB (13 851 codes × versets avec texte court).

**Parsing des clés** : les clés `bym_strongs.json` sont au format `Jn. 1:1`.
Le script doit extraire `livre` (nom complet), `chapitre`, `verset`. Utiliser la
table `BOOK_NAMES` déjà présente dans `index.js` ou la répliquer dans le script.

#### Étape 2 — Modifier `index.js` ✅

**2a. Charger l'index au démarrage** :

```js
let strongIndex = {};
try {
  strongIndex = require("./db/strongs/strong_index.json");
  console.log(`Strong's index: ${Object.keys(strongIndex).length} codes`);
} catch (e) {
  console.log("Strong's index non trouvé");
}
```

**2b. Nouvel endpoint `/bym/strong/:num`** :

```js
app.get("/bym/strong/:num", (req, res) => {
  const code = req.params.num.toUpperCase();
  const items = strongIndex[code] || [];
  const total = items.length;

  // Pagination
  const page = parseInt(req.query.page) || 1;
  const size = Math.min(parseInt(req.query.size) || 20, 100);
  const start = (page - 1) * size;
  const paged = items.slice(start, start + size);

  // Infos lexique
  const lex = lexicon[code] || {};

  res.json({
    code,
    total,
    page,
    size,
    lexicon: {
      translit: lex.translit || null,
      definition: lex.definition || null
    },
    items: paged
  });
});
```

**2c. Route existante `/strong/:code`** : inchangée (renvoie le lexique +
occurrences). Le nouvel endpoint `/bym/strong/:num` est complémentaire (renvoie
les versets). Les deux coexistent.

#### Étape 3 — Modifier le Makefile ✅

Ajouter `build_strong_index.py` dans la cible `align`, après `build_strongs.py` :

```makefile
align:
    ...
    python3 scripts/build_strongs.py --sqlite $(SQLITE)
    python3 scripts/build_strong_index.py
    ...
```

#### Étape 4 — Tester et déployer ✅

```bash
make align && make deploy
```

Tests :
- `curl /bym/strong/G2316?page=1&size=5` → 5 versets sur 1318
- `curl /bym/strong/H3068?page=1&size=10` → 10 versets sur 6442
- `curl /bym/strong/INVALID` → `{ total: 0, items: [] }`
- Vérifier backward-compat : `curl /bym/genese/1/1` (sans `?strongs=1`) inchangé

### Fichiers concernés — TOUS LIVRÉS

| Fichier | Action | Statut |
|---|---|---|
| `scripts/build_strong_index.py` | **Créé** — génère `strong_index.json` | ✅ |
| `db/strongs/strong_index.json` | **Généré** — index code → versets (3.7 MB) | ✅ |
| `index.js` | **Modifié** — charger l'index + endpoint `/bym/strong/:num` | ✅ |
| `Makefile` | **Modifié** — `make align` inclut `build_strong_index.py` | ✅ |

---

## Ajout d'une version Louis Segond 1910 (LSG)

### Contexte

L'API ne sert actuellement qu'une seule version : la Bible de Yéhoshoua Ha
Mashiah (BYM). L'utilisateur souhaite ajouter la **Louis Segond 1910** (LSG) comme
deuxième version.

**Source disponible** : `strong.sqlite` contient déjà le texte LSG 1910 dans les
tables `LSGSAT2` (AT, 23 142 versets) et `LSGSNT2` (NT, 7 957 versets), soit
**31 099 versets**. Le texte contient les numéros Strong's inline
(ex: `Au 1722 commencement 746 était 2258 (5713) la Parole 3056`) qu'il faut
nettoyer pour obtenir le texte pur.

### Objectif

Servir plusieurs versions de la Bible (LSG 1910 maintenant, plus tard SRQ,
DRBY, etc.) aux côtés de la BYM, avec **exactement les mêmes routes** — seul le
préfixe change (`/bym/` → `/lsg/` → `/srq/` etc.). Backward-compatible.

### Strong's pour LSG — avantage majeur

Le texte LSG dans `strong.sqlite` contient les numéros Strong's **nativement**
embarqués (ex: `Au commencement 07225, Dieu 0430 créa 01254 (8804) 0853 les cieux
08064 0853 et la terre 0776.`). **Aucun alignement n'est nécessaire** — il suffit
de parser les codes depuis le texte. Cela donne une **couverture Strong's de
100%** pour LSG, là où BYM a ~52% après l'alignement complexe.

Donc LSG aura **deux fichiers générés** :
- `db/lsg.json` — texte pur (codes Strong's retirés)
- `db/strongs/lsg_strongs.json` — segments avec Strong's (format identique à
  `bym_strongs.json` : `[{text, strong}]` par verset)

Et `?strongs=1` fonctionnera sur LSG tout comme sur BYM. La fonction
`maybe_attach_strongs()` utilisera les données Strong's de la version demandée
(`req.strongsData`) au lieu du global `bym_strongs`.

### Décisions de conception

**1. Routes génériques `/:version/...`** — un seul jeu de routes pour toutes
les versions, le préfixe URL identifie la version :

```
/:version                      → verset aléatoire
/:version/:livre               → tout un livre
/:version/:livre/info          → infos du livre
/:version/:livre/:chap         → un chapitre
/:version/:livre/:chap/:sel    → une sélection de versets
/:version/:livre/:chap/:sel/next → verset suivant
/:version/:livre/:chap/:sel/prev → verset précédent
/:version/:livre/read          → redirection lecteur
/:version/:livre/:chap/read    → redirection lecteur
/:version/:livre/:chap/:sel/read → redirection lecteur
```

Ajouter une nouvelle version = ajouter une entrée dans `VERSIONS` + un fichier
JSON. **Zéro nouvelle route à écrire.**

**Exception** : `/bym/strong/:num` reste spécifique à BYM (Strong's = alignement
LSG→BYM). Déclaré avant les routes génériques pour ne pas être capturé.

**2. Registre `VERSIONS`** au démarrage :

```js
const VERSIONS = {
  bym: {
    data: bym,        // db/thebym.json
    name: "Bible de Yéhoshoua Ha Mashiah",
    strongs: true,   // ?strongs=1 supporté
  },
  lsg: {
    data: lsg,        // db/lsg.json
    name: "Louis Segond 1910",
    strongs: false,  // ?strongs=1 non supporté
  },
  // Futur :
  // srq: { data: srq, name: "Segond 1910 Révisée", strongs: false },
  // drby: { data: drby, name: "Darby", strongs: false },
};
```

**3. Middleware `resolveVersion`** — valide le préfixe, attache la source de
données et le nom de version à `req` :

```js
function resolveVersion(req, res, next) {
  const v = VERSIONS[req.params.version];
  if (!v) return res.status(404).json({ error: `Version "${req.params.version}" non supportée` });
  req.source = v.data;
  req.versionName = v.name;
  req.supportsStrongs = v.strongs;
  next();
}
```

**4. Réfactoriser les fonctions clés** pour accepter `source` et `versionName` :
- `make_verse(abbr, chap, verset, ecrit, versionName)`
- `get_book(nom, source, versionName)`
- `get_all_chapter(nom, chap, source, versionName)`
- `get_all_of_selection(nom, chap, sel, source, versionName)`
- `enrich_result(result, req, source)`
- `return_result(res, result, req, source)`

Les routes génériques passent `req.source` et `req.versionName`. Backward-compat :
les routes `/bym` existantes sont remplacées par les routes génériques
(`/:version` capture `bym`), le comportement est identique.

**5. Strong's conditionnel** : `maybe_attach_strongs()` vérifie
`req.supportsStrongs` avant d'attacher les segments. Si `?strongs=1` est demandé
sur une version sans Strong's → erreur 400.

**6. Backward-compatibilité** : `/:version` avec `version=bym` remplace les
routes `/bym` existantes. Les réponses sont identiques (même `source`, même
`versionName`). Les URL `/bym/...` existantes continuent de fonctionner car
`bym` est une clé valide dans `VERSIONS`.

### Étapes de mise en œuvre

#### Étape 1 — Script `scripts/build_lsg.py` (nouveau)

Génère **deux fichiers** :
- `db/lsg.json` — texte Louis Segond 1910 pur (sans numéros Strong's),
  structuré comme `thebym.json` (clés `"Ge. 1:1"`, valeur = texte du verset)
- `db/strongs/lsg_strongs.json` — segments Strong's natifs (format identique à
  `bym_strongs.json` : `{ "Ge. 1:1": [{text, strong}] }`)

**Logique** :
1. Ouvrir `strong.sqlite`
2. Pour chaque livre (1-66), interroger `LSGSAT2` (livres 1-39) ou `LSGSNT2`
   (livres 40-66)
3. Parser chaque verset en segments `[{text, strong}]` :
   - Les codes Strong's sont placés **après** le(s) mot(s) qu'ils décrivent
   - AT : nombres zero-padded (`07225`, `0430`) → préfixe `H`, retirer le zéro
   - NT : nombres non-padded (`1722`, `746`) → préfixe `G`
   - Codes morphologiques entre parenthèses (`(8804)`, `(5713)`) → ignorés
   - Ponctuation : rattacher au segment précédent (pas au suivant)
4. Construire `lsg_strongs.json` : `{ "Ge. 1:1": [{text, strong}, ...] }`
5. Construire `lsg.json` : concaténer les `text` des segments (texte pur)
6. Mapper le numéro de livre → abréviation via `BOOK_NUM_TO_ABBR` (même table que
   `build_strongs.py`)
7. Sauvegarder les deux fichiers

**Fichier de sortie** : `db/lsg.json` (~4-5 MB) + `db/strongs/lsg_strongs.json` (~8-10 MB)

**Avantage clé** : contrairement à BYM où l'alignement est lossy (~52% de codes
alignés), LSG a **100% de couverture Strong's** car les codes sont natifs dans le
texte. Aucun alignement nécessaire.

#### Étape 2 — Modifier `index.js`

**2a. Charger `lsg.json` au démarrage** :

```js
let lsg = {};
try {
  lsg = require("./db/lsg.json");
  console.log(`LSG: ${Object.keys(lsg).length} versets chargés`);
} catch (e) {
  console.log("LSG: fichier non trouvé");
}
```

**2b. Définir le registre `VERSIONS` + middleware `resolveVersion`** :

```js
const VERSIONS = {
  bym: {
    data: bym,                // db/thebym.json
    strongsData: bym_strongs, // db/strongs/bym_strongs.json (aligné LSG→BYM, ~52%)
    name: "Bible de Yéhoshoua Ha Mashiah",
    strongs: true,
  },
  lsg: {
    data: lsg,                // db/lsg.json
    strongsData: lsg_strongs, // db/strongs/lsg_strongs.json (Strong's natifs, 100%)
    name: "Louis Segond 1910",
    strongs: true,
  },
  // Futur :
  // srq: { data: srq, name: "Segond Révisée", strongs: false },
  // drby: { data: drby, name: "Darby", strongs: false },
};

function resolveVersion(req, res, next) {
  const v = VERSIONS[req.params.version];
  if (!v) return res.status(404).json({ error: `Version "${req.params.version}" non supportée` });
  req.source = v.data;
  req.versionName = v.name;
  req.supportsStrongs = v.strongs;
  req.strongsData = v.strongsData;  // données Strong's de cette version
  next();
}
```

**2c. Réfactoriser les fonctions clés** pour accepter `source` et `versionName` :

- `make_verse(abbr, chap, verset, ecrit, versionName)` — remplace le hardcoded
  `version: "Bible de Yéhoshoua Ha Mashiah"`
- `get_book(nom, source, versionName)` — utilise `source` au lieu de `bym`
- `get_all_chapter(nom, chap, source, versionName)`
- `get_all_of_selection(nom, chap, sel, source, versionName)`
- `enrich_result(result, req, source)` — `source` au lieu de `bym`
- `return_result(res, result, req, source)` — passe `source` aux sous-fonctions
- `maybe_attach_strongs(result, req)` — vérifie `req.supportsStrongs` avant d'attacher

**2d. Remplacer les routes `/bym` par les routes génériques `/:version`** :

Ordre de déclaration (important pour Express) :

```js
// 1. Routes spécifiques BYM (avant les génériques)
app.get("/bym/strong/:num", ...);  // Strong's index — BYM uniquement

// 2. Routes génériques (capturent /bym, /lsg, /srq, etc.)
app.get("/:version", resolveVersion, (req, res) => { ... });  // verset aléatoire

app.get("/:version/:livre/read", resolveVersion, ...);
app.get("/:version/:livre/:chap/read", resolveVersion, ...);
app.get("/:version/:livre/:chap/:selections/read", resolveVersion, ...);

app.get("/:version/:livre/info", resolveVersion, ...);

app.get("/:version/:livre/:chap/:selections/next", resolveVersion, ...);
app.get("/:version/:livre/:chap/:selections/prev", resolveVersion, ...);

app.get("/:version/:livre", resolveVersion, ...);
app.get("/:version/:livre/:chap", resolveVersion, ...);
app.get("/:version/:livre/:chap/:selections", resolveVersion, ...);
```

Note : les routes `/read`, `/info`, `/next`, `/prev` doivent être déclarées
**avant** les routes génériques `/:version/:livre` et `/:version/:livre/:chap`
pour ne pas être capturées par les paramètres dynamiques.

**2e. Strong's conditionnel** dans `maybe_attach_strongs()` :

```js
function maybe_attach_strongs(result, req) {
  if (req.query.strongs !== "1") return result;
  if (!req.supportsStrongs) return result;  // version sans Strong's — pas de champ
  // Utiliser les données Strong's de LA VERSION demandée (req.strongsData)
  // au lieu du global bym_strongs
  const strongsData = req.strongsData;
  // ... attachement des segments (code existant, adapté pour utiliser strongsData)
}
```

**Note** : `bym_strongs` reste chargé en global pour la route spécifique
`/bym/strong/:num` (index Strong's → versets). L'endpoint `/:version/strong/:num`
générique (si ajouté plus tard) nécessitera un index Strong's par version.

**Backward-compat** : `/:version` avec `version=bym` remplace les anciennes
routes `/bym`. Les réponses sont identiques car `VERSIONS.bym.data = bym` et
`VERSIONS.bym.name = "Bible de Yéhoshoua Ha Mashiah"`. `?strongs=1` sur `/bym/...`
utilise `VERSIONS.bym.strongsData = bym_strongs` (même fichier qu'avant).

#### Étape 3 — Modifier le Makefile

Ajouter une cible `lsg` :

```makefile
# Construction du texte LSG depuis strong.sqlite
lsg:
	@echo "═══ Construction du texte LSG 1910 ═══"
	python3 scripts/build_lsg.py --sqlite $(SQLITE)
	@echo "✅ LSG terminé"
```

Et l'ajouter dans la cible `all` :

```makefile
all: align lsg deploy
```

#### Étape 4 — Tester et déployer

```bash
make lsg && make deploy
```

Tests :
- `curl /lsg/genese/1/1` → `"Au commencement, Dieu créa les cieux et la terre."`
  avec `version: "Louis Segond 1910"`
- `curl /lsg/jean/1/1` → `"Au commencement était la Parole, et la Parole était
  avec Dieu, et la Parole était Dieu."`
- `curl /lsg/genese/1/1?strongs=1` → segments Strong's **100% alignés** (natifs LSG)
- `curl /lsg/jean/1/1?strongs=1` → segments avec G1722, G746, G3056, etc.
- `curl /lsg` → verset aléatoire LSG
- `curl /lsg/genese/1` → tout Genèse 1
- `curl /lsg/genese/1/info` → infos du livre (communes avec BYM)
- `curl /bym/genese/1/1` → **inchangé** (backward-compat, `/:version` capture `bym`)
- `curl /bym/genese/1/1?strongs=1` → strongs toujours fonctionnel sur BYM
- `curl /xxx/genese/1/1` → erreur 404 (version non supportée)

### Fichiers concernés

| Fichier | Action |
|---|---|
| `scripts/build_lsg.py` | **Créer** — extrait le texte LSG + parse les Strong's natifs depuis `strong.sqlite` |
| `db/lsg.json` | **Généré** — texte LSG 1910 pur (~4-5 MB) |
| `db/strongs/lsg_strongs.json` | **Généré** — segments Strong's natifs LSG (~8-10 MB, 100% couverture) |
| `index.js` | **Modifier** — `VERSIONS` registry, middleware `resolveVersion`, réfactoriser fonctions, routes génériques `/:version/...` |
| `Makefile` | **Modifier** — ajouter cible `lsg` |

### Points d'attention

1. **Nettoyage du texte** : le texte LSG dans `strong.sqlite` contient des
   numéros Strong's inline. La regex de nettoyage doit être précise pour ne pas
   supprimer des nombres légitimes du texte biblique (ex: « trois troupeaux »
   dans Genèse 29:2). Les numéros Strong's sont toujours précédés d'un espace et
   suivis d'un mot ou de parenthèses. Les nombres du texte biblique sont des
   mots français ("trois", "douze") — LSG utilise des mots pour les nombres, pas
   de chiffres. À vérifier empiriquement.

2. **Couverture** : LSG 1910 a 31 099 versets vs 31 169 pour BYM. Vérifier les
   versets manquants (LSG peut avoir une numérotation légèrement différente,
   ex: Psaumes, Esther).

3. **`bym_info.json` commun** : les infos des livres (signification, auteur,
   thème) sont communes à toutes les versions. Les routes
   `/:version/:livre/info` servent le même contenu quel que soit `:version`.

4. **Strong's natifs sur LSG** : contrairement à BYM qui nécessite un
   alignement complexe (6 étapes, ~52% de couverture), LSG a les Strong's
   **nativement embarqués** dans le texte de `strong.sqlite`. Le script
   `build_lsg.py` les parse directement — aucun alignement nécessaire, couverture
   100%. Le fichier `lsg_strongs.json` a le même format que `bym_strongs.json`.

5. **Ajout d'une version future** (ex: Darby, SRQ) :
   1. Générer `db/darby.json` (+ `db/strongs/darby_strongs.json` si Strong's
      disponibles pour cette version)
   2. Ajouter une entrée dans `VERSIONS` : `darby: { data: darby, strongsData:
      darby_strongs || null, name: "Darby", strongs: !!darby_strongs }`
   3. Déployer. Aucune route à ajouter.

6. **Route `/bym/strong/:num`** : reste spécifique à BYM (préfixe codé en dur).
   Si on veut la rendre générique (`/:version/strong/:num`), il faudra un index
   Strong's par version (`lsg_strong_index.json`, etc.). Pour l'instant, seul
   BYM a cet index.

---

## ✅ Version Darby ajoutée (2026-07-25)

3ᵉ version servie : **`darby`** — Bible J.N. Darby (1885), Domaine public.
Strong's **alignés (LSG→Darby)** depuis le 2026-07-25 (Option B livrée).

- **Source** : `midvash/bible-data` (`versions/fr/darby-fr/darby-fr.json`,
  public domain). Schéma `books[].chapters[].verses[]={number,text}`, codes
  livres OSIS.
- **ETL** : `scripts/build_darby.py` (table OSIS→abbr projet, fallback curl si
  urllib échoue en SSL). Cible Makefile `make darby`. Nettoyage source :
  retrait des `*` de début de paragraphe + rétablissement de l'espace dans le
  composé divin « ÉternelDieu » → « Éternel Dieu » (38 occurrences, défaut
  source midvash).
- **Sortie texte** : `db/darby.json` (31 167 versets, 66 livres, clés `"Ge. 1:1"`).
- **Strong's (Option B)** : pipeline LSG→Darby par retargeting de
  `build_strongs.py` / `detect_versif_offsets.py` / `build_gloss_dict.py`
  via `--target darby` (fichiers curations suffixés `*_darby.json`, vides au
  départ). Cible Makefile `make align-darby`. Sorties :
  `db/strongs/darby_strongs.json` (31167 versets, **38,6 %** segments tagués —
  légèrement supérieur à BYM 38,4 %), `strong_to_darby.json`,
  `darby_strong_index.json` (13 845 codes). Invariant texte 0 violation.
- **Registry** : `index.js` `VERSIONS.darby = { data: darby,
  strongsData: darby_strongs, strongIndex: darbyStrongIndex,
  name: "Bible Darby (J.N. Darby, 1885)", strongs: true }`.
- **Comportement `?strongs=1`** : retourne le texte + segments Strong's
  (`maybe_attach_strongs`). `/darby/strong/:code` → lexique partagé + total>0
  (ex. G2316→1157, H3068→5483).
- **Versification** : protestante canonique = hébraïque, ~140/208 écarts vs
  LSG (surtout 1 Chroniques). Les marqueurs « (C.V) » de strong.sqlite
  (→numéros hébraïques) sont réutilisables tels quels pour Darby ;
  `versif_offsets_darby.json` recalculé (342 versets + 16 bords cross-chapitre).
- **Routes** : `/darby`, `/darby/:livre/:chap`, `/darby/:livre/:chap/:verset`,
  `/darby/:livre/:chap/:verset?strongs=1`, `/darby/strong/:code`, etc.

### Versions servies (statut)

| Slug | Nom | Strong's | Source |
|---|---|---|---|
| `bym` | Bible de Yéhoshoua Ha Mashiah | alignés (LSG→BYM, ~38,4 %) | GitLab `bjc-source` |
| `lsg` | Louis Segond 1910 | natifs (100 %) | `strong.sqlite` |
| `darby` | Bible Darby (1885) | alignés (LSG→Darby, ~38,6 %) | `midvash/bible-data` (public domain) |

### Suite possible (curation Darby, plus tard)

Réutiliser le pattern d'audit (scout + workflow) sur `strong_to_darby.json` si
des gloss mot-outil apparaissent (classe de défaut H518 etc.), via
`manual_variants_darby.json` / `overrides_darby.json` / `gloss_mapping_darby.json`
(vides pour l'instant). Quelques versets Darby-only (208 vs LSG) non alignés au
premier passage → traitables via offsets affinés ou overrides.
