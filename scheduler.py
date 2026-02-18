import asyncio
from scraper import buscar_olx
from database import obter_filtros, anuncio_ja_enviado, marcar_anuncio_enviado
from telegram.ext import ApplicationBuilder

async def checar_anuncios(application: ApplicationBuilder):
    filtros = obter_filtros()
    for filtro in filtros:
        _, usuario_id, modelo, ano_min, km_max, preco_max = filtro
        anuncios = buscar_olx(modelo, ano_min, km_max, preco_max)
        for link in anuncios:
            if not anuncio_ja_enviado(link):
                await application.bot.send_message(chat_id=int(usuario_id),
                                                   text=f"🚗 Novo anúncio: {link}")
                marcar_anuncio_enviado(link)
        await asyncio.sleep(1)  # não sobrecarregar

async def scheduler(application: ApplicationBuilder):
    while True:
        await checar_anuncios(application)
        await asyncio.sleep(60 * 30)  # roda a cada 30 minutos
