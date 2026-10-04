# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
The search itself is deterministic, but two of the three tools call a hosted
model on the free tier, and one rate-limit timeout or empty response in five
runs would fail the whole try even though the loop is right. 4 of 5 leaves room
for one service hiccup without excusing a broken loop.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path never touches the model: the price filter (`$5`, and the cheapest
listing is `$12`) empties the results in plain Python, and the branch is a
single `if not results` check. Nothing in it is random, so anything less than
5 of 5 means the branch is broken.

---

## 3. The item search picked is the item every later tool received

For the query `vintage graphic tee under $30`, `session["selected_item"]["id"]`
equals `session["search_results"][0]["id"]`, and the selected item's title
appears in the prompt that `suggest_outfit` sent and in the fit card's input —
checked by comparing the ids in the session after the run — in 5 of 5 tries.

**Why this target:**
State is handed over by plain dictionary assignment in `run_agent`, not by the
model, so there's no legitimate reason for it to drift; one mismatch in five
would mean a real bug (like re-running search or picking from a stale list),
not bad luck.

---

## 4. The fit card is a real caption about this item

Across 5 runs of `denim jacket under $50` with caching off, every fit card
(a) mentions the price as `$42`, (b) mentions the platform `depop`, (c) is 4
sentences or fewer, and (d) no two of the five cards share the same first
sentence — at least 4 of 5 cards meet (a)–(c), and (d) holds across all 5.

**Why this target:**
The prompt asks for the price and platform explicitly, but at temperature 0.9
the model sometimes rephrases or drops a detail, so I allow one miss on
(a)–(c). (d) is the variation check: if cache or temperature were wrong, all
five cards would open identically, and that's an all-or-nothing failure.

---

## 5. Price ceiling is never broken, and an empty wardrobe still gets advice

For `vintage graphic tee under $30`, every listing in
`session["search_results"]` has `price <= 30` — 5 of 5 tries. And for
`denim jacket under $50` run with `--empty-wardrobe`, the run finishes with a
non-empty `outfit_suggestion` and a fit card instead of an error or crash —
at least 4 of 5 tries.

**Why this target:**
The price filter is a plain numeric comparison, so one item over budget even
once is a bug; showing a user something they said they can't afford is the
fastest way to lose their trust. The empty-wardrobe path still depends on the
model answering, so I allow one service failure there, the same as criterion 1.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
