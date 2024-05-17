const express = require("express");
const app = express();
// const TOKEN = process.env.TELEGRAM_TOKEN || "YOUR_TELEGRAM_BOT_TOKEN";
const abbr_list = ["Ge. ", "Ex. ", "Lé. ", "No. ", "De. ", "Jos. ", "Jg. ", "1 S. ", "2 S. ", "1 R. ", "2 R. ", "Es. ", "Jé. ", "Ez. ", "Os. ", "Joë. ", "Am. ", "Ab. ", "Jon. ", "Mi. ", "Na. ", "Ha. ", "So. ", "Ag. ", "Za. ", "Mal. ", "Ps. ", "Pr. ", "Job ", "Ca. ", "Ru. ", "La. ", "Ec. ", "Est. ", "Da. ", "Esd. ", "Né. ", "1 Ch. ", "2 Ch. ", "Mt. ", "Mc. ", "Lu. ", "Jn. ", "Ac. ", "Ja. ", "Ga. ", "1 Th. ", "2 Th. ", "1 Co. ", "2 Co. ", "Ro. ", "Ep. ", "Ph. ", "Col. ", "Phm. ", "1 Ti. ", "Tit. ", "1 Pi. ", "2 Pi. ", "2 Ti. ", "Jud. ", "Hé. ", "1 Jn. ", "2 Jn. ", "3 Jn. ", "Ap. "]

