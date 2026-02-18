import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from flask import Flask, request
import asyncio
from bs4 import BeautifulSoup
import re

# 🔹 Estados da conversa
MODELO, ANO_MIN, ANO_MAX, PRECO_MIN, PRECO_MAX, CIDADE, ESTADO = range(7)

# 🔹 Cabeçalho para scraper
HEADERS = {"User-Agent": "Mozilla/5.0"}

# 🔹 Carrega variáveis do .env
load_dotenv()
TOKEN = os.environ.get("TELEGRAM_TOKEN").strip()
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8000))

# 🔹 Flask para webhook
app = Flask(__name__)

# 🔹 Comando /start
async def start(update: Update, context):
    await update.message.reply_text("Vamos buscar um carro! Qual é o modelo?")
    return MODELO

# 🔹 Handlers da conversa (mesmo do seu bot anterior)
async def modelo_handler(update: Update, context):
    context.user_data["modelo"] = update.message.text
    await update.message.reply_text("Qual o ano mínimo?")
    return ANO_MIN

async def ano_min_handler(update: Update, context):
    context.user_data["ano_min"] = update.message.text
    await update.message.reply_text("Qual o ano máximo?")
    return ANO_MAX

async def ano_max_handler(update: Update, context):
    context.user_data["ano_max"] = update.message.text
    await update.message.reply_text("Preço mínimo?")
    return PRECO_MIN

async def preco_min_handler(update: Update, context):
    context.user_data["preco_min"] = update.message.text
    await update.message.reply_text("Preço máximo?")
    return PRECO_MAX

async def preco_max_handler(update: Update, context):
    context.user_data["preco_max"] = update.message.text
    await update.message.reply_text("Cidade (ex: Curitiba)?")
    return CIDADE

async def cidade_handler(update: Update, context):
    context.user_data["cidade"] = update.message.text
    await update.message.reply_text("Estado (ex: PR)?")
    return ESTADO

async def estado_handler(update: Update, context):
    context.user_data["estado"] = update.message.text
    data = context.user_data

    modelo = data["modelo"]
    cidade = data["cidade"]
    estado = data["estado"]

    try:
        ano_min = int(data["ano_min"])
        ano_max = int(data["ano_max"])
        preco_min = int(re.sub(r"[^\d]", "", data["preco_min"]))
        preco_max = int(re.sub(r"[^\d]", "", data["preco_max"]))
    except ValueError:
        await update.message.reply_text("⚠️ Ano e preço devem ser números. Use /start para tentar novamente.")
        return ConversationHandler.END

    local = f"{cidade}%2C%20{estado}"
    url = (
        "https://www.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios"
        f"?q={modelo.replace(' ', '%20')}"
        f"&search[locations][0]={local}"
    )

    await update.message.reply_text(f"🔎 Buscando resultados…\n{url}")

    try:
        resposta = requests.get(url, headers=HEADERS, timeout=15)
        if resposta.status_code != 200:
            await update.message.reply_text("⚠️ Erro ao acessar OLX")
            return ConversationHandler.END

        soup = BeautifulSoup(resposta.text, "html.parser")
        items = soup.find_all("li", {"data-lurker_list_id": True})

        if not items:
            await update.message.reply_text("❌ Nenhum resultado encontrado.")
            return ConversationHandler.END

        resultados = []
        for item in items:
            titulo_tag = item.select_one("h2")
            preco_tag = item.select_one("span[data-testid='ad-price']")
            localidade_tag = item.select_one("span[data-testid='ad-location']")
            link_tag = item.select_one("a")

            titulo = titulo_tag.get_text().strip() if titulo_tag else "Sem título"
            localidade = localidade_tag.get_text().strip() if localidade_tag else "Sem local"
            link = link_tag["href"] if link_tag else ""

            ano_match = re.search(r'\b(19|20)\d{2}\b', titulo)
            ano = int(ano_match.group()) if ano_match else None

            preco = 0
            if preco_tag:
                preco_texto = re.sub(r'[^\d]', '', preco_tag.get_text())
                if preco_texto.isdigit():
                    preco = int(preco_texto)

            if ano and preco:
                if ano_min <= ano <= ano_max and preco_min <= preco <= preco_max:
                    resultados.append(f"🚗 {titulo}\n💰 R${preco}\n📍 {localidade}\n🔗 {link}")

        if resultados:
            await update.message.reply_text("\n\n".join(resultados[:5]))
        else:
            await update.message.reply_text("❌ Nenhum resultado dentro dos filtros definidos.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Erro na busca: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Busca cancelada.")
    return ConversationHandler.END

# 🔹 Cria aplicação Telegram
application = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        MODELO: [MessageHandler(filters.TEXT & ~filters.COMMAND, modelo_handler)],
        ANO_MIN: [MessageHandler(filters.TEXT, ano_min_handler)],
        ANO_MAX: [MessageHandler(filters.TEXT, ano_max_handler)],
        PRECO_MIN: [MessageHandler(filters.TEXT, preco_min_handler)],
        PRECO_MAX: [MessageHandler(filters.TEXT, preco_max_handler)],
        CIDADE: [MessageHandler(filters.TEXT, cidade_handler)],
        ESTADO: [MessageHandler(filters.TEXT, estado_handler)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(conv_handler)

# 🔹 Webhook Flask
@app.route("/webhook", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return "ok"

# 🔹 Inicializa bot
if __name__ == "__main__":
    if WEBHOOK_URL:
        print("Rodando em modo WEBHOOK (Railway)")
        asyncio.run(application.bot.set_webhook(WEBHOOK_URL))
        app.run(host="0.0.0.0", port=PORT)
    else:
        # 🔹 Modo polling local: deleta webhook antes de iniciar
        print("Rodando em modo POLLING (Local)")
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
        application.run_polling()
