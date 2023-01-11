const express = require("express");
const app = express();
// const TOKEN = process.env.TELEGRAM_TOKEN || "YOUR_TELEGRAM_BOT_TOKEN";
const abbr_list = ["Ge. ", "Ex. ", "Lé. ", "No. ", "De. ", "Jos. ", "Jg. ", "1 S. ", "2 S. ", "1 R. ", "2 R. ", "Es. ", "Jé. ", "Ez. ", "Os. ", "Joë. ", "Am. ", "Ab. ", "Jon. ", "Mi. ", "Na. ", "Ha. ", "So. ", "Ag. ", "Za. ", "Mal. ", "Ps. ", "Pr. ", "Job ", "Ca. ", "Ru. ", "La. ", "Ec. ", "Est. ", "Da. ", "Esd. ", "Né. ", "1 Ch. ", "2 Ch. ", "Mt. ", "Mc. ", "Lu. ", "Jn. ", "Ac. ", "Ja. ", "Ga. ", "1 Th. ", "2 Th. ", "1 Co. ", "2 Co. ", "Ro. ", "Ep. ", "Ph. ", "Col. ", "Phm. ", "1 Ti. ", "Tit. ", "1 Pi. ", "2 Pi. ", "2 Ti. ", "Jud. ", "Hé. ", "1 Jn. ", "2 Jn. ", "3 Jn. ", "Ap. "]

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
 * @return {string} l'abbreviation du livre
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
        break;
      case "phile":
        nom_du_livre = "Phm. ";
        break;
      case "philé":
        nom_du_livre = "Phm. ";
        break;
      case "philm":
        nom_du_livre = "Phm. ";
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
        break;
      case "2co":
          nom_du_livre = "2 Co. ";
        break;
      case "1ch":
          nom_du_livre = "1 Ch. ";
        break;
      case "2ch":
          nom_du_livre = "2 Ch. ";
        break;
      case "1pi":
          nom_du_livre = "1 Pi. ";
        break;
      case "2pi":
          nom_du_livre = "2 Pi. ";
        break;
      case "1ti":
          nom_du_livre = "1 Ti. ";
        break;
      case "2ti":
          nom_du_livre = "2 Ti. ";
        break;
      case "1jn":
          nom_du_livre = "1 Jn. ";
        break;
      case "1je":
          nom_du_livre = "1 Jn. ";
        break;
      case "2jn":
          nom_du_livre = "2 Jn. ";
        break;
      case "2je":
          nom_du_livre = "2 Jn. ";
        break;
      case "1th":
          nom_du_livre = "1 Th. ";
        break;
      case "2th":
          nom_du_livre = "2 Th. ";
        break;
      case "mat":
          nom_du_livre = "Mt. ";
        break;
      case "mar":
          nom_du_livre = "Mc. ";
        break;
          nom_du_livre = "Mc. ";
      case "mal":
          nom_du_livre = "Mal. ";
        break;
      case "jea":
          nom_du_livre = "Jn. ";
        break;
      case "job":
          nom_du_livre = "Job ";
        break;
      case "joe":
          nom_du_livre = "Joë ";
        break;
      case "jos":
          nom_du_livre = "Jos. ";
        break;
      case "jon":
          nom_du_livre = "Jon. ";
        break;
      case "est":
          nom_du_livre = "Est. ";
        break;
      case "esd":
          nom_du_livre = "Esd. ";
        break;
      case "col":
          nom_du_livre = "Col. ";
        break;
      case "phi":
          nom_du_livre = "Ph. ";
        break;
      case "phi":
          nom_du_livre = "Ph. ";
        break;
      case "tim":
          nom_du_livre = "Ti. ";
        break;
      case "tit":
          nom_du_livre = "Tit. ";
        break;
      case "jud":
          nom_du_livre = "Jud. ";
        break;
      case "jug":
          nom_du_livre = "Jg. ";
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
        break;
      case "ne":
        nom_du_livre = "Né. ";
        break;
      case "je":
        nom_du_livre = "Jé. ";
        break;
      case "ju":
        nom_du_livre = "Jg. ";
        break;
      case "1s":
        nom_du_livre = "1 S. ";
        break;
      case "2s":
        nom_du_livre = "2 S. ";
        break;
      case "1r":
        nom_du_livre = "1 R. ";
        break;
      case "2r":
        nom_du_livre = "2 R. ";
        break;
      case "1c":
        nom_du_livre = "1 Ch. ";
        break;
      case "2c":
        nom_du_livre = "2 Ch. ";
        break;
      case "1t":
        nom_du_livre = "1 Th. ";
        break;
      case "2t":
        nom_du_livre = "2 Th. ";
        break;
      case "ml":
        nom_du_livre = "Mal. ";
        break;

      default:
        correct = false;
        break;
    }
  }

  if (!correct) {
    nom_du_livre = capitalizeFirstLetter(param.substring(0, 2).toLowerCase() + ". ");
  }

  return nom_du_livre
}


