#!/usr/bin/env python3
"""
check_override_integrity.py — Vérifie que chaque override concorde avec le texte BYM.

Pour chaque verset présent dans overrides.json, la concaténation des segments
(text) doit être EXACTEMENT égale au texte de thebym.json[verse]. Sinon, l'override
est « stale » (le texte BYM a changé depuis GitLab mais l'override n'a pas été
re-curaté).

Usage:
    python3 scripts/check_override_integrity.py
    python3 scripts/check_override_integrity.py --overrides db/strongs/overrides.json --thebym db/thebym.json

Exit code:
    0 = toutes les overrides concordent
    1 = au moins une override est stale (détails affichés)
"""
import argparse
import json
import sys

DEFAULT_OVERRIDES = "db/strongs/overrides.json"
DEFAULT_THEBYM = "db/thebym.json"


def main():
    ap = argparse.ArgumentParser(description="Vérifie l'intégrité des overrides vs thebym.json")
    ap.add_argument("--overrides", default=DEFAULT_OVERRIDES)
    ap.add_argument("--thebym", default=DEFAULT_THEBYM)
    args = ap.parse_args()

    thebym = json.load(open(args.thebym, encoding="utf-8"))
    overrides = json.load(open(args.overrides, encoding="utf-8"))

    stale = []
    missing = []
    null_text_strong = []
    for key, segs in overrides.items():
        if key not in thebym:
            missing.append(key)
            continue
        concat = "".join(s.get("text") or "" for s in segs)
        if concat != thebym[key]:
            stale.append((key, len(concat), len(thebym[key])))
        for s in segs:
            if s.get("strong") and (s.get("text") is None or s.get("text") == ""):
                null_text_strong.append(key)

    print(f"Overrides totales : {len(overrides)}")
    print(f"  Concordantes    : {len(overrides) - len(stale) - len(missing)}")
    if missing:
        print(f"  Verset absent du thebym : {len(missing)}")
        for k in missing:
            print(f"    - {k}")
    if stale:
        print(f"  ❌ Overrides STALE (texte ne concorde pas) : {len(stale)}")
        for k, lo, lt in stale:
            print(f"    - {k}  (override={lo} chars, thebym={lt} chars)")
    if null_text_strong:
        print(f"  ⚠ Strong en texte nul : {set(null_text_strong)}")

    if stale or missing:
        print(
            "\n=> ÉCHEC : des overrides sont stale. Le texte BYM a changé (probablement "
            "depuis GitLab) mais l'override n'a pas été re-curaté. Refus de commettre un "
            "alignement cassé. Re-curer manuellement les versets listés ci-dessus.",
            file=sys.stderr,
        )
        sys.exit(1)
    print("\n✅ Toutes les overrides concordent avec le texte BYM.")
    sys.exit(0)


if __name__ == "__main__":
    main()