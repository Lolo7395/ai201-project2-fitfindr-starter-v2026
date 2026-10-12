# FitFindr

<!-- > ### 👋 Start here
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
> **The rest of this file is your submission.** Fill it in as you go. -->

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

FitFindr helps you find secondhand clothes and put together outfits. Enter a request like `vintage graphic tee under $30, size M`, and it searches 40 saved listings from Depop, ThredUp, and Poshmark. It picks the best match, suggests one or two outfits using clothes you already own, and writes a short caption you can post. If your wardrobe is empty, it gives general styling ideas. If nothing matches, it suggests which filters to loosen.

## Tool Inventory

### `search_listings`

- **What it does:** Searches `data/listings.json`, filters by size and budget, and ranks listings by words shared with your request. It checks the title, tags, category, colors, brand, and description.
- **Inputs:** `description` (str), `size` (str | None), and `max_price` (float | None). Using `None` skips that filter. Items priced at the maximum are included.
- **Returns:** `list[dict]` — up to 10 listing dictionaries, controlled by `config.SEARCH_RESULT_LIMIT`. Each includes `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`. The best keyword matches come first, with cheaper items first when scores tie. Sizes match whole parts: `M` matches `S/M` or `M/L`, and `8` matches `US 8` but not `US 8.5`. `S` does not match `XS` or `US 9`. `One Size` matches any requested size.
- **If nothing matches:** Returns an empty list (`[]`). The agent uses this to decide when to stop.

### `suggest_outfit`

- **What it does:** Uses the model to suggest one or two outfits built around the selected item and clothes you already own.
- **Inputs:** `new_item` (dict — one listing dictionary) and `wardrobe` (dict — with an `items` list). Each wardrobe item contains `name`, `category`, `colors`, `style_tags`, and `notes`.
- **Returns:** `str` — non-empty text describing one or two outfits, naming the new item and wardrobe pieces.
- **If the wardrobe is empty:** Gives general styling advice and explains that no wardrobe was available. If the model returns empty text, a fallback sentence uses the item's title, category, and colors.

### `create_fit_card`

- **What it does:** Uses the model to write a short social media caption for the outfit.
- **Inputs:** `outfit` (str — the text from `suggest_outfit`) and `new_item` (dict — the same listing dictionary).
- **Returns:** `str` — a 2–4 sentence caption mentioning the item, price, and platform once each. It includes the brand only if `brand` is not `None`.
- **Opening:** Each call is given one of six opening angles at random and told not to open with "Scored", "Found", "Just", "Obsessed" or "Thrifted" (added in unit 4; see The Improvement).
- **If the outfit is empty:** Skips the model call and returns `"No fit card: there was no outfit suggestion to write about for <title>."` This also applies to text containing only spaces.

## Planning Loop

**Branch rule:** If `search_listings` returns `[]`, the agent saves a message in `session["error"]` explaining the search filters and what to loosen. It then stops without calling the other tools.

If listings are found, it saves the first result in `session["selected_item"]`, calls `suggest_outfit`, and then calls `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is read:** `parse_query` in `agent.py` uses regular expressions to find the price and size. It recognizes price phrases such as `under $30`, `below $30`, `less than $30`, `max $30`, and `up to $30`, or just `$30`. It reads sizes from `size X`. After removing these parts, the remaining text becomes the description.

**Session flow:**

`query` → `parsed` → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`

`parsed` stores the description, size, and maximum price. Each tool gets its inputs from the session. The `error` field is set only when the agent stops early.

---

## Sample Run

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

### Moment 1: Filtering listings by size

- **What I asked:** I asked Claude to help me write the function `search_listings` so sizes matched whole parts of a listing's size, because the original function I wrote wasn't working a few errors.
- **What it returned:** The filter split sizes using slashes, spaces, and brackets, and removed `US`. I tested it with the data: searching for `platform sneakers` in size `8` returned only `lst_019` (`US 8`), not the `US 8.5` Chelsea boots. Size `S` also did not match `XS` or `US 9`.
- **What I changed:** I kept the size filter. However, searching for `graphic tee` under $30 included cargo pants in seventh place because of one shared word. I left that result because the agent uses only the top listing, and the first three results were tees. I rated criterion 1 as 4 out of 5 partly because keyword matching could select a weak result for a vague request.

