#!/usr/bin/env python3
"""Construit la version biblique originale (WLC/MorphHB + TR Scrivener 1894).

Les sources ne sont pas copiées dans le dépôt. Elles peuvent être clonées avec
``make original-sources`` puis consommées de façon déterministe par ce script.
"""

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, deque

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "db", "strongs", "orig_strongs.json")
REPORT = os.path.join(ROOT, "db", "strongs", "orig_build_report.json")
LEXICON = os.path.join(ROOT, "db", "strongs", "lexicon.json")
BYM_STRONGS = os.path.join(ROOT, "db", "strongs", "bym_strongs.json")
BYM = os.path.join(ROOT, "db", "thebym.json")

OT_BOOKS = {
    "Gen":"Ge.", "Exod":"Ex.", "Lev":"Lé.", "Num":"No.", "Deut":"De.",
    "Josh":"Jos.", "Judg":"Jg.", "Ruth":"Ru.", "1Sam":"1 S.", "2Sam":"2 S.",
    "1Kgs":"1 R.", "2Kgs":"2 R.", "1Chr":"1 Ch.", "2Chr":"2 Ch.",
    "Ezra":"Esd.", "Neh":"Né.", "Esth":"Est.", "Job":"Job", "Ps":"Ps.",
    "Prov":"Pr.", "Eccl":"Ec.", "Song":"Ca.", "Isa":"Es.", "Jer":"Jé.",
    "Lam":"La.", "Ezek":"Ez.", "Dan":"Da.", "Hos":"Os.", "Joel":"Joë.",
    "Amos":"Am.", "Obad":"Ab.", "Jonah":"Jon.", "Mic":"Mi.", "Nah":"Na.",
    "Hab":"Ha.", "Zeph":"So.", "Hag":"Ag.", "Zech":"Za.", "Mal":"Mal.",
}
NT_BOOKS = {
    "Matt":"Mt.", "Mark":"Mc.", "Luke":"Lu.", "John":"Jn.", "Acts":"Ac.",
    "Rom":"Ro.", "1Cor":"1 Co.", "2Cor":"2 Co.", "Gal":"Ga.", "Eph":"Ep.",
    "Phil":"Ph.", "Col":"Col.", "1Thess":"1 Th.", "2Thess":"2 Th.",
    "1Tim":"1 Ti.", "2Tim":"2 Ti.", "Titus":"Tit.", "Phlm":"Phm.",
    "Heb":"Hé.", "Jas":"Ja.", "1Pet":"1 Pi.", "2Pet":"2 Pi.",
    "1John":"1 Jn.", "2John":"2 Jn.", "3John":"3 Jn.", "Jude":"Jud.", "Rev":"Ap.",
}

# La table partagée est l'autorité pour les codes OSIS et les abréviations.
with open(os.path.join(ROOT, "db", "books_meta.json"), encoding="utf-8") as _f:
    _book_meta = json.load(_f)
OT_BOOKS = {book["osis"]: book["abbr"] for book in _book_meta[:39]}
NT_BOOKS = {book["osis"]: book["abbr"] for book in _book_meta[39:]}

NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"

def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {} if default is None else default

def canonical_strong(value, prefix):
    """MorphHB utilise des préfixes (c/d/776) et des suffixes (1254 a)."""
    numbers = re.findall(r"\d+", str(value or ""))
    return prefix + str(int(numbers[-1])) if numbers else None

def clean_hebrew(text):
    return (text or "").replace("/", "")

def french_morph_at(code):
    if not code:
        return None
    lang = "araméen" if code.startswith("A") else "hébreu"
    kinds = {"N":"nom", "V":"verbe", "A":"adjectif", "P":"pronom", "R":"préposition",
             "C":"conjonction", "T":"particule", "D":"adverbe"}
    parts = []
    for piece in code[1:].split("/"):
        label = kinds.get(piece[:1])
        if label and label not in parts:
            parts.append(label)
    return f"{lang} — " + (", ".join(parts) if parts else code[1:])

def french_morph_nt(code):
    if not code:
        return None
    kinds = {"N":"nom", "V":"verbe", "T":"article", "P":"pronom", "A":"adjectif",
             "ADV":"adverbe", "CONJ":"conjonction", "PREP":"préposition", "PRT":"particule"}
    head = code.split("-")[0]
    label = kinds.get(head, kinds.get(head[:1], head))
    cases = {"N":"nominatif", "G":"génitif", "D":"datif", "A":"accusatif", "V":"vocatif"}
    detail = code.split("-")[-1]
    if len(detail) >= 1 and detail[0] in cases:
        label += " " + cases[detail[0]]
    return label

def gloss_queues():
    queues = {}
    for key, segments in read_json(BYM_STRONGS).items():
        by_code = defaultdict(deque)
        for seg in segments:
            code = seg.get("strong")
            if code:
                by_code[code].append((seg.get("gloss") or seg.get("text") or "").strip())
        queues[key] = by_code
    return queues

def take_gloss(queues, key, code):
    q = queues.get(key, {}).get(code)
    return q.popleft() if q else ""

