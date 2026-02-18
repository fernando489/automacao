import logging

logging.basicConfig(
    filename="monitor.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_info(msg):
    logging.info(msg)
    print(msg)

def log_error(msg):
    logging.error(msg)
    print("ERRO:", msg)
