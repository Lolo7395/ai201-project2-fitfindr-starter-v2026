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
