const express = require('express')
const app = express()

const fs = require("fs");

const path = "./file.txt";

app.get('/bible', (req,res) => {
    res.send("toute la bible")
})

function fileExists(url) {
    var http = new XMLHttpRequest();
    http.open("HEAD", url, false);
    http.send();
    return http.status !== 404;
}

function book_path(param) {
    var nom_du_fichier = param + ".json";
    return "./db/" + nom_du_fichier;
}


const bym = require('./db/no.json')

app.get('/bym', (req,res) => {
    res.status(200).json(bym)
})

app.get("/bym/:livre", (req, res) => {
    const nom_du_livre = req.params.livre;

    var nom_du_fichier = nom_du_livre+".json"
    var livre_path = "./db/"+nom_du_fichier

    try {
      if (fs.existsSync(livre_path)) {
        const livre = require("./db/" + nom_du_fichier);
        res.status(200).json(livre);
      }
    } catch (err) {
      console.error(err);
    }
})

app.get("/bym/:livre/:chap", (req, res) => {
    const nom_du_livre = req.params.livre;
    const num_du_chapitre = req.params.chap;

    var nom_du_fichier = nom_du_livre+".json"
    var livre_path = "./db/"+nom_du_fichier

    try {
      if (fs.existsSync(livre_path)) {
          
        const livre = require("./db/" + nom_du_fichier);
        const chapitre = livre.ecritures[num_du_chapitre]
        res.status(200).json(chapitre)
      }
    } catch (err) {
      console.error(err);
    }
})


// choix avec verset
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

    var versets = {};
     var livre_path = book_path(nom_du_livre);
     const livre = require(livre_path);
    if (v_end === 0) {
      versets = livre.ecritures[num_du_chapitre][v_start];
    } else {
      for (let i = parseInt(v_start); i <= parseInt(v_end); i++) {
        versets[i] = livre.ecritures[num_du_chapitre][i];
      }
    }

    try {
      if (fs.existsSync(livre_path)) {
        res.status(200).json(versets);
        // res.status(200).json(JSON.stringify(versets));
      }
    } catch (err) {
      console.error(err);
    }
});

// choix du verset suivant ou le premier verset du chapitre suivant
app.get("/bym/:livre/:chap/:selections/next", (req, res) => {
  const notre_selection = req.params.selections;
  const nom_du_livre = req.params.livre;
  const num_du_chapitre = req.params.chap;

  const livre_path = book_path(nom_du_livre);

  try {
    if (fs.existsSync(livre_path)) {
      const livre = require(livre_path);
      const v_end = notre_selection.includes("-")
        ? parseInt(notre_selection.split("-")[1])
        : parseInt(notre_selection);

      const next_verse = livre.ecritures[num_du_chapitre][v_end + 1];
      if (next_verse) {
        res.status(200).json({ [v_end + 1]: next_verse });
      } else {
        const next_chap = parseInt(num_du_chapitre) + 1;
        const first_verse_next_chap = livre.ecritures[next_chap]
          ? livre.ecritures[next_chap][1]
          : undefined;
        if (first_verse_next_chap) {
          res.status(200).json({ [next_chap + ":1"]: first_verse_next_chap });
        } else {
          res.status(404).json({ message: "Aucun verset suivant trouvé" });
        }
      }
    }
  } catch (err) {
    console.error(err);
  }
});

// choix du verset précédent ou le dernier verset du chapitre précédent
app.get("/bym/:livre/:chap/:selections/prev", (req, res) => {
  const notre_selection = req.params.selections;
  const nom_du_livre = req.params.livre;
  const num_du_chapitre = req.params.chap;

  const livre_path = book_path(nom_du_livre);

  try {
    if (fs.existsSync(livre_path)) {
      const livre = require(livre_path);
      const v_start = notre_selection.includes("-")
        ? parseInt(notre_selection.split("-")[0])
        : parseInt(notre_selection);

      if (v_start > 1) {
        const prev_verse = livre.ecritures[num_du_chapitre][v_start - 1];
        if (prev_verse) {
          res.status(200).json({ [v_start - 1]: prev_verse });
        } else {
          res.status(404).json({ message: "Aucun verset précédent trouvé" });
        }
      } else {
        const prev_chap = parseInt(num_du_chapitre) - 1;
        if (prev_chap >= 1 && livre.ecritures[prev_chap]) {
          const versets_prev_chap = livre.ecritures[prev_chap];
          const last_v = Math.max(...Object.keys(versets_prev_chap).map(Number));
          res.status(200).json({ [prev_chap + ":" + last_v]: versets_prev_chap[last_v] });
        } else {
          res.status(404).json({ message: "Aucun verset précédent trouvé" });
        }
      }
    }
  } catch (err) {
    console.error(err);
  }
});

app.listen(8080, () => {
    console.log("Serveur à l'écoute")
});
