const express = require("express");
const app = express();
const bodyParser = require("body-parser");
const cors = require("cors");
const helmet = require("helmet");
const morgan = require("morgan");

const environment = "prod";

// Middleware
app.use(helmet());
app.use(bodyParser.json());
app.use(cors());
app.use(morgan("combined"));

app.use((req, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content, Accept, Content-Type, Authorization");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS");
  next();
});

// ═══════════════════════════════════════════════════════════════
//  Chargement des données au démarrage
// ═══════════════════════════════════════════════════════════════

const bym = require("./db/thebym.json");
const bym_info = require("./db/books/bym_info.json");

let lsg = {};
try {
  lsg = require("./db/lsg.json");
  console.log(`LSG: ${Object.keys(lsg).length} versets chargés`);
} catch (e) {
  console.log("LSG: fichier non trouvé");
}

let bym_strongs = {};
let lexicon = {};
try {
  bym_strongs = require("./db/strongs/bym_strongs.json");
  console.log(`Strong's BYM: ${Object.keys(bym_strongs).length} versets chargés`);
} catch (e) {
  console.log("Strong's BYM: bym_strongs.json non trouvé");
}
try {
  lexicon = require("./db/strongs/lexicon.json");
  console.log(`Lexique Strong's: ${Object.keys(lexicon).length} entrées chargées`);
} catch (e) {
  console.log("Lexique Strong's: lexicon.json non trouvé");
}
let strongsOccurrences = {};
try {
  strongsOccurrences = require("./db/strongs/occurrences.json");
} catch (e) {
  console.log("Strong's occurrences: fichier non trouvé");
}
let strongIndex = {};
try {
  strongIndex = require("./db/strongs/strong_index.json");
  console.log(`Strong's index: ${Object.keys(strongIndex).length} codes chargés`);
} catch (e) {
  console.log("Strong's index: fichier non trouvé");
}

let lsg_strongs = {};
try {
  lsg_strongs = require("./db/strongs/lsg_strongs.json");
  console.log(`Strong's LSG: ${Object.keys(lsg_strongs).length} versets chargés`);
} catch (e) {
  console.log("Strong's LSG: fichier non trouvé");
}

let lsgStrongIndex = {};
try {
  lsgStrongIndex = require("./db/strongs/lsg_strong_index.json");
  console.log(`Strong's index LSG: ${Object.keys(lsgStrongIndex).length} codes chargés`);
} catch (e) {
  console.log("Strong's index LSG: fichier non trouvé");
}

// Darby (J.N. Darby, 1885) — texte seul, pas de Strong's natifs.
// Source : midvash/bible-data (public domain), construit par scripts/build_darby.py.
let darby = {};
try {
  darby = require("./db/darby.json");
  console.log(`Darby: ${Object.keys(darby).length} versets chargés`);
} catch (e) {
  console.log("Darby: fichier non trouvé");
}

// Strong's alignés sur Darby (LSG→Darby, pipeline build_strongs.py --target darby).
let darby_strongs = {};
try {
  darby_strongs = require("./db/strongs/darby_strongs.json");
  console.log(`Darby Strong's: ${Object.keys(darby_strongs).length} versets alignés`);
} catch (e) {
  console.log("Darby Strong's: fichier non trouvé");
}

let darbyStrongIndex = {};
try {
  darbyStrongIndex = require("./db/strongs/darby_strong_index.json");
  console.log(`Strong's index Darby: ${Object.keys(darbyStrongIndex).length} codes chargés`);
} catch (e) {
  console.log("Strong's index Darby: fichier non trouvé");
}

// Texte original WLC/MorphHB (AT) + Textus Receptus Scrivener 1894 (NT).
let orig_strongs = {};
let origStrongIndex = {};
try {
  orig_strongs = require("./db/strongs/orig_strongs.json");
  console.log(`Original: ${Object.keys(orig_strongs).length} versets chargés`);
} catch (e) {
  console.log("Original: orig_strongs.json non trouvé");
}
try {
  origStrongIndex = require("./db/strongs/orig_strong_index.json");
} catch (e) {
  console.log("Original: index Strong's non trouvé");
}
const orig = Object.fromEntries(Object.entries(orig_strongs).map(([key, segments]) =>
  [key, segments.map(segment => segment.text || "").join("")]
));

// ═══════════════════════════════════════════════════════════════
//  Registre des versions
// ═══════════════════════════════════════════════════════════════

