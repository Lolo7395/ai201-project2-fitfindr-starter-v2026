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
