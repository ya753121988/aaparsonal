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
    SUPPORT, CHANNEL, PICS, FILE_PIC, FILE_CAPTION
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
        await message.reply_text(
            text=script.HELP2_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
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

        await message.reply_photo(
            photo=PICS,
            caption=script.START_TXT.format(mention, temp.U_NAME),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # ================= 7. REFERRAL SYSTEM =================
    # CRASH FIX: Added "if argument and ..."
    if argument and argument.startswith("reff_"):
        try:
            inviter_id = int(argument.split("_")[1])
        except ValueError:
            return await message.reply_text("Irna 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘙𝘦𝘧𝘦𝘳 𝘓𝘪𝘯𝘬!")
        
        if inviter_id == user_id:
            return await message.reply_text("<b>𝘠𝘰𝘶 𝘤𝘢𝘯𝘯𝘰𝘵 𝘳𝘦𝘧𝘦𝘳 𝘺𝘰𝘶𝘳𝘴𝘦𝘭𝘧! 🤣</b>")
        
        if await db.is_user_in_list(user_id):
            return await message.reply_text("<b>𝘠𝘰𝘶 𝘩𝘢𝘷𝘦 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘣𝘦𝘦𝘯 𝘪𝘯𝘷𝘪𝘵𝘦𝘥!</b>")
        
        if user_existed:
            return await message.reply_text("<b>𝘠𝘰𝘶 𝘢𝘳𝘦 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘢 𝘶𝘴𝘦𝘳!</b>")
        
        try:
            inviter = await client.get_users(inviter_id)
        except Exception:
            return await message.reply_text("𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘐𝘯𝘷𝘪𝘵𝘦𝘳 𝘐𝘋.")
        
        current_points = await db.get_refer_points(inviter_id)
        new_total = current_points + 10
        
        await message.reply_text(f"𝘠𝘰𝘶 𝘩𝘢𝘷𝘦 𝘣𝘦𝘦𝘯 𝘴𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘪𝘯𝘷𝘪𝘵𝘦𝘥 𝘣𝘺 {inviter.mention}!")
        
        if new_total >= 100:
            await db.add_refer_points(inviter_id, 0)
            seconds = 2592000
            expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            user_data = {"id": inviter_id, "expiry_time": expiry_time}
            await db.update_user(user_data)
            await client.send_message(PREMIUM_LOGS, script.PREMIUM_REFERRAL_LOG.format(inviter=inviter.mention, inviter_id=inviter_id, user=mention, user_id=user_id))
            await client.send_message(
                chat_id=inviter_id,
                text=f"🎉 𝖢𝗈𝗇𝗀𝗋𝖺𝗍𝗎𝗅𝖺𝗍𝗂𝗈𝗇𝗌 {inviter.mention}!\n\n𝖸𝗈𝗎 𝖼𝗈𝗅𝗅𝖾𝖼𝗍𝖾𝖽 100 𝖯𝗈𝗂𝗇𝗍𝗌 𝖺𝗇𝖽 𝗐𝗈𝗇 1 𝖬𝗈𝗇𝗍𝗁 𝖯𝗋𝖾𝗆𝗂𝗎𝗆 𝖲𝗎𝖻𝗌𝖼𝗋𝗂𝗉𝗍𝗂𝗈𝗇!"
            )
        else:
            await db.add_refer_points(inviter_id, new_total)
            await client.send_message(
                chat_id=inviter_id,
                text=f"✈️ 𝖭𝖾𝗐 𝖱𝖾𝖿𝖾𝗋𝗋𝖺𝗅!\n\n{mention} 𝗃𝗈𝗂𝗇𝖾𝖽 𝗏𝗂𝖺 𝗒𝗈𝗎𝗋 𝗅𝗂𝗇𝗄.\n➕ +10 𝖯𝗈𝗂𝗇𝗍𝗌\n💰 𝖳𝗈𝗍𝖺𝗅: {new_total}"
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
                    "🔄 **𝘗𝘳𝘰𝘤𝘦𝘴𝘴𝘪𝘯𝘨 𝘉𝘢𝘵𝘤𝘩 𝘙𝘦𝘲𝘶𝘦𝘴𝘵...**\n"
                    "<i>𝘚𝘦𝘯𝘥𝘪𝘯𝘨 𝘺𝘰𝘶𝘳 𝘧𝘪𝘭𝘦𝘴 </i>"
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
                        asyncio.create_task(auto_delete_message(sent_msg, 600)) 
                        await asyncio.sleep(1.5)

                    except FloodWait as e:
                        await status_msg.edit(f"⏳ **High Traffic:** Waiting {e.value}s...")
                        await asyncio.sleep(e.value + 2)
                    except Exception:
                        pass
                await status_msg.delete()
                warn_msg = await message.reply_text(
                    f"✅ 𝖠𝗅𝗅 𝖥𝗂𝗅𝖾𝗌 𝖢𝗈𝗆𝗉𝗅𝖾𝗍𝖾 😁!\n\n"
                    f"⚠️ 𝖨𝖬𝖯𝖮𝖱𝖳𝖠𝖭𝖳: 𝖥𝗂𝗅𝖾𝗌 𝗐𝗂𝗅𝗅 𝖻𝖾 𝖣𝖤𝖫𝖤𝖳𝖤𝖣 𝗂𝗇 10 𝖬𝗂𝗇𝗎𝗍𝖾𝗌.\n"
                    f"📥 𝖥𝗈𝗋𝗐𝖺𝗋𝖽 𝗍𝗈 𝖲𝖺𝗏𝖾𝖽 𝖬𝖾𝗌𝗌𝖺𝗀𝖾𝗌 𝖭𝖮𝖶!"
                )
                asyncio.create_task(auto_delete_message(warn_msg, 600))
                return
            except Exception as e:
                await message.reply_text(f"❌ Error: {e}")
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
                return await message.reply("<b>⚠️ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘍𝘪𝘭𝘦 𝘓𝘪𝘯𝘬!</b>")
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
            warn_msg = await message.reply_text(
            f"⚠️ 𝖨𝖬𝖯𝖮𝖱𝖳𝖠𝖭𝖳: 𝖥𝗂𝗅𝖾 𝗐𝗂𝗅𝗅 𝖻𝖾 𝖣𝖤𝖫𝖤𝖳𝖤𝖣 𝗂𝗇 10 𝖬𝗂𝗇𝗎𝗍𝖾𝗌.\n"
            f"📥 𝖥𝗈𝗋𝖺𝗋𝖽 𝗍𝗈 𝖲𝖺𝗏𝖾𝖽 𝖬𝖾𝗌𝗌𝖺𝗀𝖾𝗌!",
            quote=True
            )
            asyncio.create_task(auto_delete_message(sent_msg, 600)) 
            asyncio.create_task(auto_delete_message(warn_msg, 600))
            return

@Client.on_message(filters.command("add_point") & filters.user(ADMINS))
async def add_points_admin(client, message):
    try:
        parts = message.text.split()
        if len(parts) != 3: 
            return await message.reply("Usage: `/add_point user_id amount`")
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
            await message.reply(
                f"✅ 𝖯𝗈𝗂𝗇𝗍𝗌 𝖠𝖽𝖽𝖾𝖽 & 𝖯𝗋𝖾𝗆𝗂𝗎𝗆 𝖠𝖼𝗍𝗂𝗏𝖺𝗍𝖾𝖽!\n\n"
                f"👤 𝖴𝗌𝖾𝗋: {u_mention}\n"
                f"💰 𝖠𝖽𝖽𝖾𝖽: {amount}\n"
                f"🎉 𝖴𝗌𝖾𝗋 𝗎𝗉𝗀𝗋𝖺𝖽𝖾𝖽 𝗍𝗈 𝖯𝗋𝖾𝗆𝗂𝗎𝗆 𝖿𝗈𝗋 1 𝖬𝗈𝗇𝗍𝗁!\n"
                f"📢 𝖫𝗈𝗀 𝗌𝖾𝗇𝗍 𝗍𝗈 𝖢𝗁𝖺𝗇𝗇𝖾𝗅."
            )
            try:
                await client.send_message(
                    chat_id=user_id,
                    text=(
                        f"🎉 𝖢𝗈𝗇𝗀𝗋𝖺𝗍𝗎𝗅𝖺𝗍𝗂𝗈𝗇𝗌!\n\n"
                        f"𝖠𝖽𝗆𝗂𝗇 𝖺𝖽𝖽𝖾𝖽 {amount} 𝗉𝗈𝗂𝗇𝗍𝗌 𝗍𝗈 𝗒𝗈𝗎𝗋 𝗐𝖺𝗅𝗅𝖾𝗍.\n"
                        f"𝖸𝗈𝗎 𝗋𝖾𝖺𝖼𝗁𝖾𝖽 100 𝖯𝗈𝗂𝗇𝗍𝗌 𝗍𝖺𝗋𝗀𝖾𝗍!\n\n"
                        f"💎 1 𝖬𝗈𝗇𝗍𝗁 𝖯𝗋𝖾𝗆𝗂𝗎𝗆 𝖲𝗎𝖻𝗌𝖼𝗋𝗂𝗉𝗍𝗂𝗈𝗇 𝖠𝖼𝗍𝗂𝗏𝖺𝗍𝖾𝖽!"
                    )
                )
            except Exception:
                await message.reply("⚠️ Premium given, but failed to DM user.")
                
        else:
            await client.send_message(PREMIUM_LOGS, script.POINTS_ADDED_LOG.format(user=u_mention, name=u_name, uid=user_id, added_by=message.from_user.mention, amount=amount, balance=new_balance))
            try:
                await client.send_message(
                    chat_id=user_id,
                    text=(
                        f"🎉 𝖢𝗈𝗇𝗀𝗋𝖺𝗍𝗎𝗅𝖺𝗍𝗂𝗈𝗇𝗌!\n\n"
                        f"𝖠𝖽𝗆𝗂𝗇 𝖺𝖽𝖽𝖾𝖽 {amount} 𝗉𝗈𝗂𝗇𝗍𝗌 𝗍𝗈 𝗒𝗈𝗎𝗋 𝗐𝖺𝗅𝗅𝖾𝗍. 💰\n"
                        f"🔢 𝖢𝗎𝗋𝗋𝖾𝗇𝗍 𝖡𝖺𝗅𝖺𝗇𝖼𝖾: {new_balance}\n"
                        f"🎯 𝖦𝗈𝖺𝗅: 𝖱𝖾𝖺𝖼𝗁 100 𝖯𝗈𝗂𝗇𝗍𝗌 𝖿𝗈𝗋 𝖥𝗋𝖾𝖾 𝖯𝗋𝖾𝗆𝗂𝗎𝗆!"
                    )
                )
                user_notified = "User Notified ✅"
            except:
                user_notified = "Failed to DM User ❌"
            await message.reply(
               f"✅ 𝖠𝖽𝖽𝖾𝖽 {amount} 𝗉𝗈𝗂𝗇𝗍𝗌.\n"
               f"👤 𝖴𝗌𝖾𝗋: {u_mention}\n"
               f"🔢 𝖡𝖺𝗅𝖺𝗇𝖼𝖾: {new_balance}\n"
               f"📢 𝖫𝗈𝗀 𝗌𝖾𝗇𝗍 & {user_notified}"
            )

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
        await message.reply(f"✅ Removed {amount} points.\nUser: `{user_id}`\nBalance: {new_balance}")
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
    await message.reply_text(
        text=script.ABOUT_TXT.format(temp.B_NAME, temp.B_NAME, get_readable_time(time.time() - StartTime), __version__),
        disable_web_page_preview=True, 
        reply_markup=reply_markup
    )

 
@Client.on_message(filters.command("help"))
async def help(client, message):
    btn = [[
       InlineKeyboardButton('• ᴄʟᴏsᴇ •', callback_data='close_data')
    ]]
    reply_markup = InlineKeyboardMarkup(btn)
    await message.reply_text(
        text=script.HELP2_TXT,
        disable_web_page_preview=True, 
        reply_markup=reply_markup
    )

@Client.on_message(filters.private & filters.command("files"))
async def list_user_files(client, message: Message):
    user_id = message.from_user.id
    files = await db.files.find({"user_id": user_id}).to_list(length=100)
    if not files:
        return await message.reply_text("❌ Yᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴜᴘʟᴏᴀᴅᴇᴅ ᴀɴʏ ғɪʟᴇꜱ.")
    page = 1
    per_page = 7
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = (len(files) + per_page - 1) // per_page
    btns = []
    for f in files[start:end]:
        name = f["file_name"][:40]
        btns.append([InlineKeyboardButton(name, callback_data=f"sendfile_{f['file_id']}")])
    nav_btns = []
    if page < total_pages:
        nav_btns.append(InlineKeyboardButton("➡️ Nᴇxᴛ", callback_data=f"filespage_{page + 1}"))
    nav_btns.append(InlineKeyboardButton("❌ ᴄʟᴏsᴇ ❌", callback_data="close_data"))
    btns.append(nav_btns)
    await message.reply_photo(photo=FILE_PIC,
        caption=f"📁 Tᴏᴛᴀʟ ғɪʟᴇꜱ: {len(files)} | Pᴀɢᴇ {page}/{total_pages}",
        reply_markup=InlineKeyboardMarkup(btns)
    )

@Client.on_message(filters.private & filters.command("del_files"))
async def delete_files_list(client, message):
    user_id = message.from_user.id
    files = await db.files.find({"user_id": user_id}).to_list(length=100)
    if not files:
        return await message.reply_text("❌ Yᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴜᴘʟᴏᴀᴅᴇᴅ ᴀɴʏ ғɪʟᴇꜱ.")
    page = 1
    per_page = 7
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = (len(files) + per_page - 1) // per_page
    btns = []
    for f in files[start:end]:
        name = f["file_name"][:40]
        btns.append([InlineKeyboardButton(name, callback_data=f"deletefile_{f['file_id']}")])
    nav_btns = []
    if page < total_pages:
        nav_btns.append(InlineKeyboardButton("➡️ Nᴇxᴛ", callback_data=f"delfilespage_{page + 1}"))
    nav_btns.append(InlineKeyboardButton("❌ ᴄʟᴏsᴇ ❌", callback_data="close_data"))
    btns.append(nav_btns)
    await message.reply_photo(photo=FILE_PIC,
        caption=f"📁 Tᴏᴛᴀʟ ғɪʟᴇꜱ: {len(files)} | Pᴀɢᴇ {page}/{total_pages}",
        reply_markup=InlineKeyboardMarkup(btns)
   )
    
