from motor.motor_asyncio import AsyncIOMotorClient
from config import config

mongo_url = config.MONGO_URL

                                    
client = AsyncIOMotorClient(mongo_url)
db = client['Character_catchers']



             
collection = db['anime_characterss']
group_collection = db['total_groups']
user_totals_collection = db['user_totalssss']
message_counts_collection = db['message']
user_collection = db["user_collectionsss"]
group_user_totals_collection = db['group_user_totals']
top_global_groups_collection = db['top_global_groupss']
total_pm_users = db['total_pm_users']
sudo_collection = db['sudos']
spawns_collection = db['active_spawns']
sessions_collection = db['active_sessions']
quiz_questions_collection = db['quiz_questions']
