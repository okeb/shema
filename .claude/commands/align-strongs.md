# Skill : Alignement Strong's BYM

Analyse et corrige l'alignement Strong's d'un ou plusieurs versets de la BYM.

## Principe directeur : la source prime, pas la LSG

**La référence de comptage est le texte SOURCE reconstitué (grec pour le NT, hébreu pour l'AT),
mot par mot avec leurs Strong's — pas la liste Louis Segond.**

La LSG (tables `LSGSAT2`/`LSGSNT2` de `strong.sqlite`, qui produit `lsg_strongs.json`)
embarque les Strong's dans le texte français et **omet systématiquement les articles (G3588)
et de nombreux mots fonctionnels** (particules δὲ/γάρ/οὖν, prépositions, pronoms relatifs,
conjonctions de subordination, etc.). En conséquence, **un verset a presque toujours plus de
Strong's que la liste LSG ne le recense**. La liste LSG ne fait donc pas foi pour la complétude :
 elle est tronquée par construction. Le comptage de référence est le texte source reconstitué.

La skill reconstitue donc le texte source de chaque verset à partir de la connaissance du
grec/hébreu, fiabilisée par `lexicon.json` (définitions, origines, types). La LSG n'est gardée
que comme contre-vérification secondaire (repérer d'éventuels désaccords de code Strong choisi).

## Base textuelle : la BYM suit le Textus Receptus (NT), pas Nestle-Aland

**La base grecque de référence pour la BYM (NT) est le Textus Receptus** (Stephanus 1550 /
Scrivener 1894), **et non le Nestle-Aland (NA28/NA30)**. C'est un fait établi qui affecte
chaque verset du NT.

Conséquence critique : **NA28 et le TR divergent sur la présence de nombreux articles et
pronoms**. NA28 omet systématiquement des articles (οἱ, τῷ, τὸν…) et pronoms (αὐτῶν, αὐτοῦ…)
que le TR conserve. Les interlignes en ligne (BibleHub, StepHub, etc.) affichent souvent
NA28 — donc un verset NA28 anarthre peut avoir **plusieurs G3588 / G846 de plus** dans le TR.

**⚠️ Les divergences TR vs NA28 ne se limitent pas aux articles/pronoms : elles peuvent
substituer un LEXÈME entier**, ce qui change le code Strong ET le sens rendu. Exemples concrets
(Mt 15) :
- Mt 15:4 : TR **ἐνετείλατο** (G1781 « commander ») vs NA28 **εἶπεν** (G2036 « dire »).
  BYM rend « a **commandé** » → seul G1781 (TR) concilie source ET sens.
- Mt 15:6 : TR **τὴν ἐντολὴν** (G1785 « commandement ») vs NA28 **τὸν λόγον** (G3056 « parole »).
  BYM rend « **commandement** » → seul G1785 (TR) concilie source ET sens.
=> Un Strong dont la définition ne correspond pas au mot BYM est souvent le signe qu'on a
pris la lecture NA28 au lieu du TR. **Toujours vérifier la lecture TR quand le sens cloche.**

- **Toujours reconstituer le source contre le TR**, pas contre NA28. Ne pas se fier à un
  interlinaire NA28 affiché en ligne pour le comptage.
- En cas de doute sur la lecture TR exacte d'un verset (présence d'un article / pronom /
  particule), le **vérifier explicitement** (WebSearch/WebFetch ciblé « Textus Receptus » /
  Scrivener, ou cross-check TR vs NA28) plutôt que d'inventer — et signaler la lecture retenue.
- Un verset peut avoir **plusieurs G3588** (ex: Mt 15:1 TR = « τῷ Ἰησοῦ οἱ ἀπὸ Ἱεροσολύμων » →
  G3588×2 : τῷ sur « auprès de » + οἱ sur « des »). Compter chaque occurrence du TR.
- Ne jamais supprimer un G3588/G846 présent dans le TR sous prétexte qu'il est absent de NA28.

## Arguments

$ARGUMENTS

(Format attendu : soit une liste de corrections `Gxxxx -> texte - livre chap:verset`,
soit une demande de vérification `vérifie Ep 5:14`, soit les deux combinés.)

## Méthodologie

### Étape 1 — Charger les données

Lance un script Python qui charge en mémoire :
- `db/thebym.json` — texte source BYM
- `db/strongs/bym_strongs.json` — alignement actuel (format compact)
- `db/strongs/lexicon.json` — lexique Strong's (définitions grec/hébreu) — **référence sémantique**
- `db/strongs/overrides.json` — corrections manuelles (indentation 2 espaces)
- `db/strongs/lsg_strongs.json` — alignement LSG (contre-vérification secondaire, liste tronquée)

### Étape 2 — Pour chaque verset demandé

1. **Afficher le texte BYM** (`db/thebym.json[verse]`)
2. **Afficher l'alignement BYM actuel** : liste des segments `{text, strong, gloss}`
3. **Reconstituer le texte SOURCE** (grec NT / hébreu AT) mot par mot, dans l'ordre, chaque mot
   accompagné de son code Strong's et de son sens (via `lexicon.json`). Inclure **tous** les mots
   que la LSG omet : articles (G3588), particules (G1161 δὲ, G1063 γάρ, G3767 οὖν, G5037 τέ…),
   prépositions, pronoms relatifs, conjonctions de subordination. Présenter sous forme de
   liste numérotée — **cette liste est le comptage de référence**. Fiabiliser chaque mot en
   vérifiant sa définition dans `lexicon.json`. En cas d'incertitude sur le texte source exact
   d'un verset, le dire explicitement plutôt que d'inventer un mot ; croiser alors avec la LSG.

4. **Afficher la liste LSG** comme contre-vérification secondaire : non pas pour compter, mais
   pour (a) repérer les désaccords de code Strong choisi (ex: source G1531 εἰσπορευόμενον mais
   LSG/BYM utilisent G1525 — convention source héritée, à laisser sauf demande explicite) et
   (b) confirmer quels mots fonctionnels la LSG a omis (donc à ajouter depuis la source).

5. **Comparer** (contre le texte source reconstitué, NON contre la LSG) :

   a. **Complétude (contre le source reconstitué)** : le nombre de référence est le nombre de
      mots du texte source reconstitué (typiquement supérieur au nombre LSG). Lister TOUS les
      strongs manquants (présents dans le source reconstitué mais absents du BYM), en distinguant :
      - **Plaçables** : un mot visible existe dans le BYM (ex: G3588 sur « le », « la », « les »,
        « d' », « l' », « un », « une », « ce », « ce qui »)
      - **Non plaçables** : le mot grec n'a pas d'équivalent visible dans le BYM (absorbé dans la
        traduction, rendu par une ponctuation, non traduit — ex: particules δὲ/γάρ/οὖν souvent
        implicites). Ces strongs restent non placés — on n'ajoute jamais de mot au BYM.

   b. **Strong's en texte nul** : segments avec `text: null` + `strong: Gxxx` (mal placés à la fin
      du verset). Ce sont des strongs tombés de l'alignement automatique. À supprimer.

   c. **Correction sémantique** : pour chaque strong présent, vérifier que le texte BYM
      correspond au sens du mot grec/hébreu (via `lexicon.json`). **La définition prime** —
      le Strong doit être placé sur le mot ou l'expression qui capture au mieux le sens du
      mot grec. Détecter :
      - Strong sur le mauvais mot (ex: G2980 λαλέω="parler" sur "entre" au lieu de "parlant")
      - Strong sur un fragment au lieu du mot complet (ex: G1130 sur "pauvrement"
        au lieu de "pauvrement vêtus")
      - Strong sur un mot trop restreint : étendre vers l'expression complète qui capture le
        sens du mot composé ou nuancé (voir règle ci-dessous)
      - Strong manquant sur un mot visible (ex: article G3588 sur "le"/"les"/"d'"/"l'"/"ce")

   d. **Présenter un tableau récapitulatif** (aligné sur la source reconstituée) :
      | # | Strong | Source (grec/hébreu) | Sens | Texte BYM | Correct ? |
      Marquer ✅ ou ❌ pour chaque entrée. Une ligne par mot du source reconstitué ; indiquer
      « — (non plaçable) » quand le mot grec n'a pas de rendu visible en BYM.

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
3. `make deploy` (déploiement Vercel production) — **requiert autorisation explicite** de
   l'utilisateur (instance par instance) avant exécution.