### Moment 2: Reading the user's request

- **What I asked:** I asked Claude to help me write the function `parse_query` in `agent.py` to extract the price and size while keeping the item description, because the original function I wrote wasn't working a few errors as well.
- **What it returned:** It worked for all six example queries, but `looking for a vintage graphic tee under $30` left an extra `a` in the description. An attempted fix using `sed` made no change, and that version was committed.
- **What I changed:** I tested the function again, found the extra `a`, and updated the regex directly by adding `(?:an?\s+|some\s+)?` after `looking for`. I committed the fix separately. This taught me to check the result after every edit instead of assuming the change worked.


### Moment 3 (unit 4): Catching a typo in my own criterion

- **What I asked:** I asked Claude Code to move `search_listings` onto MCP, add the trace and the failure handlers, then run my five criteria five times and score them against `criteria.md`.
- **What it returned:** The MCP move, trace and handlers worked first time. When it scored criterion 4 it noticed that all five fit cards said `poshmark` and that my criterion required `depop`. It checked `data/listings.json`: the only denim jacket under $50 is `lst_007`, $42 on poshmark. It also noticed that "different first sentences" passed while 23 of 25 cards opened "Scored this".
- **What I changed:** I kept the original criterion untouched and wrote the revision underneath it with the reason, and reported the as-written verdict (MISSED) next to the revised one rather than only the flattering one. I then made one change to the fit-card prompt and re-ran everything.

### Moment 4 (unit 4): A scorer that failed for the wrong reason

- **What I asked:** I had Claude Code write `scorer.py`, because `run_eval.py` leaves PASS/FAIL blank.
- **What it returned:** The first scorer reported criterion 2 as 0 of 5, even though the log showed all five tries stopping early. The cause was the scorer searching the whole trace for `suggest_outfit`, which also appears in the branch note "`suggest_outfit` … NOT called".
- **What I changed:** I did not accept 0 of 5. I read the session and the step list, saw the branch had worked, and changed the check to match step names only, then re-scored the same log. The lesson is the same as moment 2: check the output after the change rather than assuming it, and a number that disagrees with the log is the scorer's problem until shown otherwise.



<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

`python run_eval.py --label before`, then `python scorer.py before`. Six scenarios
× five tries, caching off, 2 model calls per completed run. Logs:
[results/run_2026-10-11_2123_before.md](results/run_2026-10-11_2123_before.md)
(raw answers and traces), [results/run_2026-10-11_2123_before.json](results/run_2026-10-11_2123_before.json)
(sessions and the prompts each tool was sent) and
[results/scored_before.md](results/scored_before.md) (the table below, per-try detail).

`run_eval.py` leaves PASS/FAIL blank, so I wrote `scorer.py`: each check is the
sentence from `criteria.md` it is named after, applied the same way to every
try. Criterion 5 has two halves that run as separate scenarios; a try-cell is
PASS only if both halves passed in that try.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query runs all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | **MET** (5/5) |
| 2. A query with no matches stops early | 5 of 5 | PASS | PASS | PASS | PASS | PASS | **MET** (5/5) |
| 3. All tools use the same selected item | 5 of 5 | PASS | PASS | PASS | PASS | PASS | **MET** (5/5) |
| 4. Fit card: `$42`, `depop`, ≤4 sentences, 5 different first sentences — *as written* | 4 of 5 | FAIL | FAIL | FAIL | FAIL | FAIL | **MISSED** (0/5) |
| 4. Same, *as revised in criteria.md*: `poshmark`, 5 distinct first-four-word openers | 4 of 5 | PASS | PASS | PASS | PASS | PASS | **MISSED** (cards 5/5, openers not distinct) |
| 5. Within $30 (5 of 5) and empty wardrobe gets advice (4 of 5) | 5 of 5 / 4 of 5 | PASS | PASS | PASS | PASS | PASS | **MET** (5/5, 5/5) |

Criterion 4 appears twice because I revised it *after* seeing these results
(reasons are in `criteria.md`, under the original, which is untouched). The
as-written row is the one that counts as my verdict against what I wrote last
unit; the revised row is what I will improve against.