const VERSIONS = {
  bym: {
    data: bym,
    strongsData: bym_strongs,
    strongIndex: strongIndex,
    name: "Bible de Yéhoshoua Ha Mashiah",
    strongs: true,
  },
  lsg: {
    data: lsg,
    strongsData: lsg_strongs,
    strongIndex: lsgStrongIndex,
    name: "Louis Segond 1910",
    strongs: Object.keys(lsg_strongs).length > 0,
  },
  darby: {
    data: darby,
    strongsData: darby_strongs,
    strongIndex: darbyStrongIndex,
    name: "Bible Darby (J.N. Darby, 1885)",
    strongs: Object.keys(darby_strongs).length > 0,
  },
  orig: {
    data: orig,
    strongsData: orig_strongs,
    strongIndex: origStrongIndex,
    name: "Texte original (Hébreu / Araméen / Grec TR)",
    strongs: Object.keys(orig_strongs).length > 0,
    isOriginal: true,
  },
};

function resolveVersion(req, res, next) {
  const v = VERSIONS[req.params.version];
  if (!v) return res.status(404).json({ error: `Version "${req.params.version}" non supportée` });
  req.source = v.data;
  req.versionName = v.name;
  req.supportsStrongs = v.strongs;
  req.strongsData = v.strongsData;
  req.strongIndex = v.strongIndex || {};
  req.isOriginal = Boolean(v.isOriginal);
  if (req.isOriginal && req.query.mode && !["orig", "interlinear"].includes(req.query.mode)) {
    return res.status(400).json({ error: "Mode invalide; valeurs acceptées: orig, interlinear" });
  }
  next();
}

// ═══════════════════════════════════════════════════════════════
//  Lookups enrichissement (communs à toutes les versions)
// ═══════════════════════════════════════════════════════════════

const SECTIONS_MAP = {};
const PARAGRAPHES_SET = new Set();

for (const info of Object.values(bym_info)) {
  for (const s of (info.sections || [])) {
    SECTIONS_MAP[s.debut] = s.titre;
  }
  for (const key of (info.paragraphes || [])) {
    PARAGRAPHES_SET.add(key);
  }
}

// ═══════════════════════════════════════════════════════════════
//  Tables de correspondance livres
// ═══════════════════════════════════════════════════════════════

function get_book_info_key(abbr) {
  const trimmed = abbr.trim();
  if (trimmed === "Job") return "Job.";
  return trimmed;
}

const LEGACY_BOOK_NAMES = {
  "Ge.": "Genese", "Ex.": "Exode", "Lé.": "Levitique", "No.": "Nombres",
  "De.": "Deuteronome", "Jos.": "Josue", "Jg.": "Juges",
  "1 S.": "1 Samuel", "2 S.": "2 Samuel", "1 R.": "1 Rois", "2 R.": "2 Rois",
  "Es.": "Esaie", "Jé.": "Jeremie", "Ez.": "Ezechiel",
  "Os.": "Osee", "Joë.": "Joel", "Am.": "Amos", "Ab.": "Abdias",
  "Jon.": "Jonas", "Mi.": "Michee", "Na.": "Nahum", "Ha.": "Habakuk",
  "So.": "Sophonie", "Ag.": "Aggee", "Za.": "Zacharie", "Mal.": "Malachie",
  "Ps.": "Psaumes", "Pr.": "Proverbes", "Job": "Job", "Ca.": "Cantique",
  "Ru.": "Ruth", "La.": "Lamentations", "Ec.": "Ecclesiaste",
  "Est.": "Esther", "Da.": "Daniel", "Esd.": "Esdras", "Né.": "Nehemie",
  "1 Ch.": "1 Chroniques", "2 Ch.": "2 Chroniques",
  "Mt.": "Matthieu", "Mc.": "Marc", "Lu.": "Luc", "Jn.": "Jean",
  "Ac.": "Actes", "Ja.": "Jacques", "Ga.": "Galates",
  "1 Th.": "1 Thessaloniciens", "2 Th.": "2 Thessaloniciens",
  "1 Co.": "1 Corinthiens", "2 Co.": "2 Corinthiens", "Ro.": "Romains",
  "Ep.": "Ephesiens", "Ph.": "Philippiens", "Col.": "Colossiens",
  "Phm.": "Philemon", "1 Ti.": "1 Timothee", "Tit.": "Tite",
  "1 Pi.": "1 Pierre", "2 Pi.": "2 Pierre", "2 Ti.": "2 Timothee",
  "Jud.": "Judas", "Hé.": "Hebreux",
  "1 Jn.": "1 Jean", "2 Jn.": "2 Jean", "3 Jn.": "3 Jean", "Ap.": "Apocalypse",
};

