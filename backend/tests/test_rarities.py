"""Rarity config migration checks: live dicts refresh in place."""

from backend.core import rarities as cr


def test_apply_docs_refreshes_in_place():
    # Grab references like every consumer module holds.
    rarity_map = cr.RARITY_MAP
    sell_prices = cr.SELL_PRICES

    original_docs = cr._default_docs()
    cr._apply_docs(original_docs)
    assert rarity_map[1] == "⚪ Common"
    assert sell_prices["Celestial"] == 20000

    # Simulate an admin edit: Astral sell price doubled, plus a new rarity.
    edited = [dict(d) for d in original_docs]
    edited[-1]["sell_price"] = 80000
    edited.append({
        "_id": 26, "emoji": "🌸", "name": "Sakura",
        "spawn_weight": 0, "active_spawn_weight": 0,
        "shop_weight": 0, "claim_weight": 0,
        "shop_price": 5, "stock_limit": 10, "sell_price": 77,
    })
    cr._apply_docs(edited)

    # Same dict objects must reflect the edit — no re-import needed.
    assert rarity_map is cr.RARITY_MAP
    assert rarity_map[26] == "🌸 Sakura"
    assert cr.RARITY_IDS["🌸 Sakura"] == 26
    assert sell_prices["Astral"] == 80000
    assert sell_prices["Sakura"] == 77
    # Zero claim_weight stays out of the claim pool.
    assert "🌸 Sakura" not in cr.CLAIM_RARITY_WEIGHTS

    # Restore defaults for other tests.
    cr._apply_docs(original_docs)
    assert "Sakura" not in cr.SELL_PRICES
    assert cr.SELL_PRICES["Astral"] == 40000


def test_rarity_id_of_resolves_all_forms():
    cr._apply_docs(cr._default_docs())
    assert cr.rarity_id_of(3) == 3
    assert cr.rarity_id_of("🟠 Rare") == 3
    assert cr.rarity_id_of("Rare") == 3
    assert cr.rarity_id_of("rare") == 3
    assert cr.rarity_id_of(999) is None
    assert cr.rarity_id_of("Nope") is None
    assert cr.rarity_id_of(None) is None
