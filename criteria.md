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

## 1. A matching query runs all three tools

When a query matches at least one listing, the agent
runs all three tools and returns a fit card in at least 4 out of 5 tries.

**Why this target:**
The search gives consistent results, but two tools depend on a hosted model. 
A timeout, rate limit, or empty response could cause a run to fail. 
This target allows one service issue while still checking that the agent works.

---

## 2. A query with no matches stops early

When a query matches no listings, the agent stops before calling `suggest_outfit`. 
It returns a message explaining what the user can change in all 5 tries.

**Why this target:**
This path does not use the model. A $5 budget gives no results because the cheapest
 listing costs $12. The agent should always recognize the empty results and stop.

---

## 3. All tools use the same selected item

For `vintage graphic tee under $30`, the selected item's ID must match the first search result's ID:

`session["selected_item"]["id"] == session["search_results"][0]["id"]`

The selected item's title must also appear in the outfit prompt and the fit card's input. 
These checks must pass in all 5 tries.

**Why this target:**
The code passes the selected item between tools through the session dictionary. 
If a later tool receives a different item, there is a bug in how the agent passes the data.

---

## 4. The fit card describes the item and has variety

Run `denim jacket under $50` five times with caching off. At least 4 out of 5 fit cards must:

- Include the price as `$42`.
- Mention `depop`.
- Have no more than 4 sentences.

All five cards must have different first sentences.

**Why this target:**
The model may occasionally leave out a detail, so one card can miss the content
requirements. Different opening sentences help check that the captions have variety when caching is off.

---

## 5. Results stay within budget, and an empty wardrobe still gets advice

For `vintage graphic tee under $30`, every search result must cost $30 or less in all 5 tries.

For `denim jacket under $50` with `--empty-wardrobe`,
the agent must return a non-empty outfit suggestion and
a fit card in at least 4 out of 5 tries.

**Why this target:**

The price filter runs in Python, so it should always keep results within budget.
Styling advice for an empty wardrobe still depends on the model, so this target allows one service issue.

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
