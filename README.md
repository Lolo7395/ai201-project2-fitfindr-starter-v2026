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
× five tries, caching off, 2 model calls per completed run. 

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

First, try a casual streetwear look by layering it over a simple white baby tee and pairing it with high-waisted black 
wide-leg trousers and chunky sneakers. Fini…
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

**Criterion 4, as written (0 out of 5): The mistake was in the criterion.**

The only denim jacket under $50 in `data/listings.json` is `lst_007`, priced at $42 on `poshmark`.
 I accidentally wrote `depop` in last unit’s criterion. Every caption correctly said `poshmark`, 
 but failed my check because I had the wrong expected platform.

I am still reporting this as MISSED based on the original wording. The agent did not need a fix, 
so I corrected the criterion and explained the change below the original in `criteria.md`.

**Criterion 4, as revised: The captions had repeated openings.**

Across the 25 fit cards, 23 started with “Scored this,” one with “Found this,” and one with “Score this.”
 In the denim-jacket test, three of the five captions began with the same four words: “Scored this vintage Wrangler.”
  All five had the correct price, platform, and length, but the openings lacked variety.

I believe the prompt caused this repetition. Its only instruction about openings was `Don't open with 'Just' or 'Obsessed'`.
 It banned two words without suggesting other ways to begin, so the model kept choosing a familiar opening.
  The temperature was already 0.9, rather than the 0.0 setting in `config.py`. The next test checks whether changing the prompt improves the variety.

**Other testing limits and mistakes:**

- The original “different first sentences” check passed all five captions, even though they sounded almost identical.
 The check was too broad to catch the repetition, so I revised it.

- Criteria 1 and 5 allowed one service failure in five tries, but none occurred. The free-tier rate limit paused the run with `[rate limit] 15 requests used this minute`, but no call failed. These results show what worked in one batch of five; they do not show how the agent handles a model failure during a run.

- My first scoring script incorrectly marked Criterion 2 as 0 out of 5. It found `suggest_outfit` in a trace note saying the tool was “NOT called” and counted it as a call. The log showed that the agent stopped correctly. I fixed the scorer to check step names and scored the same log again. Like the wrong platform in Criterion 4, this was a testing mistake rather than an agent failure.

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
`generate.py` raises a `RuntimeError` if the model keeps hitting the rate limit after several retries. `run_agent` now catches this error during both model steps and tells the user, “The model is busy, wait about a minute.” I did not deliberately trigger this because it requires the free tier to reject five retries in a row. The error handling is in place, but it is still untested.

**Moving the search tool to MCP:** I registered `search_listings` in `mcp_server.py` with its input types: `description: str`, `size: str | None`, and `max_price: float | None`. Its description explains what the tool does, how sizes match, and what it returns when nothing is found, so someone can understand it without reading the code.

`run_agent()` now uses `mcp_client.call_tool("search_listings", {...})` instead of calling the function directly. In my checks, both methods returned the same results for `graphic tee` under $30. A search with no matches still returned `[]`, so the agent’s early-stop rule continued to work.

The main difference I noticed was a short delay in `run_eval.py`, because each call starts and stops the server process. Running `python mcp_client.py` also lists the tool and its input schema.
---

## The Improvement

**What I changed:** I updated the prompt in `tools.py::create_fit_card` to encourage more variety in the captions. 
Each call randomly chooses one of six opening ideas: how the item feels to wear, where you would wear it, 
its surprisingly good price, a question for the reader, its color or texture, or what you would pair it with.
I also expanded the banned opening words from “Just” and “Obsessed” to include “Scored,” “Found,” and “Thrifted.” 
 The tool’s inputs, output format, and handling of empty outfits stayed the same.

**Commit:** `create_fit_card: ask for a different opening angle per call, ban 'Scored'`

**Which failure it was meant to fix:** This change focused on the different-opening requirement in Criterion 4. 
During testing, 23 of 25 captions started with “Scored this,” and three of the five denim-jacket captions had the same first four words.
I thought this happened because the prompt banned two opening words without suggesting other ways to begin.
Giving the model a different opening idea each time and banning the repeated words lets me test whether that was the cause.

### Run Log — After

`python run_eval.py --label after`, then `python scorer.py after`. Same six
scenarios, same five tries, caching off.

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

**Did it help, and how do I know:** Yes, the change improved the caption openings without affecting the other results I checked.
 The revised Criterion 4 went from MISSED to MET because the openings were different. 
 Across all 25 captions, “Scored this” went from appearing 23 times to zero, and the number of different two-word openings increased from 3 to 18. All 25 captions still used `$42`, and none had more than four sentences. Criteria 1, 2, 3, and 5 stayed the same, which makes sense because I only changed one prompt.

**What it did not fix:** Criterion 4, as originally written, still scored 0 out of 5 and remains MISSED.
The correct platform is `poshmark`, but the criterion requires `depop`. Changing the prompt would not fix that mistake in the criterion. I am reporting the original result based on last unit’s wording.

**Limits of the results:**

- This was one batch of five runs. Since the opening idea is chosen randomly, another batch could still have repeated openings. The drop from 23 “Scored this” openings to zero shows a clear improvement, but five different four-word openings in one batch does not guarantee the same result every time.
- The chosen opening idea is not saved in the log, so I cannot tell which ideas helped most. I checked whether the captions varied, not whether one idea worked better than another.
- Before the full test, I checked three trial captions for the same item. One wrote the price as “Forty-two dollars.” I did not adjust the prompt before testing, and this did not happen in the 25 measured captions. Still, the idea about a surprisingly good price could lead to that wording again.
- Two graphic-tee captions in Criterion 1, tries 1 and 2, still began with “Putting on this.” They differed by the fourth word, so they would pass the revised check, but they still sound repetitive to a reader. The variety check only covers the denim-jacket captions.

---

## What's Still Broken

- **Criterion 4 still counts as MISSED under the original wording.** The mistake was in my expected value, not in FitFindr. 
I added the correction below the original criterion so both results are recorded. Next time, 
I would check `data/listings.json` before writing the expected value. I stopped here because this part did not need a system change.

- **The search can put a poor match first, and the agent always chooses it.** For `corduroy blazer under $60`, the first result was “Vintage Linen Blazer — Cream,” while the corduroy pants came third. The search ranks items by shared words rather than fully understanding the request. None of my five criteria checks whether the selected item is relevant; Criterion 3 only checks that the tools use the same item. This means the tests could pass even with a poor recommendation. Next, I would add a relevance check and improve the ranking or selection rule. I left this unchanged because the unit asked for one measured fix, which I had already completed.

- **Only one tool uses MCP, and every call starts a new server process.** This was part of the unit’s design, 
but the delay is noticeable in `run_eval.py`. If the server cannot start, the agent returns an error instead of calling the function directly.
 I chose this approach so a broken server would be visible. Whether to add a fallback would depend on how the system is used.

- **The rate-limit handling is still untested.** Both model steps catch the `RuntimeError` 
raised after repeated 429 rate-limit responses and return a message. However, I did not trigger this during testing, so I cannot confirm that it works.

- **I did not see the service failures allowed by Criteria 1 and 5.** Both passed all five tries, so these tests do not show what happens
if the model fails partway through a run. The broken-key test only checks failure at the first model call.
 Next, I would force a failure during the second model call to check how the fit card step handles it.

- **The variety check only covers one item.** Two graphic-tee captions still started with “Putting on this.”
 Next, I would check caption openings across every scenario that produces a fit card and record which opening idea was chosen.

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