const complet_list = [
  {
    "Ge. ": "Bereshit (Génèse)",
    "Ex. ": "Shemot (Exode)",
    "Lé. ": "Viyaqra (Lévitique)",
    "No. ": "Badmidbar (Nombres)",
    "De. ": "Davarim (Deutéronomes)",
    "Jos. ": "Yéhoshoua (Josué)",
    "Jg. ": "Shoftim (Juges)",
    "1 S. ": "1 Shemouél (1 Samuel)",
    "2 S. ": "2 Shemouél (2 Samuel)",
    "1 R. ": "1 Melakhim (1 Rois)",
    "2 R. ": "2 Melakhim (2 Rois)",
    "Es. ": "Yesha`yah (Ésaïe)",
    "Jé. ": "Yirmeyah (Jérémie)",
    "Ez. ": "Yehezkel (Ézéchiel)",
    "Os. ": "Hoshea (Osée)",
    "Joë. ": "Yoel (Joël)",
    "Am. ": "Amowc (Amos)",
    "Ab. ": "Obadyah (Abdias)",
    "Jon. ": "Yonah (Jonas)",
    "Mi. ": "Miykayah (Michée)",
    "Na. ": "Nachuwm (Nahum)",
    "Ha. ": "Habaqqouq (Habakuk)",
    "So. ": "Tsephanyah (Sophonie)",
    "Ag. ": "Chaggay (Aggée)",
    "Za. ": "Zakaryah (Zacharie)",
    "Mal. ": "Mal`akiy (Malachie)",
    "Ps. ": "Tehilim (Psaumes)",
    "Pr. ": "Mishlei (Proverbes)",
    "Job ": "Iyov (Job)",
    "Ca. ": "ShirHashirim (Cantiques des Cantiques)",
    "Ru. ": "Routh (Ruth)",
    "La. ": "Eikha (Lamentations de Jérémie)",
    "Ec. ": "Qohelet (Écclésiaste)",
    "Est. ": "Meguila Esther (Esther)",
    "Da. ": "Daniye'l (Daniel)",
    "Esd. ": "Ezra (Esdras)",
    "Né. ": "Nehemyah (Nehémie)",
    "1 Ch. ": "1 Hayyamim Dibre (1 Chroniques)",
    "2 Ch. ": "2 Hayyamim Dibre (2 Chroniques)",
    "Mt. ": "Matthaios (Matthieu)",
    "Mc. ": "Markos (Marc)",
    "Lu. ": "Loukas (Luc)",
    "Jn. ": "Yohanan (Jean)",
    "Ac. ": "Actes",
    "Ja. ": "Yaacov (Jacques)",
    "Ga. ": "Galates",
    "1 Th. ": "1 Thessaloniciens",
    "2 Th. ": "2 Thessaloniciens",
    "1 Co. ": "1 Corinthiens",
    "2 Co. ": "2 Corinthiens",
    "Ro. ": "Romains",
    "Ep. ": "Éphésiens",
    "Ph. ": "Philippiens",
    "Col. ": "Colossiens",
    "Phm. ": "Philémon",
    "1 Ti. ": "1 Timotheos (1 Timothée)",
    "Tit. ": "Titos (Tites)",
    "1 Pi. ": "1 Petros (1 Pierre)",
    "2 Pi. ": "2 Petros (2 Pierre)",
    "2 Ti. ": "2 Timotheos (2 Timothée)",
    "Jud. ": "Yéhouda (Jude)",
    "Hé. ": "Hébreux",
    "1 Jn. ": "1 Yohanan (1 Jean)",
    "2 Jn. ": "2 Yohanan (2 Jean)",
    "3 Jn. ": "3 Yohanan (3 Jean)",
    "Ap. ": "Apokalupsis (Apocalypse)",
  },
];
const bible_details = [
  {
    "Ge. ": {
      nom_complet: "Bereshit (Génèse)",
      nbre_chapitres: 50,
      max_verset: 100,
    },
    "Ex. ": {
      nom_complet: "Shemot (Exode)",
      nbre_chapitres: 40,
      max_verset: 100,
    },
    "Lé. ": {
      nom_complet: "Viyaqra (Lévitique)",
      nbre_chapitres: 27,
      max_verset: 100,
    },
    "No. ": {
      nom_complet: "Badmidbar (Nombres)",
      nbre_chapitres: 36,
      max_verset: 100,
    },
    "De. ": {
      nom_complet: "Davarim (Deutéronomes)",
      nbre_chapitres: 34,
      max_verset: 100,
    },
    "Jos. ": {
      nom_complet: "Yéhoshoua (Josué)",
      nbre_chapitres: 24,
      max_verset: 100,
    },
    "Jg. ": {
      nom_complet: "Shoftim (Juges)",
      nbre_chapitres: 21,
      max_verset: 100,
    },
    "1 S. ": {
      nom_complet: "1 Shemouél (1 Samuel)",
      nbre_chapitres: 31,
      max_verset: 100,
    },
    "2 S. ": {
      nom_complet: "2 Shemouél (2 Samuel)",
      nbre_chapitres: 24,
      max_verset: 100,
    },
    "1 R. ": {
      nom_complet: "1 Melakhim (1 Rois)",
      nbre_chapitres: 22,
      max_verset: 100,
    },
    "2 R. ": {
      nom_complet: "2 Melakhim (2 Rois)",
      nbre_chapitres: 25,
      max_verset: 100,
    },
    "Es. ": {
      nom_complet: "Yesha`yah (Ésaïe)",
      nbre_chapitres: 66,
      max_verset: 100,
    },
    "Jé. ": {
      nom_complet: "Yirmeyah (Jérémie)",
      nbre_chapitres: 52,
      max_verset: 100,
    },
    "Ez. ": {
      nom_complet: "Yehezkel (Ézéchiel)",
      nbre_chapitres: 48,
      max_verset: 100,
    },
    "Os. ": {
      nom_complet: "Hoshea (Osée)",
      nbre_chapitres: 14,
      max_verset: 100,
    },
    "Joë. ": { nom_complet: "Yoel (Joël)", nbre_chapitres: 4, max_verset: 100 },
    "Am. ": { nom_complet: "Amowc (Amos)", nbre_chapitres: 9, max_verset: 100 },
    "Ab. ": {
      nom_complet: "Obadyah (Abdias)",
      nbre_chapitres: 1,
      max_verset: 100,
    },
    "Jon. ": {
      nom_complet: "Yonah (Jonas)",
      nbre_chapitres: 4,
      max_verset: 100,
    },
    "Mi. ": {
      nom_complet: "Miykayah (Michée)",
      nbre_chapitres: 7,
      max_verset: 100,
    },
    "Na. ": {
      nom_complet: "Nachuwm (Nahum)",
      nbre_chapitres: 3,
      max_verset: 100,
    },
    "Ha. ": {
      nom_complet: "Habaqqouq (Habakuk)",
      nbre_chapitres: 3,
      max_verset: 100,
    },
    "So. ": {
      nom_complet: "Tsephanyah (Sophonie)",
      nbre_chapitres: 3,
      max_verset: 100,
    },
    "Ag. ": {
      nom_complet: "Chaggay (Aggée)",
      nbre_chapitres: 2,
      max_verset: 100,
    },
    "Za. ": {
      nom_complet: "Zakaryah (Zacharie)",
      nbre_chapitres: 14,
      max_verset: 100,
    },
    "Mal. ": {
      nom_complet: "Mal`akiy (Malachie)",
      nbre_chapitres: 3,
      max_verset: 100,
    },
    "Ps. ": {
      nom_complet: "Tehilim (Psaumes)",
      nbre_chapitres: 150,
      max_verset: 100,
    },
    "Pr. ": {
      nom_complet: "Mishlei (Proverbes)",
      nbre_chapitres: 31,
      max_verset: 100,
    },
    "Job ": { nom_complet: "Iyov (Job)", nbre_chapitres: 42, max_verset: 100 },
    "Ca. ": {
      nom_complet: "ShirHashirim (Cantiques des Cantiques)",
      nbre_chapitres: 8,
      max_verset: 100,
    },
    "Ru. ": { nom_complet: "Routh (Ruth)", nbre_chapitres: 4, max_verset: 100 },
    "La. ": {
      nom_complet: "Eikha (Lamentations de Jérémie)",
      nbre_chapitres: 5,
      max_verset: 100,
    },
    "Ec. ": {
      nom_complet: "Qohelet (Écclésiaste)",
      nbre_chapitres: 12,
      max_verset: 100,
    },
    "Est. ": {
      nom_complet: "Meguila Esther (Esther)",
      nbre_chapitres: 10,
      max_verset: 100,
    },
    "Da. ": {
      nom_complet: "Daniye'l (Daniel)",
      nbre_chapitres: 12,
      max_verset: 100,
    },
    "Esd. ": {
      nom_complet: "Ezra (Esdras)",
      nbre_chapitres: 10,
      max_verset: 100,
    },
    "Né. ": {
      nom_complet: "Nehemyah (Nehémie)",
      nbre_chapitres: 13,
      max_verset: 100,
    },
    "1 Ch. ": {
      nom_complet: "1 Hayyamim Dibre (1 Chroniques)",
      nbre_chapitres: 29,
      max_verset: 100,
    },
    "2 Ch. ": {
      nom_complet: "2 Hayyamim Dibre (2 Chroniques)",
      nbre_chapitres: 36,
      max_verset: 100,
    },
    "Mt. ": {
      nom_complet: "Matthaios (Matthieu)",
      nbre_chapitres: 28,
      max_verset: 100,
    },
    "Mc. ": {
      nom_complet: "Markos (Marc)",
      nbre_chapitres: 16,
      max_verset: 100,
    },
    "Lu. ": { nom_complet: "Loukas (Luc)", nbre_chapitres: 24, max_verset: 100 },
    "Jn. ": {
      nom_complet: "Yohanan (Jean)",
      nbre_chapitres: 21,
      max_verset: 100,
    },
    "Ac. ": { nom_complet: "Actes", nbre_chapitres: 28, max_verset: 100 },
    "Ja. ": {
      nom_complet: "Yaacov (Jacques)",
      nbre_chapitres: 5,
      max_verset: 100,
    },
    "Ga. ": { nom_complet: "Galates", nbre_chapitres: 6, max_verset: 100 },
    "1 Th. ": {
      nom_complet: "1 Thessaloniciens",
      nbre_chapitres: 5,
      max_verset: 100,
    },
    "2 Th. ": {
      nom_complet: "2 Thessaloniciens",
      nbre_chapitres: 3,
      max_verset: 100,
    },
    "1 Co. ": {
      nom_complet: "1 Corinthiens",
      nbre_chapitres: 16,
      max_verset: 100,
    },
    "2 Co. ": {
      nom_complet: "2 Corinthiens",
      nbre_chapitres: 13,
      max_verset: 100,
    },
    "Ro. ": { nom_complet: "Romains", nbre_chapitres: 16, max_verset: 100 },
    "Ep. ": { nom_complet: "Éphésiens", nbre_chapitres: 6, max_verset: 100 },
    "Ph. ": { nom_complet: "Philippiens", nbre_chapitres: 4, max_verset: 100 },
    "Col. ": { nom_complet: "Colossiens", nbre_chapitres: 4, max_verset: 100 },
    "Phm. ": { nom_complet: "Philémon", nbre_chapitres: 1, max_verset: 100 },
    "1 Ti. ": {
      nom_complet: "1 Timotheos (1 Timothée)",
      nbre_chapitres: 6,
      max_verset: 100,
    },
    "Tit. ": {
      nom_complet: "Titos (Tites)",
      nbre_chapitres:3,
      max_verset: 100,
    },
    "1 Pi. ": {
      nom_complet: "1 Petros (1 Pierre)",
      nbre_chapitres: 5,
      max_verset: 100,
    },
    "2 Pi. ": {
      nom_complet: "2 Petros (2 Pierre)",
      nbre_chapitres: 3,
      max_verset: 100,
    },
    "2 Ti. ": {
      nom_complet: "2 Timotheos (2 Timothée)",
      nbre_chapitres: 4,
      max_verset: 100,
    },
    "Jud. ": {
      nom_complet: "Yéhouda (Jude)",
      nbre_chapitres: 1,
      max_verset: 100,
    },
    "Hé. ": { nom_complet: "Hébreux", nbre_chapitres: 13, max_verset: 100 },
    "1 Jn. ": {
      nom_complet: "1 Yohanan (1 Jean)",
      nbre_chapitres: 5,
      max_verset: 100,
    },
    "2 Jn. ": {
      nom_complet: "2 Yohanan (2 Jean)",
      nbre_chapitres: 1,
      max_verset: 100,
    },
    "3 Jn. ": {
      nom_complet: "3 Yohanan (3 Jean)",
      nbre_chapitres: 1,
      max_verset: 100,
    },
    "Ap. ": {
      nom_complet: "Apokalupsis (Apocalypse)",
      nbre_chapitres: 22,
      max_verset: 100,
    },
  },
];

