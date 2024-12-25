import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import CommandHandler, Application, CallbackContext, MessageHandler, filters
from gtts import gTTS
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import json  # To store chat IDs
import logging  # For logging

# Flask app for the HTTP endpoint
app = Flask(__name__)

# Load environment variables
TELEGRAM_TOKEN = "7654820492:AAGpULuFlQ3FDl5Gc95fPY0iV02lAoPJ9Do"
bot = Bot(token=TELEGRAM_TOKEN)

# File to store user chat IDs
CHAT_IDS_FILE = "chat_ids.json"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.info(f"New user tracked: {chat_id}")

# Command to greet users
async def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    track_user(chat_id)  # Track the user's chat ID
    await update.message.reply_text(
        "Hi! I’m TuneTalkBot, here to help you with pronunciation. Type /pronounce <word> or <phrase>, and I’ll send an audio clip of the correct pronunciation! For pronunciation tips, type /tips."
    )

# Function to handle pronunciation requests
async def pronounce(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    track_user(chat_id)  # Track the user's chat ID
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text(
            "Please type a word or sentence after the command, e.g., /pronounce hello world."
        )
        return

    try:
        # Generate audio using British English
        tts = gTTS(text=text, lang="en", tld="co.uk", slow=False)
        audio_file = f"{text}.mp3"
        tts.save(audio_file)

        # Send audio to the user
        with open(audio_file, "rb") as audio:
            await update.message.reply_audio(audio)

        os.remove(audio_file)  # Clean up file after sending
    except Exception as e:
        logger.error(f"Error in pronunciation: {e}")
        await update.message.reply_text(f"Sorry, an error occurred: {e}")

# Function to handle pronunciation tips
async def tips(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    track_user(chat_id)  # Track the user's chat ID
    tips_text = (
        "Here are some tips for common pronunciation challenges:\n\n"
        "1. **'th' sound**: \n"
        "   - 'th' in 'think' is unvoiced (place your tongue between your teeth and blow air).\n"
        "   - 'th' in 'this' is voiced (same position, but use your vocal cords).\n\n"
        "2. **'v' vs 'w' sounds**:\n"
        "   - 'v' in 'van': upper teeth touch the lower lip lightly while vibrating.\n"
        "   - 'w' in 'win': round your lips without touching the teeth.\n\n"
        "3. **Silent letters**:\n"
        "   - Don't pronounce the 'k' in 'knife' or the 'b' in 'comb'.\n\n"
        "4. **'r' sound**:\n"
        "   - Avoid rolling the 'r' too much. In British English, it’s often soft, especially at the end of words like 'car'.\n\n"
        "Practice these regularly to improve!"
    )
    await update.message.reply_text(tips_text)

# Function to send tips to all tracked users
def send_daily_tips():
    tips_text = (
        "Daily Pronunciation Tip:\n\n"
        "Practice the **'th' sound** today! Unvoiced 'th' (e.g., 'think') requires blowing air gently. "
        "Voiced 'th' (e.g., 'this') requires using your vocal cords. Keep practicing!"
    )
    chat_ids = load_chat_ids()
    for chat_id in chat_ids:
        try:
            bot.send_message(chat_id=chat_id, text=tips_text)
            logger.info(f"Tip sent to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending tip to {chat_id}: {e}")

# Initialize Telegram bot handlers
def main():
    app_bot = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("pronounce", pronounce))
    app_bot.add_handler(CommandHandler("tips", tips))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, _: track_user(update.message.chat_id)))  # Track all users

    # Configure webhook
    app_bot.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),
        url_path="",  # Optional, leave empty for default
        webhook_url="https://tunetalkbot.onrender.com"  # Replace with your Render URL
    )

# Flask route to keep Render pinging service alive
@app.route("/")
def home():
    return "Bot is running!"

@app.route("/ping")
def ping():
    return "pong"

# Keep bot alive with a scheduler
def keep_alive():
    bot.get_me()

# Schedule daily tips
scheduler = BackgroundScheduler()
scheduler.add_job(keep_alive, "interval", minutes=5)

# For immediate testing: Run `send_daily_tips` once at startup
scheduler.add_job(send_daily_tips, "date", run_date=datetime.now() + timedelta(seconds=10))  # Runs 10 seconds after bot starts

# For daily tips at a specific time (e.g., 8:00 AM UTC):
scheduler.add_job(send_daily_tips, "cron", hour=8, minute=0)  # Adjust UTC time as needed
scheduler.start()

if __name__ == "__main__":
    main()
