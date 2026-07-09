from typing import List, Optional
from beanie import Document, Indexed
from pydantic import BaseModel, Field

class UserStats(BaseModel):
    level: int = 1
    xp: int = 0
    zenith: int = 0
    char_count: int = 0
    guess_count: int = 0

class UserCharacter(BaseModel):
    id: str
    name: str
    rarity: str
    anime: str
    img_url: str

class User(Document):
    id: Indexed(int, unique=True)
    first_name: str
    username: Optional[str] = None
    balance: int = 0
    zenith: int = 0
    stats: UserStats = Field(default_factory=UserStats)
    characters: List[UserCharacter] = Field(default_factory=list)

    class Settings:
        name = "user_collectionsss"
