import os
import telebot
from telebot import types
from flask import Flask
from pymongo import MongoClient
import yt_dlp
import threading

# =========================
# CONFIG
# =========================

TOKEN = "8559319537:AAG4BulP--sETSx2u67zvo5tcJ5x5snzPz0"
MONGO_URL = "mongodb+srv://javohirtojiyev99_db_user:<db_password>@cluster0.4skcgpy.mongodb.net/?appName=Cluster0"

FORCE_CHANNELS = [
    "@CLC_KINO",
    "@CLC_KINO_BOT"
]

ADMIN_ID = 7808985151

bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# =========================
# MONGODB
# =========================

client = MongoClient(MONGO_URL)
db = client["video_bot"]
users_col = db["users"]

# =========================
# FLASK
# =========================

@app.route('/')
def home():
    return "Bot ishlayapti 🚀"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# USER SAVE
# =========================

def save_user(user_id):
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id})

# =========================
# FORCE SUBSCRIBE
# =========================

def check_sub(user_id):
    try:
        for channel in FORCE_CHANNELS:
            member = bot.get_chat_member(channel, user_id)

            if member.status in ["left", "kicked"]:
                return False

        return True

    except:
        return False

def force_sub_markup():
    markup = types.InlineKeyboardMarkup()

    for channel in FORCE_CHANNELS:
        markup.add(
            types.InlineKeyboardButton(
                f"📢 {channel}",
                url=f"https://t.me/{channel.replace('@','')}"
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            "✅ Tekshirish",
            callback_data="check_sub"
        )
    )

    return markup

# =========================
# START
# =========================

@bot.message_handler(commands=['start'])
def start(message):

    user_id = message.from_user.id
    save_user(user_id)

    if not check_sub(user_id):
        bot.send_photo(
            message.chat.id,
            "https://i.imgur.com/8Km9tLL.jpg",
            caption="""
🌈━━━━━━━━━━━━━━🌈
🔥 VIDEO YUKLASH BOT 🔥
🌈━━━━━━━━━━━━━━🌈

📢 Botdan foydalanish uchun
kanallarga obuna bo‘ling.

✨ Rangli interfeys
⚡ Tez yuklash
🎬 TikTok / Instagram / YouTube

👇 Pastdagi tugmalar orqali obuna bo‘ling
""",
            reply_markup=force_sub_markup()
        )
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row("🇺🇿 Uzbekcha", "🇷🇺 Русский")
    markup.row("🇺🇸 English")

    bot.send_photo(
        message.chat.id,
        "https://i.imgur.com/8Km9tLL.jpg",
        caption="""
🌈━━━━━━━━━━━━━━🌈
🤖 VIDEO DOWNLOADER BOT
🌈━━━━━━━━━━━━━━🌈

🎬 TikTok
📸 Instagram
▶️ YouTube

📥 Video link yuboring!
""",
        reply_markup=markup
    )

# =========================
# CHECK SUB
# =========================

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):

    if check_sub(call.from_user.id):

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        markup.row("🇺🇿 Uzbekcha", "🇷🇺 Русский")
        markup.row("🇺🇸 English")

        bot.send_message(
            call.message.chat.id,
            "✅ Obuna tasdiqlandi!\n\n📥 Endi video link yuboring.",
            reply_markup=markup
        )

    else:
        bot.answer_callback_query(
            call.id,
            "❌ Hali obuna bo‘lmadingiz!"
        )

# =========================
# QUALITY SELECT
# =========================

user_links = {}

@bot.message_handler(func=lambda message: "http" in message.text)
def get_link(message):

    if not check_sub(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "❌ Avval kanallarga obuna bo‘ling!",
            reply_markup=force_sub_markup()
        )
        return

    user_links[message.chat.id] = message.text

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "🎥 1080p",
            callback_data="1080"
        ),
        types.InlineKeyboardButton(
            "📹 720p",
            callback_data="720"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "📱 480p",
            callback_data="480"
        ),
        types.InlineKeyboardButton(
            "⚡ 360p",
            callback_data="360"
        )
    )

    bot.send_message(
        message.chat.id,
        """
🌈━━━━━━━━━━━━━━🌈
🎬 VIDEO QUALITY TANLANG
🌈━━━━━━━━━━━━━━🌈
""",
        reply_markup=markup
    )

# =========================
# DOWNLOAD VIDEO
# =========================

@bot.callback_query_handler(func=lambda call: call.data in ["1080", "720", "480", "360"])
def download_video(call):

    chat_id = call.message.chat.id
    quality = call.data

    if chat_id not in user_links:
        return

    url = user_links[chat_id]

    bot.send_message(
        chat_id,
        f"⏳ {quality} format yuklanmoqda..."
    )

    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'
    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(url, download=True)

            file_name = ydl.prepare_filename(info)

        with open(file_name, 'rb') as video:

            bot.send_video(
                chat_id,
                video,
                caption=f"""
🌈━━━━━━━━━━━━━━🌈
✅ VIDEO TAYYOR
🎬 Quality: {quality}p
🌈━━━━━━━━━━━━━━🌈
"""
            )

        os.remove(file_name)

    except Exception as e:

        bot.send_message(
            chat_id,
            f"❌ Xatolik:\n{e}"
        )

# =========================
# ADMIN PANEL
# =========================

@bot.message_handler(commands=['admin'])
def admin_panel(message):

    if message.from_user.id != ADMIN_ID:
        return

    users = users_col.count_documents({})

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "📊 Statistika",
            callback_data="stats"
        )
    )

    bot.send_message(
        message.chat.id,
        f"""
🌈━━━━━━━━━━━━━━🌈
👑 ADMIN PANEL
🌈━━━━━━━━━━━━━━🌈

👥 Foydalanuvchilar: {users}

🚀 Bot aktiv ishlamoqda
""",
        reply_markup=markup
    )

# =========================
# RUN
# =========================

threading.Thread(target=run_web).start()

print("Bot ishladi 🚀")

bot.infinity_polling()