const bodyParser = require("body-parser");
const cors = require("cors");
const helmet = require("helmet");
const morgan = require('morgan');
const environment = "prod"

// adding Helmet to enhance your API's security
app.use(helmet());

// using bodyParser to parse JSON bodies into JS objects
app.use(bodyParser.json());

// enabling CORS for all requests
app.use(cors());

// adding morgan to log HTTP requests
app.use(morgan('combined'));

/**
 * Capitalize une chaine de caractère
 * @param {string} string la chaine de caractère a capitalizer
 * @returns {string}
 */
function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

/**
 * permet de recuperer l'abreviation du livre que l'utilisateur demande pour l'appel de l'API
 * @param {string} param le nom ou abbreviation du livre demandé par l'utilisateur
 * @return {string[]} l'abbreviation du livre et le nom complet
 */
function get_book_name(param){
  var correct = true;

  if (!abbr_list.includes(capitalizeFirstLetter(param).trim() + ". ")) {
    correct = false 
  }
  if (!abbr_list.includes(capitalizeFirstLetter(param).trim() + " ")) {
    correct = false 
  }
  
  if(!correct){
    correct = true;
    switch (param.substring(0, 5).toLowerCase()) {
      case "phili":
        nom_du_livre = "Ph. ";
        nom_complet_du_livre = "Philippiens";
        break;
      case "phile":
        nom_du_livre = "Phm. ";
        nom_complet_du_livre = "Philémon";
        break;
      case "philé":
        nom_du_livre = "Phm. ";
        nom_complet_du_livre = "Philémon";
        break;
      case "philm":
        nom_du_livre = "Phm. ";
        nom_complet_du_livre = "Philémon";
        break;
  
      default:
        correct = false;
        break;
    }
  }
  
  if(!correct){
    correct = true;
    switch (param.substring(0, 3).toLowerCase()) {
      case "1co":
          nom_du_livre = "1 Co. ";
          nom_complet_du_livre = "1 Corinthiens";
        break;
      case "2co":
          nom_du_livre = "2 Co. ";
          nom_complet_du_livre = "2 Corinthiens";
        break;
      case "1ch":
          nom_du_livre = "1 Ch. ";
          nom_complet_du_livre = "1 Hayyamim dibre 1 Chroniques)";
        break;
      case "2ch":
          nom_du_livre = "2 Ch. ";
          nom_complet_du_livre = "2 Hayyamim dibre (2 Chroniques)";
        break;
      case "1pi":
          nom_du_livre = "1 Pi. ";
          nom_complet_du_livre = "1 Petros (1 Pierre)";
        break;
      case "2pi":
          nom_du_livre = "2 Pi. ";
          nom_complet_du_livre = "2 Petros (2 Pierre)";
        break;
      case "1ti":
          nom_du_livre = "1 Ti. ";
          nom_complet_du_livre = "1 Timotheos (1 Timothée)";
        break;
      case "2ti":
          nom_du_livre = "2 Ti. ";
          nom_complet_du_livre = "2 Timotheos (2 Timothée)";
        break;
      case "1jn":
          nom_du_livre = "1 Jn. ";
          nom_complet_du_livre = "1 Yohanan (1 Jean)";
        break;
      case "1je":
          nom_du_livre = "1 Jn. ";
          nom_complet_du_livre = "1 Yohanan (1 Jean)";
        break;
      case "2jn":
          nom_du_livre = "2 Jn. ";
          nom_complet_du_livre = "2 Yohanan (2 Jean)";
        break;
      case "3jn":
          nom_du_livre = "3 Jn. ";
          nom_complet_du_livre = "3 Yohanan (3 Jean)";
        break;
      case "2je":
          nom_du_livre = "2 Jn. ";
          nom_complet_du_livre = "2 Yohanan (2 Jean)";
        break;
      case "3je":
          nom_du_livre = "3 Jn. ";
          nom_complet_du_livre = "3 Yohanan (3 Jean)";
        break;
      case "1th":
          nom_du_livre = "1 Th. ";
          nom_complet_du_livre = "1 Thessaloniciens";
        break;
      case "2th":
          nom_du_livre = "2 Th. ";
          nom_complet_du_livre = "2 Thessaloniciens";
        break;
      case "mat":
          nom_du_livre = "Mt. ";
          nom_complet_du_livre = "Matthaios (Matthieu)";
        break;
      case "mar":
          nom_du_livre = "Mc. ";
          nom_complet_du_livre = "Markos (Marc)";
        break;
      case "mal":
          nom_du_livre = "Mal. ";
          nom_complet_du_livre = "Mal`akiy (Malachie)";
        break;
      case "jea":
          nom_du_livre = "Jn. ";
          nom_complet_du_livre = "Yohanan (Jean)";
        break;
      case "job":
          nom_du_livre = "Job ";
          nom_complet_du_livre = "Iyov (Job)";
        break;
      case "joe":
          nom_du_livre = "Joë ";
          nom_complet_du_livre = "Yoel (Joël)";
        break;
      case "jos":
          nom_du_livre = "Jos. ";
          nom_complet_du_livre = "Yéhoshoua (Josué)";
        break;
      case "jon":
          nom_du_livre = "Jon. ";
          nom_complet_du_livre = "Yonah (Jonas)";
        break;
      case "est":
          nom_du_livre = "Est. ";
          nom_complet_du_livre = "Meguila Esther (Esther)";
        break;
      case "esd":
          nom_du_livre = "Esd. ";
          nom_complet_du_livre = "Ezra (Esdras)";
        break;
      case "col":
          nom_du_livre = "Col. ";
          nom_complet_du_livre = "Colossiens";
        break;
      case "phi":
          nom_du_livre = "Ph. ";
          nom_complet_du_livre = "Philippiens";
        break;
      case "tim":
          nom_du_livre = "1 Ti. ";
          nom_complet_du_livre = "1 Timotheos (1 Timothée)";
        break;
      case "tit":
          nom_du_livre = "Tit. ";
          nom_complet_du_livre = "Titos (Tites)";
        break;
      case "jud":
          nom_du_livre = "Jud. ";
          nom_complet_du_livre = "Yéhouda (Jude)";
        break;
      case "jug":
          nom_du_livre = "Jg. ";
          nom_complet_du_livre = "Vayiqra (Lévitique)";
        break;
  
      default:
        correct = false;
        break;
    }
  }

  if (!correct) {
    correct = true;
    switch (param.substring(0, 2).toLowerCase()) {
      case "le":
        nom_du_livre = "Lé. ";
        nom_complet_du_livre = "Vayiqra (Lévitique)";
        break;
      case "ne":
        nom_du_livre = "Né. ";
        nom_complet_du_livre = "Nehemyah (Néhémie)";
        break;
      case "je":
        nom_du_livre = "Jé. ";
        nom_complet_du_livre = "Yirmeyah (Jérémie)";
        break;
      case "ju":
        nom_du_livre = "Jg. ";
        nom_complet_du_livre = "Vayiqra (Lévitique)";
        break;
      case "1s":
        nom_du_livre = "1 S. ";
        nom_complet_du_livre = "1 Shemouél (1 Samuel)";
        break;
      case "1j":
        nom_du_livre = "1 Jn. ";
        nom_complet_du_livre = "1 Yohanan (1 Jean)";
        break;
      case "2s":
        nom_du_livre = "2 S. ";
        nom_complet_du_livre = "2 Shemouél (2 Samuel)";
        break;
      case "2j":
        nom_du_livre = "2 Jn. ";
        nom_complet_du_livre = "2 Yohanan (2 Jean)";
        break;
      case "3j":
        nom_du_livre = "3 Jn. ";
        nom_complet_du_livre = "3 Yohanan (3 Jean)";
        break;
      case "1r":
        nom_du_livre = "1 R. ";
        nom_complet_du_livre = "1 Melakhim (1 Rois)";
        break;
      case "2r":
        nom_du_livre = "2 R. ";
        nom_complet_du_livre = "2 Melakhim (2 Rois)";
        break;
      case "1c":
        nom_du_livre = "1 Ch. ";
        nom_complet_du_livre = "1 Hayyamim dibre (1 Chroniques)";
        break;
      case "2c":
        nom_du_livre = "2 Ch. ";
        nom_complet_du_livre = "2 Hayyamim dibre (2 Chroniques)";
        break;
      case "1t":
        nom_du_livre = "1 Th. ";
        nom_complet_du_livre = "1 Thessaloniciens";
        break;
      case "2t":
        nom_du_livre = "2 Th. ";
        nom_complet_du_livre = "2 Thessaloniciens";
        break;
      case "mi":
        nom_du_livre = "Mi. ";
        nom_complet_du_livre = "Miykayah (Michée)";
        break;
      case "ml":
        nom_du_livre = "Mal. ";
        nom_complet_du_livre = "Mal`akiy (Malachie)";
        break;
      case "he":
        nom_du_livre = "Hé. ";
        nom_complet_du_livre = "Hébreux";
        break;
      case "es":
        nom_du_livre = "Es. ";
        nom_complet_du_livre = "Yesha`yah (Ésaïe)";
        break;

      default:
        correct = false;
        break;
    }
  }

  if (!correct) {
    nom_du_livre = capitalizeFirstLetter(param.substring(0, 2).toLowerCase() + ". ");
    nom_complet_du_livre = complet_list[0][nom_du_livre];
  }
  return [nom_du_livre, nom_complet_du_livre]
}


