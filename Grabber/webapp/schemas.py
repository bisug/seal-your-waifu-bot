from typing import List, Optional

from pydantic import BaseModel, Field


class StatsModel(BaseModel):
    level: int = 0
    xp: int = 0
    xp_current: int = 0
    xp_needed: int = 100
    streak: int = 0
    points: int = 0
    zenith: int = 0
    badges: List[str] = Field(default_factory=list)
    total_characters: int = 0
    rank: int = 0
    percentile: float = 0.0

class PetModel(BaseModel):
    name: str
    level: int
    xp: int
    xp_needed: int
    hp: int
    atk: int
    spd: int
    luck: float
    ability: str
    desc: str
    img: str
    is_active: bool

class EggModel(BaseModel):
    # FIX: id is Optional to handle corrupt DB records where the field is missing.
    # A required str here caused a Pydantic ValidationError (500) for any user
    # with a malformed egg instead of gracefully returning the rest of the data.
    id: Optional[str] = None
    tier: str
    name: str
    status: str
    is_corrupted: bool
    hatch_time: Optional[str] = None
    remaining_mins: Optional[int] = None

class AchievementModel(BaseModel):
    id: str
    name: str
    icon: str

class TitlesModel(BaseModel):
    current: str = "Rookie"
    all: List[str] = Field(default_factory=lambda: ["Rookie"])

class UserProfileResponse(BaseModel):
    id: int
    first_name: str = "User"
    username: Optional[str] = None
    avatar: Optional[str] = None
    stats: StatsModel
    achievements: List[AchievementModel] = Field(default_factory=list)
    titles: TitlesModel
    current_pet: Optional[PetModel] = None
    pets: List[PetModel] = Field(default_factory=list)
    eggs: List[EggModel] = Field(default_factory=list)

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
    symbol: Optional[str] = "✦"
    progress: int
    target: int
    reward_xp: int
    claimed: bool

class QuestsResponse(BaseModel):
    daily: List[QuestModel]
    weekly: List[QuestModel]

class TradeOffer(BaseModel):
    id: str
    sender_id: int
    sender_name: str
    receiver_id: int
    receiver_name: str
    sender_char: CharacterModel
    receiver_char: CharacterModel
    status: str # 'pending', 'accepted', 'rejected'

class MarriageModel(BaseModel):
    partner_id: int
    partner_name: str
    partner_avatar: Optional[str] = None
    married_at: str

class ReferralModel(BaseModel):
    referred_id: int
    referred_name: str
    rewarded: bool

class BattleStatsModel(BaseModel):
    total_battles: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
