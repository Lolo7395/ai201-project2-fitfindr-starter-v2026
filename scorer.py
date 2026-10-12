#!/usr/bin/env python3
"""
Score a run_eval.py log against criteria.md.

    python scorer.py before        scores the newest results/run_*_before.json
    python scorer.py after

run_eval.py deliberately leaves PASS/FAIL blank. This is my judgment, written
down as code so that the same rule is applied to every try and to both the
before and after logs. Each check below is the sentence from criteria.md it is
named after, nothing stricter and nothing looser.

Criterion 4 is reported twice. It says the card must mention `depop`, but the
only denim jacket in data/listings.json is on poshmark (see criteria.md, where
the revision sits under the original). Both are scored from the same five cards.
"""

import json
import re
import sys
from pathlib import Path

import config

TARGETS = {1: 4, 2: 5, 3: 5, 4: 4, 5: 5}   # passes needed out of 5


def _latest(label: str) -> Path:
    found = sorted(config.RESULTS_DIR.glob(f"run_*_{label}.json"))
    if not found:
        sys.exit(f"No results/run_*_{label}.json — run `python run_eval.py --label {label}` first.")
    return found[-1]


def _steps(trace: str) -> list[str]:
    """Step names only: `[3] suggest_outfit` -> `suggest_outfit`. Notes can
    mention a tool by name without it having been called."""
    return re.findall(r"^\[\d+\] (.+)$", trace or "", flags=re.MULTILINE)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.findall(r"[^.!?]+(?:[.!?]+|$)", text or "") if s.strip()]


def _first_sentence(text: str) -> str:
    parts = _sentences(text)
    return parts[0] if parts else ""


def _completed(session) -> bool:
    return bool(
        session
        and not session.get("error")
        and (session.get("outfit_suggestion") or "").strip()
        and (session.get("fit_card") or "").strip()
        and not session["fit_card"].startswith("No fit card:")
    )


def score(rows: list[dict]) -> dict:
    by_crit: dict[int, list[dict]] = {}
    for row in rows:
        by_crit.setdefault(row["scenario"]["criterion"], []).append(row)

    out: dict = {}

    # 1. A matching query runs all three tools and returns a fit card.
    tries = by_crit[1][0]["tries"]
    cells = []
    for t in tries:
        steps = _steps(t.get("trace"))
        ok = (
            not t.get("crashed")
            and _completed(t.get("session"))
            and all(name in steps for name in
                    ("search_listings (via MCP)", "suggest_outfit", "create_fit_card"))
        )
        cells.append(ok)
    out[1] = {"cells": cells, "notes": []}

    # 2. A query with no matches stops before suggest_outfit, with a message.
    cells, notes = [], []
    for t in by_crit[2][0]["tries"]:
        s = t.get("session") or {}
        steps = _steps(t.get("trace"))
        ok = (
            not t.get("crashed")
            and bool((s.get("error") or "").strip())
            and "Try" in (s.get("error") or "")
            and s.get("outfit_suggestion") is None
            and s.get("fit_card") is None
            and "suggest_outfit" not in steps
            and "create_fit_card" not in steps
            and not t.get("prompts")
        )
        cells.append(ok)
    out[2] = {"cells": cells, "notes": notes}

    # 3. selected id == first result id; title in both model prompts.
    cells, notes = [], []
    for t in by_crit[3][0]["tries"]:
        s = t.get("session") or {}
        results, item = s.get("search_results") or [], s.get("selected_item") or {}
        prompts = t.get("prompts") or []
        same_id = bool(results) and item.get("id") == results[0].get("id")
        title = item.get("title", "\0")
        in_prompts = len(prompts) >= 2 and all(title in p for p in prompts[:2])
        cells.append(not t.get("crashed") and same_id and in_prompts)
        notes.append(f"id match={same_id}, title in {sum(title in p for p in prompts)}/{len(prompts)} prompts")
    out[3] = {"cells": cells, "notes": notes}

    # 4. fit card: $42, platform, <= 4 sentences; 5 distinct first sentences.
    tries = by_crit[4][0]["tries"]
    cards = [((t.get("session") or {}).get("fit_card") or "") for t in tries]
    firsts = [_first_sentence(c) for c in cards]
    distinct = len({f.lower() for f in firsts}) == len(firsts) and all(firsts)

    def card_ok(card: str, platform: str) -> bool:
        return "$42" in card and platform in card.lower() and len(_sentences(card)) <= 4

    notes = [
        f"$42={'$42' in c}, depop={'depop' in c.lower()}, poshmark={'poshmark' in c.lower()}, "
        f"sentences={len(_sentences(c))}"
        for c in cards
    ]
    out[4] = {
        "cells": [card_ok(c, "depop") for c in cards],
        "cells_revised": [card_ok(c, "poshmark") for c in cards],
        "distinct_first_sentences": distinct,
        "firsts": firsts,
        "notes": notes,
    }

    # 5a. every search result <= $30; 5b. empty wardrobe still gets advice.
    a_cells = []
    for t in by_crit[5][0]["tries"]:
        res = (t.get("session") or {}).get("search_results") or []
        a_cells.append(not t.get("crashed") and bool(res) and all(r["price"] <= 30 for r in res))
    b_cells = [not t.get("crashed") and _completed(t.get("session"))
               for t in by_crit[5][1]["tries"]]
    out[5] = {"a": a_cells, "b": b_cells,
              "cells": [a and b for a, b in zip(a_cells, b_cells)]}
    return out


