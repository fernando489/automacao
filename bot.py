import os
import logging
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
)
from scraper import buscar_olx  # Sua função de scraping da OLX
from dotenv import load_dotenv

# --- Carrega variáveis do .env (se existir) ---
load_dotenv()

# --- Token e chat_id ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("❌ Defina TELEGRAM_TOKEN e CHAT_ID nas variáveis de ambiente!")

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Arquivo de persistência ---
ARQUIVO_BUSCAS = "buscas.json"
buscas_ativas = []

def salvar_buscas():
    try:
        with open(ARQUIVO_BUSCAS, "w", encoding="utf-8") as f:
            json.dump(buscas_ativas, f, ensure_ascii=False, indent=2)
        logging.info("✅ Buscas salvas com sucesso.")
    except Exception as e:
        logging.error(f"❌ Erro ao salvar buscas: {e}")

def carregar_buscas():
    global buscas_ativas
    try:
        if os.path.exists(ARQUIVO_BUSCAS):
            with open(ARQUIVO_BUSCAS, "r", encoding="utf-8") as f:
                buscas_ativas = json.load(f)
            logging.info(f"✅ Carregadas {len(buscas_ativas)} buscas salvas.")
    except Exception as e:
        logging.error(f"❌ Erro ao carregar buscas: {e}")

# --- Comandos Telegram ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚗 Bot de busca OLX\n\n"
        "Use /buscar para adicionar um carro:\n"
        "/buscar modelo, ano_min, preco_max, cidades (separadas por vírgula)\n"
        "Ex: /buscar gol, 2008, 30000, curitiba, pinhais, sao jose dos pinhais"
    )

async def buscar_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        texto = " ".join(context.args)
        dados = [x.strip() for x in texto.split(",")]
        if len(dados) < 4:
            await update.message.reply_text(
                "❌ Formato inválido. Use: modelo, ano_min, preco_max, cidade1, cidade2..."
            )
            return

        novo_carro = {
            "modelo": dados[0],
            "ano_min": int(dados[1]),
            "preco_max": float(dados[2]),
            "cidades": dados[3:]
        }
        buscas_ativas.append(novo_carro)
        salvar_buscas()
        await update.message.reply_text(
            f"✅ Adicionado! Monitorando {novo_carro['modelo']} em {novo_carro['cidades']}."
        )

    except Exception as e:
        logging.error(e)
        await update.message.reply_text(f"❌ Erro ao adicionar carro: {e}")

# --- Monitoramento ---
async def monitorar(context: ContextTypes.DEFAULT_TYPE):
    if not buscas_ativas:
        logging.info("Nenhum carro na lista ainda...")
        return

    for carro in buscas_ativas:
        for cidade in carro['cidades']:
            resultados = buscar_olx(
                modelo=carro['modelo'],
                ano_min=carro.get('ano_min', 0),
                km_max=carro.get('km_max', 999999),
                preco_max=carro.get('preco_max', 99999999),
                cidade=cidade
            )
            for link in resultados[:5]:  # limitar para não spam
                await context.bot.send_message(chat_id=CHAT_ID, text=f"🚗 {link}")

    salvar_buscas()  # salva a lista periodicamente

# --- Botão de continuar (para pausas opcionais) ---
async def botao_continuar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ Monitoramento retomado!")

# --- Inicialização do bot ---
if __name__ == "__main__":
    carregar_buscas()  # carrega buscas salvas

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buscar", buscar_comando))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, buscar_comando))

    # Scheduler - a cada 10 minutos
    job_queue = app.job_queue
    job_queue.run_repeating(monitorar, interval=600, first=10)  # 600s = 10 min

    print("Bot iniciado e monitorando buscas...")
    app.run_polling()
