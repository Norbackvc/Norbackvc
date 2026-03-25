"""
Punto de Venta – Entry point.

Uso:
    python main.py
"""
import sys
import os

# Allow running as: python main.py  (from repo root) or from inside pos_system/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pos_system.database import initialize_database
from pos_system import auth
from pos_system.gui.login import LoginWindow
from pos_system.gui.main_window import MainWindow


def run() -> None:
    initialize_database()

    while True:
        # Show login window
        login = LoginWindow()
        login.mainloop()

        user = auth.current_user()
        if user is None:
            # User closed the login window without logging in → exit
            break

        # Show main application window
        app = MainWindow()
        app.mainloop()

        # If user chose "Cerrar sesión" (logout), loop back to login
        # If user closed the window (auth still set), treat as exit
        if auth.current_user() is not None:
            # Window was closed without explicit logout → exit
            break
        # else: auth.current_user() is None → user logged out → show login again


if __name__ == "__main__":
    run()
