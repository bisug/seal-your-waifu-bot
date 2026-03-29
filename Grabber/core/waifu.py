import httpx
import random
import time
from typing import Dict, List
from Grabber.database import collection, db
from Grabber import LOGGER
from config import config


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

async def upload_image_to_catbox(file_path: str) -> str or None:
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

async def upload_image_to_imgbb(file_path: str) -> str or None:
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

async def add_character_to_db(char_data: dict) -> str:
    """
    Add a new character to the database with a unique generated ID.
    """
    char_id = str(await get_next_sequence_number('character_id')).zfill(2)
    char_data['id'] = char_id
    await collection.insert_one(char_data)
    return char_id

async def get_character_by_id(char_id: str) -> dict or None:
    """
    Fetch character data from the database using its ID.
    """
    return await collection.find_one({'id': char_id})


# Cache for characters grouped by rarity to improve spawn performance
characters_by_rarity: Dict[str, list] = {}
_cache_timestamps: Dict[str, float] = {}
CACHE_TTL = 3600  # 1 hour

async def get_or_load_characters(rarity: str) -> list:
    """
    Get a list of characters for a specific rarity, loading from DB into cache if needed.
    Cache is invalidated after CACHE_TTL seconds so new uploads appear without restart.
    """
    now = time.time()
    if rarity not in characters_by_rarity or now - _cache_timestamps.get(rarity, 0) > CACHE_TTL:
        cursor = collection.find({"rarity": rarity}, projection={"_id": 0})
        chars = await cursor.to_list(length=None)
        random.shuffle(chars)
        characters_by_rarity[rarity] = chars
        _cache_timestamps[rarity] = now
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
