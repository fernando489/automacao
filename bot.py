import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler
from flask import Flask, request
import asyncio

load_dotenv()

TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8000))

app = Flask(__name__)

async def start(update, context):
    await update.message.reply_text("Bot funcionando 🚀")

application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))

@app.route("/webhook", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return "ok"

if __name__ == "__main__":

    if WEBHOOK_URL:
        print("Rodando em modo WEBHOOK (Railway)")
        asyncio.run(application.bot.set_webhook(WEBHOOK_URL))
        app.run(host="0.0.0.0", port=PORT)

    else:
        print("Rodando em modo POLLING (Local)")
        application.run_polling()
