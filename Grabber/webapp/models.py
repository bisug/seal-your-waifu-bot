from pydantic import BaseModel, Field
from typing import List, Optional

class StatsModel(BaseModel):
    level: int
    xp: int
    xp_current: int
    xp_needed: int
    streak: int
    points: int
    zenith: int
    badges: List[str]
    total_characters: int

class TitlesModel(BaseModel):
    current: str
    all: List[str]

class UserProfileResponse(BaseModel):
    id: int
    first_name: str
    username: Optional[str]
    avatar: Optional[str]
    stats: StatsModel
    achievements: List[str]
    titles: TitlesModel

class CharacterModel(BaseModel):
    id: str
    name: str
    anime: str
    rarity: str
    img_url: str
    count: Optional[int] = 1
    owned: Optional[bool] = False

class PaginatedResponse(BaseModel):
    total: int
    page: int
    items: List[CharacterModel]

class QuestModel(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    progress: int
    target: int
    reward_xp: int
    claimed: bool

class QuestsResponse(BaseModel):
    daily: List[QuestModel]
    weekly: List[QuestModel]
