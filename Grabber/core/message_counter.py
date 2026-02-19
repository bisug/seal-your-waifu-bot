import random
import datetime
import time
from pyrogram import types
from Grabber import config
from Grabber.core.spawns import (
    increment_message_count, get_chat_frequency, 
    send_character, get_spawn_order, increment_spawn_order,
    get_chat_state, track_user_activity, get_active_user_count
)
from Grabber.modules.rarities import RARITY_WEIGHTS, ACTIVE_RARITY_WEIGHTS

SPECIAL_GROUP_ID = config.SPECIAL_GROUP_ID

special_rarity_thresholds = {
    "💠 Cosmic": 300,
    "💮 Exclusive": 600,
    "🔮 Limited Edition": 900,
    "🫧 Royal": 1000
}

                                                                              
async def message_counter(_, message: types.Message):
    chat = message.chat
    if not chat or not message.from_user:
        return

    chat_id = chat.id
    user_id = message.from_user.id
    
                                                        
    await track_user_activity(chat_id, user_id)

                                          
    count = await increment_message_count(chat_id)

                                  
                                                                       
    state = await get_chat_state(chat_id)
    last_spawn_time = state.get("last_spawn_time", 0)
    current_time = time.time()
    
    if current_time - last_spawn_time < 60:
        return

                                                                       
                             
    if random.random() < 0.001:
        await send_character(chat_id, "🫧 Royal")
        return

                                                                         
    now = datetime.datetime.now(datetime.timezone.utc)
    multiplier = 1.0
    if 20 <= now.hour <= 22:
        multiplier = 0.5

                              
    for r_name, threshold in special_rarity_thresholds.items():
        if count % int(threshold * multiplier) == 0:
            if r_name == "🫧 Royal" and chat_id != SPECIAL_GROUP_ID:
                continue
            await send_character(chat_id, r_name)
            return

                              
                                             
    active_count = await get_active_user_count(chat_id)
    
    if active_count >= 6:
        base_freq = 50
    elif active_count >= 3:
        base_freq = 75
    else:
        freq = await get_chat_frequency(chat_id)
        base_freq = freq if freq is not None else 100

    if count % int(base_freq * multiplier) == 0:
                                   
        if active_count > 10:
            weights_map = ACTIVE_RARITY_WEIGHTS
        else:
            weights_map = RARITY_WEIGHTS
            
        rarities = list(weights_map.keys())
        weights = list(weights_map.values())
        
        selected_rarity = random.choices(rarities, weights=weights, k=1)[0]
            
        await send_character(chat_id, selected_rarity)
        
                                
        await increment_spawn_order(chat_id)
