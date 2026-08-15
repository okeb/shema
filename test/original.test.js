const test = require("node:test");
const assert = require("node:assert/strict");
const app = require("../index.js");

const { VERSIONS, get_all_of_selection, maybe_attach_strongs } = app._internals;

function originalVerse(book, chapter, verse, query = {}) {
  const version = VERSIONS.orig;
  const result = get_all_of_selection(book, chapter, String(verse), version.data, version.name);
  return maybe_attach_strongs(result, {
    query,
    isOriginal: true,
    strongsData: version.strongsData,
  });
}

test("Genèse 1:1 est servi en hébreu avec sept segments", () => {
  const verse = originalVerse("genese", 1, 1)["Ge. 1:1"];
  assert.match(verse.ecrit, /בְּרֵאשִׁ֖ית/);
  assert.equal(verse.strongs.length, 7);
  assert.ok(verse.strongs.every(segment => segment.lang === "hebrew"));
  assert.equal(verse.strongs[0].strong, "H7225");
});

test("le mode interlinéaire expose les gloses et l'araméen", () => {
  const segments = originalVerse("daniel", 2, 4, { mode: "interlinear" })["Da. 2:4"].strongs;
  assert.ok(segments.some(segment => segment.lang === "aramaic"));
  assert.ok(segments.some(segment => Object.hasOwn(segment, "gloss")));
});

test("Jean 3:16 expose translittération et définition à la demande", () => {
  const first = originalVerse("jean", 3, 16, { strongs: "1", translit: "1" })["Jn. 3:16"].strongs[0];
  assert.equal(first.strong, "G3779");
  assert.ok(first.translit);
  assert.ok(first.definition);
});

test("le mode original masque gloses et translittérations", () => {
  const first = originalVerse("jean", 3, 16)["Jn. 3:16"].strongs[0];
  assert.equal(Object.hasOwn(first, "gloss"), false);
  assert.equal(Object.hasOwn(first, "translit"), false);
});

test("Matthieu 15:4 suit le TR pour commander", () => {
  const segments = originalVerse("matthieu", 15, 4)["Mt. 15:4"].strongs;
  const command = segments.find(segment => segment.text.includes("ἐνετείλατο"));
  assert.equal(command.strong, "G1781");
});
