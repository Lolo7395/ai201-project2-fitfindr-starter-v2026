"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import config  # noqa: F401 — you'll use this in search_listings
from generate import generate
from utils.data_loader import load_listings

import re

# Words that say nothing about the item. Left in, "looking for a tee" would
# score every listing whose description happens to contain "a" or "for".
_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "in", "on", "of", "with", "to",
    "i", "im", "i'm", "me", "my", "want", "need", "looking", "some", "any",
    "something", "size", "under", "below", "less", "than", "max", "up",
}


def _words(text: str) -> list[str]:
    """Lowercase words, with a trailing plural 's' dropped ("jeans" -> "jean")."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words]


def _size_parts(size: str) -> set[str]:
    """
    "S/M" -> {"S", "M"}; "US 8.5" -> {"8.5"}; "XL (oversized)" -> {"XL", "OVERSIZED"}.
    Whole parts only, so "S" never matches "XS" or "US 9".
    """
    parts = re.split(r"[\s/(),]+", size.upper())
    return {p for p in parts if p and p not in {"US", "SIZE"}}


def _size_matches(wanted: str, listing_size: str) -> bool:
    if "ONE SIZE" in listing_size.upper():
        return True
    wanted_parts = _size_parts(wanted)
    return bool(wanted_parts) and wanted_parts <= _size_parts(listing_size)


def _score(listing: dict, query_words: list[str], description: str) -> int:
    """Keyword overlap, weighted toward the fields that describe what the item IS."""
    title = set(_words(listing["title"]))
    tags = set(_words(" ".join(listing["style_tags"])))
    category = set(_words(listing["category"]))
    colors = set(_words(" ".join(listing["colors"])))
    brand = set(_words(listing["brand"] or ""))
    body = set(_words(listing["description"]))

    score = 0
    for word in query_words:
        if word in title:
            score += 3
        if word in tags or word in category:
            score += 2
        if word in colors or word in brand:
            score += 1
        if word in body:
            score += 1
    # A multi-word tag the user typed in full ("graphic tee", "band tee").
    for tag in listing["style_tags"]:
        if " " in tag and tag in description.lower():
            score += 2
    return score


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """


    query_words = [w for w in _words(description or "") if w not in _STOPWORDS]
    if not query_words:
        return []

    scored = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size and not _size_matches(size, listing["size"]):
            continue
        score = _score(listing, query_words, description)
        if score > 0:
            scored.append((score, listing))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """


    item_text = _describe_item(new_item)
    items = (wardrobe or {}).get("items") or []

    system = (
        "You are a friendly personal stylist. Answer in plain text, no markdown "
        "headings, under 120 words."
    )

    if not items:
        prompt = (
            f"Someone just thrifted this item:\n{item_text}\n\n"
            "They haven't told you what's in their wardrobe. Start by saying in "
            "one short sentence that you don't know their wardrobe yet, then give "
            "two outfit ideas for this item, naming the kinds of pieces to pair "
            "it with (bottoms or top, shoes, one accessory) and why they work."
        )
    else:
        closet = "\n".join(
            f"- {w['name']} ({w['category']}; colors: {', '.join(w['colors'])}; "
            f"style: {', '.join(w['style_tags'])})"
            + (f" — {w['notes']}" if w.get("notes") else "")
            for w in items
        )
        prompt = (
            f"Someone just thrifted this item:\n{item_text}\n\n"
            f"Here is what they already own:\n{closet}\n\n"
            "Suggest one or two complete outfits built around the new item. "
            "Use only pieces from their wardrobe list above, call each piece by "
            "its name from the list, and give one sentence on why each outfit works."
        )

    response = generate(prompt, system=system).strip()
    if response:
        return response
    return (
        f"Style the {new_item.get('title', 'item')} with simple basics that pick up its "
        f"{', '.join(new_item.get('colors') or ['main'])} tones, so it stays the focus."
    )


def _describe_item(item: dict) -> str:
    """The listing as a few lines of prompt text. Brand only when there is one."""
    lines = [
        f"Title: {item.get('title')}",
        f"Category: {item.get('category')}",
        f"Colors: {', '.join(item.get('colors') or [])}",
        f"Style: {', '.join(item.get('style_tags') or [])}",
        f"Size: {item.get('size')}  Condition: {item.get('condition')}",
        f"Price: ${item.get('price', 0):.0f} on {item.get('platform')}",
    ]
    if item.get("brand"):
        lines.insert(1, f"Brand: {item['brand']}")
    return "\n".join(lines)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """


    title = (new_item or {}).get("title", "this item")
    if not outfit or not outfit.strip():
        return f"No fit card: there was no outfit suggestion to write about for {title}."

    price = f"${new_item.get('price', 0):.0f}"
    platform = new_item.get("platform")
    system = (
        "You write short, casual Instagram/TikTok captions about thrift finds. "
        "Plain text, no hashtags block, at most one emoji."
    )
    prompt = (
        f"The find:\n{_describe_item(new_item)}\n\n"
        f"How it's being styled:\n{outfit}\n\n"
        "Write a 2 to 4 sentence caption the person would actually post about this "
        f"outfit. Mention the item, the price as {price}, and {platform} exactly once each. "
        "Be specific about the vibe of the outfit. Don't open with 'Just' or 'Obsessed'."
    )
    caption = generate(prompt, system=system).strip()
    return caption or f"Thrifted the {title} for {price} on {platform} and built a whole fit around it."
