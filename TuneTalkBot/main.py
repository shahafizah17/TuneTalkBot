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
        "Here are 20 tips for common pronunciation challenges among ESL speakers:\n\n"
        "1. **'th' sound**: Unvoiced 'th' in 'think' is soft; voiced 'th' in 'this' uses vocal cords.\n"
        "2. **'v' vs 'w' sounds**: 'v' vibrates, while 'w' requires rounded lips.\n"
        "3. **Silent letters**: Avoid pronouncing silent letters, like 'k' in 'know' or 'b' in 'thumb'.\n"
        "4. **Final 'ed' sound**: Pronounce 'ed' in 'wanted' as /ɪd/, but 'played' as /d/.\n"
        "5. **'r' sound**: In British English, it's soft or silent at the end of words like 'car'.\n"
        "6. **Linking words**: British English links 'r' between words ('law and order').\n"
        "7. **Stress patterns**: Stress syllables correctly, e.g., 'PREsent' (noun) vs 'preSENT' (verb).\n"
        "8. **'s' vs 'z' sounds**: 's' in 'see' is voiceless, while 'z' in 'zoo' is voiced.\n"
        "9. **'ch' vs 'sh' sounds**: 'ch' in 'chair' is hard, while 'sh' in 'share' is softer.\n"
        "10. **'t' sound**: In British English, 't' is often crisp, not replaced with 'd'.\n"
        "11. **Vowel length**: Contrast long ('sheep') and short ('ship') vowels.\n"
        "12. **Consonant clusters**: Avoid adding extra vowels in 'school' or 'spring'.\n"
        "13. **'l' sound**: The 'l' in 'little' is darker when at the end of syllables.\n"
        "14. **Intonation**: Use rising intonation for questions and falling for statements.\n"
        "15. **Word endings**: Pronounce 's' or 'es' endings correctly in plurals ('cats' vs 'dogs').\n"
        "16. **Weak vowels**: The schwa /ə/ sound is common in unstressed syllables ('about').\n"
        "17. **'h' sound**: Don't drop 'h' in words like 'hat' unless it's silent ('honest').\n"
        "18. **'j' sound**: Pronounce 'j' in 'jump' clearly, not confused with 'y'.\n"
        "19. **Compound words**: Stress the first word in compounds like 'blackboard'.\n"
        "20. **Rhythm**: English is stress-timed, meaning stressed syllables are equally spaced.\n\n"
        "Practice these tips regularly to improve your pronunciation!"
    )
    await update.message.reply_text(tips_text)

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

if __name__ == "__main__":
    main()
