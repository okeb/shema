# Skill : Alignement Strong's BYM

Analyse et corrige l'alignement Strong's d'un ou plusieurs versets de la BYM.

## Arguments

$ARGUMENTS

(Format attendu : soit une liste de corrections `Gxxxx -> texte - livre chap:verset`,
soit une demande de vérification `vérifie Ep 5:14`, soit les deux combinés.)

## Méthodologie

### Étape 1 — Charger les données

Lance un script Python qui charge en mémoire :
- `db/thebym.json` — texte source BYM
- `db/strongs/bym_strongs.json` — alignement actuel (format compact)
- `db/strongs/lsg_strongs.json` — alignement source LSG (référence)
- `db/strongs/lexicon.json` — lexique Strong's (définitions grec/hébreu)
- `db/strongs/overrides.json` — corrections manuelles (indentation 2 espaces)

### Étape 2 — Pour chaque verset demandé

1. **Afficher le texte BYM** (`db/thebym.json[verse]`)
2. **Afficher l'alignement BYM actuel** : liste des segments `{text, strong, gloss}`
3. **Afficher l'alignement LSG** : liste des strongs avec leur texte
4. **Reconstituer le texte grec** à partir du lexique et de la LSG
5. **Comparer** :

   a. **Complétude** : le nombre de strongs BYM = nombre de strongs LSG ?
      Lister les strongs manquants (présents en LSG mais pas en BYM).

   b. **Strong's en texte nul** : segments avec `text: null` + `strong: Gxxx` (mal placés
      à la fin du verset). Ce sont des strongs tombés de l'alignement automatique.

   c. **Correction sémantique** : pour chaque strong présent, vérifier que le texte BYM
      porteé correspond au sens du mot grec/hébreu (via `lexicon.json`).
      Détecter :
      - Strong sur le mauvais mot (ex: G3956 sur "qui" au lieu de "tout")
      - Strong sur un fragment au lieu du mot complet (ex: G1130 sur "pauvrement"
        au lieu de "pauvrement vêtus")
      - Strong manquant sur un mot visible (ex: article G3588 sur "le"/"les")

   d. **Présenter un tableau récapitulatif** :
      | # | Strong | Grec | Sens | Texte BYM | Correct ? |
      Marquer ✅ ou ❌ pour chaque entrée.

### Étape 3 — Appliquer les corrections

Pour chaque correction demandée ou détectée :

1. **Modifier les segments** du verset dans `bym_strongs.json` :
   - Déplacer un strong d'un mot vers un autre
   - Étendre un strong sur une phrase plus large (ex: "pauvrement" → "pauvrement vêtus,")
   - Ajouter un strong manquant sur un mot visible
   - Supprimer les segments en texte nul (strongs mal placés)

2. **Vérifier l'intégrité du texte** : la concaténation de tous les `text` des segments
   doit être **exactement égale** au texte BYM source (`thebym.json[verse]`).
   Si mismatch → ABORT et signaler l'erreur.

3. **Vérifier qu'aucun strong n'est en texte nul** après correction.

4. **Écrire dans les deux fichiers** :
   - `db/strongs/bym_strongs.json` — format compact : `json.dump(..., separators=(",", ":"))`
   - `db/strongs/overrides.json` — format indenté 2 espaces : `json.dump(..., indent=2)` + `\n` final

   Ces deux fichiers doivent toujours rester synchrones pour les versets corrigés.
   `overrides.json` garantit que les corrections résistent aux rebuilds (`make align`).

### Étape 4 — Déployer

1. `git add db/strongs/bym_strongs.json db/strongs/overrides.json`
2. `git commit -m "fix(strongs): <résumé des corrections>"`
3. `make deploy` (déploiement Vercel production)

### Étape 5 — Rapport final

Présenter :
- Le tableau récapitulatif final (tous les strongs avec ✅/❌)
- Le statut : X/Y strongs, texte vérifié, déployé en prod
- Les éventuelles questions/doutes (strongs ambigus, typos potentiels)

## Règles importantes

- **Format des clés de versets** : utiliser le format BYM exact (ex: `1 Co. 4:11`, `Ep. 5:25`,
  `Ro. 14:23`). Les livres ont un espace après l'abréviation pour les numéros (1 Co., 2 Co.),
  pas pour les autres (Ep., Ro., Mt.).
- **Apostrophes** : vérifier le type exact d'apostrophe dans le texte BYM source
  (curly ' U+2019 ou straight ') avant de reconstruire des segments.
- **⚠️ CONTRAINTE STRICTE : NE JAMAIS MODIFIER LE TEXTE BYM** — c'est une règle absolue.
  Seuls les strongs (placements) changent. La concaténation des segments doit TOUJOURS
  reproduire le texte source à l'identique. Si un strong grec n'a pas de mot visible dans
  le BYM (rendu par une virgule, absorbé dans une paraphrase, non traduit), il reste non
  placé — on n'ajoute jamais de mot au texte BYM pour accommoder un strong.
- **overrides.json** : ajouter le verset corrigé à ce fichier (clé = référence verset,
  valeur = liste complète des segments). Ne pas écraser les autres versets déjà présents.
- **bym_strongs.json** : fichier compact, ne pas reformater (garder `separators=(",", ":")`).
- **Articles G3588** : la source LSG omet souvent les articles. Si l'utilisateur les signale
  ou si on les détecte dans le grec, les ajouter sur le mot visible (« le », « la », « les »).
- **Typo potentielle** : si un strong demandé n'existe pas dans le verset (ex: G732 au lieu
  de G737), signaler la discrepancy mais injecter ce que l'utilisateur demande (il a confirmé
  vouloir l'injection). Noter clairement la discrepancy dans le rapport.