const ABBR_LIST = [
  "Ge. ", "Ex. ", "Lé. ", "No. ", "De. ", "Jos. ", "Jg. ",
  "1 S. ", "2 S. ", "1 R. ", "2 R. ", "Es. ", "Jé. ", "Ez. ",
  "Os. ", "Joë. ", "Am. ", "Ab. ", "Jon. ", "Mi. ", "Na. ", "Ha. ",
  "So. ", "Ag. ", "Za. ", "Mal. ", "Ps. ", "Pr. ", "Job ", "Ca. ",
  "Ru. ", "La. ", "Ec. ", "Est. ", "Da. ", "Esd. ", "Né. ",
  "1 Ch. ", "2 Ch. ", "Mt. ", "Mc. ", "Lu. ", "Jn. ", "Ac. ",
  "Ja. ", "Ga. ", "1 Th. ", "2 Th. ", "1 Co. ", "2 Co. ", "Ro. ",
  "Ep. ", "Ph. ", "Col. ", "Phm. ", "1 Ti. ", "Tit. ", "1 Pi. ",
  "2 Pi. ", "2 Ti. ", "Jud. ", "Hé. ", "1 Jn. ", "2 Jn. ", "3 Jn. ", "Ap. "
];

const LEGACY_BOOK_ALIASES = {
  "ge": "Ge. ", "gen": "Ge. ", "genese": "Ge. ", "genesis": "Ge. ",
  "ex": "Ex. ", "exo": "Ex. ", "exode": "Ex. ", "exodus": "Ex. ",
  "le": "Lé. ", "lev": "Lé. ", "levitique": "Lé. ",
  "no": "No. ", "nom": "No. ", "nombres": "No. ", "num": "No. ",
  "de": "De. ", "deu": "De. ", "deut": "De. ", "deuteronome": "De. ",
  "jos": "Jos. ", "josue": "Jos. ", "joshua": "Jos. ",
  "jg": "Jg. ", "jug": "Jg. ", "juges": "Jg. ",
  "1s": "1 S. ", "1sa": "1 S. ", "1sam": "1 S. ", "1samuel": "1 S. ",
  "2s": "2 S. ", "2sa": "2 S. ", "2sam": "2 S. ", "2samuel": "2 S. ",
  "1r": "1 R. ", "1roi": "1 R. ", "1rois": "1 R. ", "1kings": "1 R. ",
  "2r": "2 R. ", "2roi": "2 R. ", "2rois": "2 R. ", "2kings": "2 R. ",
  "es": "Es. ", "esa": "Es. ", "esaie": "Es. ", "isaie": "Es. ", "isaiah": "Es. ",
  "je": "Jé. ", "jer": "Jé. ", "jeremie": "Jé. ", "jeremiah": "Jé. ",
  "ez": "Ez. ", "eze": "Ez. ", "ezechiel": "Ez. ", "ezekiel": "Ez. ",
  "os": "Os. ", "ose": "Os. ", "osee": "Os. ", "hosea": "Os. ",
  "joe": "Joë. ", "joel": "Joë. ",
  "am": "Am. ", "amos": "Am. ",
  "ab": "Ab. ", "abd": "Ab. ", "abdias": "Ab. ", "obadiah": "Ab. ",
  "jon": "Jon. ", "jonas": "Jon. ", "jonah": "Jon. ",
  "mi": "Mi. ", "mic": "Mi. ", "michee": "Mi. ", "micah": "Mi. ",
  "na": "Na. ", "nah": "Na. ", "nahum": "Na. ",
  "ha": "Ha. ", "hab": "Ha. ", "habacuc": "Ha. ", "habakkuk": "Ha. ",
  "so": "So. ", "sop": "So. ", "sophonie": "So. ", "zephaniah": "So. ",
  "ag": "Ag. ", "agg": "Ag. ", "aggee": "Ag. ", "haggai": "Ag. ",
  "za": "Za. ", "zac": "Za. ", "zacharie": "Za. ", "zechariah": "Za. ",
  "mal": "Mal. ", "malachie": "Mal. ", "malachi": "Mal. ",
  "ps": "Ps. ", "psa": "Ps. ", "psaume": "Ps. ", "psaumes": "Ps. ", "psalm": "Ps. ",
  "pr": "Pr. ", "pro": "Pr. ", "prov": "Pr. ", "proverbes": "Pr. ", "proverbs": "Pr. ",
  "job": "Job ", "jb": "Job ",
  "ca": "Ca. ", "can": "Ca. ", "cantique": "Ca. ", "song": "Ca. ",
  "ru": "Ru. ", "rut": "Ru. ", "ruth": "Ru. ",
  "la": "La. ", "lam": "La. ", "lamentations": "La. ",
  "ec": "Ec. ", "ecc": "Ec. ", "ecclesiaste": "Ec. ", "ecclesiastes": "Ec. ",
  "est": "Est. ", "esther": "Est. ",
  "da": "Da. ", "dan": "Da. ", "daniel": "Da. ",
  "esd": "Esd. ", "esdras": "Esd. ", "ezra": "Esd. ",
  "ne": "Né. ", "neh": "Né. ", "nehemie": "Né. ", "nehemiah": "Né. ",
  "1ch": "1 Ch. ", "1chr": "1 Ch. ", "1chroniques": "1 Ch. ", "1chronicles": "1 Ch. ",
  "2ch": "2 Ch. ", "2chr": "2 Ch. ", "2chroniques": "2 Ch. ", "2chronicles": "2 Ch. ",
  "mt": "Mt. ", "mat": "Mt. ", "matt": "Mt. ", "matthieu": "Mt. ", "matthew": "Mt. ",
  "mc": "Mc. ", "mar": "Mc. ", "marc": "Mc. ", "mark": "Mc. ",
  "lu": "Lu. ", "luc": "Lu. ", "luke": "Lu. ",
  "jn": "Jn. ", "jea": "Jn. ", "jean": "Jn. ", "john": "Jn. ",
  "ac": "Ac. ", "act": "Ac. ", "actes": "Ac. ", "acts": "Ac. ",
  "ja": "Ja. ", "jac": "Ja. ", "jacques": "Ja. ", "james": "Ja. ",
  "ga": "Ga. ", "gal": "Ga. ", "galates": "Ga. ", "galatians": "Ga. ",
  "1th": "1 Th. ", "1thessaloniciens": "1 Th. ", "1thessalonians": "1 Th. ",
  "2th": "2 Th. ", "2thessaloniciens": "2 Th. ", "2thessalonians": "2 Th. ",
  "1co": "1 Co. ", "1cor": "1 Co. ", "1corinthiens": "1 Co. ", "1corinthians": "1 Co. ",
  "2co": "2 Co. ", "2cor": "2 Co. ", "2corinthiens": "2 Co. ", "2corinthians": "2 Co. ",
  "ro": "Ro. ", "rom": "Ro. ", "romains": "Ro. ", "romans": "Ro. ",
  "ep": "Ep. ", "eph": "Ep. ", "ephesiens": "Ep. ", "ephesians": "Ep. ",
  "ph": "Ph. ", "phi": "Ph. ", "phili": "Ph. ", "philippiens": "Ph. ", "philippians": "Ph. ",
  "col": "Col. ", "colos": "Col. ", "colossiens": "Col. ", "colossians": "Col. ",
  "phm": "Phm. ", "phile": "Phm. ", "philemon": "Phm. ",
  "1ti": "1 Ti. ", "1tim": "1 Ti. ", "1timothee": "1 Ti. ", "1timothy": "1 Ti. ",
  "tit": "Tit. ", "tite": "Tit. ", "titus": "Tit. ",
  "1pi": "1 Pi. ", "1pierre": "1 Pi. ", "1peter": "1 Pi. ",
  "2pi": "2 Pi. ", "2pierre": "2 Pi. ", "2peter": "2 Pi. ",
  "2ti": "2 Ti. ", "2tim": "2 Ti. ", "2timothee": "2 Ti. ", "2timothy": "2 Ti. ",
  "jud": "Jud. ", "jude": "Jud. ",
  "he": "Hé. ", "heb": "Hé. ", "hebreux": "Hé. ", "hebrews": "Hé. ",
  "1jn": "1 Jn. ", "1je": "1 Jn. ", "1jean": "1 Jn. ", "1john": "1 Jn. ",
  "2jn": "2 Jn. ", "2je": "2 Jn. ", "2jean": "2 Jn. ", "2john": "2 Jn. ",
  "3jn": "3 Jn. ", "3je": "3 Jn. ", "3jean": "3 Jn. ", "3john": "3 Jn. ",
  "ap": "Ap. ", "apo": "Ap. ", "apocalypse": "Ap. ", "revelation": "Ap. ",
};