/**
 * Recupère un livre entier
 * @param {string} nom_du_livre nom du livre a récuperer
 * @param {string} action type de données que l'on souhaite obtenir ("all", "info", "")
 */
function get_book(nom_du_livre, action) {
  const bym = require("./db/thebym.json");
  const l = get_book_name(nom_du_livre);
  const livre =l[0]
  const livre_nom_complet = l[1]
  var result = {}

  if (typeof action === "undefined") {
    action = "verset"
  }

  switch (action) {
    case "verset":
      var num_chap = 1;
      var a = 1;
      var verset_actual = {};
      var search = true;

      while (search) {
        while (search) {
          a++;
          var verset = livre + num_chap + ":" + a;
          var ecriture = bym[verset];

          if (ecriture) {
            verset_actual = {};
            verset_actual["livre"] = livre;
            verset_actual["livre_nom_complet"] = livre_nom_complet;
            verset_actual["chapitre"] = num_chap;
            verset_actual["verset"] = a;
            verset_actual["ecrit"] = ecriture;
            verset_actual["version"] = "Bible de Yéhoshoua Ha Mashiah";
            verset_actual["version_abbr"] = "BYM";
            result[verset] = verset_actual;
          }else{
            search = false;
          }
        }
        num_chap++;
        if (a > 0) {
          a = 0;
          search = true;
        }
        if (!bym[livre + num_chap + ":1"]) {
          search = false;
        }
      }
      break;
  
    default:
      break;
  }
  
  return result;
}


