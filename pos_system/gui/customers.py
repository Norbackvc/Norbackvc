"""
Customer management frame.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from .. import sales as sales_mod
from .styles import *


class CustomersFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=DARK_BG)
        self._build()
        self.refresh()

    def _build(self):
        # Toolbar
        toolbar = tk.Frame(self, bg=PANEL_BG, padx=PAD, pady=8)
        toolbar.pack(fill="x")
        tk.Label(toolbar, text="👥  Clientes", font=FONT_H1,
                 bg=PANEL_BG, fg=TEXT).pack(side="left")
        tk.Button(toolbar, text="+ Nuevo", command=self._new,
                  **BTN_PRIMARY).pack(side="right", padx=4)

        # Search
        sf = tk.Frame(self, bg=DARK_BG, padx=PAD, pady=6)
        sf.pack(fill="x")
        tk.Label(sf, text="Buscar:", font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        tk.Entry(sf, textvariable=self.search_var, font=FONT_BODY,
                 bg=INPUT_BG, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=6, width=30).pack(side="left", padx=8)

        # Table
        cols = ("ID", "Nombre", "Teléfono", "Email", "RFC", "Dirección")
        frame = tk.Frame(self, bg=DARK_BG)
        frame.pack(fill="both", expand=True, padx=PAD, pady=4)

        style = ttk.Style()
        style.configure("POS.Treeview",
                        background=CARD_BG, foreground=TEXT,
                        fieldbackground=CARD_BG, rowheight=26, font=FONT_BODY)
        style.configure("POS.Treeview.Heading",
                        background=PANEL_BG, foreground=TEXT_DIM, font=FONT_SMALL)
        style.map("POS.Treeview", background=[("selected", ACCENT)])

        self.tree = ttk.Treeview(frame, columns=cols, show="headings",
                                 style="POS.Treeview", selectmode="browse")
        widths = (40, 200, 110, 160, 100, 200)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w,
                             anchor="w" if w > 80 else "center")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda e: self._edit_selected())

        # Bottom bar
        bot = tk.Frame(self, bg=DARK_BG, padx=PAD, pady=6)
        bot.pack(fill="x")
        tk.Button(bot, text="✏ Editar", command=self._edit_selected,
                  **BTN_NEUTRAL).pack(side="left", padx=4)
        tk.Button(bot, text="🗑 Eliminar", command=self._delete_selected,
                  **BTN_DANGER).pack(side="left", padx=4)

    def refresh(self):
        customers = sales_mod.list_customers(self.search_var.get())
        self.tree.delete(*self.tree.get_children())
        for c in customers:
            self.tree.insert("", "end", iid=str(c["id"]),
                             values=(c["id"], c["name"], c["phone"],
                                     c["email"], c["rfc"], c["address"]))

    def _selected_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _new(self):
        CustomerDialog(self, "Nuevo Cliente").grab_set()
        self.wait_window(self.winfo_children()[-1])
        self.refresh()

    def _edit_selected(self):
        cid = self._selected_id()
        if cid is None:
            return
        cust = sales_mod.get_customer(cid)
        if cust:
            CustomerDialog(self, "Editar Cliente", customer=cust).grab_set()
            self.wait_window(self.winfo_children()[-1])
            self.refresh()

    def _delete_selected(self):
        cid = self._selected_id()
        if cid is None:
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar cliente seleccionado?",
                               parent=self):
            sales_mod.delete_customer(cid)
            self.refresh()


class CustomerDialog(tk.Toplevel):
    def __init__(self, parent, title="Cliente", customer=None):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=PANEL_BG)
        self.resizable(False, False)
        self._customer = customer
        self._build()
        if customer:
            self._populate(customer)
        self.geometry("400x440")

    def _build(self):
        tk.Label(self, text="Datos del Cliente", font=FONT_H2,
                 bg=PANEL_BG, fg=TEXT).pack(pady=(14, 6))
        form = tk.Frame(self, bg=PANEL_BG)
        form.pack(fill="both", padx=16, pady=4)
        self._vars = {}
        for label, key in [
            ("Nombre*", "name"), ("Teléfono", "phone"), ("Email", "email"),
            ("RFC", "rfc"), ("Dirección", "address"), ("Notas", "notes"),
        ]:
            row = tk.Frame(form, bg=PANEL_BG)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, font=FONT_SMALL, bg=PANEL_BG,
                     fg=TEXT_DIM, width=12, anchor="w").pack(side="left")
            var = tk.StringVar()
            tk.Entry(row, textvariable=var, font=FONT_BODY, bg=INPUT_BG,
                     fg=TEXT, insertbackground=TEXT, relief="flat", bd=4,
                     ).pack(side="left", fill="x", expand=True)
            self._vars[key] = var

        btn_row = tk.Frame(self, bg=PANEL_BG)
        btn_row.pack(fill="x", padx=16, pady=12)
        tk.Button(btn_row, text="Cancelar", command=self.destroy,
                  **BTN_NEUTRAL).pack(side="right", padx=4)
        tk.Button(btn_row, text="Guardar", command=self._save,
                  **BTN_PRIMARY).pack(side="right", padx=4)

    def _populate(self, c):
        for key in self._vars:
            self._vars[key].set(c.get(key, "") or "")

    def _save(self):
        name = self._vars["name"].get().strip()
        if not name:
            from tkinter import messagebox
            messagebox.showerror("Error", "El nombre es obligatorio.", parent=self)
            return
        kw = {k: self._vars[k].get().strip() for k in self._vars if k != "name"}
        if self._customer:
            sales_mod.update_customer(self._customer["id"], name, **kw)
        else:
            sales_mod.add_customer(name, **kw)
        self.destroy()
