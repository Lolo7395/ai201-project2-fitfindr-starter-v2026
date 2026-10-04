# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr takes a plain-language thrift request like `vintage graphic tee under $30, size M`
and searches 40 secondhand listings from Depop, ThredUp and Poshmark for the best match within
that size and budget. It then takes the top listing and the user's saved wardrobe and suggests
one or two outfits using pieces they already own (or general styling ideas if the wardrobe is
empty). Finally it writes a short, postable "fit card" caption that names the item, its price
and where it was found. If nothing matches, it stops early and says which filter to loosen.


---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the 40 listings in `data/listings.json` by price ceiling and size, then ranks what's left by how many words of the description appear in each listing's title, style tags, category, colors, brand and description.
- **Inputs:** `description` (str) — keywords like `"vintage graphic tee"`; `size` (str | None) — e.g. `"M"` or `"8"`, `None` skips the size filter; `max_price` (float | None) — inclusive ceiling in dollars, `None` skips the price filter.
- **Returns:** `list[dict]` — up to `config.SEARCH_RESULT_LIMIT` (10) full listing dicts (`id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`), highest keyword score first, cheaper first on ties. A size matches when it equals one whole part of the listing's size after splitting on `/`, spaces and brackets and dropping `US`/`SIZE` — so `M` matches `S/M` and `M/L`, `8` matches `US 8` but not `US 8.5`, and `S` does not match `XS` or `US 9`. `One Size` listings match any size.
- **When it has nothing:** returns `[]` — an empty list, never `None` and never an exception. That empty list is what the loop branches on.

### `suggest_outfit`

- **What it does:** Asks the model for one or two complete outfits built around the thrifted item, naming pieces the user already owns.
- **Inputs:** `new_item` (dict) — one listing dict from `search_listings`; `wardrobe` (dict) — `{"items": [...]}` where each item has `name`, `category`, `colors`, `style_tags`, `notes`.
- **Returns:** `str` — a non-empty plain-text suggestion of one or two outfits, each naming the new item plus wardrobe pieces by their `name`.
- **When it has nothing:** if `wardrobe["items"]` is empty (or missing), it asks the model for general styling advice for the item instead (what kinds of pieces to pair it with), and says it had no wardrobe to work from. If the model returns an empty string, it returns a fixed fallback sentence built from the item's title, category and colors — never `""`.

### `create_fit_card`

- **What it does:** Asks the model to write a short social-media caption for the find, as if the user were posting the outfit.
- **Inputs:** `outfit` (str) — the text returned by `suggest_outfit`; `new_item` (dict) — the same listing dict that went into `suggest_outfit`.
- **Returns:** `str` — a 2–4 sentence caption that mentions the item, its price (`$24`) and its platform once each; mentions the brand only when `brand` is not `None`.
- **When it has nothing:** if `outfit` is empty or only whitespace, it does not call the model and returns `"No fit card: there was no outfit suggestion to write about for <title>."`

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, the loop writes a message into `session["error"]` that names the filters it used (description, size, price) and suggests what to loosen, then returns the session without calling `suggest_outfit` or `create_fit_card`. Otherwise it puts the first (best-scoring) result into `session["selected_item"]` and goes on to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** regex, in `agent.py::parse_query`. A price comes from `under/below/less than/max/up to $N` (or a bare `$N`), a size from `size X`. Both phrases are removed and what's left is the description.

**What moves through the session:** `query` → `parsed` (`description`, `size`, `max_price`) → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`. Each tool reads its inputs back out of the session, not from the previous call's return value. `error` is set only on an early stop.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Graphic Tee — 2003 Tour Bootleg Style — $24.0 on depop

  Outfit:   Hey there! That 2003 tour tee is an absolute score for twenty-four bucks. Here are two effortless ways to style it using your current wardrobe.

Outfit 1: Pair the graphic tee with your baggy straight-leg jeans, black combat boots, and the black crossbody bag. This works because it leans fully into a classic, grungy streetwear vibe that feels totally cohesive and effortlessly cool.

Outfit 2: Layer the vintage black denim jacket over the graphic tee, worn with your wide-leg khaki trousers and chunky white sneakers. This works because the tan trousers soften the edgy black pieces, creating a balanced, textured look with a great mix of styles.

Fit card: Scored this 2003 tour tee on depop for just twenty-four bucks and I'm living for the grungy streetwear energy. Paired it with baggy denim and combat boots for an effortlessly cool look.

2 model calls this session, 687 prompt + 181 output tokens
```

