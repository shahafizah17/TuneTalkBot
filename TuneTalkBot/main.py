import os
from flask import Flask
from telegram import Update, Bot
from telegram.ext import CommandHandler, Application, CallbackContext, MessageHandler, filters
from gtts import gTTS
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
        "   - Avoid rolling the 'r' too much. In British English, it’s often soft, especially at the end of words like 'car'.\n\n"
        "5. **'ed' endings**:\n"
        "   - 'ed' is pronounced as /t/ in 'worked', /d/ in 'played', and /\u026ad/ in 'wanted'.\n\n"
        "6. **Stress in words**:\n"
        "   - Learn which syllable to stress, e.g., 'record' (noun: REcord, verb: reCORD).\n\n"
        "7. **Schwa sound (/\u0259/)**:\n"
        "   - The 'a' in 'sofa' and the 'e' in 'the' often sound like /\u0259/.\n\n"
        "8. **'l' vs 'r' sounds**:\n"
        "   - 'l' in 'lake' uses the tongue tip touching the roof of the mouth.\n"
        "   - 'r' in 'rake' requires curving the tongue back without touching the roof.\n\n"
        "9. **Linking sounds**:\n"
        "   - In connected speech, 'go on' may sound like 'gowoan'.\n\n"
        "10. **Intonation**:\n"
        "    - Use rising intonation for questions and falling intonation for statements.\n\n"
        "11. **'s' vs 'z' sounds**:\n"
        "    - 's' in 'sit' is voiceless, while 'z' in 'zoo' is voiced.\n\n"
        "12. **Diphthongs**:\n"
        "    - Words like 'coin' and 'cake' contain two vowel sounds combined.\n\n"
        "13. **Elision**:\n"
        "    - Native speakers may drop sounds, e.g., 'friendship' sounds like 'frenship'.\n\n"
        "14. **'t' sound variations**:\n"
        "    - In 'butter', the 't' often sounds like a soft 'd' (flap t) in American English.\n\n"
        "15. **'a' sounds**:\n"
        "    - 'a' in 'cat' is short, while 'a' in 'car' is long.\n\n"
        "16. **Minimal pairs practice**:\n"
        "    - Practice pairs like 'ship' vs 'sheep' to improve vowel clarity.\n\n"
        "17. **'j' vs 'y' sounds**:\n        "    - 'j' in 'juice' is harder than 'y' in 'yes', which is softer.\n\n"
        "18. **Word endings**:\n        "    - Be careful with plurals like 'cats' (s) and 'dogs' (z).\n\n"
        "19. **Contractions**:\n        "    - 'I am' becomes 'I'm'; practice these for natural flow.\n\n"
        "20. **Practice with tongue twisters**:\n        "    - E.g., 'She sells sea shells by the sea shore'."
    )
    await update.message.reply_text(tips_text)

# Initialize Telegram bot handlers
def main():
    app_bot = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("pronounce", pronounce))
    app_bot.add_handler(CommandHandler("tips", tips))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, _: track_user(update.message.chat_id)))

    # Configure webhook
    app_bot.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),
        url_path="",
        webhook_url="https://tunetalkbot.onrender.com"  # Replace with your Render URL
    )

# Flask route to keep Render pinging service alive
@app.route("/")
def home():
    return "Bot is running!"

@app.route("/ping")
def ping():
    return "pong"

if __name__ == "__main__":
    main()
