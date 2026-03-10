from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from config import config

class Database:
    """
    Database abstraction layer.
    Manages the MongoDB connection and collection references.
    """
    def __init__(self, uri):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client['Character_catchers']

        # Initialize collections
        self.anime_characters = self.db['anime_characterss']
        self.groups = self.db['total_groups']
        self.user_totals = self.db['user_totalssss']
        self.message_counts = self.db['message']
        self.users = self.db["user_collectionsss"]
        self.group_user_totals = self.db['group_user_totals']
        self.top_global_groups = self.db['top_global_groupss']
        self.total_pm_users = self.db['total_pm_users']
        self.sudo_users = self.db['sudos']
        self.spawns = self.db['active_spawns']
        self.sessions = self.db['active_sessions']
        self.quiz_questions = self.db['quiz_questions']
        self.nguess_enabled_groups = self.db['nguess_enabled_groups']
        self.deletion_queue = self.db['deletion_queue']

    async def ensure_indexes(self):
        """Create necessary indexes for performance."""
        await self.users.create_index("id", unique=True)
        await self.anime_characters.create_index("id", unique=True)
        await self.anime_characters.create_index("rarity")
        print("Database indexes ensured.")

# Initialize Database
try:
    seal_db = Database(config.MONGO_URL)
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    raise e

# Initialize Redis
try:
    redis_url = config.REDIS_URL
    if not redis_url:
        print("Warning: REDIS_URL not found in environment. Redis features will fail.")
        r = None
    else:
        r = redis.from_url(redis_url, decode_responses=True)
except Exception as e:
    print(f"Failed to initialize Redis: {e}")
    r = None

# Export variables for backward compatibility
client = seal_db.client
db = seal_db.db

collection = seal_db.anime_characters
group_collection = seal_db.groups
user_totals_collection = seal_db.user_totals
message_counts_collection = seal_db.message_counts
user_collection = seal_db.users
group_user_totals_collection = seal_db.group_user_totals
top_global_groups_collection = seal_db.top_global_groups
total_pm_users = seal_db.total_pm_users
sudo_collection = seal_db.sudo_users
spawns_collection = seal_db.spawns
sessions_collection = seal_db.sessions
quiz_questions_collection = seal_db.quiz_questions
nguess_enabled_groups_collection = seal_db.nguess_enabled_groups
deletion_queue_collection = seal_db.deletion_queue