// Source partagée avec les scripts Python. Les tables historiques restent en
// repli afin de préserver strictement tous les anciens alias publics.
const BOOK_META = require("./db/books_meta.json");
const BOOK_NAMES = {
  ...LEGACY_BOOK_NAMES,
  ...Object.fromEntries(BOOK_META.map(book => [book.abbr, book.name])),
};
const BOOK_ALIASES = {
  ...LEGACY_BOOK_ALIASES,
  ...Object.fromEntries(BOOK_META.flatMap(book => book.aliases.map(alias => [alias, `${book.abbr} `]))),
};

// ═══════════════════════════════════════════════════════════════
//  Fonctions utilitaires (version-aware)
// ═══════════════════════════════════════════════════════════════

function normalizeParam(param) {
  return param
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\./g, "")
    .replace(/\s+/g, "");
}

function get_book_abbr(param) {
  return BOOK_ALIASES[normalizeParam(param)] || null;
}

function make_verse(abbr, chapitre, verset, ecrit, versionName) {
  return {
    livre: abbr,
    chapitre: parseInt(chapitre),
    verset: parseInt(verset),
    ecrit,
    version: versionName || "Bible de Yéhoshoua Ha Mashiah"
  };
}

function get_book(nom_du_livre, source, versionName) {
  const abbr = get_book_abbr(nom_du_livre);
  if (!abbr) return null;
  const src = source || bym;
  const vName = versionName || "Bible de Yéhoshoua Ha Mashiah";

  return Object.entries(src)
    .filter(([key]) => key.startsWith(abbr))
    .reduce((acc, [key, ecrit]) => {
      const [chap, verset] = key.slice(abbr.length).split(":");
      acc[key] = make_verse(abbr, chap, verset, ecrit, vName);
      return acc;
    }, {});
}

