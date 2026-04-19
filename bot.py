import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN
from mood import initialize_db, save_mood, save_message
from reel import process_reel
from brain import process_reel_and_respond, chat, check_and_summarise, classify_mood, learn_command, knowledge_command
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    chat_id = update.effective_chat.id

    # Save chat_id so daily checkin knows where to send
    context.bot_data["chat_id"] = chat_id

    # Schedule daily check-in for this user
    context.job_queue.run_daily(
        daily_checkin,
        time=datetime.time(9, 0, 0),
        chat_id=chat_id,
        name=str(chat_id)
    )

    await update.message.reply_text(
        f"Hey {user_name}! 👋 I'm Luma, your personal companion.\n\n"
        f"Here's what you can do:\n"
        f"• Just tell me how you're feeling anytime\n"
        f"• Share an Instagram reel URL and I'll respond based on your mood\n"
        f"• Use /mood to tell me how you're feeling right now\n\n"
        f"I'll also check in with you every morning at 9am 🌅\n\n"
        f"So... how are you feeling today? 😊"
    )


async def daily_checkin(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        context.job.chat_id,
        "Good morning! ☀️ How are you feeling today? "
        "Tell me anything on your mind 🙂"
    )


async def mood_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Tell me how you're feeling right now. "
        "Don't hold back — I'm here to listen 🙂"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Check if it's an Instagram reel URL
    if "instagram.com/reel" in text or "instagram.com/p/" in text:
        processing_msg = await update.message.reply_text(
            "🎬 Got your reel! Let me watch it and think about it...\n"
            "This might take a minute ⏳"
        )

        try:
            # Process the reel
            reel_data = process_reel(text)
            save_message(user_id, "user", f"Shared a reel: {text}")

            # Get emotional response
            response = process_reel_and_respond(
                user_id,
                reel_data["transcript"],
                reel_data["frames"]
            )

            save_message(user_id, "assistant", response)
            await processing_msg.delete()
            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error processing reel: {e}")
            await processing_msg.delete()
            await update.message.reply_text(
                "Hmm, I had trouble processing that reel 😕\n"
                "Make sure it's a public Instagram reel and try again?"
            )

    else:
        # Everything else is a conversation
        # Save what user said
        save_message(user_id, "user", text)
        # Get conversational response from LLaMA
        thinking_msg = await update.message.reply_text("💭...")
        mood_data = classify_mood(text)
        save_mood(
            user_id,
            mood_text=text,
            sentiment=mood_data["sentiment"],
            emotion=mood_data["emotion"],
            intensity=mood_data["intensity"],
            mood_summary=mood_data["mood_summary"]
        )
        print(f"📊 Mood: {mood_data['emotion']} "
              f"({mood_data['sentiment']}, "
              f"intensity: {mood_data['intensity']})")


        try:
            response = chat(user_id, text)
            save_message(user_id, "assistant", response)
            check_and_summarise(user_id)
            await thinking_msg.delete()
            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            await thinking_msg.delete()
            await update.message.reply_text(
                "My brain glitched for a second 😅 try again?"
            )


def main():
    print("🗄️ Initializing database...")
    initialize_db()

    print("🤖 Starting bot...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mood", mood_command))
    app.add_handler(CommandHandler("learn", learn_command))
    app.add_handler(CommandHandler("knowledge", knowledge_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running! Open Telegram and send /start")
    print("Press Ctrl+C to stop")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()