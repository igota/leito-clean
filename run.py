import os
import threading
from waitress import serve
from pystray import Icon, Menu, MenuItem
from PIL import Image

# IMPORTANTE: apenas importa o app
# As threads de background DEVEM nascer no app.py
from app import app


# ================================
# ÍCONE NA BANDEJA DO SISTEMA
# ================================
def setup_tray_icon():
    try:
        icon = Icon("LeitoClean")

        icon.icon = Image.open(
            "C:/MEGA/Projeto Leito Clean/static/img/logo_leitoclean.ico"
        )

        icon.title = "LeitoClean - 1.0"

        icon.menu = Menu(
            MenuItem("Sair", on_exit)
        )

        icon.run()

    except Exception as e:
        print(f"❌ Erro no ícone da bandeja: {e}")


def on_exit(icon, item):
    icon.stop()
    print("🛑 Encerrando aplicação...")
    os._exit(0)   # encerra tudo imediatamente


# ================================
# MAIN
# ================================
if __name__ == "__main__":

    # Inicia o ícone da bandeja em background
    tray_thread = threading.Thread(
        target=setup_tray_icon,
        daemon=True
    )
    tray_thread.start()

    print("🚀 Servidor LeitoClean iniciado em http://0.0.0.0:5000")

    # ⚠️ SERVE É BLOQUEANTE — deve ser a ÚLTIMA coisa
    serve(
        app,
        host="0.0.0.0",
        port=5000,
        threads=20
    )
