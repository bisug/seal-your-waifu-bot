import asyncio
import os
import time
from typing import Dict, Optional
import httpx
from config import config
from backend import LOGGER
from backend.database import collection, db
IMGBB_API_KEY = config.IMGBB_API_KEY
def _read_file_sync(file_path: str) -> bytes:
    with open(file_path, 'rb') as f:
        return f.read()
async def get_next_sequence_number(sequence_name: str) -> int:
    """
    Get the next sequence number for a given sequence name from the database.
    On first use, initializes the counter from the highest existing character ID
    so that a fresh deploy never collides with pre-existing records.
    """
    sequence_collection = db.sequences
    # Check if the sequence document already exists
    existing = await sequence_collection.find_one({'_id': sequence_name})
    if existing is None:
        # Bootstrap from the current max ID to avoid collisions
        max_id = 0
        async for doc in collection.find({'id': {'$exists': True}}, {'id': 1, '_id': 0}):
            try:
                val = int(doc['id'])
                if val > max_id:
                    max_id = val
            except (ValueError, TypeError):
                pass
        LOGGER.info(f"Initializing sequence '{sequence_name}' from max existing ID: {max_id}")
        # Use insert with ignore-if-exists to handle concurrent startups
        try:
            await sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': max_id})
        except Exception:
            pass  # Another instance already inserted it — that's fine
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        upsert=True,
        return_document=True
    )
    return sequence_document['sequence_value']
async def upload_image_to_catbox(file_path: str) -> Optional[str]:
    """
    Upload an image file to Catbox.moe and return the URL.
    """
    try:
        file_bytes = await asyncio.to_thread(_read_file_sync, file_path)
        async with httpx.AsyncClient() as client:
            files = {'fileToUpload': (os.path.basename(file_path), file_bytes)}
            data = {'reqtype': 'fileupload', 'userhash': ''}
            response = await client.post(
                "https://catbox.moe/user/api.php",
                data=data,
                files=files,
                timeout=60
            )
            if response.status_code == 200 and response.text.startswith("https://"):
                return response.text.strip()
        return None
    except httpx.HTTPError as e:
        LOGGER.error(f"Catbox Upload Error: {e}")
        return None
async def upload_image_to_imgbb(file_path: str) -> Optional[str]:
    """
    Upload an image file to ImgBB and return the URL.
    """
    try:
        file_bytes = await asyncio.to_thread(_read_file_sync, file_path)
        async with httpx.AsyncClient() as client:
            files = {'image': (os.path.basename(file_path), file_bytes)}
            data = {'key': IMGBB_API_KEY}
            response = await client.post(
                "https://api.imgbb.com/1/upload",
                data=data,
                files=files,
                timeout=60
            )
            response_data = response.json()
            if response_data.get('success'):
                return response_data['data']['url']
        return None
    except httpx.HTTPError as e:
        LOGGER.error(f"ImgBB Upload Error: {e}")
        return None
async def upload_media_safely(file_path: str) -> Optional[str]:
    """
    Best-effort wrapper for uploading media.
    1. Tries Catbox first (supports all media).
    2. If Catbox fails and the file is NOT a video/GIF, tries ImgBB.
    """
    url = await upload_image_to_catbox(file_path)
    if url:
        return url
    if not str(file_path).endswith(('.mp4', '.webm', '.gif')):
        LOGGER.warning(f"Catbox failed for {file_path}. Falling back to ImgBB...")
        url = await upload_image_to_imgbb(file_path)
        if url:
            return url
    LOGGER.error(f"Complete upload failure for {file_path}")
    return None
async def add_character_to_db(char_data: dict) -> str:
    """
    Add a new character to the database with a unique generated ID.
    Retries up to 10 times on DuplicateKeyError to handle sequence gaps
    or race conditions during concurrent approvals.
    """
    from pymongo.errors import DuplicateKeyError
    from backend.core.rarities import rarity_id_of
    for attempt in range(10):
        char_id = str(await get_next_sequence_number('character_id')).zfill(4)
        char_data['id'] = char_id
        # Dual-write the rarity_id alongside the display label so the
        # rarity table stays the single source of truth for renames.
        if 'rarity_id' not in char_data:
            rid = rarity_id_of(char_data.get('rarity'))
            if rid is not None:
                char_data['rarity_id'] = rid
        # Stored numeric form of the ID so the gallery can sort by an indexed
        # field instead of converting per-document at query time.
        try:
            char_data['numeric_id'] = int(char_id)
        except (TypeError, ValueError):
            char_data.pop('numeric_id', None)
        char_data.pop('_id', None)  # Remove any stale _id from a previous failed attempt
        try:
            await collection.insert_one(char_data)
            return char_id
        except DuplicateKeyError:
            LOGGER.warning(f"DuplicateKeyError for char_id={char_id} (attempt {attempt + 1}/10). Skipping to next ID...")
            continue
    raise RuntimeError("add_character_to_db: failed after 10 retries due to duplicate key — check sequence collection")
async def get_character_by_id(char_id: str) -> Optional[dict]:
    """
    Fetch character data from the database using its ID.
    """
    return await collection.find_one({'id': char_id})
# Cache for characters grouped by rarity to improve spawn performance
characters_by_rarity: Dict[str, list] = {}
_cache_timestamps: Dict[str, float] = {}
_rarity_locks: Dict[str, asyncio.Lock] = {}  # Per-rarity lock to prevent concurrent stampede
CACHE_TTL = 3600  # 1 hour
async def get_or_load_characters(rarity: str) -> list:
    """
    Get a list of characters for a specific rarity, loading from DB into cache if needed.
    Cache is invalidated after CACHE_TTL seconds so new uploads appear without restart.
    Uses a per-rarity lock to prevent concurrent cache misses from firing duplicate DB queries.
    """
    now = time.time()
    # Fast path: cache hit, no lock needed
    if rarity in characters_by_rarity and now - _cache_timestamps.get(rarity, 0) <= CACHE_TTL:
        return characters_by_rarity[rarity]
    # Slow path: acquire per-rarity lock to serialize DB fetch
    if rarity not in _rarity_locks:
        _rarity_locks[rarity] = asyncio.Lock()
    async with _rarity_locks[rarity]:
        # Double-check after acquiring lock — another waiter may have already loaded
        now = time.time()
        if rarity not in characters_by_rarity or now - _cache_timestamps.get(rarity, 0) > CACHE_TTL:
            MAX_CACHED_PER_RARITY = 500
            cursor = await collection.aggregate([
                {"$match": {"rarity": rarity}},
                {"$sample": {"size": MAX_CACHED_PER_RARITY}},
                {"$project": {"_id": 0}}
            ])
            chars = await cursor.to_list(length=MAX_CACHED_PER_RARITY)
            characters_by_rarity[rarity] = chars
            _cache_timestamps[rarity] = time.time()
        return characters_by_rarity[rarity]
def invalidate_character_cache(rarity: str = None):
    """
    Invalidate the character cache. Pass a rarity to invalidate only that rarity,
    or call with no args to invalidate all. Call this after uploading new characters.
    """
    if rarity:
        _cache_timestamps.pop(rarity, None)
        characters_by_rarity.pop(rarity, None)
    else:
        _cache_timestamps.clear()
        characters_by_rarity.clear()
