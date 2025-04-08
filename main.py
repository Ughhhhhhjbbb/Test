# ai_telegram_bot.py

import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Replace with your actual tokens
TELEGRAM_TOKEN = "6528857056:AAFPb3NEKX41qnlCfpiPcGd1YFIueJtVTcU"
OPENAI_API_KEY = "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"

openai.api_key = OPENAI_API_KEY

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey! I’m your AI assistant. Ask me anything.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        reply = f"Error: {e}"

    await update.message.reply_text(reply)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()
    
