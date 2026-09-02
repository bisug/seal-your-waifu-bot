from typing import List, Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    id: int
    first_name: str
    username: Optional[str] = None
    balance: int = 0
    zenith: int = 0
    characters: List[dict] = Field(default_factory=list)

    # Daily Streak
    daily_streak: int = 0
    last_daily_date: Optional[str] = None

    # Weekly
    last_weekly_date: Optional[str] = None

    # Progression
    xp: int = 0
    claimed_levels: List[int] = Field(default_factory=list)
    pass_claims: dict = Field(default_factory=dict)
    pass_bank_by_season: dict = Field(default_factory=dict)
    pass_entitlements: dict = Field(default_factory=dict)
    pass_payment_locks: dict = Field(default_factory=dict)
    # Name Guessing Game
    guess_count: int = 0

    pass_type: str = "free" # free, premium, elite
    version: int = 0

class Character(BaseModel):
    id: str
    name: str
    anime: str
    rarity: str
    img_url: str
    zenith_price: int = 5
    sold_count: int = 0
