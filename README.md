# Gram Car Monitor

Bot Telegram para monitoramento de carros na OLX.

## Comandos
- `/start` → Ativa o bot
- `/carro` → Define filtros (modelo, ano_min, km_max, preco_max)

## Estrutura
- `bot.py` → Bot Telegram
- `database.py` → Banco SQLite
- `scraper.py` → Scraper OLX
- `scheduler.py` → Scheduler periódico
- `logger.py` → Logs
- `.env` → Token do bot
- `requirements.txt` → Dependências do Python
- `Procfile` → Deploy Render
