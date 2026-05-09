"""
Defines the Battle Pass (Seal Pass) reward tracks for levels 1 to 100.
The dictionary maps Level -> Track Data.
"""
PASS_TRACKS = {}
for level in range(1, 101):
    # Default for all levels (generic scaling)
    track = {
        "free": {"type": "shards", "amount": 100 + (level * 2)},
        "premium": {"type": "shards", "amount": 300 + (level * 4)},
        "elite": {"type": "shards", "amount": 500 + (level * 6)}
    }
    # Milestone every 5 levels
    if level % 5 == 0 and level % 10 != 0:
        track["free"] = {"type": "shards", "amount": 1000}
        track["premium"] = {"type": "egg", "tier": 1} # Common
        track["elite"] = {"type": "egg", "tier": 2}   # Rare
    # Milestone every 10 levels
    if level % 10 == 0 and level % 50 != 0:
        track["free"] = {"type": "egg", "tier": 1}
        track["premium"] = {"type": "egg", "tier": 2}   
        track["elite"] = {"type": "egg", "tier": 3}   # Epic
        track["premium_extra_amount"] = 2000
    # Major milestone every 50
    if level % 50 == 0 and level != 100:
        track["free"] = {"type": "egg", "tier": 2}
        track["premium"] = {"type": "egg", "tier": 3}
        track["elite"] = {"type": "egg", "tier": 4}   # Legendary
        track["elite_extra_amount"] = 10000
    # Level 100 capstone
    if level == 100:
        track["free"] = {"type": "egg", "tier": 3}
        track["premium"] = {"type": "egg", "tier": 4}
        track["elite"] = {"type": "egg", "tier": 5}   # Very Legendary? Wait, tiers go 1-5? Let's use 4
        track["elite_extra_amount"] = 50000
    PASS_TRACKS[level] = track
MAX_PASS_LEVEL = 100
