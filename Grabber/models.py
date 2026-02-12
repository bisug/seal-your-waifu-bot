from pydantic import BaseModel, Field
from typing import List, Optional

class Character(BaseModel):
    id: str
    name: str
    anime: str
    rarity: str
    img_url: str
    zenith_price: int = 5
    sold_count: int = 0

class UserCharacter(BaseModel):
    id: str
    name: str
    anime: str
    rarity: str
    img_url: str

class User(BaseModel):
    id: int
    zenith: int = 0
    characters: List[UserCharacter] = Field(default_factory=list)