function get_all_chapter(nom_du_livre, chapitre, source, versionName) {
  const abbr = get_book_abbr(nom_du_livre);
  if (!abbr) return null;
  const src = source || bym;
  const vName = versionName || "Bible de Yéhoshoua Ha Mashiah";

  const prefix = abbr + chapitre + ":";
  return Object.entries(src)
    .filter(([key]) => key.startsWith(prefix))
    .reduce((acc, [key, ecrit]) => {
      const verset = key.split(":")[1];
      acc[key] = make_verse(abbr, chapitre, verset, ecrit, vName);
      return acc;
    }, {});
}

function make_selection(versets) {
  const selection = [];
  for (const partie of versets.split(",")) {
    if (partie.includes("-")) {
      const [debut, fin] = partie.split("-").map(Number);
      for (let v = debut; v <= fin; v++) selection.push(v);
    } else {
      selection.push(parseInt(partie));
    }
  }
  return selection.sort((a, b) => a - b);
}

function get_all_of_selection(nom_livre, chapitre, notre_selection, source, versionName) {
  const abbr = get_book_abbr(nom_livre);
  if (!abbr) return null;
  const src = source || bym;
  const vName = versionName || "Bible de Yéhoshoua Ha Mashiah";

  const selection = make_selection(notre_selection);
  return selection.reduce((acc, num_verset) => {
    const key = abbr + chapitre + ":" + num_verset;
    if (src[key]) {
      acc[key] = make_verse(abbr, chapitre, num_verset, src[key], vName);
    }
    return acc;
  }, {});
}

function enrich_result(result) {
  const keys = Object.keys(result);
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i];
    const verse = result[key];
    if (SECTIONS_MAP[key] !== undefined) verse.titre = SECTIONS_MAP[key];
    const isStart = PARAGRAPHES_SET.has(key);
    const nextKey = keys[i + 1];
    const isEnd = nextKey !== undefined && PARAGRAPHES_SET.has(nextKey);
    if (isStart) verse.paragraphe = "start";
    else if (isEnd) verse.paragraphe = "end";
  }
  return result;
}

function resolve_strongs(verseKey, strongsData, options = {}) {
  const data = strongsData || bym_strongs;
  const segments = data[verseKey];
  if (!segments) return null;
  return segments.map(seg => {
    const entry = seg.strong ? lexicon[seg.strong] : null;
    const result = { text: seg.text, strong: seg.strong };
    if (seg.gloss && options.interlinear !== false) result.gloss = seg.gloss;
    if (seg.morph) result.morph = seg.morph;
    if (seg.morph_fr) result.morph_fr = seg.morph_fr;
    if (seg.lang) result.lang = seg.lang;
    if (entry) {
      result.lemma = entry.lemma;
      if (options.translit !== false) {
        result.translit = entry.translit;
        result.phonetique = entry.phonetique;
      }
      result.origine = entry.origine;
      result.type = entry.type;
      result.definition = entry.definition;
      if (!result.lang) result.lang = entry.lang;
    }
    return result;
  });
}