/**
 * recupère tout le chapitre d'un livre de la bible
 * @param {striong} nom_du_livre nom du livre
 * @param {string} chapitre chapitre du livre
 * @returns {JSON} versets du chapitre du livre demandé
 */
function get_all_chapter(nom_du_livre, chapitre){
  const bym = require("./db/thebym.json");
  const l = get_book_name(nom_du_livre);
  const livre = l[0];
  const livre_nom_complet = l[1];
  var result = {};
  var a = 0
  var continued = true;

  while (continued) {
    a++;
    var verset = livre + chapitre + ":" + a;
    var ecriture = bym[verset];


    if (ecriture) {
      var verset_actual = {};
      verset_actual["livre"] = livre;
      verset_actual["livre_nom_complet"] = livre_nom_complet;
      verset_actual["chapitre"] = parseInt(chapitre, 10);
      verset_actual["num_verset"] = parseInt(verset.split(":")[1]);
      verset_actual["verset"] = verset;
      verset_actual["ecrit"] = ecriture;
      verset_actual["version"] = "Bible de Yéhoshoua Ha Mashiah";
      verset_actual["version_abbr"] = "BYM";
      result[verset] = verset_actual;
    } else {
      continued = false;
    }
  }

  return result;
}


/**
 * crée un tableau contenant tous les numéros de verset contenu dans le params
 * @param {string} versets liste des verset qu'on souhaite recupérer
 * @returns selection tableau contenant la liste des numero des versets
 */