/**
 * Recupère un livre entier
 * @param {string} nom_du_livre nom du livre a récuperer
 * @param {string} action type de données que l'on souhaite obtenir ("all", "info", "")
 */
function get_book(nom_du_livre, action) {
  const bym = require("./db/thebym.json");
  const livre = get_book_name(nom_du_livre);
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
            verset_actual["chapitre"] = num_chap;
            verset_actual["verset"] = a;
            verset_actual["ecrit"] = ecriture;
            verset_actual["version"] = "Bible de Yéhoshoua Ha Mashiah";
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
  const livre = get_book_name(nom_du_livre);
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
      verset_actual["chapitre"] = chapitre;
      verset_actual["verset"] = verset;
      verset_actual["ecrit"] = ecriture;
      verset_actual["version"] = "Bible de Yéhoshoua Ha Mashiah";
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
 * @param {string} nom_livre c'est le nom du livre dans lequel on va récuperer les verset
 * @param {string} chapitre c'est le nom du chapitre du livre 
 * @param {array} notre_selection un tableau de tous les versets selectionnés
 * @returns {JSON} un json contenant les versets choisi de la bible 
 */
function get_all_of_selection(nom_livre, chapitre, notre_selection) {
  const bym = require("./db/thebym.json");
  const selection = make_selection(notre_selection);
  var result = {};

  nom_du_livre = get_book_name(nom_livre);

  for (let x = 0; x < selection.length; x++) {
    const num_verset = selection[x];
    const v_name = nom_du_livre + chapitre + ":" + num_verset;
    v_value = bym[v_name];
    if (typeof v_value !== "undefined") {
      var verset_actual = {};

      verset_actual["livre"] = nom_du_livre;
      verset_actual["chapitre"] = chapitre;
      verset_actual["verset"] = num_verset;
      verset_actual["ecrit"] = v_value;
      verset_actual["version"] = "Bible de Yéhoshoua Ha Mashiah";

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


  function find_verset(abbr_list){
    abbr_list = [
    "Ge. ", "Ex. ", "Lé. ", "No. ", "De. ", "Jos. ", "Jg. ", "1 S. ", "2 S. ", "1 R. ", "2 R. ", "Es. ", "Jé. ", "Ez. ", "Os. ", "Joë. ", "Am. ", "Ab. ", "Jon. ", "Mi. ", "Na. ", "Ha. ", "So. ", "Ag. ", "Za. ", "Mal. ", "Ps. ", "Pr. ", "Job ", "Ca. ", "Ru. ", "La. ", "Ec. ", "Est. ", "Da. ", "Esd. ", "Né. ", "1 Ch. ", "2 Ch. ", "Mt. ", "Mc. ", "Lu. ", "Jn. ", "Ac. ", "Ja. ", "Ga. ", "1 Th. ", "2 Th. ", "1 Co. ", "2 Co. ", "Ro. ", "Ep. ", "Ph. ", "Col. ", "Phm. ", "1 Ti. ", "Tit. ", "1 Pi. ", "2 Pi. ", "2 Ti. ", "Jud. ", "Hé. ", "1 Jn. ", "2 Jn. ", "3 Jn. ", "Ap. "
    ]
    return abbr_list[getRandomInt(abbr_list.length)] + getRandomInt(100) + ":" + getRandomInt(250)
  }

  // var book = books[abbr_list[getRandomInt(abbr_list.length)]]

  var random_verset = find_verset();

  while (typeof thebym[random_verset] === "undefined") {
    random_verset = find_verset();
  }
  resultat = {
    verset: random_verset,
    ecrit: thebym[random_verset],
    version: "Bible de Yéhoshoua Ha Mashiah",
    APIinfo: "https://www.shemaproject.org/bibleapi"
  };

  try {
    res.status(200).json(resultat);
  } catch (err) {
    console.error(err);
  }
});


// servir des fichiers statiques

// app.use("/home", express.static("src"));
// app.use("/contact", express.static("src/contact"));


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


// Recuperation des versets choisit

app.get("/bym/:livre/:chap/:selections", (req, res) => {
  const notre_selection = req.params.selections;
  const nom_du_livre = req.params.livre;
  const num_du_chapitre = req.params.chap;

  const result = get_all_of_selection(nom_du_livre, num_du_chapitre, notre_selection);
  return_result(res, result, environment);
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
