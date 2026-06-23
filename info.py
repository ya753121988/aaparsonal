import re
import os
import time
import asyncio
import threading
import urllib.request
from datetime import datetime
from os import environ, getenv
from Script import script

# --- Helper Functions ---
def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "on"]:
        return True
    elif value.lower() in ["false", "no", "0", "off"]:
        return False
    return default

# 🤖 BOT INFO & CREDENTIALS
SESSION = environ.get('SESSION', 'Webavbot')
API_ID = int(environ.get('API_ID', '29904834'))
API_HASH = environ.get('API_HASH', '8b4fd9ef578af114502feeafa2d31938')
BOT_TOKEN = environ.get('BOT_TOKEN', '8714836567:AAEUM36b-_Nri1HFjmAa0Yv1r_A_TPxI0eU')

# Admin Settings
ADMINS = [int(x) for x in environ.get('ADMINS', '7120801813').split()]
OWNER_USERNAME = environ.get("OWNER_USERNAME", 'ya_movies')

# 🗄️ DATABASE CONNECTION
DB_URL = environ.get('DATABASE_URI', "mongodb+srv://Testbot:Testbot@cluster0.5iukc4c.mongodb.net/?appName=Cluster0")
DB_NAME = environ.get('DATABASE_NAME', "testing")

# 📢 CHANNELS & LOGS
BIN_CHANNEL = int(environ.get("BIN_CHANNEL", '-1004498638459'))
LOG_CHANNEL = int(environ.get("LOG_CHANNEL", '-1004498638459'))
PREMIUM_LOGS = int(environ.get("PREMIUM_LOGS", '-1004498638459'))
VERIFIED_LOG = int(environ.get('VERIFIED_LOG', '-1004498638459'))
SUPPORT_GROUP = int(environ.get("SUPPORT_GROUP", "-1004498638459"))
auth_channel_str = environ.get("AUTH_CHANNEL", "-1004498638459")
AUTH_CHANNEL = [int(x) for x in auth_channel_str.split()] if auth_channel_str else []

# 🔗 LINKS & URLS
CHANNEL = environ.get('CHANNEL', 'https://t.me/AV_BOTz_UPDATE')
SUPPORT = environ.get('SUPPORT', 'https://t.me/AV_SUPPORT_GROUP')
TUTORIAL_LINK_1 = environ.get('TUTORIAL_LINK_1', 'https://t.me/1')
TUTORIAL_LINK_2 = environ.get('TUTORIAL_LINK_2', 'https://t.me/2')

# 🔐 VERIFICATION & SHORTENER
IS_VERIFY = is_enabled(environ.get("IS_VERIFY", "False"), True)
IS_SECOND_VERIFY = is_enabled(environ.get("IS_SECOND_VERIFY", "True"), True)
IS_SHORTLINK = is_enabled(environ.get('IS_SHORTLINK', "True"), True)
VERIFY_EXPIRE = int(environ.get('VERIFY_EXPIRE', 60)) 
SHORTLINK_URL = environ.get('SHORTLINK_URL', 'mdiskshortner.link')
SHORTLINK_API = environ.get('SHORTLINK_API', '96a3c0e8ae1b1abd429906762e38a40d3f2ec56c')
SHORTLINK_WEBSITE2 = environ.get("SHORTENER_WEBSITE2", "mdiskshortner.link")
SHORTLINK_API2 = environ.get("SHORTENER_API2", "96a3c0e8ae1b1abd429906762e38a40d3f2ec56c")

# ⚙️ SETTINGS & LIMITS
FSUB = is_enabled(environ.get("FSUB", "True"), True)
ENABLE_LIMIT = is_enabled(environ.get("ENABLE_LIMIT", "True"), True)
MAINTENANCE_MODE = is_enabled(environ.get("MAINTENANCE_MODE", "False"), False)
TIMEZONE = environ.get("TIMEZONE", "Asia/Kolkata")
PING_INTERVAL = int(environ.get("PING_INTERVAL", "1200"))
SLEEP_THRESHOLD = int(getenv('SLEEP_THRESHOLD', '60'))
RATE_LIMIT_TIMEOUT = int(environ.get("RATE_LIMIT_TIMEOUT", "60"))
MAX_FILES = int(environ.get("MAX_FILES", "50"))
BATCH_LIMIT = int(environ.get('BATCH_LIMIT', 60))

# 🗑️ AUTO DELETE SETTINGS
AUTO_DELETE = is_enabled(environ.get("AUTO_DELETE", "True"), True)
AUTO_DELETE_TIME = int(environ.get("AUTO_DELETE_TIME", "600"))

# 🖼️ MEDIA & CAPTIONS
QR_CODE = environ.get('QR_CODE', 'https://graph.org/file/6afb4093d5ec5c4176979.jpg')
VERIFY_IMG = environ.get("VERIFY_IMG", "https://graph.org/file/1669ab9af68eaa62c3ca4.jpg")
AUTH_PICS = environ.get('AUTH_PICS', 'https://envs.sh/AwV.jpg')
PICS = environ.get('PICS', 'https://ibb.co/VpTJNNCN')
FILE_PIC = environ.get('FILE_PIC', 'https://i.ibb.co/bj4My0bW/photo-2025-07-21-02-15-21-7529360175656861700.jpg')
FILE_CAPTION = environ.get('FILE_CAPTION', script.CAPTION)

# 🌐 SERVER & APP CONFIG
URL = environ.get("URL", "https://forward-jolyn-vnnmbs-62200c9e.koyeb.app/")
if not URL.endswith("/"): URL += "/"

# 🚀 AUTO UPTIME
def ping_server():
    while True:
        try:
            urllib.request.urlopen(URL)
        except:
            pass
        time.sleep(PING_INTERVAL)

if is_enabled(environ.get("AUTO_KEEP_ALIVE", "True"), True):
    threading.Thread(target=ping_server, daemon=True).start()
