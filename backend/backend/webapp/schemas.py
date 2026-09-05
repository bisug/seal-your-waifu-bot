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
    unique_characters: int = 0
    total_available_characters: int = 0
    collection_percent: float = 0.0
    rank: int = 0
    percentile: float = 0.0
    pass_type: str = "free"
    incubation_slots: int = 1
    active_incubations: int = 0
    energy: int = 5
    last_energy_recharge: Optional[str] = None

class EggModel(BaseModel):
    # id is Optional to handle corrupt DB records where the field is missing.
    # A required str here caused a Pydantic ValidationError (500) for any user
    # with a malformed egg instead of gracefully returning the rest of the data.
    id: Optional[str] = None
    tier: str
    name: str
    status: str
    is_corrupted: bool
    hatch_time: Optional[str] = None
    remaining_mins: Optional[int] = None
    base_wait_min: Optional[int] = None
    wait_min: Optional[int] = None
    incubation_pass_type: Optional[str] = None
    sell_price: Optional[int] = None
    purify_price: Optional[int] = None

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
    last_name: Optional[str] = None
    username: Optional[str] = None
    avatar: Optional[str] = None
    is_sudo: bool = False
    terms_accepted: bool = False
    role: Optional[str] = None
    role_label: Optional[str] = None
    role_tag: Optional[str] = None
    role_symbol: Optional[str] = None
    is_staff: bool = False
    can_upload: bool = False
    can_edit_character: bool = False
    upload_reward: Optional[dict[str, int]] = None
    role_perks: dict[str, int] = Field(default_factory=dict)
    role_benefits: List[str] = Field(default_factory=list)
    balance: int = 0
    zenith: int = 0
    stats: StatsModel
    achievements: List[AchievementModel] = Field(default_factory=list)
    titles: TitlesModel
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
    reward_shards: Optional[int] = 0
    claimed: bool
    locked: bool = False

class QuestsResponse(BaseModel):
    daily: List[QuestModel]
    weekly: List[QuestModel]
    pass_type: str = "free"
    pass_: List[QuestModel] = Field(default_factory=list, alias="pass")

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

class ReferralStatsModel(BaseModel):
    invited_count: int = 0
    tracked_count: int = 0
    earned_shards: int = 0
    referrer_reward_shards: int
    referrer_reward_xp: int
    referred_reward_shards: int

class BattleStatsModel(BaseModel):
    total_battles: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