**Real output from one try**, `agent.py::run_agent` → `tools.py::create_fit_card`,
as recorded by `run_eval.py::run_once` for the scenario `denim jacket under $50`
(five cards, caching off):

```
try 1: Scored this vintage cropped Wrangler denim jacket for $42 on poshmark and it instantly elevated my streetwear game. Double denim with baggy jeans and fresh white sneakers makes for the ultimate effortless weekend fit. Layering it over an oversized crewneck with khaki trousers brings the exact proportions I was going for. 🧥

try 2: Scored this vintage Wrangler denim jacket on poshmark for only $42 and it instantly elevates any streetwear fit. Throwing it on over baggy jeans or wide-leg trousers gives the ultimate effortless look. Finding pieces like this makes thrifting too addictive 🧥

try 3: Scored this vintage Wrangler denim jacket on poshmark for only $42 and it is the ultimate streetwear staple. Threw it over an oversized grey crewneck with khaki trousers and combat boots for that perfect slouchy silhouette. It adds just the right amount of structure to all those loose layers. 🧥

try 4: Scored this vintage Wrangler denim jacket for just $42 on poshmark and it instantly leveled up my double-denim streetwear game. The cropped fit makes it super easy to style with baggy jeans and chunky sneakers for that effortless off-duty look 🧥

try 5: Scored this cropped Wrangler denim jacket for $42 on poshmark and it instantly leveled up my double-denim game. The light wash gives it that perfectly worn-in streetwear edge. Total wardrobe staple.
```

Criterion 2, `agent.py::run_agent` for `designer ballgown size XXS under $5`
(`session["error"]`; `outfit_suggestion` and `fit_card` were `None` and no
prompt was sent, in all five tries):

```
No listings matched "designer ballgown", size XXS, under $5. Try to drop the size, or raise the price ceiling, or use broader words (e.g. 'jacket' instead of a specific style).
```

Criterion 3, the fit-card prompt `tools.py::create_fit_card` actually sent
(first 8 lines, try 1 of `vintage graphic tee under $30`) — the selected item's
title is in it, and it matched `search_results[0]["id"]` in 5 of 5 tries:

```
The find:
Title: Graphic Tee — 2003 Tour Bootleg Style
Category: tops
Colors: black
Style: graphic tee, vintage, grunge, streetwear, band tee
Size: L  Condition: good
Price: $24 on depop

```

Criterion 5, empty wardrobe, `tools.py::suggest_outfit` (first 280 characters, try 1):

```
Since I don't know the rest of your closet yet, here are two versatile ways to style your cool new Wrangler jacket! 

First, try a casual streetwear look by layering it over a simple white baby tee and pairing it with high-waisted black wide-leg trousers and chunky sneakers. Fini…
```

---

## Verdicts and Diagnoses

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | A matching query runs all three tools | 4 of 5 | **MET** | 5 of 5 tries had `search_listings (via MCP)`, `suggest_outfit` and `create_fit_card` in the trace and a non-empty fit card. The target allowed one service failure and none happened. |
| 2 | A no-match query stops early | 5 of 5 | **MET** | 5 of 5 tries: error message with something to change, no `suggest_outfit`/`create_fit_card` step, and zero prompts sent. |
| 3 | All tools use the same item | 5 of 5 | **MET** | 5 of 5: `selected_item.id == search_results[0].id`, and the title was in both model prompts (2/2 in every try). |
| 4 | Fit card detail and variety | 4 of 5 + 5 different | **MISSED as written** | 0 of 5 cards mention `depop`. All five say `poshmark`, which is correct. The "5 different first sentences" half did pass, on the letter. |
| 5 | Within budget; empty wardrobe advice | 5 of 5 / 4 of 5 | **MET** | Largest result price was $26 in all five tries; the empty-wardrobe run returned an outfit and a fit card 5 of 5 times. |

**Diagnoses**

