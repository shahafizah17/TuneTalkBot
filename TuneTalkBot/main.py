import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackContext
from gtts import gTTS
from apscheduler.schedulers.background import BackgroundScheduler

# Flask app for the HTTP endpoint
app = Flask(__name__)

# Load environment variables
TELEGRAM_TOKEN = "7654820492:AAGpULuFlQ3FDl5Gc95fPY0iV02lAoPJ9Do"
bot = Bot(token=TELEGRAM_TOKEN)

# Command to greet users
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Hello! I’m TuneTalkBot. Need help with pronunciation? Type /pronounce <word> or <phrase>, and and I’ll send an audio clip of the correct pronunciation!"
    )

# Function to handle pronunciation requests
def pronounce(update: Update, context: CallbackContext):
    text = " ".join(context.args)
    if not text:
        update.message.reply_text("Please type a word or sentence after the command, e.g., /pronounce hello world.")
        return

    try:
        # Generate audio using British English
        tts = gTTS(text=text, lang="en", tld="co.uk", slow=False)
        audio_file = f"{text}.mp3"
        tts.save(audio_file)

        # Send audio to the user
        with open(audio_file, "rb") as audio:
            update.message.reply_audio(audio)

        os.remove(audio_file)  # Clean up file after sending
    except Exception as e:
        update.message.reply_text(f"Sorry, an error occurred: {e}")

# Initialize Telegram bot handlers
def main():
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("pronounce", pronounce))

    # Start the bot
    updater.start_polling()
    updater.idle()

# Flask route to keep Railway pinging service alive
@app.route("/")
def home():
    return "Bot is running!"

@app.route("/ping")
def ping():
    return "pong"

# Keep bot alive with a scheduler
def keep_alive():
    bot.get_me()

scheduler = BackgroundScheduler()
scheduler.add_job(keep_alive, "interval", minutes=5)
scheduler.start()

if __name__ == "__main__":
    main()
