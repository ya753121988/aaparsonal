import asyncio
from web.utils.file_properties import get_hash
from pyrogram import Client, filters, enums
from info import BIN_CHANNEL, URL, CHANNEL, IS_SHORTLINK, TUTORIAL_LINK_1, FILE_CAPTION
from utils import temp, get_size, get_shortlink
from Script import script
from database.users_db import db
from pyrogram.errors import FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

@Client.on_message(filters.channel & (filters.document | filters.video) & ~filters.forwarded, group=-1)
async def channel_receive_handler(bot: Client, broadcast: Message):
    try:
        chat_id = broadcast.chat.id
        is_banned = await db.is_channel_blocked(chat_id)
        if is_banned:
            await bot.leave_chat(chat_id)
            return

        file = broadcast.document or broadcast.video
        file_name = file.file_name if file else "Unknown File"
        msg = await broadcast.forward(chat_id=BIN_CHANNEL)
        
        raw_stream = f"{URL}watch/{msg.id}/avbotz.mkv?hash={get_hash(msg)}"
        raw_download = f"{URL}{msg.id}?hash={get_hash(msg)}"
        raw_file_link = f"https://t.me/{temp.U_NAME}?start=file_{msg.id}"
        
        if IS_SHORTLINK:
            stream = await get_shortlink(raw_stream)
            download = await get_shortlink(raw_download)
            file_link = await get_shortlink(raw_file_link)
        else:
            stream, download, file_link = raw_stream, raw_download, raw_file_link

        new_caption = FILE_CAPTION.format(CHANNEL, file_name)
        buttons = [
            [InlineKeyboardButton("• ꜱᴛʀᴇᴀᴍ •", url=stream), InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ •", url=download)],
            [InlineKeyboardButton('• ᴄʜᴇᴄᴋ ʜᴇʀᴇ ᴛᴏ ɢᴇᴛ ғɪʟᴇ •', url=file_link)]
        ]
        if IS_SHORTLINK:
            buttons.append([InlineKeyboardButton("• ʜᴏᴡ ᴛᴏ ᴏᴘᴇɴ •", url=TUTORIAL_LINK_1)])

        await bot.edit_message_caption(
            chat_id=broadcast.chat.id,
            message_id=broadcast.id,
            caption=new_caption,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        print(f"Channel Edit Error: {e}")

@Client.on_message(filters.command("link") & filters.group & filters.reply)
async def group_link_handler(bot: Client, message: Message):
    try:
        reply = message.reply_to_message
        if not reply or not (reply.document or reply.video):
            return await message.reply_text("❌ Reply to a File/Video!")
        
        status_msg = await message.reply_text("🔄 Generating Link...")
        log_msg = await reply.forward(chat_id=BIN_CHANNEL)
        file = reply.document or reply.video
        file_name = getattr(file, 'file_name', 'Unknown File')

        raw_stream = f"{URL}watch/{log_msg.id}/avbotz.mkv?hash={get_hash(log_msg)}"
        raw_download = f"{URL}{log_msg.id}?hash={get_hash(log_msg)}"
        raw_file_link = f"https://t.me/{temp.U_NAME}?start=file_{log_msg.id}"
        
        if IS_SHORTLINK:
            stream = await get_shortlink(raw_stream)
            download = await get_shortlink(raw_download)
            file_link = await get_shortlink(raw_file_link)
        else:
            stream, download, file_link = raw_stream, raw_download, raw_file_link

        buttons = [
            [InlineKeyboardButton("• ꜱᴛʀᴇᴀᴍ •", url=stream), InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ •", url=download)],
            [InlineKeyboardButton('• ᴄʜᴇᴄᴋ ʜᴇʀᴇ ᴛᴏ ɢᴇᴛ ғɪʟᴇ •', url=file_link)]
        ]
        await status_msg.edit_text(
            text=f"📂 **File:** {file_name}\n\n🔗 Links Generated!",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")
