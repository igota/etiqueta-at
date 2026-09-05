# run.py - Sistema de Etiqueta AT
from datetime import time
import os
import sys
import tkinter as tk
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import threading
from waitress import serve
from app import app
import subprocess
import webbrowser

# Variável global para controle do servidor
server_running = True

# Pasta onde está o .exe (build) ou o run.py (dev) — usada para localizar o ícone padrão
_base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

# Configurações do servidor (lidas do .env, com fallback para os valores padrão)
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))
THREADS = int(os.environ.get('THREADS', 100))

# Cria um ícone a partir de uma imagem
def create_image():
    # Tenta carregar a logo do sistema de etiqueta AT
    image_paths = [
        p for p in [
            os.environ.get('ICON_PATH'),
            os.path.join(_base_dir, 'static', 'icone_etiquetaAT.jpg'),
        ] if p
    ]

    for path in image_paths:
        if os.path.exists(path):
            try:
                image = Image.open(path)
                image = image.resize((128, 128))
                return image
            except:
                continue
    
    # Ícone padrão se não encontrar imagem
    image = Image.new('RGB', (64, 64), color='#e74c3c')
    draw = ImageDraw.Draw(image)
    draw.rectangle([10, 10, 54, 54], outline='white', width=2)
    draw.text((18, 20), "E", fill='white', font=None)
    draw.text((30, 20), "T", fill='white', font=None)
    return image

# Função para parar o servidor
def stop_server():
    global server_running
    server_running = False

# Mostra janela com informações do sistema
def show_about():
    root = tk.Tk()
    root.title("Sobre - Sistema de Etiqueta AT")
    root.geometry("450x350")
    root.resizable(False, False)
    
    # Centralizar na tela
    root.eval('tk::PlaceWindow . center')
    
    # Frame principal
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Título
    tk.Label(frame, text="Sistema de Etiqueta AT", font=("Arial", 16, "bold"), fg="#e74c3c").pack(pady=(0, 10))
    
    # Informações
    info_text = """
    Sistema de Etiqueta para Agência Transfusional
    Versão: 1.0
    Desenvolvido por: Igor Maciel de Sousa
    
    Funcionalidades:
    • Geração de etiquetas
    • Impressão de etiquetas
    • Integração com Vitae
    
    ISGH - INSTITUTO DE SAÚDE E GESTÃO HOSPITALAR
    """
    
    tk.Label(frame, text=info_text, justify=tk.LEFT, font=("Arial", 10)).pack()
    
    # Status do servidor
    status_frame = tk.Frame(frame)
    status_frame.pack(fill=tk.X, pady=(15, 10))
    
    tk.Label(status_frame, text="Status:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
    tk.Label(status_frame, text="🟢 Online", font=("Arial", 10), fg="green").pack(side=tk.LEFT, padx=(5, 0))
    
    # Botão Fechar
    tk.Button(frame, text="Fechar", command=root.destroy, bg="#e74c3c", fg="white", 
              padx=20, pady=5, font=("Arial", 10, "bold")).pack(pady=(20, 0))
    
    root.mainloop()

# Função para abrir o navegador
def open_browser():
    webbrowser.open(f"http://127.0.0.1:{PORT}")

# Função para verificar status do servidor
def show_status():
    root = tk.Tk()
    root.title("Status do Servidor")
    root.geometry("400x250")
    root.resizable(False, False)
    root.eval('tk::PlaceWindow . center')
    
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    tk.Label(frame, text="Status do Servidor", font=("Arial", 14, "bold"), fg="#e74c3c").pack(pady=(0, 15))
    
    info = f"""
    Servidor: {HOST}:{PORT}
    Threads: {THREADS}
    Status: 🟢 Executando
    
    Endereços de acesso:
    • Local: http://127.0.0.1:{PORT}
    • Rede: http://{HOST}:{PORT}
    """
    
    tk.Label(frame, text=info, justify=tk.LEFT, font=("Arial", 10)).pack()
    
    tk.Button(frame, text="Fechar", command=root.destroy, bg="#e74c3c", fg="white", 
              padx=20, pady=5, font=("Arial", 10, "bold")).pack(pady=(20, 0))
    
    root.mainloop()

# Ação para sair
def quit_action(icon, item):
    icon.stop()
    stop_server()
    os._exit(0)

# Função principal do ícone de bandeja
def setup_tray_icon():
    icon = Icon("EtiquetaAT")
    icon.icon = create_image()
    icon.title = "Sistema de Etiqueta AT"
    
    icon.menu = Menu(
        MenuItem("🌐 Abrir no Navegador", lambda icon, item: open_browser()),
        MenuItem("📊 Status do Servidor", lambda icon, item: show_status()),
        MenuItem("ℹ️ Sobre", lambda icon, item: show_about()),
        MenuItem("❌ Sair", quit_action)
    )
    icon.run()

# Função para iniciar o servidor com Waitress
def run_server():
    print(f"🚀 Iniciando servidor em http://{HOST}:{PORT}")
    print(f"📁 Servindo aplicação com Waitress ({THREADS} threads)")
    
    while server_running:
        try:
            serve(app, host=HOST, port=PORT, threads=THREADS)
        except Exception as e:
            if server_running:
                print(f"❌ Erro no servidor: {e}")
                time.sleep(2)

# Função para iniciar com console (debug)
def run_with_console():
    """Inicia o servidor com console para debug"""
    print("="*60)
    print(" SISTEMA DE ETIQUETA AT ")
    print("="*60)
    print(f" 🌐 Servidor: http://{HOST}:{PORT}")
    print(" 🔧 Modo: Console (debug ativo)")
    print("="*60)
    print()
    
    app.run(debug=True, host=HOST, port=PORT, use_reloader=False)

if __name__ == "__main__":
    import sys
    
    # Verificar se deve rodar com console ou com bandeja
    if len(sys.argv) > 1 and sys.argv[1] == '--console':
        # Modo console (para debug)
        run_with_console()
    else:
        # Modo bandeja (para produção)
        print("🔧 Iniciando Sistema de Etiqueta AT em modo bandeja...")
        
        # Inicia o ícone da bandeja em uma thread separada
        tray_thread = threading.Thread(target=setup_tray_icon, daemon=True)
        tray_thread.start()
        
        # Inicia o servidor Flask com waitress em outra thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        print(f"✅ Servidor iniciado em http://{HOST}:{PORT}")
        print("📌 Ícone na bandeja do sistema (clique com botão direito para opções)")
        print("   Para encerrar, clique em 'Sair' no menu da bandeja")
        
        # Mantém o programa principal ativo
        tray_thread.join()
        server_thread.join()