function make_selection(versets){
  var selection = []

  const listes = versets.split(",");
  for (let i = 0; i < listes.length; i++) {
    const liste = listes[i];
    if(liste.includes("-")){
      const v_debut = parseInt(liste.split("-")[0])
      const v_fin = parseInt(liste.split("-")[1]);
      for (var y = v_debut; y <= v_fin; y++) {
        selection.push(y);
      }

    }else{
      selection.push(parseInt(liste));
    } 
  }

  selection.sort((a, b) =>(a - b))

  // console.log(selection)
  return selection
}


/**
 * recupere tous les versets selectionnés
 * @param {string} nom_du_livre c'est le nom du livre dans lequel on va récuperer les verset
 * @param {string} chapitre c'est le nom du chapitre du livre 
 * @param {array} notre_selection un tableau de tous les versets selectionnés
 * @returns {JSON} un json contenant les versets choisi de la bible 
 */
function get_all_of_selection(nom_du_livre, chapitre, notre_selection) {
  const bym = require("./db/thebym.json");
  const selection = make_selection(notre_selection);
  const l = get_book_name(nom_du_livre);
  const livre = l[0];
  const livre_nom_complet = l[1];
  var result = {};

  for (let x = 0; x < selection.length; x++) {
    const num_verset = selection[x];
    const v_name = livre + chapitre + ":" + num_verset;
    v_value = bym[v_name];
    if (typeof v_value !== "undefined") {
      var verset_actual = {};

      verset_actual["livre"] = livre;
      verset_actual["livre_nom_complet"] = livre_nom_complet;
      verset_actual["chapitre"] = parseInt(chapitre, 10);
      verset_actual["num_verset"] = num_verset;
      verset_actual["verset"] = `${livre}${chapitre}:${num_verset}`;
      verset_actual["ecrit"] = v_value;
      verset_actual["version"] = "Bible de Yéhoshoua Ha Mashiah";
      verset_actual["version_abbr"] = "BYM";

      result[v_name] = verset_actual;
    }
  }
  return result;
}


/**
 * renvoi la reponse au client
 * @param {response} res la reponse du serveur
 * @param {JSON} result resultat a envoyer au client
 */
function return_result(res, result, environment) {
  try {
    res.status(200).json(result);
  } catch (err) {
    if (environment === "dev") {
      console.error(err);
    } else {
      res.status(500);
    }
  }
}


// ajoute des entêtes

app.use((req, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader(
    "Access-Control-Allow-Headers",
    "Origin, X-Requested-With, Content, Accept, Content-Type, Authorization"
  );
  res.setHeader(
    "Access-Control-Allow-Methods",
    "GET, POST, PUT, DELETE, PATCH, OPTIONS"
  );
  next();
});


// Récupére toute la bible

