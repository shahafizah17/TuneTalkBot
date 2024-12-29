import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import CommandHandler, Application, CallbackContext, MessageHandler, filters
from gtts import gTTS
import json  # To store chat IDs
import logging  # For logging
import pyphen  # For syllable-based spelling

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
        "Hi! I’m TuneTalkBot, here to help you with pronunciation. Type /pronounce <word> or <phrase>, and I’ll send an audio clip of the correct pronunciation! For pronunciation tips, type /tips. For phonetic spelling, type /spell <word>."
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
        "5. **Long and short vowels**:\n"
        "   - Compare 'ship' (short vowel) and 'sheep' (long vowel). Lengthen the vowel for long sounds.\n\n"
        "6. **Word stress**:\n"
        "   - Place stress on the correct syllable, e.g., 'PREsent' (noun) vs. 'preSENT' (verb).\n\n"
        "7. **'s' vs 'z' sounds**:\n"
        "   - 's' is unvoiced as in 'snake'; 'z' is voiced as in 'zebra'.\n\n"
        "8. **Dropping the final consonant**:\n"
        "   - Avoid dropping final sounds, e.g., say 'cat' with the 't' sound.\n\n"
        "9. **Linking words**:\n"
        "   - Connect words smoothly, e.g., 'go on' becomes 'gwon'.\n\n"
        "10. **Intonation**:\n"
        "   - Use rising intonation for questions (e.g., 'Are you coming?').\n\n"
        "11. **'l' vs 'r' sounds**:\n"
        "   - 'l' as in 'lake' requires the tongue to touch the roof of the mouth. 'r' as in 'right' pulls the tongue back.\n\n"
        "12. **Aspirated 'p', 't', 'k' sounds**:\n"
        "   - Add a small burst of air for 'p' in 'pot', 't' in 'top', and 'k' in 'cat'.\n\n"
        "13. **Consonant clusters**:\n"
        "   - Practice groups like 'str' in 'street' and 'spl' in 'splash'.\n\n"
        "14. **Schwa sound**:\n"
        "   - The 'uh' sound in unstressed syllables, e.g., 'about'.\n\n"
        "15. **Glottal stop**:\n"
        "   - Common in British accents, replacing 't' in words like 'bottle'.\n\n"
        "16. **'h' dropping**:\n"
        "   - Don’t drop 'h' sounds unless it’s part of the accent, e.g., 'happy'.\n\n"
        "17. **Double consonants**:\n"
        "   - Hold the sound slightly longer, e.g., 'big game' (pause between 'g').\n\n"
        "18. **'ing' endings**:\n"
        "   - Say 'singing' with a soft 'g', not 'singin'.\n\n"
        "19. **Homophones**:\n"
        "   - Words like 'there', 'their', and 'they’re' sound the same but have different meanings.\n\n"
        "20. **Practice minimal pairs**:\n"
        "   - Compare words like 'bat' vs. 'pat' to hear subtle differences."
    )
    await update.message.reply_text(tips_text)

# Function to spell words phonetically
async def spell(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    track_user(chat_id)  # Track the user's chat ID
    word = "".join(context.args)
    if not word:
        await update.message.reply_text("Please provide a word to spell phonetically, e.g., /spell hello.")
        return

    try:
        # Break the word into syllables
        dic = pyphen.Pyphen(lang='en')
        phonetic_spelling = dic.inserted(word)
        await update.message.reply_text(f"Phonetic spelling of '{word}': {phonetic_spelling}")
    except Exception as e:
        logger.error(f"Error in spelling: {e}")
        await update.message.reply_text(f"Sorry, an error occurred while processing the spelling.")

# Initialize Telegram bot handlers
def main():
    app_bot = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("pronounce", pronounce))
    app_bot.add_handler(CommandHandler("tips", tips))
    app_bot.add_handler(CommandHandler("spell", spell))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, _: track_user(update.message.chat_id)))  # Track all users

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