def parse_ot(source, queues):
    out = {}
    for osis, abbr in OT_BOOKS.items():
        path = os.path.join(source, f"{osis}.xml")
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        root = ET.parse(path).getroot()
        for verse in root.iter(NS + "verse"):
            ref = verse.get("osisID", "").split(".")
            if len(ref) != 3:
                continue
            key = f"{abbr} {int(ref[1])}:{int(ref[2])}"
            segments = []
            # Ne pas descendre dans les notes : le texte principal conserve le Ketiv.
            for child in list(verse):
                if child.tag == NS + "w":
                    if segments and not segments[-1]["text"].endswith((" ", "־")):
                        segments[-1]["text"] += " "
                    text = clean_hebrew("".join(child.itertext()))
                    strong = canonical_strong(child.get("lemma"), "H")
                    morph = child.get("morph")
                    seg = {"text": text, "strong": strong, "morph": morph,
                           "morph_fr": french_morph_at(morph),
                           "lang": "aramaic" if (morph or "").startswith("A") else "hebrew",
                           "gloss": take_gloss(queues, key, strong)}
                    segments.append(seg)
                elif child.tag == NS + "seg":
                    text = "".join(child.itertext())
                    if text:
                        if segments:
                            segments[-1]["text"] += text
                        else:
                            segments.append({"text": text, "strong": None, "lang": "hebrew"})
            out[key] = segments
    return out

def parse_nt(source, queues):
    raw = read_json(source)
    if not isinstance(raw, list):
        raise ValueError("La source NT doit être le JSON plat de honza/textus-receptus")
    out = {}
    for verse in raw:
        osis = verse.get("book_name_osis")
        abbr = NT_BOOKS.get(osis)
        if not abbr:
            continue
        key = f"{abbr} {int(verse['chapter'])}:{int(verse['verse'])}"
        segments = []
        for word in verse.get("words", []):
            if segments:
                segments[-1]["text"] += " "
            strong = canonical_strong(word.get("strong"), "G")
            morph = word.get("grammar") or ""
            segments.append({"text": word.get("greek", ""), "strong": strong,
                             "morph": morph, "morph_fr": french_morph_nt(morph),
                             "lang": "greek", "gloss": take_gloss(queues, key, strong)})
        out[key] = segments
    return out

def validate(data, lexicon, bym):
    orphan_strongs = defaultdict(int)
    missing_bym = []
    empty = []
    for key, segments in data.items():
        if key not in bym:
            missing_bym.append(key)
        if not segments or not "".join(s.get("text", "") for s in segments):
            empty.append(key)
        for seg in segments:
            code = seg.get("strong")
            if code and code not in lexicon:
                orphan_strongs[code] += 1
    return {"verses": len(data), "missing_bym": missing_bym,
            "empty_verses": empty, "orphan_strongs": dict(sorted(orphan_strongs.items()))}

def apply_versification(data, bym):
    """Réconcilie les rares bornes WLC qui ne sont pas des clés BYM.

    MorphHB isole la formule post-peste dans Nb 25:19, tandis que la
    versification protestante du projet la place au début de Nb 26:1.
    """
    source, target = "No. 25:19", "No. 26:1"
    if source in data and source not in bym and target in data:
        prefix = data.pop(source)
        if prefix and not prefix[-1]["text"].endswith(" "):
            prefix[-1]["text"] += " "
        data[target] = prefix + data[target]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=("ot", "nt", "all"), default="all")
    parser.add_argument("--ot-source", default="/tmp/shema-morphhb/wlc")
    parser.add_argument("--nt-source", default="/tmp/shema-scrivener/data/gnt.flat.json")
    parser.add_argument("--out", default=OUT)
    parser.add_argument("--sqlite", help="Compatibilité Makefile; le lexique JSON existant est utilisé")
    args = parser.parse_args()

    existing = read_json(args.out)
    queues = gloss_queues()
    if args.lang in ("ot", "all"):
        existing = {k:v for k,v in existing.items() if not k.startswith(tuple(a + " " for a in OT_BOOKS.values()))}
        existing.update(parse_ot(args.ot_source, queues))
    if args.lang in ("nt", "all"):
        existing = {k:v for k,v in existing.items() if not k.startswith(tuple(a + " " for a in NT_BOOKS.values()))}
        existing.update(parse_nt(args.nt_source, queues))

    order = {abbr: i for i, abbr in enumerate(list(OT_BOOKS.values()) + list(NT_BOOKS.values()))}
    def sort_key(item):
        m = re.match(r"^(.+?) (\d+):(\d+)$", item[0])
        return (order.get(m.group(1), 999), int(m.group(2)), int(m.group(3)))
    bym = read_json(BYM)
    apply_versification(existing, bym)
    existing = dict(sorted(existing.items(), key=sort_key))
    report = validate(existing, read_json(LEXICON), bym)
    if report["empty_verses"]:
        sys.exit(f"Versets originaux vides: {report['empty_verses'][:5]}")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, separators=(",", ":"))
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Texte original: {len(existing)} versets; Strong's orphelins: {len(report['orphan_strongs'])}")
    print(f"Rapport: {REPORT}")

if __name__ == "__main__":
    main()