### Étape 5 — Rapport final

Présenter :
- Le tableau récapitulatif final (tous les strongs du source reconstitué avec ✅/❌)
- Le statut : X/Y strongs (X placés sur le source reconstitué de Y mots), texte vérifié,
  déployé en prod
- Les éventuelles questions/doutes :
  - strongs ambigus ou source incertaine (le dire franchement)
  - typos potentielles (code Strong inexistant dans le verset)
  - divergences de code entre source reconstituée et convention LSG/BYM (ex: G1531 vs G1525)
  - divergences TR vs NA28 (articles/pronoms présents dans le TR mais absents de NA28) —
    noter les mots ajoutés depuis le TR (ex: « +οἱ, +τῷ, +αὐτῶν ») et les non-plaçables qui en
    résultent (pronom possessif absorbé), pour traçabilité.

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
- **Articles G3588 (issus de la source, pas de la LSG)** : la source reconstituée contient
  chaque article grec (ὁ/ἡ/τό/τῶν/τοῦ/τῇ/τὴν etc.) ; la LSG les omet presque toujours. La skill
  place chaque G3588 sur le mot visible du BYM qui le rend (« le », « la », « les », « d' »,
  « l' », « un », « une », « ce », « ce qui »). Exemples : τῷ λουτρῷ → « **le** bain »
  (G3588 sur « le »), τοῦ ὕδατος → « **d'**eau » (G3588 sur « d' », G5204 sur « eau »),
  Τὸ δὲ εἰσπορευόμενον → « **Ce** qui entre » (G3588 sur « Ce », G1161 δὲ non plaçable).