function maybe_attach_strongs(result, req) {
  if (!result || typeof result !== "object") return result;
  if (!req || (req.query.strongs !== "1" && !req.isOriginal)) return result;
  const strongsData = req.strongsData || bym_strongs;
  if (!strongsData || Object.keys(strongsData).length === 0) return result;
  for (const key of Object.keys(result)) {
    const segs = resolve_strongs(key, strongsData, {
      interlinear: !req.isOriginal || req.query.mode === "interlinear",
      translit: !req.isOriginal || req.query.translit === "1",
    });
    if (segs) result[key].strongs = segs;
  }
  return result;
}

function return_result(res, result, req) {
  if (result === null) {
    return res.status(404).json({ error: "Livre introuvable" });
  }
  if (Object.keys(result).length === 0) {
    return res.status(404).json({ error: "Aucun résultat trouvé" });
  }
  const enriched = enrich_result(result);
  if (req && (req.query.strongs === "1" || req.isOriginal)) {
    maybe_attach_strongs(enriched, req);
  }
  res.status(200).json(enriched);
}

// ═══════════════════════════════════════════════════════════════
//  Redirections vers le Reader
// ═══════════════════════════════════════════════════════════════

const READER_BASE_URL = (process.env.READER_BASE_URL || "http://localhost:3000").replace(/\/$/, "");

const ABBR_TO_SLUG = {
  "Ge. ": "genese", "Ex. ": "exode", "Lé. ": "levitique", "No. ": "nombres", "De. ": "deuteronome",
  "Jos. ": "josue", "Jg. ": "juges", "1 S. ": "1samuel", "2 S. ": "2samuel", "1 R. ": "1rois",
  "2 R. ": "2rois", "Es. ": "esaie", "Jé. ": "jeremie", "Ez. ": "ezechiel", "Os. ": "osee",
  "Joë. ": "joel", "Am. ": "amos", "Ab. ": "abdias", "Jon. ": "jonas", "Mi. ": "michee",
  "Na. ": "nahum", "Ha. ": "habacuc", "So. ": "sophonie", "Ag. ": "aggee", "Za. ": "zacharie",
  "Mal. ": "malachie", "Ps. ": "psaumes", "Pr. ": "proverbes", "Job ": "job", "Ca. ": "cantique",
  "Ru. ": "ruth", "La. ": "lamentations", "Ec. ": "ecclesiaste", "Est. ": "esther", "Da. ": "daniel",
  "Esd. ": "esdras", "Né. ": "nehemie", "1 Ch. ": "1chroniques", "2 Ch. ": "2chroniques",
  "Mt. ": "matthieu", "Mc. ": "marc", "Lu. ": "luc", "Jn. ": "jean", "Ac. ": "actes",
  "Ja. ": "jacques", "Ga. ": "galates", "1 Th. ": "1thessaloniciens", "2 Th. ": "2thessaloniciens",
  "1 Co. ": "1corinthiens", "2 Co. ": "2corinthiens", "Ro. ": "romains", "Ep. ": "ephesiens",
  "Ph. ": "philippiens", "Col. ": "colossiens", "Phm. ": "philemon", "1 Ti. ": "1timothee",
  "Tit. ": "tite", "1 Pi. ": "1pierre", "2 Pi. ": "2pierre", "2 Ti. ": "2timothee", "Jud. ": "jude",
  "Hé. ": "hebreux", "1 Jn. ": "1jean", "2 Jn. ": "2jean", "3 Jn. ": "3jean", "Ap. ": "apocalypse"
};

function readerSlug(param) {
  const abbr = get_book_abbr(param);
  return abbr ? (ABBR_TO_SLUG[abbr] || null) : null;
}

// ═══════════════════════════════════════════════════════════════
//  Routes
// ═══════════════════════════════════════════════════════════════

// 1. Routes spécifiques (doivent être avant les routes génériques /:version)