**The empty-search path** (stops before `suggest_outfit`, no model calls):

```
$ python app.py ask 'designer ballgown size XXS under $5'

  No listings matched "designer ballgown", size XXS, under $5. Try to drop the size, or raise the price ceiling, or use broader words (e.g. 'jacket' instead of a specific style).

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print([(r['id'], r['title'], r['price']) for r in search_listings('graphic tee', max_price=30)])"
[('lst_006', 'Graphic Tee — 2003 Tour Bootleg Style', 24.0), ('lst_002', 'Y2K Baby Tee — Butterfly Print', 18.0), ('lst_033', 'Vintage Band Tee — Faded Grey', 19.0), ('lst_015', 'Vintage Graphic Hoodie — Faded Black', 26.0), ('lst_017', 'Mesh Long-Sleeve Top — Black', 15.0), ('lst_012', 'Oversized Crewneck Sweatshirt — Vintage Navy', 20.0), ('lst_011', 'Low-Rise Cargo Pants — Khaki', 27.0)]

$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
[]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[5], get_example_wardrobe()))"
Hey there! That 2003 tour tee is an absolute score for twenty-four bucks. Here are two effortless ways to style it using your current wardrobe.

Outfit 1: Pair the graphic tee with your baggy straight-leg jeans, black combat boots, and the black crossbody bag. This works because it leans fully into a classic, grungy streetwear vibe that feels totally cohesive and effortlessly cool.

Outfit 2: Layer the vintage black denim jacket over the graphic tee, worn with your wide-leg khaki trousers and chunky white sneakers. This works because the tan trousers soften the edgy black pieces, creating a balanced, textured look with a great mix of styles.
```

```
$ AI201_CACHE=0 python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('baggy dark-wash jeans and chunky white sneakers', load_listings()[5]))"
Scored this 2003 tour graphic tee for only $24 and it totally anchors this whole grunge look. Paired it with baggy dark-wash jeans and chunky sneakers for the ultimate effortless streetwear fit. Found it scrolling on depop and it’s already my new favorite shirt. 🛹

$ AI201_CACHE=0 python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('baggy dark-wash jeans and chunky white sneakers', load_listings()[5]))"
Scored this 2003 tour bootleg graphic tee for only $24 and it totally makes the grunge aesthetic. Paired it with baggy dark-wash denim and chunky kicks for an effortless streetwear look. Found it on depop and I'm never taking it off 🎸

$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[5]))"
No fit card: there was no outfit suggestion to write about for Graphic Tee — 2003 Tour Bootleg Style.
```

Same input, cache off, two different captions — so neither the cache nor a 0.0 temperature is flattening the output. The last call is the empty-outfit guard: it returns a message without calling the model.

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I gave Claude my `search_listings` spec, including the rule that a size has to match a whole part of the listing's size, and asked it to implement the filter.
- *What came back:* A filter that splits sizes on `/`, spaces and brackets and drops `US`, so `M` matches `S/M` and `8` matches `US 8`. I checked it against the data: `platform sneakers` with size `8` returned only `lst_019` (US 8), not the US 8.5 Chelsea boots, and size `S` didn't match `XS` or `US 9`.
- *What I changed:* The size logic I kept as-is. But testing `graphic tee` under $30 showed Low-Rise Cargo Pants at rank 7, a weak match on one shared word. I left it in, because the loop only uses the top result and the top three were all real tees, and I wrote criterion 1 at 4 of 5 partly because keyword scoring can pick a weak match first on vaguer queries.

**Moment 2**

- *What I asked for:* A regex `parse_query` in `agent.py` that pulls the price and size out of a query and leaves the rest as the description.
- *What came back:* It worked on all six example queries, but `looking for a vintage graphic tee under $30` came back with the description `"a vintage graphic tee"`. The first attempt to fix it was a `sed` command that silently matched nothing, and the unfixed version got committed anyway.
- *What I changed:* I re-ran `parse_query` after the commit, saw the stray `"a"` still there, made the fix directly in the regex (`(?:an?\s+|some\s+)?` after "looking for"), and committed it separately. Lesson: re-run the check after an edit, don't trust that it applied.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
