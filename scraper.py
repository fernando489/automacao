import requests
from bs4 import BeautifulSoup
import time
import random

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def buscar_olx(termo, tempo_monitoramento=600):
    url = f"https://www.olx.com.br/brasil?q={termo.replace(' ', '%20')}"
    inicio = time.time()

    while True:
        try:
            resposta = requests.get(url, headers=HEADERS, timeout=15)

            # 🚨 Bloqueio ou erro
            if resposta.status_code in [403, 429]:
                return "🚨 A OLX bloqueou a requisição temporariamente."

            if resposta.status_code != 200:
                return "⚠️ Erro ao acessar OLX."

            soup = BeautifulSoup(resposta.text, "html.parser")
            anuncios = soup.find_all("a")

            encontrados = []

            for anuncio in anuncios:
                texto = anuncio.get_text()
                link = anuncio.get("href")

                if texto and link and "olx.com.br" in link:
                    if termo.lower() in texto.lower():
                        encontrados.append(
                            f"🚗 {texto.strip()[:80]}\n🔗 {link}"
                        )

            # ✅ Achou resultado
            if encontrados:
                return "\n\n".join(encontrados[:5])

            # ⏳ Tempo acabou
            if time.time() - inicio > tempo_monitoramento:
                return "❌ Nenhum anúncio encontrado nos últimos 10 minutos."

            # Espera antes da próxima tentativa
            time.sleep(random.randint(25, 35))

        except requests.exceptions.RequestException:
            return "⚠️ Erro de conexão ou possível bloqueio da OLX."
