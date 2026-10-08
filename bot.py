import os
import uuid
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_INSTALLED = True
except ImportError:
    TELEGRAM_INSTALLED = False

from store import insert_reports
from audio import process_audio

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="🚨 Emergency Assistant Bot Active!\n\nSend:\n• Text reports\n• Voice notes (auto-transcribed)\n• GPS Location\n\nAll reports will appear on the dashboard."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chat_id = update.effective_chat.id
    text = update.message.text
    user_name = update.message.from_user.username or str(user_chat_id)
    
    report = {
        'id': f"TG-{uuid.uuid4().hex[:8]}",
        'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'source': 'telegram_text',
        'sender': str(user_chat_id), # Store the unique chat_id in sender for future outbound routing
        'text': text,
        'stage': 1,
        'session_id': 'live', 
        'origin': 'live'
    }

    insert_reports([report])
    
    # Reply strictly to the mobile phone that sent this specific report
    await context.bot.send_message(
        chat_id=user_chat_id, 
        text="🚨 Report logged! Emergency team has been notified."
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chat_id = update.effective_chat.id
    user_location = update.message.location
    lat = user_location.latitude
    lng = user_location.longitude
    user_name = update.message.from_user.username or str(user_chat_id)

    report = {
        'id': f"TG-LOC-{uuid.uuid4().hex[:6]}",
        'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'source': 'telegram_gps',
        'sender': str(user_chat_id),
        'text': "User shared exact GPS Location via Telegram pin.",
        'stage': 1,
        'session_id': 'live',
        'origin': 'live',
        # Insert native GPS coords right into the queue so worker.py skips geocoding
        'lat': lat,
        'lng': lng
    }

    insert_reports([report])

    await context.bot.send_message(
        chat_id=user_chat_id,
        text=f"📍 Exact GPS Location pinned ({lat:.5f}, {lng:.5f}) and queued for the dashboard."
    )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chat_id = update.effective_chat.id
    voice = update.message.voice
    user_name = update.message.from_user.username or str(user_chat_id)

    # Download voice file
    await context.bot.send_message(chat_id=user_chat_id, text="🎤 Processing voice note...")
    file = await context.bot.get_file(voice.file_id)

    # Save to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
        await file.download_to_drive(temp_file.name)
        temp_path = temp_file.name

    try:
        # Transcribe using Groq (fastest)
        transcript = process_audio(temp_path)

        report = {
            'id': f"TG-VOICE-{uuid.uuid4().hex[:6]}",
            'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'source': 'telegram_voice',
            'sender': str(user_chat_id),
            'text': transcript,
            'stage': 1,
            'session_id': 'live',
            'origin': 'live'
        }

        insert_reports([report])

        await context.bot.send_message(
            chat_id=user_chat_id,
            text=f"🎤 Voice transcribed: {transcript}\n\n🚨 Report logged to dashboard!"
        )
    except Exception as e:
        await context.bot.send_message(
            chat_id=user_chat_id,
            text=f"❌ Voice processing failed: {str(e)}"
        )
    finally:
        # Cleanup temp file
        import os
        try:
            os.unlink(temp_path)
        except:
            pass

def main():
    print("DEBUG: Starting main function...")
    print(f"DEBUG: TELEGRAM_INSTALLED = {TELEGRAM_INSTALLED}")
    print(f"DEBUG: TOKEN = {TOKEN[:10] + '...' if TOKEN else 'None'}")

    if not TELEGRAM_INSTALLED:
        print("WARNING: python-telegram-bot is not installed. Bot will not start.")
        return

    if not TOKEN:
        print("WARNING: TELEGRAM_BOT_TOKEN not set in .env. Telegram bot will not start. The rest of the application is unaffected.")
        return

    print("DEBUG: Building application...")
    application = Application.builder().token(TOKEN).build()
    print("DEBUG: Adding handlers...")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("Telegram bot polling started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
