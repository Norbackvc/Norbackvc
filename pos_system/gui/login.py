"""
Login window.
"""
import tkinter as tk
from tkinter import messagebox
from .. import auth
from .styles import *


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("POS – Iniciar Sesión")
        self.resizable(False, False)
        self.configure(bg=DARK_BG)
        self._center(380, 440)
        self._build()

    def _center(self, w: int, h: int) -> None:
        self.geometry(f"{w}x{h}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self) -> None:
        container = tk.Frame(self, bg=PANEL_BG, padx=30, pady=30)
        container.place(relx=0.5, rely=0.5, anchor="center")

        # Logo / title
        tk.Label(container, text="🛒", font=("Segoe UI", 42),
                 bg=PANEL_BG, fg=ACCENT).pack()
        tk.Label(container, text="Punto de Venta",
                 font=FONT_TITLE, bg=PANEL_BG, fg=TEXT).pack(pady=(0, 4))
        tk.Label(container, text="Ingresa tus credenciales",
                 font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(pady=(0, 20))

        # Username
        tk.Label(container, text="Usuario", font=FONT_BODY,
                 bg=PANEL_BG, fg=TEXT_DIM, anchor="w").pack(fill="x")
        self.user_var = tk.StringVar()
        tk.Entry(container, textvariable=self.user_var, font=FONT_BODY,
                 bg=INPUT_BG, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=6).pack(fill="x", pady=(2, 12))

        # Password
        tk.Label(container, text="Contraseña", font=FONT_BODY,
                 bg=PANEL_BG, fg=TEXT_DIM, anchor="w").pack(fill="x")
        self.pass_var = tk.StringVar()
        pw_entry = tk.Entry(container, textvariable=self.pass_var, show="•",
                            font=FONT_BODY, bg=INPUT_BG, fg=TEXT,
                            insertbackground=TEXT, relief="flat", bd=6)
        pw_entry.pack(fill="x", pady=(2, 20))
        pw_entry.bind("<Return>", lambda e: self._login())

        # Login button
        tk.Button(container, text="Ingresar →", command=self._login,
                  **BTN_PRIMARY, width=22).pack()

        self.status_var = tk.StringVar()
        tk.Label(container, textvariable=self.status_var, font=FONT_SMALL,
                 bg=PANEL_BG, fg=DANGER).pack(pady=(8, 0))

    def _login(self) -> None:
        username = self.user_var.get().strip()
        password = self.pass_var.get()
        if not username or not password:
            self.status_var.set("Ingresa usuario y contraseña.")
            return
        user = auth.login(username, password)
        if user:
            self.destroy()
        else:
            self.status_var.set("Usuario o contraseña incorrectos.")
            self.pass_var.set("")