- **Mots fonctionnels omis par la LSG** : au-delà des articles, la source contient des
  particules (G1161 δὲ, G1063 γάρ, G3767 οὖν, G5037 τέ, G2532 δέ/καί selon contexte),
  pronoms relatifs et conjonctions que la LSG ne numerote pas. Les ajouter depuis la source
  reconstituée lorsqu'un mot visible du BYM les rend ; sinon les laisser non plaçables.
- **Divergences de code Strong (source vs convention LSG/BYM)** : la source reconstituée
  donne parfois un code différent de celui hérité de la LSG (ex: εἰσπορευόμενον = G1531 en
  source, mais LSG/BYM utilisent G1525 εἰσέρχομαι). Par défaut on **laisse la convention
  existante** (ne pas casser l'alignement hérité) sauf demande explicite de l'utilisateur.
  Toujours noter la divergence dans le rapport.
- **Typo potentielle** : si un strong demandé n'existe pas dans le verset (ex: G732 au lieu
  de G737), signaler la discrepancy mais injecter ce que l'utilisateur demande (il a confirmé
  vouloir l'injection). Noter clairement la discrepancy dans le rapport.
- **Honnêteté sur l'incertitude** : si la reconstitution du texte source d'un verset est
  incertaine (verset long, forme verbale rare, lecture textuelle variantes), le dire dans le
  rapport et ne pas inventer de strongs. Mieux vaut un alignement partiel honnête qu'un
  alignement complet inventé.
- **Pronoms possessifs non-plaçables (TR αὐτῶν / αὐτοῦ / αὐτῆς = G846)** : le TR conserve
  souvent un pronom possessif que le français rend par l'article possessif intégré à un
  syntagme corps/partie du corps (idiome français). Ex: « τὰς χεῖρας **αὐτῶν** » (litt. « les
  mains **de eux** ») → BYM « **les** mains » (pas « *leurs* mains ») ; « τὸ πρόσωπον
  **αὐτοῦ** » → BYM « **son** visage » (le « son » n'existe pas comme mot séparé, il est
  porté par l'article « le/la/son » qui rend déjà τὸν/τὴν). Dans ce cas, **G846 est
  non-plaçable** : ne pas le forcer sur un mot visible qui porte déjà un autre Strong
  (typiquement « les »/« le »/« la » qui portent déjà G3588 pour τὰς/τὸν/τὴν). Ne jamais
  déplacer un G3588 d'article pour y loger un G846. Laisser G846 non placé et le signaler
  explicitement comme « non-plaçable (pronom possessif absorbé) » dans le tableau récapitulatif.
- **Ne pas déplacer un Strong pour en loger un autre** : règle générale. Quand un mot visible
  du BYM rend deux mots grecs (ex: « les » rend τὰς + αὐτῶν), le Strong du mot fonctionnel
  principal (l'article τὰς G3588) reste placé sur ce mot ; le second (αὐτῶν G846) est
  non-plaçable. On n'inverse jamais pour privilégier le pronom sur l'article.
- **Possessifs de parenté (ton/ta/tes/votre = adjectif possessif français)** : quand le BYM
  rend un syntagme de parenté par un adjectif possessif (« ton père », « tes disciples »,
  « votre tradition »), regarder si le TR a un pronom possessif explicite (σου G4675,
  ὑμῶν G5216) en plus de l'article :
  - **Pronom présent** (ex: TR « τὸν πατέρα **σου** » → « ton père » ; « οἱ μαθηταί **σου** » →
    « tes disciples » ; « τὴν παράδοσιν **ὑμῶν** » → « votre tradition ») : l'adjectif possessif
    BYM (« ton »/« tes »/« votre ») porte le **pronom** (G4675/G5216) ; l'article grec
    (τὸν/οἱ/τὴν = G3588) est **non-plaçable** (absorbé par l'adjectif possessif français, qui
    remplace l'article). Cohérent avec la règle ci-dessus.
  - **Pronom absent** (ex: TR « **τὴν** μητέρα » sans σου, σου distribué depuis le père ;
    « **τῷ** πατρὶ » sans αὐτοῦ en Mt 15:5) : l'adjectif possessif BYM (« ta »/« son ») rend
    alors l'**article** grec (G3588) via l'idiome de parenté (français : possessif là où le
    grec met l'article). G3588 sur « ta »/« son » est correct.
  - L'asymétrie « ton »→G4675 / « ta »→G3588 dans un même verset (Mt 15:4) est **normale** :
    elle reflète la présence/absence du pronom dans le TR. Ne pas forcer la symétrie.