def verdicts(out: dict) -> dict:
    v = {}
    for n in (1, 2, 3):
        v[n] = sum(out[n]["cells"]) >= TARGETS[n]
    c4 = out[4]
    v[4] = sum(c4["cells"]) >= 4 and c4["distinct_first_sentences"]
    v["4r"] = sum(c4["cells_revised"]) >= 4 and c4["distinct_first_sentences"]
    v[5] = sum(out[5]["a"]) == 5 and sum(out[5]["b"]) >= 4
    return v


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "before"
    path = _latest(label)
    out = score(json.loads(path.read_text(encoding="utf-8")))
    v = verdicts(out)

    def cell(ok):
        return "PASS" if ok else "FAIL"

    names = {
        1: ("1. A matching query runs all three tools", "4 of 5"),
        2: ("2. A query with no matches stops early", "5 of 5"),
        3: ("3. All tools use the same selected item", "5 of 5"),
        4: ("4. Fit card has price, platform, length, variety (as written: depop)", "4 of 5 + 5 distinct"),
        5: ("5. Within budget (5/5) and empty wardrobe advice (4/5)", "5 of 5 / 4 of 5"),
    }
    lines = [f"# Scored — {label}", "", f"Source: `{path.name}`", "",
             "| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Passes | Verdict |",
             "|---|---|---|---|---|---|---|---|---|"]
    for n in (1, 2, 3, 4, 5):
        c = out[n]["cells"]
        verdict = "MET" if v[n] else "MISSED"
        lines.append(f"| {names[n][0]} | {names[n][1]} | "
                     + " | ".join(cell(x) for x in c)
                     + f" | {sum(c)}/5 | {verdict} |")
    c4 = out[4]
    lines += ["", "## Detail", "",
              f"- Criterion 5a (budget): {sum(out[5]['a'])}/5 · 5b (empty wardrobe): {sum(out[5]['b'])}/5",
              f"- Criterion 4, content (as written, depop): {sum(c4['cells'])}/5",
              f"- Criterion 4, content (revised, poshmark): {sum(c4['cells_revised'])}/5",
              f"- Criterion 4, five distinct first sentences: {c4['distinct_first_sentences']}",
              f"- Criterion 4 verdict as written: {'MET' if v[4] else 'MISSED'}; "
              f"with the revision: {'MET' if v['4r'] else 'MISSED'}",
              "", "Criterion 4 per card:", ""]
    for i, (f, note) in enumerate(zip(c4["firsts"], c4["notes"]), 1):
        lines.append(f"- try {i}: {note}\n  first sentence: {f!r}")
    lines += ["", "Criterion 3 per try:", ""]
    lines += [f"- try {i}: {n}" for i, n in enumerate(out[3]["notes"], 1)]

    text = "\n".join(lines)
    print(text)
    (config.RESULTS_DIR / f"scored_{label}.md").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
