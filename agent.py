"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import suggest_outfit, create_fit_card
from mcp_client import call_tool, MCPError
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
        "notice": None,              # a heads-up that doesn't stop the run
    }


# ── query parsing ─────────────────────────────────────────────────────────────

_PRICE = re.compile(
    r"(?:under|below|less than|max|up to|<)\s*\$?\s*(\d+(?:\.\d+)?)|\$(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_SIZE = re.compile(r"\b(?:in\s+)?size\s+([a-z0-9.]+(?:/[a-z0-9.]+)?)", re.IGNORECASE)


def parse_query(query: str) -> dict:
    """
    Regex parse: a price ceiling, a size, and whatever words are left over.

        "vintage graphic tee under $30, size M"
        -> {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}
    """
    text = query
    max_price = None
    price_match = _PRICE.search(text)
    if price_match:
        max_price = float(price_match.group(1) or price_match.group(2))
        text = text[: price_match.start()] + " " + text[price_match.end():]

    size = None
    size_match = _SIZE.search(text)
    if size_match:
        size = size_match.group(1).upper()
        text = text[: size_match.start()] + " " + text[size_match.end():]

    description = re.sub(r"^\s*(?:i'?m\s+)?(?:looking for|i want|find me|show me)\s+(?:an?\s+|some\s+)?", "", text, flags=re.IGNORECASE)
    description = re.sub(r"[,;]+", " ", description)
    description = re.sub(r"\s+", " ", description).strip()
    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """Say what was searched for and what to loosen — not just "no results"."""
    used = [f'"{parsed["description"]}"']
    tips = []
    if parsed["size"]:
        used.append(f"size {parsed['size']}")
        tips.append("drop the size")
    if parsed["max_price"] is not None:
        used.append(f"under ${parsed['max_price']:.0f}")
        tips.append("raise the price ceiling")
    tips.append("use broader words (e.g. 'jacket' instead of a specific style)")
    return (
        f"No listings matched {', '.join(used)}. Try to "
        + ", or ".join(tips)
        + "."
    )


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    steps = ["parse", "search", "suggest", "fit_card"]

    for count, step_name in enumerate(steps, 1):
        trace.check_iterations(count)

        if step_name == "parse":
            session["parsed"] = parse_query(session["query"])
            trace.step("parse_query", inputs=repr(session["query"]),
                       returned=_fmt(session["parsed"]))

        elif step_name == "search":
            parsed = session["parsed"]
            args = {
                "description": parsed["description"],
                "size": parsed["size"],
                "max_price": parsed["max_price"],
            }
            try:
                # search_listings now lives behind MCP: this spawns
                # mcp_server.py, calls the tool over stdio, and unwraps the
                # JSON back into the same list of dicts the direct call gave.
                session["search_results"] = call_tool("search_listings", args)
            except MCPError as exc:
                session["error"] = (
                    "Search is unavailable: couldn't reach the listings tool "
                    "(mcp_server.py). Check that `python mcp_server.py` starts "
                    "on its own, then try again.\n"
                    f"Detail: {str(exc).splitlines()[0]}"
                )
                trace.step("search_listings (via MCP)", inputs=_fmt(args),
                           note="MCPError — stopping, no tools after this")
                return session

            # The branch: nothing found means stop here, before any model call.
            if not session["search_results"]:
                session["error"] = _no_results_message(parsed)
                trace.step("search_listings (via MCP)", inputs=_fmt(args),
                           returned=session["search_results"],
                           note="branch: empty — stopping, suggest_outfit and "
                                "create_fit_card are NOT called")
                return session
            session["selected_item"] = session["search_results"][0]
            trace.step("search_listings (via MCP)", inputs=_fmt(args),
                       returned=session["search_results"],
                       note=f"selected first result: {session['selected_item']['id']}")

        elif step_name == "suggest":
            items = (session["wardrobe"] or {}).get("items") or []
            if not items:
                session["notice"] = (
                    "Your wardrobe is empty, so these outfit ideas are general "
                    "styling advice, not built from clothes you own. Add "
                    "wardrobe items to get outfits that use them."
                )
            try:
                session["outfit_suggestion"] = suggest_outfit(
                    session["selected_item"], session["wardrobe"]
                )
            except (ModelUnavailable, RuntimeError) as exc:
                session["error"] = _model_down_message(exc)
                trace.step("suggest_outfit",
                           inputs=f"{session['selected_item']['title']}, "
                                  f"{len(items)} wardrobe items",
                           note=f"{type(exc).__name__} — stopping")
                return session
            trace.step("suggest_outfit",
                       inputs=f"{session['selected_item']['title']}, "
                              f"{len(items)} wardrobe items",
                       returned=session["outfit_suggestion"],
                       note="wardrobe empty: general advice" if not items else "")

        elif step_name == "fit_card":
            try:
                session["fit_card"] = create_fit_card(
                    session["outfit_suggestion"], session["selected_item"]
                )
            except (ModelUnavailable, RuntimeError) as exc:
                session["error"] = _model_down_message(exc)
                trace.step("create_fit_card",
                           inputs=session["selected_item"]["title"],
                           note=f"{type(exc).__name__} — stopping")
                return session
            trace.step("create_fit_card",
                       inputs=f"outfit text + {session['selected_item']['title']}",
                       returned=session["fit_card"])

    return session


def _fmt(values: dict) -> str:
    """A dict as `key=value, ...` so the trace shows values, not just keys."""
    return ", ".join(f"{k}={v!r}" for k, v in values.items())


def _model_down_message(exc: Exception) -> str:
    """What the user sees when the model can't be reached. No stack trace."""
    if isinstance(exc, RuntimeError) and "rate limited" in str(exc).lower():
        return (
            "The model is busy right now (free-tier request limit). Your search "
            "worked, but the outfit and fit card could not be written. Wait "
            "about a minute and run the same query again."
        )
    return (
        "The model isn't available, so the outfit and fit card could not be "
        "written. Your search worked: the listing above is the best match "
        f"it found. {exc} Fix that and run the query again."
    )


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    if session["notice"]:
        print(f"  note:     {session['notice']}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
