"""One-time PokéAPI import: populate `pokemon_catalog` from pokeapi.co.

Fetches every Pokémon (Gen 1-9, dex 1-1025) with the full PokéAPI feature
set and upserts into `pokemon_catalog` (organized by type categories).

Idempotent: re-running updates existing docs (keyed on dex) and inserts
missing ones. Run from backend/: `uv run python scripts/pokemon_import.py`.

Field mapping (per docs/dev/CONTEXT.md):
  dex# <- pokedex number        name <- species name
  types <- type slots            img <- official artwork URL
  shiny_img <- shiny artwork     cry <- latest cry URL
  sort_order <- dex order
  hp/atk/def/spatk/spdef/spd <- base stats
  height/weight <- decimetres/hectograms (÷10 for display units)
  abilities <- [{name, is_hidden}] (en names)
  moves <- move names (en, capped)
  desc <- English genus (e.g. "Seed Pokémon")
  flavor_text <- English Pokédex entry (latest version)
  growth_rate <- leveling rate (slow/medium/fast...)
  gender_rate <- female chance in eighths (-1 = genderless)
  capture_rate <- base catch rate
  base_happiness <- base friendship
  egg_groups <- breeding groups
  evolves_from <- dex of pre-evolution (None for base)
  evolution_chain <- ordered dex list of the full line
  is_legendary / is_mythical <- species flags
  generation <- e.g. "generation-i"
"""
import asyncio
import sys
import urllib.request

sys.path.insert(0, ".")

API = "https://pokeapi.co/api/v2"
UA = {"User-Agent": "seal-bot-pokemon-import/1.0"}
MAX_MOVES = 24  # keep doc size sane; full move list can be 100+


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        import json
        return json.loads(resp.read().decode())


def _en(names: list, key: str = "name") -> str | None:
    """First English entry from a PokéAPI localized list."""
    return next((n[key] for n in names if n["language"]["name"] == "en"), None)


def build_doc(pokemon: dict, species: dict, evolution_dexes: list[int]) -> dict:
    dex = pokemon["id"]
    stats = {s["stat"]["name"]: s["base_stat"] for s in pokemon["stats"]}
    total = sum(stats.values())
    # English flavor text (latest English entry wins — PokéAPI lists oldest first).
    flavor = next(
        (
            ft["flavor_text"].replace("\f", " ").replace("\n", " ").strip()
            for ft in reversed(species.get("flavor_text_entries", []))
            if ft["language"]["name"] == "en"
        ),
        None,
    )
    genus = _en(species.get("genera", []), "genus") or "Pokémon"
    artwork = (
        pokemon["sprites"]
        .get("other", {})
        .get("official-artwork", {})
        .get("front_default")
    )
    shiny_artwork = (
        pokemon["sprites"]
        .get("other", {})
        .get("official-artwork", {})
        .get("front_shiny")
    )
    evolves_from = None
    if species.get("evolves_from_species"):
        # Species URL tail is the dex of the pre-evolution.
        evolves_from = int(species["evolves_from_species"]["url"].rstrip("/").split("/")[-1])
    return {
        "dex": dex,
        "name": pokemon["name"].replace("-", " ").title(),
        "types": [t["type"]["name"] for t in pokemon["types"]],
        # jsDelivr CDN — raw.githubusercontent.com is 20-50x slower for
        # these PNGs and made the Mini App Pokédex unusable.
        "img": artwork or f"https://cdn.jsdelivr.net/gh/PokeAPI/sprites@master/sprites/pokemon/other/official-artwork/{dex}.png",
        "shiny_img": shiny_artwork,
        "cry": pokemon.get("cries", {}).get("latest"),
        "height_dm": pokemon.get("height", 0),
        "weight_hg": pokemon.get("weight", 0),
        "abilities": [
            {"name": a["ability"]["name"], "is_hidden": a["is_hidden"]}
            for a in pokemon.get("abilities", [])
        ],
        "moves": [m["move"]["name"] for m in pokemon.get("moves", [])][:MAX_MOVES],
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
        "flavor_text": flavor,
        "growth_rate": (species.get("growth_rate") or {}).get("name"),
        "gender_rate": species.get("gender_rate"),
        "capture_rate": species.get("capture_rate"),
        "base_happiness": species.get("base_happiness"),
        "egg_groups": [g["name"] for g in species.get("egg_groups", [])],
        "evolves_from": evolves_from,
        "evolution_chain": evolution_dexes,
        "is_legendary": bool(species.get("is_legendary")),
        "is_mythical": bool(species.get("is_mythical")),
        "generation": (species.get("generation") or {}).get("name"),
        "sort_order": dex,
        "enabled": True,
    }


def evolution_dexes(species: dict) -> list[int]:
    """Ordered dex list of the full evolution line (walk the chain tree)."""
    chain = species.get("evolution_chain", {}).get("url")
    if not chain:
        return []
    evo = fetch_json(chain)
    out = []

    def walk(node: dict) -> None:
        out.append(int(node["species"]["url"].rstrip("/").split("/")[-1]))
        for child in node.get("evolves_to", []):
            walk(child)

    walk(evo["chain"])
    return out


async def main() -> None:
    from backend.database import pokemon_catalog_collection

    count = 0
    # PokéAPI lists 1025 species; fetch each by id (stable, no pagination drift).
    for dex in range(1, 1026):
        try:
            pokemon = fetch_json(f"{API}/pokemon/{dex}")
            species = fetch_json(pokemon["species"]["url"])
            evo_dexes = evolution_dexes(species)
        except Exception as e:
            print(f"skip dex {dex}: {e}")
            continue
        doc = build_doc(pokemon, species, evo_dexes)
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