**Criterion 4, as written (0 of 5) — the miss is in the criterion, not the system.**
This is not one of the four places a run can go wrong (a tool, the loop's
branch, the session, the model's output). The only denim jacket under $50 in
`data/listings.json` is `lst_007`, $42 on poshmark. I wrote `depop` in last
unit's criterion. Every card correctly said poshmark and every one failed my
check. I'm not calling this a pass: against what I wrote, it is MISSED. But no
fix to the agent could make it pass, so I revised the criterion rather than
the code, and said so under the original in `criteria.md`.

**Criterion 4, as revised (openers not distinct) — the model's output, caused by the `create_fit_card` prompt.**
23 of the 25 fit cards across the whole run open with "Scored this" (one
"Found this", one "Score this"). In the denim-jacket scenario, three of the
five cards open with the same first four words, "Scored this vintage Wrangler".
The tool works: price, platform and length were all right in 5 of 5. The
mechanism I believe is this: `create_fit_card`'s prompt has exactly one
instruction about openings, `Don't open with 'Just' or 'Obsessed'`, which bans
two words and names no alternative, so the model takes the next most likely
opener. Temperature is 0.9, so this isn't the 0.0 case from `config.py`; the
prompt itself leaves the opening to a single high-probability choice. The
"after" run below tests that explanation.

**Not misses, but worth saying plainly.**
- Criterion 4's "different first sentences" passed 5 of 5 while the cards were
  near-duplicates. That is the criterion's measurement problem (revised), not a
  success of the system.
- Criteria 1 and 5 allow one service failure in five, and none happened. The
  free-tier rate limit paused the run (`[rate limit] 15 requests used this
  minute`) but never failed a call, so I have no evidence about how criterion
  1 behaves when the model does fail. Both are bounded by one run of five.
- My first scorer marked criterion 2 as 0 of 5. That was my bug (it matched the
  word `suggest_outfit` inside the trace *note* "…NOT called"), not the agent;
  the log was always showing the branch working. Fixed to match step names and
  re-scored the same log. Noted here because a criterion that "fails" for the
  wrong reason is exactly what happened with criterion 4's `depop`.

---

## Loop Trace

`python app.py ask '...' --trace`. The `search_listings (via MCP)` step is the
call that goes over `mcp_client.call_tool` to `mcp_server.py`; the other two
tools are still called directly.

**Happy path** (`AI201_CACHE=0`, so both model calls are real)

```
[1] parse_query
      in:  'vintage graphic tee under $30'
      out: description='vintage graphic tee', size=None, max_price=30.0
[2] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey, Y2K Baby Tee — Butterfly Print … +7 more
      →    selected first result: lst_006
[3] suggest_outfit
      in:  Graphic Tee — 2003 Tour Bootleg Style, 10 wardrobe items
      out: Hey there! What an awesome find, that 2003 tour graphic tee is so cool and versatile.   For your first outfit,…
[4] create_fit_card
      in:  outfit text + Graphic Tee — 2003 Tour Bootleg Style
      out: Scored this 2003 tour graphic tee for only $24 on depop and it is already doing heavy lifting for my grungy st…
```

**Empty search** — visibly shorter: two steps, then the branch stops the loop
and neither model tool is called (0 model calls):

```
[1] parse_query
      in:  'purple unicorn onesie size XXS under $3'
      out: description='purple unicorn onesie', size='XXS', max_price=3.0
[2] search_listings (via MCP)
      in:  description='purple unicorn onesie', size='XXS', max_price=3.0
      out: [] (empty)
      →    branch: empty — stopping, suggest_outfit and create_fit_card are NOT called
```

### Three failures, triggered on purpose

| # | Failure | How I triggered it | What the user saw before | What the user sees now |
|---|---|---|---|---|
| 1 | Empty search | `ask 'purple unicorn onesie size XXS under $3'` | Already handled (the branch) | Unchanged: a message naming what was searched and what to loosen, 0 model calls |
| 2 | Empty wardrobe | `ask 'denim jacket under $50' --empty-wardrobe` | No crash, but silent: nothing told the user the outfit was generic (only the model's own wording) | A `Note:` line saying the wardrobe is empty and the outfit is general advice; trace says `wardrobe empty: general advice` |
| 3 | Model unavailable | `GEMINI_API_KEY=<broken> ask 'corduroy blazer under $60'` (new query, so not cached) | `ModelUnavailable` raised out of `run_agent`, loop crashed, listing lost; `run_eval.py` would log a crash | The found listing, plus "The model isn't available… Check GEMINI_API_KEY…" and the trace stops at `suggest_outfit — ModelUnavailable` |

I overrode `GEMINI_API_KEY` in the environment for failure 3 instead of editing
`.env`: `config.py` loads `.env` without overriding an existing variable, so it
is the same broken key reaching the same call, and my real key was never
touched. The empty-wardrobe and broken-key runs, as printed (the empty search is the trace above):

```
$ python app.py ask 'denim jacket under $50' --empty-wardrobe --trace
(running with an empty wardrobe)
[1] parse_query
      in:  'denim jacket under $50'
      out: description='denim jacket', size=None, max_price=50.0
[2] search_listings (via MCP)
      in:  description='denim jacket', size=None, max_price=50.0
      out: 7 items: Denim Jacket — Light Wash, Cropped, High-Waisted Denim Shorts — Cutoff, Denim Vest — Medium Wash, Studded … +4 more
      →    selected first result: lst_007
[3] suggest_outfit
      in:  Denim Jacket — Light Wash, Cropped, 0 wardrobe items
      out: Since I don’t know your closet yet, here are two fun ways to style your cool new Wrangler jacket!   First, try…
      →    wardrobe empty: general advice
[4] create_fit_card
      in:  outfit text + Denim Jacket — Light Wash, Cropped
      out: Scored this vintage Wrangler denim jacket on Poshmark for only $42 and the light wash is absolute perfection. …

  Found:    Denim Jacket — Light Wash, Cropped — $42.0 on poshmark

  Note:     Your wardrobe is empty, so these outfit ideas are general styling advice, not built from clothes you own. Add wardrobe items to get outfits that use them.

  Outfit:   Since I don’t know your closet yet, here are two fun ways to style your cool new Wrangler jacket! 

First, try a casual streetwear look by layering it over an oversized graphic tee, paired with high-waisted black biker shorts and chunky white sneakers. Finish with a canvas tote bag. This works because the light wash denim contrasts nicely with black, and the cropped fit balances the longer tee.

Second, go for a retro vibe by wearing it with a floral midi dress and canvas sneakers, accented with a simple bucket hat. This combo works because the rugged denim instantly tones down the sweetness of the dress for an effortless, balanced outfit.

  Fit card: Scored this vintage Wrangler denim jacket on Poshmark for only $42 and the light wash is absolute perfection. Threw it over an oversized graphic tee and biker shorts for the ultimate casual streetwear fit. Such a good find. 🧥
```

```
[1] parse_query
      in:  'corduroy blazer under $60'
      out: description='corduroy blazer', size=None, max_price=60.0
[2] search_listings (via MCP)
      in:  description='corduroy blazer', size=None, max_price=60.0
      out: 3 items: Vintage Linen Blazer — Cream, Velvet Blazer — Emerald Green, Corduroy Wide-Leg Pants — Rust
      →    selected first result: lst_018
[3] suggest_outfit
      in:  Vintage Linen Blazer — Cream, 10 wardrobe items
      →    ModelUnavailable — stopping

  Found:    Vintage Linen Blazer — Cream — $38.0 on thredUp

  The model isn't available, so the outfit and fit card could not be written. Your search worked: the listing above is the best match it found. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. Fix that and run the query again.
```

`generate.py` also raises a plain `RuntimeError` after repeated rate-limit
retries; `run_agent` now catches that around the two model steps too and says
"the model is busy, wait about a minute". I did not trigger that path on
purpose (it needs the free tier to refuse five retries in a row), so it is
handled but untested.

**On the MCP move:** `search_listings` is registered in `mcp_server.py` with its
typed inputs (`description: str`, `size: str | None`, `max_price: float | None`)
and a description written for a reader who cannot see the code, including the
size-matching rule and the empty case. `run_agent()` calls
`mcp_client.call_tool("search_listings", {...})` instead of the function.
Nothing behaved differently: the MCP result equals the direct call
(`call_tool(...) == search_listings(...)` was `True` for `graphic tee` under
$30, and an empty search came back as `[]`, not `None`, so the branch still
fires). The one thing I did notice is cost: each call starts and stops the
server process, which is visible as a short pause in `run_eval.py`.
`python mcp_client.py` lists the tool with its schema.

---

## The Improvement

**What I changed:** One change to one prompt, in `tools.py::create_fit_card`.
Each call now picks one of six opening angles at random (`_OPENING_ANGLES`: how
it feels to wear, where you'd wear it, the price as a pleasant surprise, a
question to the reader, the colour or texture, the piece it pairs with) and
puts it in the prompt, and the old ban on `'Just'`/`'Obsessed'` became a ban on
`'Scored'`, `'Found'`, `'Just'`, `'Obsessed'` and `'Thrifted'`. The tool's
signature, return shape and empty-outfit guard are unchanged. Commit
`create_fit_card: ask for a different opening angle per call, ban 'Scored'`.

**Which failure it was meant to fix:** Criterion 4 as revised, the
distinct-openers half: 23 of 25 cards opened "Scored this", and three of the
five denim-jacket cards shared their first four words. My diagnosis was that
the prompt's only instruction about openings banned two words and named no
alternative, so the model took the next most likely opener. Asking for a
specific, varying angle, and banning the actual common opener, tests that
explanation directly.

### Run Log — After

`python run_eval.py --label after`, then `python scorer.py after`. Same six
scenarios, same five tries, caching off. Logs:
[results/run_2026-10-11_2129_after.md](results/run_2026-10-11_2129_after.md),
[results/run_2026-10-11_2129_after.json](results/run_2026-10-11_2129_after.json),
[results/scored_after.md](results/scored_after.md).

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query runs all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | **MET** (5/5) |
| 2. A query with no matches stops early | 5 of 5 | PASS | PASS | PASS | PASS | PASS | **MET** (5/5) |
| 3. All tools use the same selected item | 5 of 5 | PASS | PASS | PASS | PASS | PASS | **MET** (5/5) |
| 4. *As written* (`depop`) | 4 of 5 | FAIL | FAIL | FAIL | FAIL | FAIL | **MISSED** (0/5) |
| 4. *As revised* (`poshmark`, distinct 4-word openers) | 4 of 5 | PASS | PASS | PASS | PASS | PASS | **MET** (5/5, openers distinct) |
| 5. Within $30 (5 of 5) and empty wardrobe advice (4 of 5) | 5 of 5 / 4 of 5 | PASS | PASS | PASS | PASS | PASS | **MET** (5/5, 5/5) |

**Before and after, side by side**

| Measure | Before | After |
|---|---|---|
| 1. Three tools + fit card | 5/5 MET | 5/5 MET |
| 2. No-match stops early | 5/5 MET | 5/5 MET |
| 3. Same item everywhere | 5/5 MET | 5/5 MET |
| 4. As written (`depop`) | 0/5 MISSED | 0/5 MISSED |
| 4. As revised: cards with `$42`, `poshmark`, ≤4 sentences | 5/5 | 5/5 |
| 4. As revised: five distinct first-four-word openers | **No** (3 cards open "Scored this vintage Wrangler") | **Yes** |
| 4. As revised, verdict | **MISSED** | **MET** |
| 5. Budget (5/5) and empty wardrobe (4/5) | 5/5, 5/5 MET | 5/5, 5/5 MET |
| Cards opening with "Scored" (all 25 fit cards in the run) | 23 of 25 | 0 of 25 |
| Distinct two-word openers (all 25 cards) | 3 | 18 |
| Price written as `$N` (all 25 cards) | 25 of 25 | 25 of 25 |
| Longest card, in sentences | 4 | 4 |

The five denim-jacket cards after the change (`results/run_2026-10-11_2129_after.md`):

```
try 1: Farmers market mornings call for throwing on this vintage Wrangler denim jacket. Snagged it on Poshmark for $42 and it completes the ultimate double-denim streetwear fit. Ready to live in this all season long 🧥

try 2: $42 for this vintage Wrangler denim jacket on poshmark was an absolute steal. It adds the ultimate laid-back streetwear vibe when paired with a white tank and chunky sneakers. 🧥

try 3: Coffee runs and weekend thrift markets are calling for this exact streetwear fit. Snagged this vintage Wrangler denim jacket on poshmark for only $42 and it immediately brought the whole double-denim look together. The cropped wash makes it super easy to style with baggy jeans or wide-leg trousers. 👖

try 4: Are we feeling the double denim today? Snagged this vintage Wrangler jacket on Poshmark for $42 and it completely nails that effortless streetwear vibe. Paired it with baggy jeans and chunky sneakers for the ultimate casual look.

try 5: Light-wash denim makes this cropped Wrangler jacket the ultimate streetwear piece for throwing over a simple tank and baggy jeans. Snagged this vintage gem on poshmark for only $42.
```

**Did it help, and how do I know:** Yes, on the thing it was aimed at, and it
did not break anything I could measure. The revised criterion 4 went from
MISSED to MET because the openers are now distinct; across all 25 cards the
"Scored this" opener went from 23 to 0 and the distinct two-word openers from 3
to 18, while `$42` stayed written as `$42` in 25 of 25 cards and no card passed
four sentences. Criteria 1, 2, 3 and 5 did not move, which is what a change
confined to one prompt should do.

What it did **not** do, and could not: criterion 4 *as written* is still
MISSED at 0 of 5, because a correct card says poshmark and the criterion says
depop. No prompt change fixes a typo in a criterion. That verdict is the one I
am reporting against last unit's wording.

Caveats on the measurement, so it isn't oversold:
- It is one run of five. The angle is random, so a different run could still
  put two cards in the same opener by chance. The 23-to-0 change is strong
  evidence the template opener is gone; "distinct 4-word openers in 5 of 5" is
  one sample of a random process, not a guarantee.
- The angle chosen is not written to the log, so I can't say which angles did
  the work. I only checked that the output varies, not that one angle is better.
- Before the full run I looked at three throwaway cards on the same item and
  one wrote the price out as "Forty-two dollars". I did not tune for it before
  measuring. It did not recur in 25 cards, but "the price as a pleasant
  surprise" is the angle most likely to cause it again.
- Two graphic-tee cards (criterion 1, tries 1 and 2) still start "Putting on
  this". They differ by the fourth word, so the revised check would pass them,
  but a reader would call that a repeat. The variety check only scores the
  denim-jacket scenario.

---

## What's Still Broken

- **Criterion 4 as written is MISSED and stays MISSED.** It is a wrong value in
  my criterion, not a defect in FitFindr. I corrected it under the original
  instead of editing it, so both verdicts are on the record. Next time I'd check
  the expected value against `data/listings.json` before writing it down; that
  is a five-second grep I didn't do. I stopped here because there is nothing
  left to fix in the system for this half.
- **Search ranking picks the wrong first result for some queries, and the agent
  always uses the first result.** `corduroy blazer under $60` returned the
  "Vintage Linen Blazer — Cream" first and the corduroy item (pants) third:
  `search_listings` scores by shared words, so matching only "blazer" beats the
  closer-but-differently-categorised item, and `selected_item` is just
  `search_results[0]`. None of my five criteria checks relevance (criterion 3
  only checks that the same item is used consistently), so every verdict above
  would still be MET with a poor first pick. Next I would write a criterion
  about the selected item matching what was asked for, and then change either
  the scoring or the selection rule. I did not touch it because the unit asks
  for one measured fix and I'd already spent mine.
- **Only one tool is on MCP, and each call starts a new server process.** That
  is by design this unit, and it is slow enough to see in `run_eval.py`. The
  agent also has no fallback: if the MCP server can't start, the run stops with
  an error message instead of calling the function directly. I chose the
  message because a silent fallback would hide a broken server; whether that is
  the right trade is something I'd decide by how the server is used.
- **The rate-limit failure path is handled but never triggered.** The
  `RuntimeError` after repeated 429s is caught around both model steps, and the
  message was written, but I did not reproduce it. Treat it as untested code.
- **Criteria 1 and 5 allowed one service failure in five and I never saw one.**
  Five-for-five means I have no evidence about how they behave when the model
  fails mid-run (other than the broken-key test, which fails at the first model
  call). A harder test would inject a failure on the second model call, to see
  whether the fit card step recovers.
- **Variety is only scored on one item.** The graphic-tee cards still repeat
  "Putting on this" in two tries. Next I'd run the opener check on every
  scenario that produces cards and log the chosen angle.

---

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
