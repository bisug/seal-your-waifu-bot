from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber.core.utils import md_escape
from Grabber import app, collection, LOGGER

@app.on_message(filters.command("animes"))
async def anime_list(_, message: types.Message) -> None:
                                                                      
    try:
                                                      
        anime_names = await collection.distinct("anime")

        if not anime_names:
            await message.reply_text("No anime found in the database.")
            return

                                                
        anime_list_text = "\n".join(f"• {md_escape(anime)}" for anime in sorted(anime_names))

                                                           
        if len(anime_list_text) > 4000:
                                                                                       
            anime_list_text = anime_list_text[:4000] + "\n...(truncated)"

        await message.reply_text(
            f"📜 **Anime List in Database:**\n\n{anime_list_text}",
            parse_mode=ParseMode.MARKDOWN_V2
        )

    except Exception as e:
        LOGGER.error(f"Error in anime_list: {e}")
        await message.reply_text(f"Error fetching anime list: {str(e)}")
