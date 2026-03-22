import os
import sys
import tkinter as tk
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import threading
from waitress import serve
from app import app
import subprocess

# Variável global para controle do servidor e processo de logs
server_running = True
log_process = None  # Para manter o processo do console aberto

# Cria um ícone a partir de uma imagem JPG
def create_image():
    image_path = "C:\Projeto Etiqueta Ag Transfusional\static\icone_etiquetaAT.jpg"  # Substitua pelo caminho da sua imagem
    image = Image.open(image_path)
    image = image.resize((64, 64))  # Redimensiona a imagem para 64x64 pixels, se necessário
    return image

# Função para parar o servidor
def stop_server():
    global server_running
    server_running = False

# Mostra uma janela de debug com logs ao clicar em "Sobre"
def show_logs():
    global log_process
    if log_process is None or log_process.poll() is not None:
        # Abre um terminal que exibe o log do servidor Flask
        log_process = subprocess.Popen([sys.executable, "-u", "app.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)

# Ação para sair e fechar completamente o aplicativo
def quit_action(icon, item):
    icon.stop()  # Para o ícone da bandeja
    stop_server()  # Para o servidor
    if log_process:
        log_process.terminate()  # Termina o processo de logs, se aberto
    os._exit(0)   # Fecha o programa imediatamente

# Função principal do ícone de bandeja
def setup_tray_icon():
    icon = Icon("EtiquetaAT")
    icon.icon = create_image()
    icon.title = "Etiqueta AT - 1.0"
    icon.menu = Menu(
    
        MenuItem("Sobre", lambda icon, item: show_logs()),  # Abre logs ao clicar em "Sobre"
        MenuItem("Sair", quit_action)  # Chama a função para sair
    )
    icon.run()

    

# Função para iniciar o servidor em loop, verificando a variável server_running
def run_server():
    while server_running:
        serve(app, host='0.0.0.0', port=5010)

if __name__ == "__main__":
    # Inicia o ícone da bandeja em uma thread separada
    tray_thread = threading.Thread(target=setup_tray_icon, daemon=True)
    tray_thread.start()
    
    # Inicia o servidor Flask com waitress em outra thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Mantém o programa principal ativo enquanto as threads de servidor e tray icon estão ativas
    tray_thread.join()
    server_thread.join()
