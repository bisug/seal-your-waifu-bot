import inspect
import logging

import redis.asyncio as redis
from pymongo import AsyncMongoClient

from config import config

LOGGER = logging.getLogger(__name__)


class Database:
    """Database abstraction layer for MongoDB connections."""
    def __init__(self, uri):
        """Initialize MongoDB client and collection references."""
        self.client = AsyncMongoClient(
            uri,
            appname="seal-bot",
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=20000,
            maxPoolSize=100,
            minPoolSize=0,
        )
        self.db = self.client['Character_catchers']

        # NOTE: Legacy collection names contain intentional typos (e.g. 'user_totalssss')
        self.anime_characters = self.db['anime_characterss']
        self.groups = self.db['total_groups']
        self.message_counts = self.db['message']
        self.users = self.db["user_collectionsss"]
        self.group_user_totals = self.db['group_user_totals']
        self.total_pm_users = self.db['total_pm_users']
        self.sudo_users = self.db['sudos']
        self.spawns = self.db['active_spawns']
        self.sessions = self.db['active_sessions']
        self.quiz_questions = self.db['quiz_questions']
        self.deletion_queue = self.db['deletion_queue']
        self.daily_shop = self.db['daily_shop_inventory']
        self.star_orders = self.db['star_orders']
        self.global_user_bans = self.db['global_user_bans']
        self.global_group_bans = self.db['global_group_bans']
        self.rarities = self.db['rarities']
        self.takedown_log = self.db['takedown_log']

    async def ensure_indexes(self):
        """Create performance indexes for all collections."""
        indexes = [
            (self.users,             lambda c: c.create_index("id", unique=True, sparse=True)),
            (self.anime_characters,  lambda c: c.create_index("id", unique=True, sparse=True)),
            (self.anime_characters,  lambda c: c.create_index("rarity")),
            (self.anime_characters,  lambda c: c.create_index("rarity_id", sparse=True)),
            (self.anime_characters,  lambda c: c.create_index("name")),
            (self.spawns,            lambda c: c.create_index("chat_id")),
            (self.message_counts,    lambda c: c.create_index("chat_id")),
            (self.deletion_queue,    lambda c: c.create_index("delete_at")),
            (self.group_user_totals, lambda c: c.create_index([("group_id", 1), ("user_id", 1)])),
            (self.group_user_totals, lambda c: c.create_index([("group_id", 1), ("count", -1)])),
            (self.groups,            lambda c: c.create_index("group_id", unique=True)),
            # WebApp Specific Indexes
            (self.users,             lambda c: c.create_index("characters.id")),
            (self.users,             lambda c: c.create_index([("id", 1), ("characters.id", 1)])),
            (self.anime_characters,  lambda c: c.create_index([("rarity", 1), ("name", 1)])),
            (self.anime_characters,  lambda c: c.create_index("numeric_id", sparse=True)),
            (self.anime_characters,  lambda c: c.create_index([("added_by_id", 1), ("uploaded_at", -1)], sparse=True)),
            (self.users,             lambda c: c.create_index("char_count", sparse=True)),
            (self.users,             lambda c: c.create_index("xp", sparse=True)),
            (self.users,             lambda c: c.create_index("balance", sparse=True)),
            (self.users,             lambda c: c.create_index("zenith", sparse=True)),
            (self.users,             lambda c: c.create_index("guess_count", sparse=True)),
            # Search Performance Indexes (Multi-key for harem filtering)
            (self.users,             lambda c: c.create_index([("id", 1), ("characters.rarity", 1), ("characters.name", 1)])),
            (self.users,             lambda c: c.create_index([("id", 1), ("characters.anime", 1)])),
            (self.sessions,          lambda c: c.create_index("expires_at_dt", expireAfterSeconds=0)),
            (self.sessions,          lambda c: c.create_index([("id", 1), ("type", 1), ("status", 1)])),
            (self.sessions,          lambda c: c.create_index([("type", 1), ("sender_id", 1), ("receiver_id", 1), ("status", 1)])),
            (self.sessions,          lambda c: c.create_index("token", sparse=True)),
            (self.sessions,          lambda c: c.create_index("token_digest", sparse=True)),
            (self.daily_shop,        lambda c: c.create_index("date", unique=True)),
            (self.star_orders,       lambda c: c.create_index("order_id", unique=True)),
            (self.star_orders,       lambda c: c.create_index("payload", unique=True)),
            (self.star_orders,       lambda c: c.create_index("telegram_payment_charge_id", unique=True, sparse=True)),
            (self.star_orders,       lambda c: c.create_index([("user_id", 1), ("status", 1), ("created_at", -1)])),
            (self.star_orders,       lambda c: c.create_index("expires_at_dt", expireAfterSeconds=0)),
            (self.global_user_bans,  lambda c: c.create_index("user_id", unique=True)),
            (self.global_user_bans,  lambda c: c.create_index("expires_at_dt", expireAfterSeconds=0)),
            (self.global_group_bans, lambda c: c.create_index("chat_id", unique=True)),
            (self.global_group_bans, lambda c: c.create_index("expires_at_dt", expireAfterSeconds=0)),
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

    async def ping(self):
        """Validate MongoDB connectivity without forcing this check at import time."""
        await self.client.admin.command("ping")

    async def close(self):
        """Close MongoDB client resources during graceful shutdown."""
        result = self.client.close()
        if inspect.isawaitable(result):
            await result

# Initialize Database
# Eager construction is required for the module-level collection exports below,
# but AsyncMongoClient("") raises a ConfigurationError at parse time when
# MONGO_URL is unset (e.g. CI/tests). Fall back to a lazy localhost client so
# imports succeed without credentials; runner startup still fails loudly via
# seal_db.ping() if MongoDB is genuinely unreachable in production.
try:
    seal_db = Database(config.MONGO_URL or "mongodb://localhost:27017")
except Exception as e:
    LOGGER.exception("Failed to initialize MongoDB client")
    raise e

# Initialize Redis
try:
    if not config.REDIS_URL:
        r = None
    else:
        r = redis.from_url(
            config.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            health_check_interval=30,
            retry_on_timeout=True,
        )
except Exception:
    LOGGER.exception("Failed to initialize Redis client")
    r = None

# Export variables for backward compatibility
client = seal_db.client
db = seal_db.db

collection = seal_db.anime_characters
group_collection = seal_db.groups
message_counts_collection = seal_db.message_counts
user_collection = seal_db.users
group_user_totals_collection = seal_db.group_user_totals
total_pm_users = seal_db.total_pm_users
sudo_collection = seal_db.sudo_users
spawns_collection = seal_db.spawns
sessions_collection = seal_db.sessions
quiz_questions_collection = seal_db.quiz_questions
deletion_queue_collection = seal_db.deletion_queue
daily_shop_collection = seal_db.daily_shop
star_orders_collection = seal_db.star_orders
global_user_bans_collection = seal_db.global_user_bans
global_group_bans_collection = seal_db.global_group_bans
rarities_collection = seal_db.rarities
takedown_log_collection = seal_db.takedown_log


async def close_connections():
    """Close infrastructure clients during process shutdown."""
    if r:
        try:
            await r.aclose()
        except Exception as e:
            LOGGER.warning(f"Redis close failed: {e}")
    try:
        await seal_db.close()
    except Exception as e:
        LOGGER.warning(f"MongoDB close failed: {e}")
