import os
import re
import asyncio
import requests
from dotenv import load_dotenv
from flask import Flask, request
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from threading import Thread

# 🔹 Estados da conversa
MODELO, ANO_MIN, ANO_MAX, PRECO_MIN, PRECO_MAX, CIDADE, ESTADO = range(7)

# 🔹 Cabeçalho para scraper
HEADERS = {"User-Agent": "Mozilla/5.0"}

# 🔹 Carrega variáveis do .env
load_dotenv()
TOKEN = os.environ.get("TELEGRAM_TOKEN").strip()
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Ex: https://seusite.up.railway.app/webhook
PORT = int(os.environ.get("PORT", 8000))

# 🔹 Flask
app = Flask(__name__)

# 🔹 Função de busca OLX
def buscar_olx(modelo, cidade, estado, ano_min, ano_max, preco_min, preco_max):
    local = f"{cidade}%2C%20{estado}"
    url = (
        "https://www.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios"
        f"?q={modelo.replace(' ', '%20')}"
        f"&search[locations][0]={local}"
        "&private_business=1"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return "⚠️ Erro ao acessar OLX."
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.find_all("li", {"data-lurker_list_id": True})
        resultados = []
        links_vistos = set()

        for item in items:
            titulo_tag = item.select_one("h2")
            preco_tag = item.select_one("span[data-testid='ad-price']")
            localidade_tag = item.select_one("span[data-testid='ad-location']")
            link_tag = item.select_one("a")

            titulo = titulo_tag.get_text().strip() if titulo_tag else "Sem título"
            localidade = localidade_tag.get_text().strip() if localidade_tag else "Sem local"
            link = link_tag["href"] if link_tag else ""
            if not link or link in links_vistos:
                continue
            links_vistos.add(link)

            ano_match = re.search(r'\b(19|20)\d{2}\b', titulo)
            ano = int(ano_match.group()) if ano_match else None

            preco = 0
            if preco_tag:
                preco_texto = re.sub(r'[^\d]', '', preco_tag.get_text())
                if preco_texto.isdigit():
                    preco = int(preco_texto)

            if ano and preco and ano_min <= ano <= ano_max and preco_min <= preco <= preco_max:
                resultados.append(f"🚗 {titulo}\n💰 R${preco}\n📍 {localidade}\n🔗 {link}")

        return "\n\n".join(resultados[:5]) if resultados else "❌ Nenhum resultado dentro dos filtros definidos."

    except Exception as e:
        return f"⚠️ Erro na busca: {e}"

# 🔹 Handlers da conversa
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Vamos buscar um carro! Qual é o modelo?")
    return MODELO

async def modelo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["modelo"] = update.message.text
    await update.message.reply_text("Qual o ano mínimo?")
    return ANO_MIN

async def ano_min_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ano_min"] = update.message.text
    await update.message.reply_text("Qual o ano máximo?")
    return ANO_MAX

async def ano_max_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ano_max"] = update.message.text
    await update.message.reply_text("Preço mínimo?")
    return PRECO_MIN

async def preco_min_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["preco_min"] = update.message.text
    await update.message.reply_text("Preço máximo?")
    return PRECO_MAX

async def preco_max_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["preco_max"] = update.message.text
    await update.message.reply_text("Cidade (ex: Curitiba)?")
    return CIDADE

async def cidade_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cidade"] = update.message.text
    await update.message.reply_text("Estado (ex: PR)?")
    return ESTADO

async def estado_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    await update.message.reply_text("🔎 Buscando anúncios de particulares…")
    resultados = buscar_olx(modelo, cidade, estado, ano_min, ano_max, preco_min, preco_max)
    await update.message.reply_text(resultados)
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

# 🔹 Webhook Flask (CORRIGIDO - função síncrona)
@app.route("/webhook", methods=["POST"])
def webhook():
    """Recebe updates do Telegram via webhook"""
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        
        # Cria novo event loop para processar update
        asyncio.run(application.process_update(update))
        
        return "ok", 200
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        return "error", 500

@app.route("/")
def index():
    """Rota de health check"""
    return "Bot OLX está rodando! ✅", 200

# 🔹 Inicializa bot
async def setup_webhook():
    """Configura o webhook do bot"""
    await application.initialize()
    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    print(f"✅ Webhook configurado: {WEBHOOK_URL}/webhook")

if __name__ == "__main__":
    if WEBHOOK_URL:
        print("🚀 Rodando em modo WEBHOOK (Railway/Render)")
        
        # Configura webhook
        asyncio.run(setup_webhook())
        
        # Roda Flask
        app.run(host="0.0.0.0", port=PORT)
    else:
        print("🏠 Rodando em modo POLLING (Local)")
        application.run_polling()
