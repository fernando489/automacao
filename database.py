import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
DB_FILE = "carros.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS filtros (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 usuario_id TEXT,
                 modelo TEXT,
                 ano_min INTEGER,
                 km_max INTEGER,
                 preco_max REAL
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS anuncios (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 link TEXT UNIQUE
                 )''')
    conn.commit()
    conn.close()
    logging.info("Banco inicializado")

def salvar_filtro(usuario_id, modelo, ano_min, km_max, preco_max):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO filtros (usuario_id, modelo, ano_min, km_max, preco_max) VALUES (?,?,?,?,?)',
              (usuario_id, modelo, ano_min, km_max, preco_max))
    conn.commit()
    conn.close()
    logging.info(f"Filtro salvo para {usuario_id}: {modelo}, ano>={ano_min}, km<={km_max}, preco<={preco_max}")

def obter_filtros():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM filtros')
    resultados = c.fetchall()
    conn.close()
    return resultados

def anuncio_ja_enviado(link):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT 1 FROM anuncios WHERE link=?', (link,))
    existe = c.fetchone() is not None
    conn.close()
    return existe

def marcar_anuncio_enviado(link):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO anuncios (link) VALUES (?)', (link,))
    conn.commit()
    conn.close()
    logging.info(f"Anuncio marcado como enviado: {link}")
