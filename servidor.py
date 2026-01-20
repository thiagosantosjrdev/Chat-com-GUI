import socket
import pandas as pd
from pathlib import Path
import threading
import logging


HOST = "127.0.0.1"
PORT = 31424

logging.basicConfig(
    format="[%(asctime)s] - %(levelname)s > %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO
)

clientes: list = []
clientes_lock = threading.Lock()


def broadcast(msg, origem=None):
    with clientes_lock:
        for c in clientes[:]:
            try:
                c.send(msg.encode())
            except:
                clientes.remove(c)
                c.close()


def cliente_handler(conn, addr):
    logging.info(f"Cliente conectado: {addr}")

    try:
        # ===== LOGIN =====
        data = conn.recv(1024).decode().strip()
        if not data.startswith("LOGIN|"):
            conn.close()
            return

        _, username, password = data.split("|", 2)
        logging.info(f"{addr} tentou login como '{username}'")

        arq = pd.read_csv(Path(__file__).with_name("dados.csv"))
        valido = not arq[
            (arq["username"] == username) &
            (arq["password"] == password)
        ].empty

        if not valido:
            conn.send(b"FAIL")
            conn.close()
            return

        conn.send(b"OK")

        # ===== REGISTRA CLIENTE =====
        with clientes_lock:
            clientes.append(conn)

        broadcast(f"[+] {username} entrou no chat")

        # ===== CHAT =====
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            if data.startswith("MSG|"):
                conteudo = data[4:]
                logging.info(f"{username}: {conteudo}")
                broadcast(f"{username}: {conteudo}", origem=conn)

    except Exception as e:
        logging.warning(f"{addr} desconectado ({e})")

    finally:
        with clientes_lock:
            if conn in clientes:
                clientes.remove(conn)

        broadcast(f"[-] {username} saiu do chat")
        conn.close()
        logging.info(f"Cliente desconectado: {addr}")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        logging.info("Servidor rodando com broadcast...")

        while True:
            conn, addr = s.accept()
            threading.Thread(
                target=cliente_handler,
                args=(conn, addr),
                daemon=True
            ).start()


if __name__ == "__main__":
    main()
