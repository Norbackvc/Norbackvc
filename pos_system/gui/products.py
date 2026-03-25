"""
Product management window (embedded as a Toplevel or Frame).
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from .. import inventory, auth
from .styles import *


class ProductsFrame(tk.Frame):
    """Full product catalog manager embedded in a parent notebook tab."""

    def __init__(self, parent):
        super().__init__(parent, bg=DARK_BG)
        self._build()
        self.refresh()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # Toolbar
        toolbar = tk.Frame(self, bg=PANEL_BG, padx=PAD, pady=8)
        toolbar.pack(fill="x")

        tk.Label(toolbar, text="📦  Productos", font=FONT_H1,
                 bg=PANEL_BG, fg=TEXT).pack(side="left")

        if auth.is_admin():
            tk.Button(toolbar, text="+ Nuevo", command=self._new,
                      **BTN_PRIMARY).pack(side="right", padx=4)
            tk.Button(toolbar, text="Categorías", command=self._manage_categories,
                      **BTN_NEUTRAL).pack(side="right", padx=4)

        # Search bar
        search_frame = tk.Frame(self, bg=DARK_BG, padx=PAD, pady=6)
        search_frame.pack(fill="x")
        tk.Label(search_frame, text="Buscar:", font=FONT_BODY,
                 bg=DARK_BG, fg=TEXT_DIM).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        tk.Entry(search_frame, textvariable=self.search_var, font=FONT_BODY,
                 bg=INPUT_BG, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=6, width=30).pack(side="left", padx=8)

        # Category filter
        tk.Label(search_frame, text="Categoría:", font=FONT_BODY,
                 bg=DARK_BG, fg=TEXT_DIM).pack(side="left")
        self.cat_var = tk.StringVar(value="Todas")
        self.cat_cb = ttk.Combobox(search_frame, textvariable=self.cat_var,
                                   state="readonly", width=16, font=FONT_BODY)
        self.cat_cb.pack(side="left", padx=8)
        self.cat_cb.bind("<<ComboboxSelected>>", lambda *_: self.refresh())

        # Table
        cols = ("ID", "Código", "Nombre", "Categoría", "Precio",
                "Costo", "Stock", "Mín.", "Unidad")
        frame = tk.Frame(self, bg=DARK_BG)
        frame.pack(fill="both", expand=True, padx=PAD, pady=4)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("POS.Treeview",
                        background=CARD_BG, foreground=TEXT,
                        fieldbackground=CARD_BG, rowheight=26,
                        font=FONT_BODY)
        style.configure("POS.Treeview.Heading",
                        background=PANEL_BG, foreground=TEXT_DIM,
                        font=FONT_SMALL)
        style.map("POS.Treeview", background=[("selected", ACCENT)])

        self.tree = ttk.Treeview(frame, columns=cols, show="headings",
                                 style="POS.Treeview", selectmode="browse")
        widths = (40, 90, 180, 100, 70, 70, 60, 50, 60)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center" if w < 100 else "w")
        self.tree.column("Nombre", anchor="w")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda e: self._edit_selected())

        # Bottom action bar
        if auth.is_admin():
            bot = tk.Frame(self, bg=DARK_BG, padx=PAD, pady=6)
            bot.pack(fill="x")
            tk.Button(bot, text="✏ Editar", command=self._edit_selected,
                      **BTN_NEUTRAL).pack(side="left", padx=4)
            tk.Button(bot, text="🗑 Eliminar", command=self._delete_selected,
                      **BTN_DANGER).pack(side="left", padx=4)
            tk.Button(bot, text="📦 Ajustar Stock", command=self._adjust_stock,
                      **BTN_PRIMARY).pack(side="left", padx=4)

    # ── Data ─────────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        # Update categories combobox
        cats = [{"id": None, "name": "Todas"}] + inventory.list_categories()
        self._cat_map = {c["name"]: c["id"] for c in cats}
        self.cat_cb["values"] = list(self._cat_map.keys())
        if self.cat_var.get() not in self._cat_map:
            self.cat_var.set("Todas")

        cat_id = self._cat_map.get(self.cat_var.get())
        products = inventory.list_products(
            search=self.search_var.get(),
            category_id=cat_id,
        )

        self.tree.delete(*self.tree.get_children())
        sym = "$"
        for p in products:
            low = p["stock"] <= p["min_stock"]
            tag = "low" if low else ""
            self.tree.insert("", "end", iid=str(p["id"]),
                             values=(p["id"], p["barcode"] or "", p["name"],
                                     p["category_name"] or "",
                                     f"{sym}{p['price']:.2f}",
                                     f"{sym}{p['cost']:.2f}",
                                     p["stock"], p["min_stock"], p["unit"]),
                             tags=(tag,))
        self.tree.tag_configure("low", foreground=WARNING)

    def _selected_id(self) -> int | None:
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    # ── Actions ───────────────────────────────────────────────────────────────

    def _new(self) -> None:
        ProductDialog(self, title="Nuevo Producto").grab_set()
        self.wait_window(self.winfo_children()[-1])
        self.refresh()

    def _edit_selected(self) -> None:
        pid = self._selected_id()
        if pid is None:
            return
        prod = inventory.get_product(pid)
        if prod:
            ProductDialog(self, title="Editar Producto", product=prod).grab_set()
            self.wait_window(self.winfo_children()[-1])
            self.refresh()

    def _delete_selected(self) -> None:
        pid = self._selected_id()
        if pid is None:
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar producto seleccionado?",
                               parent=self):
            inventory.delete_product(pid)
            self.refresh()

    def _adjust_stock(self) -> None:
        pid = self._selected_id()
        if pid is None:
            return
        prod = inventory.get_product(pid)
        delta = simpledialog.askinteger(
            "Ajuste de Stock",
            f"Ingresa la cantidad a agregar (negativa para restar)\nActual: {prod['stock']}",
            parent=self,
        )
        if delta is not None:
            inventory.adjust_stock(pid, delta)
            self.refresh()

    def _manage_categories(self) -> None:
        CategoriesDialog(self).grab_set()
        self.wait_window(self.winfo_children()[-1])
        self.refresh()


# ── Product Dialog ────────────────────────────────────────────────────────────

class ProductDialog(tk.Toplevel):
    def __init__(self, parent, title: str = "Producto", product: dict = None):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=PANEL_BG)
        self.resizable(False, False)
        self._product = product
        self._build()
        if product:
            self._populate(product)
        self._center(440, 540)

    def _center(self, w, h):
        self.geometry(f"{w}x{h}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        pad = dict(padx=16, pady=4)
        tk.Label(self, text="Datos del Producto", font=FONT_H2,
                 bg=PANEL_BG, fg=TEXT).pack(**pad, pady=(16, 8))

        form = tk.Frame(self, bg=PANEL_BG)
        form.pack(fill="both", padx=16, pady=4)

        self._vars = {}
        fields = [
            ("Nombre*", "name", "entry"),
            ("Código de barras", "barcode", "entry"),
            ("Descripción", "description", "entry"),
            ("Categoría", "category_id", "combo"),
            ("Precio*", "price", "entry"),
            ("Costo", "cost", "entry"),
            ("Stock inicial", "stock", "entry"),
            ("Stock mínimo", "min_stock", "entry"),
            ("Unidad", "unit", "entry"),
        ]
        for label, key, kind in fields:
            row = tk.Frame(form, bg=PANEL_BG)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, font=FONT_SMALL, bg=PANEL_BG,
                     fg=TEXT_DIM, width=18, anchor="w").pack(side="left")
            if kind == "entry":
                var = tk.StringVar()
                tk.Entry(row, textvariable=var, font=FONT_BODY, bg=INPUT_BG,
                         fg=TEXT, insertbackground=TEXT, relief="flat", bd=4
                         ).pack(side="left", fill="x", expand=True)
                self._vars[key] = var
            elif kind == "combo":
                cats = inventory.list_categories()
                self._cat_map = {c["name"]: c["id"] for c in cats}
                self._cat_map["Sin categoría"] = None
                var = tk.StringVar(value="Sin categoría")
                cb = ttk.Combobox(row, textvariable=var,
                                  values=["Sin categoría"] + [c["name"] for c in cats],
                                  state="readonly", font=FONT_BODY, width=20)
                cb.pack(side="left")
                self._vars[key] = var

        btn_row = tk.Frame(self, bg=PANEL_BG)
        btn_row.pack(fill="x", padx=16, pady=12)
        tk.Button(btn_row, text="Cancelar", command=self.destroy,
                  **BTN_NEUTRAL).pack(side="right", padx=4)
        tk.Button(btn_row, text="Guardar", command=self._save,
                  **BTN_PRIMARY).pack(side="right", padx=4)

    def _populate(self, p):
        self._vars["name"].set(p["name"])
        self._vars["barcode"].set(p["barcode"] or "")
        self._vars["description"].set(p["description"] or "")
        self._vars["price"].set(str(p["price"]))
        self._vars["cost"].set(str(p["cost"]))
        self._vars["stock"].set(str(p["stock"]))
        self._vars["min_stock"].set(str(p["min_stock"]))
        self._vars["unit"].set(p["unit"])
        # Set category
        cats = inventory.list_categories()
        cat_name = "Sin categoría"
        for c in cats:
            if c["id"] == p.get("category_id"):
                cat_name = c["name"]
        self._vars["category_id"].set(cat_name)

    def _save(self):
        name = self._vars["name"].get().strip()
        if not name:
            messagebox.showerror("Error", "El nombre es obligatorio.", parent=self)
            return
        try:
            price = float(self._vars["price"].get() or 0)
            cost  = float(self._vars["cost"].get() or 0)
            stock = int(self._vars["stock"].get() or 0)
            min_s = int(self._vars["min_stock"].get() or 5)
        except ValueError:
            messagebox.showerror("Error", "Precio/Costo/Stock deben ser números.", parent=self)
            return

        cat_name = self._vars["category_id"].get()
        cat_id   = self._cat_map.get(cat_name)

        if self._product:
            inventory.update_product(
                self._product["id"], name, price, cost, stock, min_s,
                self._vars["barcode"].get().strip(),
                self._vars["description"].get().strip(),
                cat_id, self._vars["unit"].get().strip() or "pza",
            )
        else:
            inventory.add_product(
                name=name, price=price, cost=cost, stock=stock, min_stock=min_s,
                barcode=self._vars["barcode"].get().strip(),
                description=self._vars["description"].get().strip(),
                category_id=cat_id,
                unit=self._vars["unit"].get().strip() or "pza",
            )
        self.destroy()


# ── Categories Dialog ─────────────────────────────────────────────────────────

class CategoriesDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Categorías")
        self.configure(bg=PANEL_BG)
        self.resizable(False, False)
        self.geometry("300x380")
        self._build()
        self._load()

    def _build(self):
        tk.Label(self, text="Categorías", font=FONT_H2,
                 bg=PANEL_BG, fg=TEXT).pack(pady=(12, 6))
        self.listbox = tk.Listbox(self, font=FONT_BODY,
                                   bg=CARD_BG, fg=TEXT, selectbackground=ACCENT,
                                   relief="flat", bd=0)
        self.listbox.pack(fill="both", expand=True, padx=16, pady=4)
        row = tk.Frame(self, bg=PANEL_BG)
        row.pack(fill="x", padx=16, pady=8)
        self.new_var = tk.StringVar()
        tk.Entry(row, textvariable=self.new_var, font=FONT_BODY,
                 bg=INPUT_BG, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=4).pack(side="left", fill="x", expand=True)
        tk.Button(row, text="Agregar", command=self._add,
                  **BTN_PRIMARY).pack(side="right", padx=4)
        tk.Button(self, text="Eliminar seleccionada", command=self._delete,
                  **BTN_DANGER).pack(pady=(0, 12))

    def _load(self):
        self.listbox.delete(0, "end")
        self._cats = inventory.list_categories()
        for c in self._cats:
            self.listbox.insert("end", c["name"])

    def _add(self):
        name = self.new_var.get().strip()
        if name:
            inventory.add_category(name)
            self.new_var.set("")
            self._load()

    def _delete(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        cat = self._cats[sel[0]]
        if messagebox.askyesno("Confirmar",
                               f"¿Eliminar categoría '{cat['name']}'?", parent=self):
            inventory.delete_category(cat["id"])
            self._load()
