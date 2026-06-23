import os
import random
import asyncio
import time
import re
import pytz
import logging
import datetime
from Script import script
from database.users_db import db
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from info import (
    LOG_CHANNEL, PREMIUM_LOGS, ADMINS, FSUB, BIN_CHANNEL, 
    SUPPORT, CHANNEL, PICS, FILE_PIC, FILE_CAPTION,
    AUTO_DELETE, AUTO_DELETE_TIME
)
from plugins.utils import is_user_joined
from plugins.batch import decode
from web.utils import StartTime, __version__
from plugins.check_verification import av_x_verification, verify_user_on_start
from utils import temp, get_size, get_readable_time, auto_delete_message

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    user_id = message.from_user.id
    mention = message.from_user.mention
    me2 = temp.B_NAME  
    if len(message.command) > 1:
        argument = message.command[1]
    else:
        argument = None
    if argument and argument.startswith('avbotz'):
        await verify_user_on_start(client, message)
        return
    is_referral = argument and argument.startswith("reff_")
    
    if FSUB and not is_referral:
        try:
            if not await is_user_joined(client, message):
                return
        except FloodWait as e:
            await asyncio.sleep(e.value)
            if not await is_user_joined(client, message):
                return

    # 4. Add User to Database
    user_existed = await db.is_user_exist(user_id)
    if not user_existed:
        await db.add_user(user_id, message.from_user.first_name)
        await client.send_message(
            LOG_CHANNEL,
            script.LOG_TEXT.format(me2, user_id, mention)
        )

    # 5. Handle Help Command
    if argument == "help":
        buttons = [[InlineKeyboardButton('• ᴄʟᴏsᴇ •', callback_data='close_data')]]
        help_msg = await message.reply_text(
            text=script.HELP2_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
        if AUTO_DELETE:
            asyncio.create_task(auto_delete_message(help_msg, AUTO_DELETE_TIME))
        return

    # 6. Default Welcome Message (Only sends if NO argument is passed)
    if not argument or argument == "start":
        buttons = [
            [
                InlineKeyboardButton('• ᴜᴘᴅᴀᴛᴇᴅ •', url=CHANNEL),
                InlineKeyboardButton('• sᴜᴘᴘᴏʀᴛ •', url=SUPPORT)
            ],
            [
                InlineKeyboardButton('• ʜᴇʟᴘ •', callback_data='help'),
                InlineKeyboardButton('• ᴀʙᴏᴜᴛ •', callback_data='about')
            ],
            [
                InlineKeyboardButton(
                    '✨ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ : ʀᴇᴍᴏᴠᴇ ᴀᴅꜱ ✨',
                    callback_data="premium_info"
                )
            ],
            [
                InlineKeyboardButton(
                    '🎁 ʀᴇғᴇʀ & ᴇᴀʀɴ 🎁',
                    callback_data="reffff"
                )
            ]
        ]

        welcome_msg = await message.reply_photo(
            photo=PICS,
            caption=script.START_TXT.format(mention, temp.U_NAME),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        if AUTO_DELETE:
            asyncio.create_task(auto_delete_message(welcome_msg, AUTO_DELETE_TIME))
        return

    # ================= 7. REFERRAL SYSTEM =================
    # CRASH FIX: Added "if argument and ..."
    if argument and argument.startswith("reff_"):
        try:
            inviter_id = int(argument.split("_")[1])
        except ValueError:
            reff_err = await message.reply_text("Irna 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘙𝘦𝘧𝘦𝘳 𝘓𝘪𝘯𝘬!")
            if AUTO_DELETE: asyncio.create_task(auto_delete_message(reff_err, 30))
            return
        
        if inviter_id == user_id:
            self_reff = await message.reply_text("<b>𝘠𝘰𝘶 𝘤𝘢𝘯𝘯𝘰𝘵 𝘳𝘦𝘧𝘦𝘳 𝘺𝘰𝘶𝘳𝘴𝘦𝘭𝘧! 🤣</b>")
            if AUTO_DELETE: asyncio.create_task(auto_delete_message(self_reff, 30))
            return
        
        if await db.is_user_in_list(user_id):
            already_invited = await message.reply_text("<b>𝘠𝘰𝘶 𝘩𝘢ᴠ𝘦 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘣𝘦𝘦𝘯 𝘪𝘯𝘷𝘪𝘵𝘦𝘥!</b>")
            if AUTO_DELETE: asyncio.create_task(auto_delete_message(already_invited, 30))
            return
        
        if user_existed:
            already_user = await message.reply_text("<b>𝘠𝘰𝘶 𝘢𝘳𝘦 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘢 𝘶𝘴𝘦𝘳!</b>")
            if AUTO_DELETE: asyncio.create_task(auto_delete_message(already_user, 30))
            return
        
        try:
            inviter = await client.get_users(inviter_id)
        except Exception:
            inv_err = await message.reply_text("𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘐𝘯𝘷𝘪ᴛ𝘦𝘳 𝘐𝘋.")
            if AUTO_DELETE: asyncio.create_task(auto_delete_message(inv_err, 30))
            return
        
        current_points = await db.get_refer_points(inviter_id)
        new_total = current_points + 10
        
        reff_msg = await message.reply_text(f"𝘠𝘰𝘶 𝘩𝘢ᴠ𝘦 𝘣𝘦𝘦𝘯 𝘴𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘪𝘯𝘷𝘪𝘵𝘦𝘥 𝘣𝘺 {inviter.mention}!")
        if AUTO_DELETE: asyncio.create_task(auto_delete_message(reff_msg, 60))
        
        if new_total >= 100:
            await db.add_refer_points(inviter_id, 0)
            seconds = 2592000
            expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            user_data = {"id": inviter_id, "expiry_time": expiry_time}
            await db.update_user(user_data)
            await client.send_message(PREMIUM_LOGS, script.PREMIUM_REFERRAL_LOG.format(inviter=inviter.mention, inviter_id=inviter_id, user=mention, user_id=user_id))
            await client.send_message(
                chat_id=inviter_id,
                text=f"🎉 𝖢𝗈𝗇𝗀𝗋𝖺𝗍𝗎𝗅𝖺𝗍𝗂𝗈𝗇𝗌 {inviter.mention}!\n\n𝖸𝗈𝗎 𝖼𝗈𝗅𝗅𝖾𝖼𝗍𝖾𝖽 100 𝖯𝗈𝗂𝗇𝗍𝗌 𝖺𝗇𝖽 𝗐𝗈𝗇 1 𝖬𝗈𝗇𝗍𝗁 𝖯𝗋𝖾ᴍ𝗂𝗎ᴍ 𝖲𝗎𝖻𝗌𝖼𝗋𝗂𝗉𝗍𝗂ᴏ𝗇!"
            )
        else:
            await db.add_refer_points(inviter_id, new_total)
            await client.send_message(
                chat_id=inviter_id,
                text=f"✈️ 𝖭𝖾𝗐 𝖱𝖾𝖿𝖾𝗋𝗋𝖺𝗅!\n\n{mention} 𝗃𝗈𝗂𝗇𝖾𝖽 𝗏𝗂𝖺 𝗒ᴏ𝗎𝗋 𝗅𝗂𝗇𝗄.\n➕ +10 𝖯𝗈𝗂𝗇𝗍𝗌\n💰 𝖳𝗈𝗍𝖺𝗅: {new_total}"
            )
        return

    # ================= 8. BATCH & FILE START =================
    # CRASH FIX: Ensure argument exists before decoding
    if argument and argument != "start":
        
        # Try/Except block to catch base64 errors if random text is sent
        try:
            decoded_data = decode(argument)
        except Exception:
            return # Ignore invalid arguments

        if decoded_data and decoded_data.startswith("batch-"):
            if FSUB:
                 if not await is_user_joined(client, message):
                     return

            if not await db.has_premium_access(user_id):
                verified = await av_x_verification(client, message)
                if not verified:
                    return

            try:
                _, start_id, end_id = decoded_data.split("-")
                start_id = int(start_id)
                end_id = int(end_id)
                status_msg = await message.reply_text(
                    "🔄 **𝘗𝘳𝘰𝘤𝘦𝘴𝘴𝘪𝘯𝘨 𝘉𝘢𝘵ᴄ𝘩 𝘙𝘦𝘲𝘶𝘦𝘴𝘵...**\n"
                    "<i>𝘚𝘦𝘯𝘥𝘪𝘯𝘨 𝘺ᴏᴜร์ 𝘧𝘪𝘭𝘦𝘴 </i>"
                )
                for i in range(start_id, end_id + 1):
                    try:
                        msg_obj = await client.get_messages(int(BIN_CHANNEL), i)
                        if not msg_obj or msg_obj.empty: continue
                        
                        file_name = "File"
                        if msg_obj.video: file_name = msg_obj.video.file_name
                        elif msg_obj.document: file_name = msg_obj.document.file_name
                        elif msg_obj.audio: file_name = msg_obj.audio.file_name
                        if not file_name: file_name = "File"
                        caption = FILE_CAPTION.format(CHANNEL, file_name)
                        file_btn = InlineKeyboardMarkup(
                            [[InlineKeyboardButton("🔴 ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ & ғᴀsᴛ ᴅᴏᴡɴʟᴏᴀᴅ 🔴", callback_data=f'stream#{i}')]]
                        )
                        sent_msg = await client.copy_message(
                            chat_id=user_id,
                            from_chat_id=int(BIN_CHANNEL),
                            message_id=i,
                            caption=caption,
                            reply_markup=file_btn
                        )
                        if AUTO_DELETE:
                            asyncio.create_task(auto_delete_message(sent_msg, AUTO_DELETE_TIME)) 
                        await asyncio.sleep(1.5)

                    except FloodWait as e:
                        await status_msg.edit(f"⏳ **High Traffic:** Waiting {e.value}s...")
                        await asyncio.sleep(e.value + 2)
                    except Exception:
                        pass
                await status_msg.delete()
                
                # টাইম ক্যালকুলেশন (সেকেন্ড থেকে মিনিট)
                del_time_display = AUTO_DELETE_TIME // 60
                warn_msg = await message.reply_text(
                    f"✅ 𝖠𝗅𝗅 𝖥𝗂𝗅𝖾𝗌 𝖢𝗈𝗆𝗉𝗅𝖾𝗍𝖾 😁!\n\n"
                    f"⚠️ 𝖨𝖬𝖯𝖮𝖱𝖳𝖠𝖭𝖳: 𝖥𝗂𝗅𝖾𝗌 𝗐𝗂𝗅𝗅 𝖻𝖾 𝖣𝖤𝖫𝖤𝖳𝖤𝖣 𝗂𝗇 {del_time_display} 𝖬𝗂𝗇𝗎𝗍𝖾𝗌.\n"
                    f"📥 𝖥𝗈𝗋𝗐𝖺𝗋𝖽 𝗍𝗈 𝖲𝖺𝗏𝖾𝖽 𝖬𝖾𝗌𝚜𝖺ɢ𝖾𝗌 𝖭𝖶!"
                )
                if AUTO_DELETE:
                    asyncio.create_task(auto_delete_message(warn_msg, AUTO_DELETE_TIME))
                return
            except Exception as e:
                err_m = await message.reply_text(f"❌ Error: {e}")
                if AUTO_DELETE: asyncio.create_task(auto_delete_message(err_m, 60))
                return

        # ================= SINGLE FILE START =================
        if argument.startswith("file_"):
            if FSUB:
                 if not await is_user_joined(client, message):
                     return

            if not await db.has_premium_access(user_id):
                verified = await av_x_verification(client, message)
                if not verified:
                    return
            try:
                _, file_id = argument.split("_", 1)
            except ValueError:
                inv_f = await message.reply("<b>⚠️ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘍𝘪𝘭𝘦 𝘓𝘪𝘯𝘬!</b>")
                if AUTO_DELETE: asyncio.create_task(auto_delete_message(inv_f, 30))
                return
            
            original_message = await client.get_messages(int(BIN_CHANNEL), int(file_id))
            media = original_message.document or original_message.video or original_message.audio
            caption = None
            if media:
                file_name = getattr(media, "file_name", "Unnamed File") or "Unnamed File"
                try: caption = FILE_CAPTION.format(channel=CHANNEL, file_name=file_name)
                except: caption = FILE_CAPTION.format(CHANNEL, file_name)
            
            btn_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔴 ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ & ғᴀsᴛ ᴅᴏᴡɴʟᴏᴀᴅ 🔴", callback_data=f'stream#{file_id}')]]
            )
            sent_msg = await client.copy_message(
                chat_id=user_id,
                from_chat_id=int(BIN_CHANNEL),
                message_id=int(file_id),
                caption=caption,
                reply_markup=btn_markup
            )
            
            del_time_display = AUTO_DELETE_TIME // 60
            warn_msg = await message.reply_text(
            f"⚠️ 𝖨𝖬𝖯𝖮𝖱𝖳𝖠𝖭𝖳: 𝖥𝗂𝗅𝖾 𝗐𝗂𝗅𝗅 𝖻𝖾 𝖣𝖤𝖫𝖤𝖳𝖤𝖣 𝗂𝗇 {del_time_display} 𝖬𝗂𝗇𝗎𝗍𝖾𝗌.\n"
            f"📥 𝖥𝗈𝗋ᴡᴀʀ𝖽 𝗍𝗈 𝖲𝖺𝗏𝖾𝖽 𝖬𝖾𝗌𝚜𝖺ɢ𝖾𝗌!",
            quote=True
            )
            if AUTO_DELETE:
                asyncio.create_task(auto_delete_message(sent_msg, AUTO_DELETE_TIME)) 
                asyncio.create_task(auto_delete_message(warn_msg, AUTO_DELETE_TIME))
            return

@Client.on_message(filters.command("autodelete") & filters.user(ADMINS))
async def autodelete_info(client, message):
    """📌 এটি একটি নতুন কমান্ড যা অটো ডিলিট স্ট্যাটাস দেখাবে"""
    status = "Enabled ✅" if AUTO_DELETE else "Disabled ❌"
    del_m = await message.reply_text(
        f"🗑️ **Auto Delete Status**\n\n"
        f"📊 Status: {status}\n"
        f"⏰ Time: {AUTO_DELETE_TIME // 60} Minutes\n\n"
        f"💡 আপনি info.py থেকে এটি পরিবর্তন করতে পারেন।"
    )
    if AUTO_DELETE: asyncio.create_task(auto_delete_message(del_m, 60))

@Client.on_message(filters.command("add_point") & filters.user(ADMINS))
async def add_points_admin(client, message):
    try:
        parts = message.text.split()
        if len(parts) != 3: 
            usage = await message.reply("Usage: `/add_point user_id amount`")
            if AUTO_DELETE: asyncio.create_task(auto_delete_message(usage, 30))
            return
        user_id = int(parts[1])
        amount = int(parts[2])
        try:
            usr = await client.get_users(user_id)
            u_name = usr.first_name
            u_mention = usr.mention
            u_username = f"@{usr.username}" if usr.username else "N/A"
        except:
            u_name = "Unknown"
            u_mention = f"`{user_id}`"
            u_username = "N/A"
        new_balance = await db.change_points(user_id, amount)
        if new_balance >= 100:
            await db.add_refer_points(user_id, 0)
            seconds = 2592000 # 30 Days in seconds
            expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            await db.update_user({"id": user_id, "expiry_time": expiry_time})
            await client.send_message(PREMIUM_LOGS, script.PREMIUM_POINTS_LOG.format(user=u_mention, name=u_name, uid=user_id, username=u_username, added_by=message.from_user.mention, points=amount))
            p_msg = await message.reply(
                f"✅ 𝖯𝗈𝗂𝗇𝗍𝗌 𝖠𝖽𝖽𝖾𝖽 & 𝖯𝗋𝖾ᴍɪᴜᴍ 𝖠𝖼ᴛɪ𝗏𝖺ᴛ𝖾𝖽!\n\n"
                f"👤 𝖴𝗌𝖾𝗋: {u_mention}\n"
                f"💰 𝖠𝖽𝖽𝖾𝖽: {amount}\n"
                f"🎉 𝖴𝗌𝖾𝗋 𝗎𝗉𝗀𝗋𝖺𝖽𝖾𝖽 𝗍𝗈 𝖯𝗋𝖾𝗆𝗂ᴜᴍ 𝖿ᴏ𝗋 1 𝖬ᴏ𝗇ᴛ𝗁!\n"
            )
            if AUTO_DELETE: asyncio.create_task(auto_delete_message(p_msg, 60))
            try:
                await client.send_message(
                    chat_id=user_id,
                    text=(
                        f"🎉 𝖢𝗈𝗇𝗀𝗋𝖺ᴛ𝗎𝗅𝖺ᴛ𝗂ᴏɴ𝗌!\n\n"
                        f"𝖠𝖽ᴍɪɴ 𝖺𝖽𝖽𝖾𝖽 {amount} 𝗉ᴏɪ𝗇ᴛ𝗌 𝗍ᴏ 𝗒ᴏᴜ𝗋 𝗐𝖺𝗅𝗅𝖾ᴛ.\n"
                        f"𝖸ᴏ𝗎 𝗋𝖾𝖺𝼇𝗁𝖾𝖽 100 𝖯ᴏɪ𝗇ᴛ𝗌 𝗍𝖺𝗋ɢᴇᴛ!\n\n"
                        f"💎 1 𝖬ᴏ𝗇ᴛ𝗁 𝖯𝗋𝖾ᴍ𝗂ᴜᴍ 𝖲ᴜ𝖻𝗌𝖼𝗋𝗂𝗉ᴛ𝗂ᴏ𝗇 𝖠𝼇ᴛ𝗂𝗏𝖺ᴛ𝖾𝖽!"
                    )
                )
            except Exception:
                pass
                
        else:
            await client.send_message(PREMIUM_LOGS, script.POINTS_ADDED_LOG.format(user=u_mention, name=u_name, uid=user_id, added_by=message.from_user.mention, amount=amount, balance=new_balance))
            p_msg2 = await message.reply(
               f"✅ 𝖠𝖽𝖽𝖾𝖽 {amount} 𝗉ᴏɪ𝗇ᴛ𝗌.\n👤 𝖴𝗌𝖾𝗋: {u_mention}\n🔢 𝖡𝖺𝗅𝖺𝗇𝼇𝖾: {new_balance}"
            )
            if AUTO_DELETE: asyncio.create_task(auto_delete_message(p_msg2, 60))
            try:
                await client.send_message(chat_id=user_id, text=f"🎉 𝖠𝖽𝗆𝗂𝗇 𝖺𝖽𝖽𝖾𝖽 {amount} 𝗉ᴏɪ𝗇ᴛ𝗌 𝗍ᴏ 𝗒ᴏᴜ𝗋 𝗐𝖺𝗅𝗅𝖾ᴛ. 💰")
            except: pass

    except Exception as e:
        await message.reply(f"Error: {e}")
        

@Client.on_message(filters.command("remove_point") & filters.user(ADMINS))
async def remove_points_admin(client, message):
    try:
        parts = message.text.split()
        if len(parts) != 3: return await message.reply("Usage: `/remove_point user_id amount`")
        user_id = int(parts[1])
        amount = int(parts[2])
        new_balance = await db.change_points(user_id, -amount)
        rem_msg = await message.reply(f"✅ Removed {amount} points.\nUser: `{user_id}`\nBalance: {new_balance}")
        if AUTO_DELETE: asyncio.create_task(auto_delete_message(rem_msg, 60))
    except Exception as e:
        await message.reply(f"Error: {e}")

@Client.on_message(filters.command("about"))
async def about(client, message):
    buttons = [[
       InlineKeyboardButton('💻 sᴏᴜʀᴄᴇ ᴄᴏᴅᴇ', url='https://github.com/Botsthe/AV-FILE-TO-LINK-PRO.git')
    ],[
       InlineKeyboardButton('• ᴄʟᴏsᴇ •', callback_data='close_data')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    about_m = await message.reply_text(
        text=script.ABOUT_TXT.format(temp.B_NAME, temp.B_NAME, get_readable_time(time.time() - StartTime), __version__),
        disable_web_page_preview=True, 
        reply_markup=reply_markup
    )
    if AUTO_DELETE: asyncio.create_task(auto_delete_message(about_m, AUTO_DELETE_TIME))

@Client.on_message(filters.command("help"))
async def help(client, message):
    btn = [[InlineKeyboardButton('• ᴄʟᴏsᴇ •', callback_data='close_data')]]
    reply_markup = InlineKeyboardMarkup(btn)
    help_m = await message.reply_text(
        text=script.HELP2_TXT,
        disable_web_page_preview=True, 
        reply_markup=reply_markup
    )
    if AUTO_DELETE: asyncio.create_task(auto_delete_message(help_m, AUTO_DELETE_TIME))

@Client.on_message(filters.private & filters.command("files"))
async def list_user_files(client, message: Message):
    user_id = message.from_user.id
    files = await db.files.find({"user_id": user_id}).to_list(length=100)
    if not files:
        no_f = await message.reply_text("❌ Yᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴜᴘʟᴏᴀᴅᴇᴅ ᴀɴʏ ғɪʟᴇꜱ.")
        if AUTO_DELETE: asyncio.create_task(auto_delete_message(no_f, 30))
        return
    page, per_page = 1, 7
    total_pages = (len(files) + per_page - 1) // per_page
    btns = []
    for f in files[:per_page]:
        btns.append([InlineKeyboardButton(f["file_name"][:40], callback_data=f"sendfile_{f['file_id']}")])
    nav = [InlineKeyboardButton("❌ ᴄʟᴏsᴇ ❌", callback_data="close_data")]
    if page < total_pages: nav.insert(0, InlineKeyboardButton("➡️ Nᴇxᴛ", callback_data=f"filespage_{page + 1}"))
    btns.append(nav)
    f_list = await message.reply_photo(photo=FILE_PIC, caption=f"📁 Tᴏᴛᴀʟ ғɪʟᴇꜱ: {len(files)} | Pᴀɢᴇ {page}/{total_pages}", reply_markup=InlineKeyboardMarkup(btns))
    if AUTO_DELETE: asyncio.create_task(auto_delete_message(f_list, AUTO_DELETE_TIME))

@Client.on_message(filters.private & filters.command("del_files"))
async def delete_files_list(client, message):
    user_id = message.from_user.id
    files = await db.files.find({"user_id": user_id}).to_list(length=100)
    if not files:
        no_d = await message.reply_text("❌ Yᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴜᴘʟᴏᴀᴅᴇᴅ ᴀɴʏ ғɪʟᴇꜱ.")
        if AUTO_DELETE: asyncio.create_task(auto_delete_message(no_d, 30))
        return
    page, per_page = 1, 7
    total_pages = (len(files) + per_page - 1) // per_page
    btns = []
    for f in files[:per_page]:
        btns.append([InlineKeyboardButton(f["file_name"][:40], callback_data=f"deletefile_{f['file_id']}")])
    nav = [InlineKeyboardButton("❌ ᴄʟᴏsᴇ ❌", callback_data="close_data")]
    if page < total_pages: nav.insert(0, InlineKeyboardButton("➡️ Nᴇxᴛ", callback_data=f"delfilespage_{page + 1}"))
    btns.append(nav)
    d_list = await message.reply_photo(photo=FILE_PIC, caption=f"📁 Tᴏᴛᴀʟ ғɪʟᴇꜱ: {len(files)} | Pᴀɢᴇ {page}/{total_pages}", reply_markup=InlineKeyboardMarkup(btns))
    if AUTO_DELETE: asyncio.create_task(auto_delete_message(d_list, AUTO_DELETE_TIME))
