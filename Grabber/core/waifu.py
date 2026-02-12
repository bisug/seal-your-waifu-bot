import httpx
from Grabber.database import collection, db
from Grabber import LOGGER
from config import config


IMGBB_API_KEY = config.IMGBB_API_KEY

async def get_next_sequence_number(sequence_name: str) -> int:
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        upsert=True,
        return_document=True
    )
    return sequence_document['sequence_value']

async def upload_image_to_catbox(file_path: str) -> str or None:
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
    char_id = str(await get_next_sequence_number('character_id')).zfill(2)
    char_data['id'] = char_id
    await collection.insert_one(char_data)
    return char_id

async def get_character_by_id(char_id: str) -> dict or None:
    return await collection.find_one({'id': char_id})
