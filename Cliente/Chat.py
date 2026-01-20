from tkinter import *
from tkinter import messagebox
from pathlib import Path
import socket
import threading
from datetime import datetime


HOST = "127.0.0.1"
PORT = 31424
LIMITE_MENSAGENS = 16


def main(username, sock):
    janela = Tk()
    janela.iconbitmap(Path(__file__).with_name("hacker.ico"))
    janela.title("Chat principal")
    janela.geometry("550x320")
    janela.resizable(False, False)

    historico = []

    # ===== RECEBER MENSAGENS DO SERVIDOR =====
    def ouvir_servidor():
        while True:
            try:
                resposta = sock.recv(1024).decode()
                if not resposta:
                    break

                historico.append(resposta)
                if len(historico) > LIMITE_MENSAGENS:
                    historico.pop(0)

                Mensagens.config(text="\n".join(historico))
            except:
                break

        messagebox.showwarning("Conexão", "Conexão encerrada pelo servidor")
        janela.destroy()

    # ===== ENVIAR MENSAGEM =====
    def enviar_msg(event=None):

        texto = Mensagem.get().strip()
        if not texto:
            return
        elif texto == "/exit":
            exit(0)
        elif texto == "/clear":
            historico.clear()
            Mensagens.config(text="")
        else:
            hora = datetime.now().strftime("%H:%M")
            msg = f"{hora} | {username}: {texto}"

            try:
                # ⚠️ NÃO adiciona no histórico aqui
                # quem devolve é o servidor (broadcast)
                sock.send(f"MSG|{msg}".encode())
            except:
                messagebox.showerror("Erro", "Falha ao enviar mensagem")
                return

        Mensagem.delete(0, END)

    # ===== UI =====
    Label(janela, text=f"Usuário: {username}")\
        .grid(column=0, row=0, pady=10, sticky="w", padx=10)

    Mensagens = Label(
        janela,
        width=60,
        height=LIMITE_MENSAGENS,
        anchor="nw",
        justify="left",
        relief="solid"
    )
    Mensagens.grid(column=0, row=1, columnspan=2, padx=10)

    Mensagem = Entry(janela, width=60)
    Mensagem.grid(column=0, row=2, padx=10, pady=10, sticky="w")
    Mensagem.bind("<Return>", enviar_msg)

    Button(janela, text="Enviar", width=10, command=enviar_msg)\
        .grid(column=1, row=2, padx=10)

    threading.Thread(target=ouvir_servidor, daemon=True).start()
    janela.mainloop()


def register():
    def tentar_login():
        username = user_input.get().strip()
        password = pass_input.get().strip()

        if not username or not password:
            messagebox.showerror("Erro", "Preencha todos os campos")
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))

            sock.send(f"LOGIN|{username}|{password}".encode())
            resposta = sock.recv(1024).decode()

            if resposta == "OK":
                janela.after(0, lambda: sucesso_login(sock, username))
            else:
                sock.close()
                janela.after(0, lambda: messagebox.showerror("Erro", "Login inválido"))

        except Exception as e:
            janela.after(0, lambda: messagebox.showerror("Erro", str(e)))

    def sucesso_login(sock, username):
        janela.destroy()
        main(username, sock)

    def iniciar_login(event=None):
        threading.Thread(target=tentar_login, daemon=True).start()

    # ===== JANELA LOGIN =====
    janela = Tk()
    janela.iconbitmap(Path(__file__).with_name("hacker.ico"))
    janela.title("Login")
    janela.geometry("330x120")
    janela.resizable(False, False)

    Label(janela, text="Username:").grid(column=0, row=0, padx=10, pady=10)
    user_input = Entry(janela)
    user_input.grid(column=1, row=0)

    Label(janela, text="Password:").grid(column=0, row=1, padx=10)
    pass_input = Entry(janela, show="*")
    pass_input.grid(column=1, row=1)

    Button(janela, text="Login", width=10, command=iniciar_login)\
        .grid(column=2, row=0, rowspan=2, padx=10)

    janela.bind("<Return>", iniciar_login)
    janela.mainloop()


if __name__ == "__main__":
    register()
