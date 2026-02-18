import requests
from bs4 import BeautifulSoup
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def buscar_olx(termo, tempo_monitoramento=0):
    url = f"https://www.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios?q={termo.replace(' ', '%20')}&search[locations][0]=Curitiba%2C%20PR&private_business=1"

    inicio = time.time()

    while True:
        try:
            resposta = requests.get(url, headers=HEADERS, timeout=15)

            if resposta.status_code != 200:
                return "⚠️ OLX pode ter bloqueado a requisição."

            soup = BeautifulSoup(resposta.text, "html.parser")
            anuncios = soup.find_all("a")

            encontrados = []

            for anuncio in anuncios:
                texto = anuncio.get_text()
                link = anuncio.get("href")

                if termo.lower() in texto.lower() and link and "olx.com.br" in link:
                    encontrados.append(f"🚗 {texto.strip()[:80]}\n🔗 {link}")

            if encontrados:
                return "\n\n".join(encontrados[:5])

            if tempo_monitoramento == 0:
                return "❌ Nenhum resultado encontrado agora."

            if time.time() - inicio > tempo_monitoramento:
                return "⏳ Monitoramento encerrado. Nada encontrado."

            time.sleep(30)

        except requests.exceptions.RequestException:
            return "⚠️ Erro de conexão ou possível bloqueio da OLX."