// Handler partagé pour l'index inversé Strong's (code → versets), version-aware.
function strongIndexHandler(req, res, index, source) {
  const code = req.params.num.toUpperCase();
  const keys = index[code] || [];
  const total = keys.length;

  const page = parseInt(req.query.page) || 1;
  const size = Math.min(parseInt(req.query.size) || 20, 100);
  const start = (page - 1) * size;
  const pagedKeys = keys.slice(start, start + size);

  const items = pagedKeys.map(key => {
    const m = key.match(/^(.+?)\s+(\d+):(\d+)$/);
    if (!m) return null;
    const abbr = m[1].trim();
    const chapitre = parseInt(m[2]);
    const verset = parseInt(m[3]);
    const livre = BOOK_NAMES[abbr] || abbr;
    const ecrit = source[key] || "";
    return { livre, chapitre, verset, ecrit };
  }).filter(Boolean);

  const lex = lexicon[code] || {};

  res.status(200).json({
    code,
    total,
    page,
    size,
    // Lexique complet du code : la page détail d'un code Strong tire toutes ses métadonnées
    // (lemme, langue, phonétique, origine, type, translittération, définition) de ce seul fetch,
    // cohérent avec le modèle « une page par code » (pas de second appel à /strong/:code).
    lexicon: {
      lemma: lex.lemma || null,
      lang: lex.lang || null,
      translit: lex.translit || null,
      phonetique: lex.phonetique || null,
      origine: lex.origine || null,
      type: lex.type || null,
      definition: lex.definition || null
    },
    items
  });
}

// /bym/strong/:num — rétro-compat (consommé en prod). Équivaut à /:version/strong/:num.
app.get("/bym/strong/:num", (req, res) =>
  strongIndexHandler(req, res, strongIndex, bym));

// /:version/strong/:num — index inversé Strong's, agnostique de la version (bym, lsg, …)
app.get("/:version/strong/:num", resolveVersion, (req, res) =>
  strongIndexHandler(req, res, req.strongIndex, req.source));

// /strong/:code — entrée du lexique Strong's
app.get("/strong/:code", (req, res) => {
  const code = req.params.code.toUpperCase();
  const entry = lexicon[code];
  if (!entry) {
    return res.status(404).json({ error: "Code Strong introuvable", code });
  }
  res.status(200).json({
    code,
    occurrences: strongsOccurrences[code] || 0,
    ...entry
  });
});

// 2. Routes génériques /:version/... (capturent /bym, /lsg, etc.)

// /:version — verset aléatoire
app.get("/:version", resolveVersion, (req, res) => {
  function randomVerset() {
    const abbr = ABBR_LIST[Math.floor(Math.random() * ABBR_LIST.length)];
    const chap = 1 + Math.floor(Math.random() * 100);
    const v = 1 + Math.floor(Math.random() * 250);
    return abbr + chap + ":" + v;
  }

  let key = randomVerset();
  while (!req.source[key]) {
    key = randomVerset();
  }

  const response = {
    verset: key,
    ecrit: req.source[key],
    version: req.versionName,
    APIinfo: "https://www.shemaproject.org/bibleapi"
  };
  if ((req.query.strongs === "1" || req.isOriginal) && req.supportsStrongs) {
    const segs = resolve_strongs(key, req.strongsData, {
      interlinear: !req.isOriginal || req.query.mode === "interlinear",
      translit: !req.isOriginal || req.query.translit === "1",
    });
    if (segs) response.strongs = segs;
  }
  res.status(200).json(response);
});

// /:version/:livre/read — redirection lecteur
app.get("/:version/:livre/read", resolveVersion, (req, res) => {
  const slug = readerSlug(req.params.livre);
  if (!slug) return res.status(404).json({ error: "Livre introuvable" });
  res.redirect(302, `${READER_BASE_URL}/bym/read?livre=${slug}&chap=1`);
});

// /:version/:livre/info — infos du livre (communes)
app.get("/:version/:livre/info", resolveVersion, (req, res) => {
  const abbr = get_book_abbr(req.params.livre);
  if (!abbr) return res.status(404).json({ error: "Livre introuvable" });
  const info = bym_info[get_book_info_key(abbr)];
  if (!info) return res.status(404).json({ error: "Informations non disponibles pour ce livre" });
  res.status(200).json(info);
});

// /:version/:livre/:chap/read — redirection lecteur
app.get("/:version/:livre/:chap/read", resolveVersion, (req, res) => {
  const slug = readerSlug(req.params.livre);
  if (!slug) return res.status(404).json({ error: "Livre introuvable" });
  res.redirect(302, `${READER_BASE_URL}/bym/read?livre=${slug}&chap=${req.params.chap}`);
});

