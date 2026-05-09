import logging

import redis.asyncio as redis
from pymongo import AsyncMongoClient

from config import config

LOGGER = logging.getLogger(__name__)


class Database:
    """Database abstraction layer for MongoDB connections."""
    def __init__(self, uri):
        """Initialize MongoDB client and collection references."""
        self.client = AsyncMongoClient(uri)
        self.db = self.client['Character_catchers']

        # NOTE: Legacy collection names contain intentional typos (e.g. 'user_totalssss')
        self.anime_characters = self.db['anime_characterss']
        self.groups = self.db['total_groups']
        self.user_totals = self.db['user_totalssss']
        self.message_counts = self.db['message']
        self.users = self.db["user_collectionsss"]
        self.group_user_totals = self.db['group_user_totals']
        self.total_pm_users = self.db['total_pm_users']
        self.sudo_users = self.db['sudos']
        self.spawns = self.db['active_spawns']
        self.sessions = self.db['active_sessions']
        self.quiz_questions = self.db['quiz_questions']
        self.gamebot_enabled_groups = self.db['nguess_enabled_groups']
        self.deletion_queue = self.db['deletion_queue']
        self.daily_shop = self.db['daily_shop_inventory']
        self.scraped_characters = self.db['scraped_characters']

    async def ensure_indexes(self):
        """Create performance indexes for all collections."""
        indexes = [
            (self.users,             lambda c: c.create_index("id", unique=True, sparse=True)),
            (self.anime_characters,  lambda c: c.create_index("id", unique=True, sparse=True)),
            (self.anime_characters,  lambda c: c.create_index("rarity")),
            (self.spawns,            lambda c: c.create_index("chat_id")),
            (self.message_counts,    lambda c: c.create_index("chat_id")),
            (self.deletion_queue,    lambda c: c.create_index("delete_at")),
            (self.group_user_totals, lambda c: c.create_index([("group_id", 1), ("user_id", 1)])),
            (self.group_user_totals, lambda c: c.create_index([("group_id", 1), ("count", -1)])),
            (self.groups,            lambda c: c.create_index("group_id", unique=True)),
            # Previously missing indexes — added for query performance
            (self.user_totals,       lambda c: c.create_index("chat_id")),
            (self.gamebot_enabled_groups, lambda c: c.create_index("chat_id", unique=True, sparse=True)),
            (self.total_pm_users,    lambda c: c.create_index("_id")),
            # WebApp Specific Indexes
            (self.users,             lambda c: c.create_index("characters.id")),
            (self.users,             lambda c: c.create_index([("id", 1), ("characters.id", 1)])),
            (self.anime_characters,  lambda c: c.create_index([("rarity", 1), ("name", 1)])),
            (self.users,             lambda c: c.create_index("char_count", sparse=True)),
            # Search Performance Indexes (Multi-key for harem filtering)
            (self.users,             lambda c: c.create_index([("id", 1), ("characters.rarity", 1), ("characters.name", 1)])),
            (self.users,             lambda c: c.create_index([("id", 1), ("characters.anime", 1)])),
            (self.scraped_characters, lambda c: c.create_index([("name", 1), ("anime", 1)], unique=True)),
        ]
        failed = 0
        for collection, idx_fn in indexes:
            try:
                await idx_fn(collection)
            except Exception as e:
                failed += 1
                LOGGER.warning(f"Index skipped on {collection.name}: {e}")
        if failed:
            LOGGER.warning(f"DB index setup: {failed} index(es) skipped (see above).")
        else:
            LOGGER.info("Database indexes ensured successfully.")

# Initialize Database
try:
    seal_db = Database(config.MONGO_URL)
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    raise e

# Initialize Redis
try:
    if not config.REDIS_URL:
        r = None
    else:
        r = redis.from_url(config.REDIS_URL, decode_responses=True)
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
total_pm_users = seal_db.total_pm_users
sudo_collection = seal_db.sudo_users
spawns_collection = seal_db.spawns
sessions_collection = seal_db.sessions
quiz_questions_collection = seal_db.quiz_questions
gamebot_enabled_groups_collection = seal_db.gamebot_enabled_groups
deletion_queue_collection = seal_db.deletion_queue
daily_shop_collection = seal_db.daily_shop
scraped_characters_collection = seal_db.scraped_characters
