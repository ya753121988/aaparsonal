import asyncio
import time
import math
import urllib.request
from pyrogram.types import Message
from info import AUTO_DELETE, AUTO_DELETE_TIME, URL, PING_INTERVAL

# ===============================
# GLOBAL TEMP STORAGE
# ===============================
class Temp:
    ME = None
    U_NAME = None
    B_NAME = None
    B_LINK = None

temp = Temp()

# ===============================
# TIME & SIZE HELPERS
# ===============================
def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for i in range(len(time_list)):
        time_list[i] = str(time_list[i]) + time_suffix_list[i]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "
    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time

def get_size(size):
    if not size:
        return "0 B"
    size = int(size)
    units = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size, 1024)))
    return f"{round(size / math.pow(1024, i), 2)} {units[i]}"

# ===============================
# AUTO DELETE LOGIC
# ===============================
async def auto_delete_message(message: Message, delay: int = None):
    """এটি নির্দিষ্ট সময় পর মেসেজ ডিলিট করবে"""
    if not AUTO_DELETE:
        return
    
    wait_time = delay if delay is not None else AUTO_DELETE_TIME
    await asyncio.sleep(wait_time)
    
    try:
        await message.delete()
        if hasattr(message, 'reply_to_message') and message.reply_to_message:
            try:
                await message.reply_to_message.delete()
            except:
                pass
    except Exception:
        pass

# ===============================
# PING SERVER FUNCTION (মেইন ফিক্স)
# ===============================
def ping_server():
    """বটকে অ্যাক্টিভ রাখার জন্য সার্ভার পিং করার ফাংশন"""
    while True:
        try:
            urllib.request.urlopen(URL)
            print(f"Ping successful to: {URL}")
        except Exception as e:
            print(f"Ping failed: {e}")
        time.sleep(PING_INTERVAL)