// /:version/:livre/:chap/:selections/read — redirection lecteur
app.get("/:version/:livre/:chap/:selections/read", resolveVersion, (req, res) => {
  const slug = readerSlug(req.params.livre);
  if (!slug) return res.status(404).json({ error: "Livre introuvable" });
  const v = encodeURIComponent(req.params.selections);
  res.redirect(302, `${READER_BASE_URL}/bym/read?livre=${slug}&chap=${req.params.chap}&v=${v}`);
});

// /:version/:livre/:chap/:selections/next — verset suivant
app.get("/:version/:livre/:chap/:selections/next", resolveVersion, (req, res) => {
  const abbr = get_book_abbr(req.params.livre);
  if (!abbr) return res.status(404).json({ error: "Livre introuvable" });

  const chapitre = parseInt(req.params.chap);
  const selection = make_selection(req.params.selections);
  const last_verse = Math.max(...selection);

  const next_key = abbr + chapitre + ":" + (last_verse + 1);
  if (req.source[next_key]) {
    const result = enrich_result({
      [next_key]: make_verse(abbr, chapitre, last_verse + 1, req.source[next_key], req.versionName)
    });
    return res.status(200).json(maybe_attach_strongs(result, req));
  }

  const next_chap_key = abbr + (chapitre + 1) + ":1";
  if (req.source[next_chap_key]) {
    const result = enrich_result({
      [next_chap_key]: make_verse(abbr, chapitre + 1, 1, req.source[next_chap_key], req.versionName)
    });
    return res.status(200).json(maybe_attach_strongs(result, req));
  }

  res.status(404).json({ error: "Aucun verset suivant trouvé" });
});

// /:version/:livre/:chap/:selections/prev — verset précédent
app.get("/:version/:livre/:chap/:selections/prev", resolveVersion, (req, res) => {
  const abbr = get_book_abbr(req.params.livre);
  if (!abbr) return res.status(404).json({ error: "Livre introuvable" });

  const chapitre = parseInt(req.params.chap);
  const selection = make_selection(req.params.selections);
  const first_verse = Math.min(...selection);

  if (first_verse > 1) {
    const prev_key = abbr + chapitre + ":" + (first_verse - 1);
    if (req.source[prev_key]) {
      const result = enrich_result({
        [prev_key]: make_verse(abbr, chapitre, first_verse - 1, req.source[prev_key], req.versionName)
      });
      return res.status(200).json(maybe_attach_strongs(result, req));
    }
  }

  if (chapitre > 1) {
    const prev_chap = chapitre - 1;
    const all_prev = Object.keys(req.source).filter(k => k.startsWith(abbr + prev_chap + ":"));
    if (all_prev.length > 0) {
      const last_key = all_prev[all_prev.length - 1];
      const last_v = parseInt(last_key.split(":")[1]);
      const result = enrich_result({
        [last_key]: make_verse(abbr, prev_chap, last_v, req.source[last_key], req.versionName)
      });
      return res.status(200).json(maybe_attach_strongs(result, req));
    }
  }

  res.status(404).json({ error: "Aucun verset précédent trouvé" });
});

// /:version/:livre — tout un livre
app.get("/:version/:livre", resolveVersion, (req, res) => {
  const result = get_book(req.params.livre, req.source, req.versionName);
  return_result(res, result, req);
});

// /:version/:livre/:chap — un chapitre
app.get("/:version/:livre/:chap", resolveVersion, (req, res) => {
  const result = get_all_chapter(req.params.livre, req.params.chap, req.source, req.versionName);
  return_result(res, result, req);
});

// /:version/:livre/:chap/:selections — sélection de versets
app.get("/:version/:livre/:chap/:selections", resolveVersion, (req, res) => {
  const result = get_all_of_selection(req.params.livre, req.params.chap, req.params.selections, req.source, req.versionName);
  return_result(res, result, req);
});

// 3. Route racine + démarrage
app.get("/", (req, res) => {
  res.sendFile(__dirname + "/public/index.html");
});

app.use(express.static("public"));

if (require.main === module) {
  app.listen(process.env.PORT || 8080, () => {
    console.log("Que Yehowshuw`a Ha-Mashiyah soit glorifié. Amen 🙏🏾");
  });
}

module.exports = app;
module.exports._internals = {
  VERSIONS,
  get_all_of_selection,
  maybe_attach_strongs,
  resolve_strongs,
};