app.get("/bym", (req, res) => {
  // const all = require("./db/thebym.json");
  // try {
  //   res.status(200).json(all);
  // } catch (err) {
  //   console.error(err);
  // }
  const thebym = require("./db/thebym.json");
  function getRandomInt(max) {
    return 1 + Math.floor(Math.random() * max);
  }
  var abbr_list = [
    "Ge. ", "Ex. ", "Lé. ", "No. ", "De. ", "Jos. ", "Jg. ", "1 S. ", "2 S. ", "1 R. ", "2 R. ", "Es. ", "Jé. ", "Ez. ", "Os. ", "Joë. ", "Am. ", "Ab. ", "Jon. ", "Mi. ", "Na. ", "Ha. ", "So. ", "Ag. ", "Za. ", "Mal. ", "Ps. ", "Pr. ", "Job ", "Ca. ", "Ru. ", "La. ", "Ec. ", "Est. ", "Da. ", "Esd. ", "Né. ", "1 Ch. ", "2 Ch. ", "Mt. ", "Mc. ", "Lu. ", "Jn. ", "Ac. ", "Ja. ", "Ga. ", "1 Th. ", "2 Th. ", "1 Co. ", "2 Co. ", "Ro. ", "Ep. ", "Ph. ", "Col. ", "Phm. ", "1 Ti. ", "Tit. ", "1 Pi. ", "2 Pi. ", "2 Ti. ", "Jud. ", "Hé. ", "1 Jn. ", "2 Jn. ", "3 Jn. ", "Ap. "
  ]

  var books_list = {
    "Ge. ": [
      {
        "livre": "Genèse",
        "abbreviation": "Ge.",
        "auteur": "Probablement Moshèh (Moïse)",
        "signification": "Au commencement",
        "theme": "La Création de L'être humain",
        "date": "Env.1450 - 1410 av. Y.-M. (J.-C.)",
        "explication": "Premier livre du Tanakh, Bereshit est le livre du commencement. Il relate l'histoire des origines de l'humanité, la création des cieux, de la Terre et de tout ce qui s'y trouve par YHWH, l'Elohîm créateur.\nIl y est décrit le péché de l'être humain et sa séparation d'avec Elohîm, ainsi que la décadence de l'univers qui en résulta. En réponse à la méchanceté du cœur de l'humain, YHWH exerça sa justice en détruisant la Terre par le déluge. Dans sa prescience, YHWH avait cependant résolu de se réconcilier avec l'être humain. Il se révéla donc comme Sauveur en accordant sa grâce à Noah (Noé) et à sa famille. Après cet événement, les êtres humains se tournèrent une fois de plus vers le mal en tentant Elohîm par la construction de la tour de Babel, œuvre à l'origine de la dispersion des nations.\nCe livre présente aussi l'élection d'Abraham, originaire d'Our en Chaldée (Mésopotamie antique, dans l'actuel Irak), qui reçut la promesse divine de devenir une grande nation, en qui toutes les familles de la Terre seraient bénies. Le récit se poursuit par l'histoire de ses descendants : Yitzhak (Isaac), Yaacov (Jacob) et ses douze fils, qui formèrent par la suite la nation d'Israël.",
        "nbrchap": 50,
        "chapitres": [
          {1: 31},
        ]
      }
    ],
    "Ex. ": [
        {
          "livre": "",
          "abbreviation": "",
          "auteur": "",
          "signification": "",
          "theme": "",
          "date": "",
          "explication": "",
          "nbrchap": 50,
          "chapitres": [
            {1: 31},
          ]
        }
      ], 
    "Lé. ": [{
          "livre": "",
          "abbreviation": "",
          "auteur": "",
          "signification": "",
          "theme": "",
          "date": "",
          "explication": "",
          "nbrchap": 50,
          "chapitres": [
            {1: 31},
          ]
      }], 
    "No. ": [], 
    "De. ": [], 
    "Jos. ": [], 
    "Jg. ": [], 
    "1 S. ": [], 
    "2 S. ": [], 
    "1 R. ": [], 
    "2 R. ": [], 
    "Es. ": [], 
    "Jé. ": [], 
    "Ez. ": [], 
    "Os. ": [], 
    "Joë. ": [], 
    "Am. ": [], 
    "Ab. ": [], 
    "Jon. ": [], 
    "Mi. ": [], 
    "Na. ": [], 
    "Ha. ": [], 
    "So. ": [], 
    "Ag. ": [], 
    "Za. ": [], 
    "Mal. ": [], 
    "Ps. ": [], 
    "Pr. ": [], 
    "Job ": [],
    "Ca. ": [], 
    "Ru. ": [], 
    "La. ": [], 
    "Ec. ": [], 
    "Est. ": [], 
    "Da. ": [], 
    "Esd. ": [], 
    "Né. ": [], 
    "1 Ch. ": [], 
    "2 Ch. ": [], 
    "Mt. ": [], 
    "Mc. ": [], 
    "Lu. ": [], 
    "Jn. ": [], 
    "Ac. ": [], 
    "Ja. ": [], 
    "Ga. ": [], 
    "1 Th. ": [], 
    "2 Th. ": [], 
    "1 Co. ": [], 
    "2 Co. ": [], 
    "Ro. ": [], 
    "Ep. ": [], 
    "Ph. ": [], 
    "Col. ": [], 
    "Phm. ": [], 
    "1 Ti. ": [], 
    "Tit. ": [], 
    "1 Pi. ": [], 
    "2 Pi. ": [], 
    "2 Ti. ": [], 
    "Jud. ": [], 
    "Hé. ": [], 
    "1 Jn. ": [], 
    "2 Jn. ": [], 
    "3 Jn. ": [], 
    "Ap. ": []
  }


  function find_verset(complet_list) {
    abbr_list = [
    "Ge. ", "Ex. ", "Lé. ", "No. ", "De. ", "Jos. ", "Jg. ", "1 S. ", "2 S. ", "1 R. ", "2 R. ", "Es. ", "Jé. ", "Ez. ", "Os. ", "Joë. ", "Am. ", "Ab. ", "Jon. ", "Mi. ", "Na. ", "Ha. ", "So. ", "Ag. ", "Za. ", "Mal. ", "Ps. ", "Pr. ", "Job ", "Ca. ", "Ru. ", "La. ", "Ec. ", "Est. ", "Da. ", "Esd. ", "Né. ", "1 Ch. ", "2 Ch. ", "Mt. ", "Mc. ", "Lu. ", "Jn. ", "Ac. ", "Ja. ", "Ga. ", "1 Th. ", "2 Th. ", "1 Co. ", "2 Co. ", "Ro. ", "Ep. ", "Ph. ", "Col. ", "Phm. ", "1 Ti. ", "Tit. ", "1 Pi. ", "2 Pi. ", "2 Ti. ", "Jud. ", "Hé. ", "1 Jn. ", "2 Jn. ", "3 Jn. ", "Ap. "
    ]
    nbr_list = getRandomInt(abbr_list.length);
    const livre_abbr = abbr_list[nbr_list];
    const chapitre = getRandomInt(100);
    const num_verset = getRandomInt(250);

  // console.log(livre_abbr, chapitre, num_verset);

    return [livre_abbr, chapitre, num_verset]
  }

  // var book = books[abbr_list[getRandomInt(abbr_list.length)]]
  var result = find_verset();
  var livre_abbr = result[0] 
  var chapitre = result[1]
  var num_verset = result[2]

  var random_verset = `${livre_abbr}${chapitre}:${num_verset}`;

  while (typeof thebym[random_verset] === "undefined") {
    result = find_verset();
    livre_abbr = result[0];
    chapitre = result[1];
    num_verset = result[2];
    random_verset = `${livre_abbr}${chapitre}:${num_verset}`;
  }

  resultat = {
    livre: livre_abbr,
    livre_nom_complet: complet_list[0][livre_abbr],
    chapitre: chapitre,
    num_verset: num_verset,
    verset: `${livre_abbr}${chapitre}:${num_verset}`,
    ecrit: thebym[random_verset],
    version: "Bible de Yéhoshoua Ha Mashiah",
    version_abbr: "BYM",
    APIinfo: "https://www.shemaproject.org/bibleapi",
  };


  try {
    res.status(200).json(resultat);
  } catch (err) {
    console.error(err);
  }
});


// servir des fichiers statiques

app.use("/home", express.static("src"));
app.use("/contact", express.static("src/contact"));


