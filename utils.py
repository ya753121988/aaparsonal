import asyncio
import time
from pyrogram.errors import UserNotParticipant, ChatAdminRequired
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.enums import ParseMode
from Script import script
from info import AUTH_PICS, AUTH_CHANNEL, ENABLE_LIMIT, RATE_LIMIT_TIMEOUT, MAX_FILES, AUTO_DELETE, AUTO_DELETE_TIME

# Global Temp class to store bot names
class Temp:
    B_NAME = None
    U_NAME = None

temp = Temp()
rate_limit = {}

async def is_user_joined(bot, message: Message) -> bool:
    user_id = message.from_user.id
    bot_user = await bot.get_me()    
    not_joined_channels = []
    for channel_id in AUTH_CHANNEL:
        try:
            await bot.get_chat_member(channel_id, user_id)
        except UserNotParticipant:
            try:
                chat = await bot.get_chat(channel_id)
                invite_link = await bot.export_chat_invite_link(channel_id)
                not_joined_channels.append((chat.title, invite_link))
            except ChatAdminRequired:
                return False
            except: continue
        except: continue

    if not_joined_channels:
        buttons = [[InlineKeyboardButton(f"Join {title}", url=link)] for title, link in not_joined_channels]
        buttons.append([InlineKeyboardButton("🔄 Try Again", url=f"https://t.me/{bot_user.username}?start=start")])
        await message.reply_photo(
            photo=AUTH_PICS,
            caption=script.AUTH_TXT.format(message.from_user.mention),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return False
    return True
    
async def is_user_allowed(user_id):
    if not ENABLE_LIMIT: return True, 0
    current_time = time.time()
    if user_id in rate_limit:
        file_count, last_time = rate_limit[user_id]
        if file_count >= MAX_FILES and (current_time - last_time) < RATE_LIMIT_TIMEOUT:
            return False, int(RATE_LIMIT_TIMEOUT - (current_time - last_time))
        elif (current_time - last_time) >= RATE_LIMIT_TIMEOUT:
            rate_limit[user_id] = [1, current_time]
        else: rate_limit[user_id][0] += 1
    else:
        rate_limit[user_id] = [1, current_time]
    return True, 0

async def auto_delete_message(message: Message, delay: int = None):
    """📌 এটি নির্দিষ্ট সময় পর মেসেজ ডিলিট করবে"""
    if not AUTO_DELETE:
        return
    wait_time = delay if delay is not None else AUTO_DELETE_TIME
    await asyncio.sleep(wait_time)
    try:
        await message.delete()
        if message.reply_to_message:
            await message.reply_to_message.delete()
    except:
        pass
