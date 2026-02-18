import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask, request
import asyncio
from scraper import buscar_olx  # seu scraper

load_dotenv()

TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8000))

app = Flask(__name__)

# ========================
# COMANDOS
# ========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot funcionando 🚀")

# 🔎 Busca imediata
async def agora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    termo = " ".join(context.args)

    if not termo:
        await update.message.reply_text("Use assim:\n/agora civic 2018")
        return

    await update.message.reply_text("🔍 Buscando na OLX...")

    resultado = buscar_olx(termo)

    await update.message.reply_text(resultado)

# 🔁 Monitoramento 10 minutos
async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    termo = " ".join(context.args)

    if not termo:
        await update.message.reply_text("Use assim:\n/monitor civic 2018")
        return

    await update.message.reply_text("🔁 Monitorando por 10 minutos...")

    resultado = buscar_olx(termo, tempo_monitoramento=600)

    await update.message.reply_text(resultado)

# ========================
# TELEGRAM
# ========================

application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("agora", agora))
application.add_handler(CommandHandler("monitor", monitor))

# ========================
# WEBHOOK
# ========================

@app.route("/webhook", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return "ok"

# ========================
# EXECUÇÃO
# ========================

if __name__ == "__main__":

    if WEBHOOK_URL:
        print("Rodando em modo WEBHOOK (Railway)")
        asyncio.run(application.bot.set_webhook(WEBHOOK_URL))
        app.run(host="0.0.0.0", port=PORT)

    else:
        print("Rodando em modo POLLING (Local)")
        application.run_polling()
