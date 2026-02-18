import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO)

def buscar_olx(modelo, ano_min=0, km_max=999999, preco_max=99999999, cidade=""):
    logging.info(f"Buscando: {modelo}, ano>={ano_min}, km<={km_max}, preco<={preco_max}, cidade={cidade}")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = "/usr/bin/chromium"

    driver = webdriver.Chrome(options=options)

    url = f"https://www.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios?q={modelo}"
    if cidade:
        cidade_url = cidade.replace(" ", "-").lower()
        url += f"&o={cidade_url}"

    driver.get(url)
    time.sleep(3)

    anuncios = []

    try:
        items = driver.find_elements(By.TAG_NAME, "a")
        for item in items:
            link = item.get_attribute("href")
            if link and "autos-e-pecas" in link:
                anuncios.append(link)

    except Exception as e:
        logging.warning(f"Erro ao buscar elementos: {e}")

    driver.quit()
    logging.info(f"{len(anuncios)} anúncios encontrados")
    return anuncios
