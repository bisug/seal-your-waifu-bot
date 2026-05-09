import asyncio
import random
import time
from typing import Dict, List, Optional

import httpx

from config import config
from Grabber import LOGGER
from Grabber.database import collection, db

IMGBB_API_KEY = config.IMGBB_API_KEY

async def get_next_sequence_number(sequence_name: str) -> int:
    """
    Get the next sequence number for a given sequence name from the database.
    Used primarily for generating unique character IDs.
    """
    sequence_collection = db.sequences
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
        async with httpx.AsyncClient() as client:
            with open(file_path, 'rb') as f:
                files = {'fileToUpload': f}
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
    except Exception as e:
        LOGGER.error(f"Catbox Upload Error: {e}")
        return None

async def upload_image_to_imgbb(file_path: str) -> Optional[str]:
    """
    Upload an image file to ImgBB and return the URL.
    """
    try:
        async with httpx.AsyncClient() as client:
            with open(file_path, 'rb') as f:
                files = {'image': f}
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
    except Exception as e:
        LOGGER.error(f"ImgBB Upload Error: {e}")
        return None

async def upload_media_safely(file_path: str) -> Optional[str]:
    """
    Maximized wrapper for uploading media.
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
    """
    char_id = str(await get_next_sequence_number('character_id')).zfill(2)
    char_data['id'] = char_id
    await collection.insert_one(char_data)
    return char_id

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
