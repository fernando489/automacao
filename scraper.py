import requests
from bs4 import BeautifulSoup

def buscar_olx(termo):
    termo_url = termo.replace(" ", "-")
    url = f"https://www.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios?q={termo_url}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Erro ao acessar OLX: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    resultados = []

    for anuncio in soup.select("li.sc-1fcmfeb-2"):
        try:
            titulo = anuncio.select_one("h2.sc-1qoge2i-0").get_text(strip=True)
            preco_tag = anuncio.select_one("p.sc-ifAKCX.cHGsRk")
            preco = preco_tag.get_text(strip=True) if preco_tag else "Sem preço"
            link_tag = anuncio.select_one("a.sc-1fcmfeb-1")
            link = link_tag["href"] if link_tag else "#"
            cidade_tag = anuncio.select_one("span.sc-ifAKCX.fVYUd")
            cidade = cidade_tag.get_text(strip=True) if cidade_tag else "Indefinida"

            resultados.append({
                "titulo": titulo,
                "preco": preco,
                "link": link,
                "cidade": cidade
            })
        except:
            continue

    return resultados
