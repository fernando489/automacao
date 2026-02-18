# ----------------------------
# bot.py final
# ----------------------------

from dotenv import load_dotenv
import os
import psycopg2
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from scraper import buscar_olx

# ----------------------------
# Carregar variáveis de ambiente
# ----------------------------
load_dotenv()  # carrega .env

TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8000))

bot = Bot(token=TOKEN)
app = Flask(__name__)

# ----------------------------
# Conexão com PostgreSQL (Railway)
# ----------------------------
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Criar tabela caso não exista
cursor.execute("""
CREATE TABLE IF NOT EXISTS pesquisas (
    id SERIAL PRIMARY KEY,
    usuario TEXT,
    termo TEXT,
    data TIMESTAMP DEFAULT NOW()
)
""")
conn.commit()

# ----------------------------
# Função que processa updates do Telegram
# ----------------------------
def process_update(update: Update):
    message = update.message
    if message is None:
        return

    texto = message.text
    usuario = message.from_user.username or str(message.from_user.id)

    if texto.startswith("/start"):
        bot.send_message(
            chat_id=message.chat.id,
            text="Olá! Eu posso te ajudar a buscar carros na OLX.\nUse /buscar <termo> para começar."
        )

    elif texto.startswith("/buscar"):
        args = texto.split()[1:]
        if not args:
            bot.send_message(chat_id=message.chat.id, text="Envie o termo de pesquisa: /buscar <termo>")
            return

        termo = " ".join(args)

        # Salvar pesquisa no banco
        cursor.execute(
            "INSERT INTO pesquisas (usuario, termo) VALUES (%s, %s)",
            (usuario, termo)
        )
        conn.commit()

        resultados = buscar_olx(termo)
        if not resultados:
            bot.send_message(chat_id=message.chat.id, text="Nenhum resultado encontrado.")
            return

        # Criar botões com link
        buttons = [
            [InlineKeyboardButton(f"{r['titulo']} - {r['preco']} ({r['cidade']})", url=r['link'])]
            for r in resultados[:5]
        ]
        markup = InlineKeyboardMarkup(buttons)
        bot.send_message(chat_id=message.chat.id, text="Resultados:", reply_markup=markup)

    else:
        bot.send_message(chat_id=message.chat.id, text="Use /start ou /buscar <termo> para começar.")

# ----------------------------
# Rota do webhook
# ----------------------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    process_update(update)
    return "ok"

@app.route("/")
def index():
    return "Bot rodando!"

# ----------------------------
# Configurar webhook e rodar Flask
# ----------------------------
import asyncio

async def configurar_webhook():
    # Aqui chamamos a coroutine corretamente com await
    await bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    print(f"Webhook configurado: {WEBHOOK_URL}/{TOKEN}")

if __name__ == "__main__":
    # Executa a coroutine e depois inicia o Flask
    asyncio.run(configurar_webhook())
    app.run(host="0.0.0.0", port=PORT)
