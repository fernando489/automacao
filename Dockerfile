# --- Base Python slim ---
FROM python:3.11-slim

# --- Variáveis de ambiente para Chromium headless ---
ENV CHROME_BIN=/usr/bin/chromium
ENV DEBIAN_FRONTEND=noninteractive

# --- Instala Chromium + dependências Selenium/Headless ---
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libx11-xcb1 \
    libxcb1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# --- Diretório de trabalho ---
WORKDIR /app

# --- Instala dependências Python ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Copia o código do projeto ---
COPY . .

# --- Comando padrão para rodar o bot ---
CMD ["python", "bot.py"]