// Récupérer tout un livre


app.get("/bym/:livre", (req, res) => {
  const nom_du_livre = req.params.livre;

  const result = get_book(nom_du_livre);
  return_result(res, result, environment);
})


// Récupérer tous les versets d'un chapitre

app.get("/bym/:livre/:chap", (req, res) => {
  const nom_du_livre = req.params.livre;
  const chapitre = req.params.chap;

  const result = get_all_chapter(nom_du_livre, chapitre);
  return_result(res, result, environment);
});


app.get("/bym/:livre/:chap/:selections", (req, res) => {
  const notre_selection = req.params.selections;
  const nom_du_livre = req.params.livre;
  const num_du_chapitre = req.params.chap;
  console.log(nom_du_livre, num_du_chapitre, notre_selection);
  const result = get_all_of_selection(nom_du_livre, num_du_chapitre, notre_selection);
  return_result(res, result, environment);
});



app.get("/bym/:livre/:chap/:selections/:goto", (req, res) => {
  const notre_selection = req.params.selections;
  const nom_du_livre = req.params.livre;
  const num_du_chapitre = req.params.chap;
  const thegoto = req.params.goto;
  if (thegoto === undefined) {
    return res.status(200);
  }

  livre_actuel = get_book_name(
    nom_du_livre.toLowerCase().replace(".", "").replace(" ", "")
  )[0];
  if (abbr_list.indexOf(livre_actuel) === 65) {
    livre_suivant = get_book_name("gen");
    livre_precedent = get_book_name("3jn");
  } else if (abbr_list.indexOf(livre_actuel) === 0) {
    livre_suivant = get_book_name("ex");
    livre_precedent = get_book_name("ap");
  } else {
    livre_suivant = get_book_name(
      abbr_list[abbr_list.indexOf(livre_actuel) + 1]
        .toLowerCase()
        .replace(".", "")
        .replace(" ", "")
    );
    livre_precedent = get_book_name(
      abbr_list[abbr_list.indexOf(livre_actuel) - 1]
        .toLowerCase()
        .replace(".", "")
        .replace(" ", "")
    );
    livre_actuel = get_book_name(
      abbr_list[abbr_list.indexOf(livre_actuel)]
        .toLowerCase()
        .replace(".", "")
        .replace(" ", "")
    );
  }
  nom_du_livre_actuel = livre_actuel[0]
    .toLowerCase()
    .replace(".", "")
    .replace(" ", "");
  nom_du_livre_precedent = livre_precedent[0]
    .toLowerCase()
    .replace(".", "")
    .replace(" ", "");
  nom_du_livre_suivant = livre_suivant[0]
    .toLowerCase()
    .replace(".", "")
    .replace(" ", "");

  
  selection = make_selection(notre_selection);
  const first = selection[0];
  const last = selection[selection.length - 1];
  prev = first - 1;
  next = last + 1;
  
  switch (thegoto) {
    case 'prev':
      if (prev === 0) {
        prev_chapitre = bible_details[0][livre_precedent[0]].nbre_chapitres;
        getchapitre = get_all_chapter(nom_du_livre_precedent, prev_chapitre);
        last_num_verset = Object.keys(getchapitre).length;

        chapitre = prev_chapitre;
        selection = `${last_num_verset}-${last_num_verset}`;
        livre = nom_du_livre_precedent;
        
      } else {
        chapitre = num_du_chapitre
        if (last === first) {
          selection = `${prev}-${prev}`;
        }else {
          selection = `${prev}-${last}`
        }
        
        livre = nom_du_livre_actuel
          .toLowerCase()
          .replace(".", "")
          .replace(" ", "")
          .replace("é", "e")
          .replace("ö", "o");
      }

      resultat = get_all_of_selection(livre, chapitre, selection); 
      break;

    case 'next':
      livre_actuel = get_book_name(
        abbr_list[abbr_list.indexOf(livre_actuel)]
          .toLowerCase()
          .replace(".", "")
          .replace(" ", "")
      );
      nom_du_livre_act = livre_actuel[0]
        .toLowerCase()
        .replace(".", "")
        .replace(" ", "");
      // on verifie qu'il existe
      if (last === first){
        selection = `${next}-${next}`;
      }else {
        selection = `${last}-${next}`;
      }
      livre = nom_du_livre_act;
      chapitre = num_du_chapitre
      console.log("data:", livre, chapitre, selection);
      it_s_exit = get_all_of_selection(livre, chapitre, selection); 
      if (Object.keys(it_s_exit).length > 0) {
        resultat = it_s_exit;
      } else {
        chapitre = parseInt(num_du_chapitre) + 1;
        selection = "1-1"
        if (chapitre > bible_details[0][livre_actuel[0]].nbre_chapitres) {
          livre = nom_du_livre_suivant;
          chapitre = 1;
        } else {
          livre = nom_du_livre_act;
          selection = "1-1";
        }
        resultat = get_all_of_selection(livre, chapitre, selection);
      }
      break;

    default:
      resultat = [{}]
      break;
  }
  return_result(res, resultat, environment);

});


app.get("/", (req, res) => {
  res.send("Que Yehowshuw`a Ha-Mashiyah soit glorifié. Amen 🙏🏾");
});

// Start server

app.listen(process.env.PORT || 8080, () => {
  console.log("Que Yehowshuw`a Ha-Mashiyah soit glorifié. Amen 🙏🏾");
});


// Export the Express API
module.exports = app;
