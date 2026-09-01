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
    astral = next(d for d in edited if d["name"] == "Astral")
    astral["sell_price"] = 80000
    edited.append({
        "_id": 99, "emoji": "🌸", "name": "Sakura",
        "spawn_weight": 0, "active_spawn_weight": 0,
        "shop_weight": 0, "claim_weight": 0,
        "shop_price": 5, "stock_limit": 10, "sell_price": 77,
    })
    cr._apply_docs(edited)

    # Same dict objects must reflect the edit — no re-import needed.
    assert rarity_map is cr.RARITY_MAP
    assert rarity_map[99] == "🌸 Sakura"
    assert cr.RARITY_IDS["🌸 Sakura"] == 99
    assert sell_prices["Astral"] == 80000
    assert sell_prices["Sakura"] == 77
    # Zero claim_weight stays out of the claim pool.
    assert "🌸 Sakura" not in cr.CLAIM_RARITY_WEIGHTS

    # Restore defaults for other tests.
    cr._apply_docs(original_docs)
    assert "Sakura" not in cr.SELL_PRICES
    assert cr.SELL_PRICES["Astral"] == 40000


def test_default_shop_price_ladder_is_balanced():
    """Shop prices must stay keyed to actual rarity.

    Regression: top tiers used to cost 1000-2500 Zenith (~3-7 YEARS of
    grinding at ~1 Zenith/day income), making them effectively
    unpurchasable. The ladder now caps at 100 Zenith (~3 months) and
    every strictly-rarer spawn band must cost strictly more.
    """
    docs = cr._default_docs()

    # 1. Ceiling: nothing costs more than 100 Zenith.
    for doc in docs:
        assert doc["shop_price"] <= 100, f"{doc['name']} costs {doc['shop_price']}⧫"

    # 2. Strict ladder: rarer spawn band => strictly higher price.
    #    (spawn_weight, active_spawn_weight) pairs define the bands.
    bands = {}
    for doc in docs:
        band = (doc["spawn_weight"], doc["active_spawn_weight"])
        bands.setdefault(band, []).append(doc["shop_price"])
    ladder = sorted(bands.items(), key=lambda kv: (-kv[0][0], -kv[0][1]))
    for i in range(len(ladder) - 1):
        rarer_max = max(ladder[i + 1][1])
        commoner_min = min(ladder[i][1])
        assert rarer_max > commoner_min, (
            f"Band {ladder[i + 1][0]} (max {rarer_max}⧫) must cost more "
            f"than band {ladder[i][0]} (min {commoner_min}⧫)"
        )

    # 3. Sanity anchors on the rebalanced values.
    by_name = {d["name"]: d for d in docs}
    assert by_name["Common"]["shop_price"] == 1
    assert by_name["Royal"]["shop_price"] == 60
    assert by_name["Astral"]["shop_price"] == 100


def test_rarity_id_of_resolves_all_forms():
    cr._apply_docs(cr._default_docs())
    assert cr.rarity_id_of(3) == 3
    assert cr.rarity_id_of("🟠 Rare") == 3
    assert cr.rarity_id_of("Rare") == 3
    assert cr.rarity_id_of("rare") == 3
    assert cr.rarity_id_of(999) is None
    assert cr.rarity_id_of("Nope") is None
    assert cr.rarity_id_of(None) is None
