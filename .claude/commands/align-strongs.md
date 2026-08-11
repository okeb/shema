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

   a. **Complétude (contre le grec, pas seulement la LSG)** : reconstituer le texte
      grec mot par mot avec leurs Strong's (y compris les articles G3588). Le comptage
      LSG est un point de départ mais **ne fait pas foi** — la LSG omet systématiquement
      les articles (G3588) et parfois d'autres mots. Le comptage de référence est le
      **texte grec reconstitué**. Lister TOUS les strongs manquants (présents en grec
      mais pas en BYM), en distinguant :
      - **Plaçables** : un mot visible existe dans le BYM (ex: G3588 sur « le », « la »,
        « les », « d' », « l' »)
      - **Non plaçables** : le mot grec n'a pas d'équivalent visible dans le BYM
        (absorbé dans la traduction, rendu par une virgule, non traduit)

   b. **Strong's en texte nul** : segments avec `text: null` + `strong: Gxxx` (mal placés
      à la fin du verset). Ce sont des strongs tombés de l'alignement automatique.

   c. **Correction sémantique** : pour chaque strong présent, vérifier que le texte BYM
      correspond au sens du mot grec/hébreu (via `lexicon.json`). **La définition prime** —
      le Strong doit être placé sur le mot ou l'expression qui capture au mieux le sens
      du mot grec. Détecter :
      - Strong sur le mauvais mot (ex: G2980 λαλέω="parler" sur "entre" au lieu de "parlant")
      - Strong sur un fragment au lieu du mot complet (ex: G1130 sur "pauvrement"
        au lieu de "pauvrement vêtus")
      - Strong sur un mot trop restreint : étendre vers l'expression complète qui
        capture le sens du mot composé ou nuancé (voir règle ci-dessous)
      - Strong manquant sur un mot visible (ex: article G3588 sur "le"/"les"/"d'"/"l'")
      - **Articles G3588 systématiques** : vérifier chaque article grec (ὁ/ἡ/τό/τῶν/τοῦ/τῇ/τὴν
        etc.) et le placer sur le mot visible correspondant du BYM (« le », « la », « les »,
        « d' », « l' », « un », « une »). La LSG omet presque toujours les articles —
        il faut donc les ajouter manuellement à partir du grec reconstitué.

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

## Règle clé : la définition prime

**Le Strong doit capturer l'expression qui rend au mieux le sens (définition) du mot grec/hébreu.**
Un mot grec composé ou nuancé doit couvrir toute l'expression BYM qui traduit ce sens,
 pas seulement un fragment.

### Quand étendre un Strong sur une expression plus large

Un Strong doit être **étendu** sur l'expression complète lorsque :

1. **Le mot grec est un composé** dont un élément est rendu séparément en français :
   - G2017 ἐπιφαύσκω (ἐπί=sur + φαύω=briller) → « brillera sur » (pas juste « brillera »)
   - G2175 εὐωδία (εὖ=bon + ὀδή=odeur) → « bonne odeur » (pas juste « odeur »)

2. **Le mot grec a un sens réciproque/réfléchi** rendu par plusieurs mots français :
   - G1438 ἑαυτοῖς = « à vous-mêmes / entre vous » → « entre vous » (pas juste « vous »)

3. **Le mot grec est une construction négative** (ne...pas, ne...pas même) :
   - G3366 μηδὲ = « ne...pas même » → « ne soient pas même » (pas juste « même »)
   - G3361 μή = « ne...pas » → étendre si possible (voir contraintes ci-dessous)

4. **Le verbe grec implique un état/condition** rendu par une expression française :
   - G1130 γυμνιτεύω = « être pauvrement vêtu » → « pauvrement vêtus » (pas juste « pauvrement »)
   - G790 ἀστατέω = « être sans domicile fixe » → « sans domiciles fixes » (pas juste « domiciles »)

### Contraintes pour l'extension

- **Ne JAMAIS modifier le texte BYM** (règle absolue).
- **Ne pas absorber un autre Strong** : si un mot entre « ne » et « pas » a son propre
  Strong (ex: un verbe G1096), on ne peut pas fusionner. L'extension n'est possible que
  si les mots intermédiaires n'ont pas de Strong grec propre (ex: auxiliaire français « soient »).
- Vérifier systématiquement la définition dans `lexicon.json` avant de placer ou d'étendre.
- La concaténation des segments doit toujours reproduire le texte source à l'identique.

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
- **Articles G3588 (systématique)** : la LSG omet presque toujours les articles grecs.
  La skill doit reconstituer le texte grec et ajouter chaque G3588 sur le mot visible
  du BYM qui le rend (« le », « la », « les », « d' », « l' », « un », « une »).
  Exemples : τῷ λουτρῷ → « **le** bain » (G3588 sur « le »), τοῦ ὕδατος → « **d'**eau »
  (G3588 sur « d' », G5204 sur « eau »). Toujours compter le grec, pas seulement la LSG.
- **Typo potentielle** : si un strong demandé n'existe pas dans le verset (ex: G732 au lieu
  de G737), signaler la discrepancy mais injecter ce que l'utilisateur demande (il a confirmé
  vouloir l'injection). Noter clairement la discrepancy dans le rapport.