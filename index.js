const express = require("express");
const app = express();
var nom_du_livre = "";
var chapitre = 1;
var a = 0;
var z = "";


// Récupérer toute la bible

app.get("/bym", (req, res) => {
  res.status(200).json(bym);
});

function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

function get_book_name(param){
  if (param.toLowerCase() != "job") {
    nom_du_livre = capitalizeFirstLetter(
      param.substring(0, 2).toLowerCase() + ". "
    );
  } else {
    nom_du_livre = capitalizeFirstLetter(param.toLowerCase() + " ");
  }

  return nom_du_livre
}


function get_selection(res, nom_livre, chapitre, a, z) {
  const bym = require("./db/thebym.json");
  resultats = {};
  var y = 0;
  var has_z = true;
  var has_a = true;
  var has_chap = true;

  nom_du_livre = get_book_name(nom_livre);

  if (z === "" || z === 0 || typeof z === "undefined") {
    has_z = false;
  } else {
    z = parseInt(z);
  }

  if (a === "" || a === 0 || typeof a === "undefined") {
    a = 1;
    x = 1;
    has_a = false;
  } else {
    a = parseInt(a);
    x = parseInt(a);
  }

  if (chapitre === "" || typeof chapitre === "undefined") {
    has_chap = false;
    y = 1;
    chapitre = y;
    var next_c = y;
  }

  var v_name = nom_du_livre + chapitre + ":" + a;
  var v_value = bym[v_name];

  // var verset_actual = {}

  while (y !== "stop") {
    while (x !== "stop") {
      v_name = nom_du_livre + chapitre + ":" + x;
      v_value = bym[v_name];

      if (typeof v_value !== "undefined") {
        resultats[v_name] = v_value;
        // verset_actual["chapitre"] = chapitre;
        // verset_actual["verset"]= i;
        // verset_actual["value"] = v_value;
        x++;

        switch (true) {
          case has_z && a <= x:
            if (x > z) {
              x = "stop";
              y = "stop";
            }
            break;

          case !has_z && a <= x:
            if (has_chap) {
              y = "stop";
              if (has_a) {
                x = "stop";
              }
            }
            break;

          default:
            x = "stop";
            break;
        }
      } else {
        x = "stop";
        if (has_z) {
          y = "stop";
        }
      }
    }

    var next_c = parseInt(chapitre) + 1;
    q = nom_du_livre + next_c + ":1";
    v_value = bym[q];
    if (typeof bym[q] !== "undefined" && !has_z && y !== "stop") {
      chapitre = next_c;
      x = 1;
      y++;
    } else {
      y = "stop";
    }
  }

  try {
    res.status(200).json(resultats);
  } catch (err) {
    console.error(err);
  }
}


// Récupérer tous un livre

app.get("/bym/:livre", (req, res) => {
  const nom_du_livre = req.params.livre;

  get_selection(res, nom_du_livre);
})

// Récupérer tous les versets d'un chapitre

app.get("/bym/:livre/:chap", (req, res) => {
  const nom_du_livre = req.params.livre;
  const chapitre = req.params.chap;

  get_selection(res, nom_du_livre, chapitre);
});

// Recuperation des versets choisit

app.get("/bym/:livre/:chap/:selections", (req, res) => {
  const notre_selection = req.params.selections;
  const nom_du_livre = req.params.livre;
  const num_du_chapitre = req.params.chap;
  var v_start;
  var v_end;

  if (notre_selection.includes("-")) {
    v_start = notre_selection.split("-")[0];
    v_end = notre_selection.split("-")[1];
  } else {
    v_start = notre_selection;
    v_end = 0;
  }

  get_selection(res, nom_du_livre, num_du_chapitre, v_start, v_end);
});


// Start server

app.listen(8080, () => {
  console.log("Que Yehowshuw`a Ha-Mashiyah soit glorifié. Amen 🙏🏾");
});


// Export the Express API
module.exports = app;
