import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import CommandHandler, Application, CallbackContext
from gtts import gTTS
import logging
import json

# Flask app for the HTTP endpoint
app = Flask(__name__)

# Load environment variables
TELEGRAM_TOKEN = "YOUR_TELEGRAM_TOKEN"  # Replace with your bot's token
bot = Bot(token=TELEGRAM_TOKEN)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.info(f"New user tracked: {chat_id}")

# Command to greet users
async def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    track_user(chat_id)
    await update.message.reply_text(
        "Hi! I’m TuneTalkBot, here to help you with pronunciation. "
        "Type /pronounce <word> or <phrase>, and I’ll send an audio clip of the correct pronunciation! "
        "For pronunciation tips, type /tips. To explore regional differences, use /regional <word>."
    )

# Function to handle pronunciation requests
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
        # Generate audio using British English
        tts = gTTS(text=text, lang="en", tld="co.uk", slow=False)
        audio_file = f"{text}_british.mp3"
        tts.save(audio_file)

        # Send audio to the user
        with open(audio_file, "rb") as audio:
            await update.message.reply_audio(audio, caption="British English Pronunciation")

        os.remove(audio_file)
    except Exception as e:
        logger.error(f"Error in pronunciation: {e}")
        await update.message.reply_text(f"Sorry, an error occurred: {e}")

# Function to handle regional pronunciation differences
async def regional(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    track_user(chat_id)
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text(
            "Please type a word after the command to get regional pronunciations, e.g., /regional water."
        )
        return

    try:
        # Generate audio for British English
        tts_british = gTTS(text=text, lang="en", tld="co.uk", slow=False)
        british_audio = f"{text}_british.mp3"
        tts_british.save(british_audio)

        # Generate audio for American English
        tts_american = gTTS(text=text, lang="en", tld="com", slow=False)
        american_audio = f"{text}_american.mp3"
        tts_american.save(american_audio)

        # Send both audio files to the user
        await update.message.reply_audio(open(british_audio, "rb"), caption="British English Pronunciation")
        await update.message.reply_audio(open(american_audio, "rb"), caption="American English Pronunciation")

        # Clean up files after sending
        os.remove(british_audio)
        os.remove(american_audio)
    except Exception as e:
        logger.error(f"Error in regional pronunciation: {e}")
        await update.message.reply_text(f"Sorry, an error occurred: {e}")

# Function to handle pronunciation tips
async def tips(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    track_user(chat_id)
    tips_text = (
        "Here are some tips for common pronunciation challenges among ESL speakers:\n\n"
        "1. **'th' sound**: \n"
        "   - 'th' in 'think' is unvoiced (place your tongue between your teeth and blow air).\n"
        "   - 'th' in 'this' is voiced (same position, but use your vocal cords).\n\n"
        "2. **'v' vs 'w' sounds**:\n"
        "   - 'v' in 'van': upper teeth touch the lower lip lightly while vibrating.\n"
        "   - 'w' in 'win': round your lips without touching the teeth.\n\n"
        "3. **Silent letters**:\n"
        "   - Don't pronounce the 'k' in 'knife' or the 'b' in 'comb'.\n\n"
        "4. **'r' sound**:\n"
        "   - Avoid rolling the 'r' too much. In British English, it’s often soft, especially at the end of words like 'car'."
    )
    await update.message.reply_text(tips_text)

# Initialize Telegram bot handlers
def main():
    app_bot = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("pronounce", pronounce))
    app_bot.add_handler(CommandHandler("regional", regional))
    app_bot.add_handler(CommandHandler("tips", tips))

    # Configure webhook
    app_bot.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),
        url_path="",
        webhook_url="https://YOUR_RENDER_URL"  # Replace with your Render URL
    )

# Flask route to keep Render service alive
@app.route("/")
def home():
    return "Bot is running!"

if __name__ == "__main__":
    main()
