import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters
from gtts import gTTS
from apscheduler.schedulers.background import BackgroundScheduler
import json

# Flask app
app = Flask(__name__)

# Load environment variables
TELEGRAM_TOKEN = "7654820492:AAGpULuFlQ3FDl5Gc95fPY0iV02lAoPJ9Do"
bot = Bot(token=TELEGRAM_TOKEN)

# File to store user chat IDs
CHAT_IDS_FILE = "chat_ids.json"

# Helper function to load chat IDs from file
def load_chat_ids():
    if os.path.exists(CHAT_IDS_FILE):
        with open(CHAT_IDS_FILE, "r") as file:
            return json.load(file)
    return []

# Helper function to save chat IDs to file
def save_chat_ids(chat_ids):
    with open(CHAT_IDS_FILE, "w") as file:
        json.dump(chat_ids, file)

# Track user chat IDs
def track_user(chat_id):
    chat_ids = load_chat_ids()
    if chat_id not in chat_ids:
        chat_ids.append(chat_id)
        save_chat_ids(chat_ids)

# Telegram bot commands
async def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    track_user(chat_id)
    await update.message.reply_text(
        "Hi! I’m TuneTalk Bot, and I'm here to help you with pronunciation. Type /pronounce <word> or <phrase>, and I’ll send an audio clip of the correct pronunciation! For pronunciation tips, type /tips."
    )

async def pronounce(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    track_user(chat_id)
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text(
            "Please type a word or sentence after the command, e.g., /pronounce hello world."
        )
        return

    try:
        tts = gTTS(text=text, lang="en", tld="co.uk", slow=False)
        audio_file = f"{text}.mp3"
        tts.save(audio_file)
        with open(audio_file, "rb") as audio:
            await update.message.reply_audio(audio)
        os.remove(audio_file)
    except Exception as e:
        await update.message.reply_text(f"Sorry, an error occurred: {e}")

async def tips(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    track_user(chat_id)
    tips_text = (
        "Here are some tips for common pronunciation challenges:\n\n"
        "1. **'th' sound**: \n"
        "   - 'th' in 'think' is unvoiced (tongue between teeth, blow air).\n"
        "   - 'th' in 'this' is voiced (same position, use vocal cords).\n\n"
        "2. **'v' vs 'w' sounds**:\n"
        "   - 'v' in 'van': upper teeth lightly touch lower lip.\n"
        "   - 'w' in 'win': round your lips without touching teeth.\n\n"
        "3. **Silent letters**: Don't pronounce the 'k' in 'knife' or 'b' in 'comb'.\n\n"
        "4. **'r' sound**: In British English, it's soft (e.g., 'car').\n\n"
        "Practice these regularly!"
    )
    await update.message.reply_text(tips_text)

# Function to send daily tips to users
def send_daily_tips():
    tips_text = "Daily Pronunciation Tip:\n\nPractice the **'th' sound** today!"
    chat_ids = load_chat_ids()
    for chat_id in chat_ids:
        try:
            bot.send_message(chat_id=chat_id, text=tips_text)
        except Exception as e:
            print(f"Error sending tip to {chat_id}: {e}")

# Flask routes
@app.route("/", methods=["GET", "POST", "HEAD"])
def home():
    return "Bot is running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = Update.de_json(json.loads(json_str), bot)
    app_bot.process_update(update)
    return "ok", 200

@app.route("/ping")
def ping():
    return "pong", 200

# Scheduler to keep bot alive
def keep_alive():
    bot.get_me()

scheduler = BackgroundScheduler()
scheduler.add_job(keep_alive, "interval", minutes=5)
scheduler.add_job(send_daily_tips, "interval", hours=24)
scheduler.start()

# Initialize Telegram handlers
app_bot = Application.builder().token(TELEGRAM_TOKEN).build()
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(CommandHandler("pronounce", pronounce))
app_bot.add_handler(CommandHandler("tips", tips))

# Main function to start the bot
if __name__ == "__main__":
    app_bot.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),
        webhook_url="https://tunetalkbot.onrender.com/webhook"
    )
