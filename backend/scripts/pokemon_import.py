"""One-time PokéAPI import: populate `pokemon_catalog` from pokeapi.co.

Fetches every Pokémon (Gen 1-9, dex 1-1025) with stats + official artwork,
derives rarity from base-stat total, and upserts into `pokemon_catalog`.

Idempotent: re-running updates existing docs (keyed on dex) and inserts
missing ones. Run from backend/: `uv run python scripts/pokemon_import.py`.

Field mapping (per docs/dev/CONTEXT.md):
  dex# <- pokedex number        name <- species name
  types <- type slots            img <- official artwork URL
  rarity <- base-stat total      sort_order <- dex order
  hp/atk/def/spatk/spdef/spd <- base stats
"""
import asyncio
import sys
import urllib.request

sys.path.insert(0, ".")

API = "https://pokeapi.co/api/v2"
UA = {"User-Agent": "seal-bot-pokemon-import/1.0"}

# Base-stat total -> rarity tier. Thresholds tuned so the distribution
# roughly matches the character rarity spread (common-heavy, legendary-rare).
RARITY_TIERS = [
    (600, "Legendary"),
    (540, "Mythic"),
    (480, "Epic"),
    (410, "Rare"),
    (0, "Common"),
]


def rarity_for(total: int) -> str:
    for threshold, label in RARITY_TIERS:
        if total >= threshold:
            return label
    return "Common"


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        import json
        return json.loads(resp.read().decode())


def build_doc(pokemon: dict) -> dict:
    dex = pokemon["id"]
    stats = {s["stat"]["name"]: s["base_stat"] for s in pokemon["stats"]}
    total = sum(stats.values())
    species = fetch_json(pokemon["species"]["url"])
    # English flavor text (first genus entry) for the description.
    genus = next(
        (g["genus"] for g in species.get("genera", []) if g["language"]["name"] == "en"),
        "Pokémon",
    )
    artwork = (
        pokemon["sprites"]
        .get("other", {})
        .get("official-artwork", {})
        .get("front_default")
    )
    return {
        "dex": dex,
        "name": pokemon["name"].replace("-", " ").title(),
        "types": [t["type"]["name"] for t in pokemon["types"]],
        "img": artwork or f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{dex}.png",
        "rarity": rarity_for(total),
        "base_stats": {
            "hp": stats.get("hp", 50),
            "atk": stats.get("attack", 50),
            "def": stats.get("defense", 50),
            "spatk": stats.get("special-attack", 50),
            "spdef": stats.get("special-defense", 50),
            "spd": stats.get("speed", 50),
        },
        "base_total": total,
        "desc": genus,
        "sort_order": dex,
        "enabled": True,
    }


async def main() -> None:
    from backend.database import pokemon_catalog_collection

    count = 0
    # PokéAPI lists 1025 species; fetch each by id (stable, no pagination drift).
    for dex in range(1, 1026):
        try:
            pokemon = fetch_json(f"{API}/pokemon/{dex}")
        except Exception as e:
            print(f"skip dex {dex}: {e}")
            continue
        doc = build_doc(pokemon)
        await pokemon_catalog_collection.update_one(
            {"dex": dex},
            {"$set": doc},
            upsert=True,
        )
        count += 1
        if count % 100 == 0:
            print(f"{count} imported...")

    print(f"done: {count} pokemon in pokemon_catalog")


if __name__ == "__main__":
    asyncio.run(main())
