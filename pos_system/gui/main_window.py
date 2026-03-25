"""
Main POS application window with tabbed interface.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from .. import auth, inventory as inv, sales as sales_mod
from ..sales import Cart
from ..receipt import build_receipt
from ..database import get_setting
from .styles import *
from .products import ProductsFrame
from .customers import CustomersFrame
from .reports_view import ReportsFrame


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        user = auth.current_user()
        self.title(f"Punto de Venta  ·  {get_setting('store_name')}  ·  {user.full_name}")
        self.configure(bg=DARK_BG)
        self._set_geometry(1200, 750)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.cart = Cart()
        self._build()
        self._refresh_low_stock_badge()

    def _set_geometry(self, w, h):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = (sw - w) // 2, (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Top header bar ────────────────────────────────────────────────────
        header = tk.Frame(self, bg=PANEL_BG, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)

        store_name = get_setting("store_name", "Mi Tienda")
        tk.Label(header, text=f"🛒  {store_name}", font=FONT_H1,
                 bg=PANEL_BG, fg=TEXT).pack(side="left", padx=PAD)

        user = auth.current_user()
        tk.Label(header, text=f"👤 {user.full_name} [{user.role}]",
                 font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(side="right", padx=PAD)
        tk.Button(header, text="Cerrar sesión", command=self._logout,
                  **BTN_NEUTRAL).pack(side="right", padx=4)

        # ── Notebook tabs ─────────────────────────────────────────────────────
        style = ttk.Style()
        style.configure("POS.TNotebook", background=DARK_BG, borderwidth=0)
        style.configure("POS.TNotebook.Tab", background=CARD_BG, foreground=TEXT_DIM,
                        padding=(14, 6), font=FONT_BODY)
        style.map("POS.TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", WHITE)])

        self.nb = ttk.Notebook(self, style="POS.TNotebook")
        self.nb.pack(fill="both", expand=True)

        # Tab 1: POS (sell)
        pos_tab = tk.Frame(self.nb, bg=DARK_BG)
        self.nb.add(pos_tab, text="  🛍 Vender  ")
        self._build_pos_tab(pos_tab)

        # Tab 2: Products
        self.prod_frame = ProductsFrame(self.nb)
        self.nb.add(self.prod_frame, text="  📦 Productos  ")

        # Tab 3: Customers
        self.cust_frame = CustomersFrame(self.nb)
        self.nb.add(self.cust_frame, text="  👥 Clientes  ")

        # Tab 4: Reports
        self.rep_frame = ReportsFrame(self.nb)
        self.nb.add(self.rep_frame, text="  📊 Reportes  ")

        # Tab 5: Settings (admin only)
        if auth.is_admin():
            self.settings_frame = SettingsFrame(self.nb)
            self.nb.add(self.settings_frame, text="  ⚙ Configuración  ")

        # Refresh sub-frames on tab change
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        tab = self.nb.index(self.nb.select())
        if tab == 1:
            self.prod_frame.refresh()
        elif tab == 2:
            self.cust_frame.refresh()
        elif tab == 3:
            self.rep_frame.refresh()

    # ── POS Tab ───────────────────────────────────────────────────────────────

    def _build_pos_tab(self, parent):
        # Left panel: product search + cart
        left = tk.Frame(parent, bg=DARK_BG)
        left.pack(side="left", fill="both", expand=True, padx=(PAD, 4), pady=PAD)

        # Search row
        search_row = tk.Frame(left, bg=DARK_BG)
        search_row.pack(fill="x", pady=(0, 6))
        tk.Label(search_row, text="Buscar / Código:", font=FONT_BODY,
                 bg=DARK_BG, fg=TEXT_DIM).pack(side="left")
        self.pos_search_var = tk.StringVar()
        self.pos_search_entry = tk.Entry(
            search_row, textvariable=self.pos_search_var, font=FONT_BODY,
            bg=INPUT_BG, fg=TEXT, insertbackground=TEXT, relief="flat", bd=6, width=28)
        self.pos_search_entry.pack(side="left", padx=6)
        self.pos_search_entry.bind("<Return>", self._on_search_enter)
        tk.Button(search_row, text="🔍", command=self._open_product_picker,
                  **BTN_NEUTRAL).pack(side="left")

        # Customer row
        cust_row = tk.Frame(left, bg=DARK_BG)
        cust_row.pack(fill="x", pady=(0, 6))
        tk.Label(cust_row, text="Cliente:", font=FONT_BODY,
                 bg=DARK_BG, fg=TEXT_DIM).pack(side="left")
        self.customer_label = tk.Label(cust_row, text="Público General",
                                        font=FONT_BODY, bg=DARK_BG, fg=TEXT)
        self.customer_label.pack(side="left", padx=6)
        tk.Button(cust_row, text="Cambiar", command=self._select_customer,
                  **BTN_NEUTRAL).pack(side="left")
        tk.Button(cust_row, text="Quitar", command=self._clear_customer,
                  **BTN_NEUTRAL).pack(side="left", padx=4)

        # Cart table
        cols = ("Artículo", "Precio", "Cant.", "Dto%", "Importe")
        style = ttk.Style()
        style.configure("Cart.Treeview",
                        background=CARD_BG, foreground=TEXT,
                        fieldbackground=CARD_BG, rowheight=28, font=FONT_BODY)
        style.configure("Cart.Treeview.Heading",
                        background=PANEL_BG, foreground=TEXT_DIM, font=FONT_SMALL)
        style.map("Cart.Treeview", background=[("selected", ACCENT)])

        cart_frame = tk.Frame(left, bg=DARK_BG)
        cart_frame.pack(fill="both", expand=True)
        self.cart_tree = ttk.Treeview(cart_frame, columns=cols,
                                       show="headings", style="Cart.Treeview")
        widths = (240, 80, 60, 50, 80)
        for col, w in zip(cols, widths):
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=w, anchor="w" if w > 80 else "center")
        vsb = ttk.Scrollbar(cart_frame, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=vsb.set)
        self.cart_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Cart action row
        cart_actions = tk.Frame(left, bg=DARK_BG, pady=4)
        cart_actions.pack(fill="x")
        tk.Button(cart_actions, text="✏ Cambiar Cant.",
                  command=self._change_qty, **BTN_NEUTRAL).pack(side="left", padx=2)
        tk.Button(cart_actions, text="% Descuento línea",
                  command=self._line_discount, **BTN_NEUTRAL).pack(side="left", padx=2)
        tk.Button(cart_actions, text="🗑 Quitar",
                  command=self._remove_item, **BTN_DANGER).pack(side="left", padx=2)
        tk.Button(cart_actions, text="🗑 Vaciar carrito",
                  command=self._clear_cart, **BTN_DANGER).pack(side="right", padx=2)

        # ── Right panel: totals + payment ─────────────────────────────────────
        right = tk.Frame(parent, bg=PANEL_BG, width=280)
        right.pack(side="right", fill="y", padx=(4, PAD), pady=PAD)
        right.pack_propagate(False)

        tk.Label(right, text="Resumen", font=FONT_H2, bg=PANEL_BG, fg=TEXT
                 ).pack(pady=(16, 8))

        # Totals display
        totals_frame = tk.Frame(right, bg=PANEL_BG)
        totals_frame.pack(fill="x", padx=12)

        self.lbl_subtotal  = self._total_row(totals_frame, "Subtotal:")
        self.lbl_discount  = self._total_row(totals_frame, "Descuento:")
        self.lbl_tax       = self._total_row(totals_frame, f"IVA ({get_setting('tax_rate')}%):")
        sep = tk.Frame(right, bg=BORDER, height=1)
        sep.pack(fill="x", padx=12, pady=6)
        self.lbl_total     = self._total_row(right, "TOTAL:", font=FONT_H1, fg=SUCCESS)

        # Global discount
        disco_frame = tk.Frame(right, bg=PANEL_BG, padx=12, pady=4)
        disco_frame.pack(fill="x")
        tk.Label(disco_frame, text="Descuento global (%):", font=FONT_SMALL,
                 bg=PANEL_BG, fg=TEXT_DIM).pack(side="left")
        self.discount_var = tk.StringVar(value="0")
        self.discount_var.trace_add("write", self._on_discount_change)
        tk.Entry(disco_frame, textvariable=self.discount_var, width=5, font=FONT_BODY,
                 bg=INPUT_BG, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=4).pack(side="right")

        # Payment method
        pay_frame = tk.Frame(right, bg=PANEL_BG, padx=12, pady=6)
        pay_frame.pack(fill="x")
        tk.Label(pay_frame, text="Forma de pago:", font=FONT_SMALL,
                 bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w")
        self.pay_var = tk.StringVar(value="cash")
        for text, val in [("Efectivo", "cash"), ("Tarjeta", "card"),
                           ("Transferencia", "transfer"), ("Otro", "other")]:
            tk.Radiobutton(pay_frame, text=text, variable=self.pay_var, value=val,
                           bg=PANEL_BG, fg=TEXT, selectcolor=ACCENT,
                           activebackground=PANEL_BG, font=FONT_SMALL).pack(
                anchor="w", pady=1)

        # Amount paid
        paid_frame = tk.Frame(right, bg=PANEL_BG, padx=12, pady=4)
        paid_frame.pack(fill="x")
        tk.Label(paid_frame, text="Monto recibido:", font=FONT_SMALL,
                 bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w")
        self.paid_var = tk.StringVar()
        self.paid_var.trace_add("write", self._on_paid_change)
        tk.Entry(paid_frame, textvariable=self.paid_var, font=FONT_H2,
                 bg=INPUT_BG, fg=SUCCESS, insertbackground=SUCCESS,
                 relief="flat", bd=6).pack(fill="x", pady=4)

        self.lbl_change = self._total_row(right, "Cambio:", font=FONT_H2, fg=WARNING,
                                           parent=right)

        # Process button
        tk.Button(right, text="✅  COBRAR", command=self._process_sale,
                  bg=SUCCESS, fg=WHITE, font=("Segoe UI", 14, "bold"),
                  relief="flat", cursor="hand2", pady=14,
                  activebackground="#27ae60", activeforeground=WHITE,
                  ).pack(fill="x", padx=12, pady=(12, 4))

        tk.Button(right, text="⚠ Cancelar venta", command=self._clear_cart,
                  **BTN_DANGER).pack(fill="x", padx=12, pady=4)

        # Low stock badge
        self.low_stock_lbl = tk.Label(right, text="", font=FONT_SMALL,
                                       bg=PANEL_BG, fg=WARNING, cursor="hand2")
        self.low_stock_lbl.pack(pady=4)
        self.low_stock_lbl.bind("<Button-1>", lambda e: self.nb.select(1))

    # ── Total row helper ──────────────────────────────────────────────────────

    def _total_row(self, parent=None, label="", font=FONT_BODY, fg=TEXT):
        if parent is None:
            parent = self
        row = tk.Frame(parent, bg=PANEL_BG)
        row.pack(fill="x", padx=12, pady=1)
        tk.Label(row, text=label, font=font, bg=PANEL_BG, fg=TEXT_DIM,
                 anchor="w").pack(side="left")
        lbl = tk.Label(row, text="$0.00", font=font, bg=PANEL_BG, fg=fg)
        lbl.pack(side="right")
        return lbl

    # ── Cart logic ────────────────────────────────────────────────────────────

    def _on_search_enter(self, event=None):
        query = self.pos_search_var.get().strip()
        if not query:
            return
        # Try barcode first
        prod = inv.get_product_by_barcode(query)
        if prod:
            self.cart.add_item(prod["id"], prod["name"], prod["price"])
            self._refresh_cart()
            self.pos_search_var.set("")
        else:
            self._open_product_picker(query=query)

    def _open_product_picker(self, event=None, query=""):
        ProductPickerDialog(self, query=query, on_select=self._add_product_to_cart
                            ).grab_set()

    def _add_product_to_cart(self, prod, qty=1, discount=0):
        self.cart.add_item(prod["id"], prod["name"], prod["price"], qty, discount)
        self._refresh_cart()
        self.pos_search_var.set("")
        self.pos_search_entry.focus()

    def _refresh_cart(self):
        sym = get_setting("currency_symbol", "$")
        self.cart_tree.delete(*self.cart_tree.get_children())
        for i, item in enumerate(self.cart.items):
            self.cart_tree.insert("", "end", iid=str(i),
                                   values=(item.name,
                                           f"{sym}{item.unit_price:.2f}",
                                           item.quantity,
                                           f"{item.discount:.0f}%",
                                           f"{sym}{item.subtotal:.2f}"))
        self._update_totals()

    def _update_totals(self):
        sym = get_setting("currency_symbol", "$")
        self.lbl_subtotal.config(text=f"{sym}{self.cart.subtotal:.2f}")
        self.lbl_discount.config(text=f"-{sym}{self.cart.discount_amount:.2f}")
        self.lbl_tax.config(text=f"{sym}{self.cart.tax_amount:.2f}")
        self.lbl_total.config(text=f"{sym}{self.cart.total:.2f}")
        self._on_paid_change()

    def _on_discount_change(self, *_):
        try:
            self.cart.discount = float(self.discount_var.get() or 0)
        except ValueError:
            self.cart.discount = 0
        self._update_totals()

    def _on_paid_change(self, *_):
        sym = get_setting("currency_symbol", "$")
        try:
            self.cart.amount_paid = float(self.paid_var.get() or 0)
        except ValueError:
            self.cart.amount_paid = 0
        self.lbl_change.config(text=f"{sym}{self.cart.change_due:.2f}")

    def _selected_cart_index(self):
        sel = self.cart_tree.selection()
        return int(sel[0]) if sel else None

    def _change_qty(self):
        idx = self._selected_cart_index()
        if idx is None:
            return
        item = self.cart.items[idx]
        qty = simpledialog.askfloat(
            "Cantidad", f"Nueva cantidad para '{item.name}':",
            initialvalue=item.quantity, minvalue=0.01, parent=self)
        if qty is not None:
            self.cart.update_quantity(idx, qty)
            self._refresh_cart()

    def _line_discount(self):
        idx = self._selected_cart_index()
        if idx is None:
            return
        item = self.cart.items[idx]
        disc = simpledialog.askfloat(
            "Descuento", f"Descuento % para '{item.name}' (0-100):",
            initialvalue=item.discount, minvalue=0, maxvalue=100, parent=self)
        if disc is not None:
            item.discount = disc
            self._refresh_cart()

    def _remove_item(self):
        idx = self._selected_cart_index()
        if idx is not None:
            self.cart.remove_item(idx)
            self._refresh_cart()

    def _clear_cart(self):
        if self.cart.is_empty() or messagebox.askyesno(
                "Confirmar", "¿Vaciar el carrito?", parent=self):
            self.cart.clear()
            self.discount_var.set("0")
            self.paid_var.set("")
            self.customer_label.config(text="Público General")
            self._refresh_cart()

    # ── Customer selection ────────────────────────────────────────────────────

    def _select_customer(self):
        CustomerPickerDialog(self, on_select=self._set_customer).grab_set()

    def _set_customer(self, cust):
        self.cart.customer_id = cust["id"]
        self.customer_label.config(text=cust["name"])

    def _clear_customer(self):
        self.cart.customer_id = None
        self.customer_label.config(text="Público General")

    # ── Sale processing ───────────────────────────────────────────────────────

    def _process_sale(self):
        if self.cart.is_empty():
            messagebox.showwarning("Carrito vacío",
                                   "Agrega productos al carrito antes de cobrar.", parent=self)
            return
        self.cart.payment_method = self.pay_var.get()
        try:
            paid = float(self.paid_var.get() or 0)
        except ValueError:
            paid = 0
        self.cart.amount_paid = paid

        if self.cart.amount_paid < self.cart.total:
            messagebox.showerror("Monto insuficiente",
                                  f"Monto recibido (${paid:.2f}) es menor al total (${self.cart.total:.2f}).",
                                  parent=self)
            return

        user = auth.current_user()
        try:
            sale_id = sales_mod.process_sale(self.cart, user.id)
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)
            return

        sale = sales_mod.get_sale(sale_id)
        receipt_text = build_receipt(sale)
        ReceiptWindow(self, receipt_text)

        self._clear_cart()
        self._refresh_low_stock_badge()

    # ── Low-stock badge ───────────────────────────────────────────────────────

    def _refresh_low_stock_badge(self):
        low = inv.low_stock_products()
        if low:
            self.low_stock_lbl.config(
                text=f"⚠ {len(low)} producto(s) con stock bajo")
        else:
            self.low_stock_lbl.config(text="")

    # ── Logout / close ────────────────────────────────────────────────────────

    def _logout(self):
        auth.logout()
        self.destroy()

    def _on_close(self):
        if messagebox.askokcancel("Salir", "¿Deseas cerrar el sistema?", parent=self):
            self.destroy()


# ── Product Picker Dialog ──────────────────────────────────────────────────────

class ProductPickerDialog(tk.Toplevel):
    def __init__(self, parent, query="", on_select=None):
        super().__init__(parent)
        self.title("Seleccionar Producto")
        self.configure(bg=PANEL_BG)
        self._on_select = on_select
        self._build(query)
        self.geometry("560x480")

    def _build(self, initial_query=""):
        tk.Label(self, text="Buscar producto", font=FONT_H2,
                 bg=PANEL_BG, fg=TEXT).pack(pady=(10, 6))

        row = tk.Frame(self, bg=PANEL_BG)
        row.pack(fill="x", padx=12)
        self.sv = tk.StringVar(value=initial_query)
        self.sv.trace_add("write", lambda *_: self._search())
        tk.Entry(row, textvariable=self.sv, font=FONT_BODY, bg=INPUT_BG,
                 fg=TEXT, insertbackground=TEXT, relief="flat", bd=6).pack(fill="x")

        cols = ("ID", "Nombre", "Código", "Precio", "Stock")
        style = ttk.Style()
        style.configure("Picker.Treeview",
                        background=CARD_BG, foreground=TEXT,
                        fieldbackground=CARD_BG, rowheight=26, font=FONT_BODY)
        style.map("Picker.Treeview", background=[("selected", ACCENT)])
        style.configure("Picker.Treeview.Heading",
                        background=PANEL_BG, foreground=TEXT_DIM, font=FONT_SMALL)

        frame = tk.Frame(self, bg=PANEL_BG)
        frame.pack(fill="both", expand=True, padx=12, pady=6)
        self.tree = ttk.Treeview(frame, columns=cols, show="headings",
                                  style="Picker.Treeview")
        for col, w in zip(cols, (50, 260, 100, 70, 60)):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="w" if w > 80 else "center")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda e: self._confirm())

        qty_row = tk.Frame(self, bg=PANEL_BG)
        qty_row.pack(fill="x", padx=12, pady=4)
        tk.Label(qty_row, text="Cantidad:", font=FONT_BODY,
                 bg=PANEL_BG, fg=TEXT_DIM).pack(side="left")
        self.qty_var = tk.StringVar(value="1")
        tk.Entry(qty_row, textvariable=self.qty_var, width=6, font=FONT_BODY,
                 bg=INPUT_BG, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=4).pack(side="left", padx=4)

        tk.Button(self, text="Agregar al carrito", command=self._confirm,
                  **BTN_PRIMARY).pack(padx=12, pady=6, fill="x")

        self._search()

    def _search(self):
        results = inv.list_products(search=self.sv.get())
        self.tree.delete(*self.tree.get_children())
        for p in results:
            self.tree.insert("", "end", iid=str(p["id"]),
                             values=(p["id"], p["name"],
                                     p["barcode"] or "",
                                     f"${p['price']:.2f}",
                                     p["stock"]))

    def _confirm(self):
        sel = self.tree.selection()
        if not sel:
            return
        pid = int(sel[0])
        prod = inv.get_product(pid)
        if prod:
            try:
                qty = float(self.qty_var.get() or 1)
            except ValueError:
                qty = 1
            if self._on_select:
                self._on_select(prod, qty)
        self.destroy()


# ── Customer Picker Dialog ────────────────────────────────────────────────────

class CustomerPickerDialog(tk.Toplevel):
    def __init__(self, parent, on_select=None):
        super().__init__(parent)
        self.title("Seleccionar Cliente")
        self.configure(bg=PANEL_BG)
        self._on_select = on_select
        self._build()
        self.geometry("460x400")

    def _build(self):
        tk.Label(self, text="Buscar cliente", font=FONT_H2,
                 bg=PANEL_BG, fg=TEXT).pack(pady=(10, 6))
        row = tk.Frame(self, bg=PANEL_BG)
        row.pack(fill="x", padx=12)
        self.sv = tk.StringVar()
        self.sv.trace_add("write", lambda *_: self._search())
        tk.Entry(row, textvariable=self.sv, font=FONT_BODY, bg=INPUT_BG,
                 fg=TEXT, insertbackground=TEXT, relief="flat", bd=6).pack(fill="x")

        cols = ("ID", "Nombre", "Teléfono", "Email")
        style = ttk.Style()
        style.configure("Picker.Treeview",
                        background=CARD_BG, foreground=TEXT,
                        fieldbackground=CARD_BG, rowheight=26, font=FONT_BODY)
        style.map("Picker.Treeview", background=[("selected", ACCENT)])

        frame = tk.Frame(self, bg=PANEL_BG)
        frame.pack(fill="both", expand=True, padx=12, pady=6)
        self.tree = ttk.Treeview(frame, columns=cols, show="headings",
                                  style="Picker.Treeview")
        for col, w in zip(cols, (50, 200, 100, 150)):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda e: self._confirm())

        tk.Button(self, text="Seleccionar", command=self._confirm,
                  **BTN_PRIMARY).pack(padx=12, pady=8, fill="x")
        self._search()

    def _search(self):
        customers = sales_mod.list_customers(self.sv.get())
        self.tree.delete(*self.tree.get_children())
        for c in customers:
            self.tree.insert("", "end", iid=str(c["id"]),
                             values=(c["id"], c["name"], c["phone"], c["email"]))

    def _confirm(self):
        sel = self.tree.selection()
        if not sel:
            return
        cid = int(sel[0])
        cust = sales_mod.get_customer(cid)
        if cust and self._on_select:
            self._on_select(cust)
        self.destroy()


# ── Receipt Window ────────────────────────────────────────────────────────────

class ReceiptWindow(tk.Toplevel):
    def __init__(self, parent, receipt_text: str):
        super().__init__(parent)
        self.title("Recibo de Venta")
        self.configure(bg=DARK_BG)
        self.geometry("440x600")

        tk.Label(self, text="Recibo", font=FONT_H1,
                 bg=DARK_BG, fg=TEXT).pack(pady=(10, 4))

        txt_frame = tk.Frame(self, bg=CARD_BG, padx=8, pady=8)
        txt_frame.pack(fill="both", expand=True, padx=12, pady=4)

        self.txt = tk.Text(txt_frame, font=FONT_MONO, bg=CARD_BG, fg=TEXT,
                            relief="flat", wrap="none", state="normal")
        self.txt.insert("1.0", receipt_text)
        self.txt.config(state="disabled")
        vsb = ttk.Scrollbar(txt_frame, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=vsb.set)
        self.txt.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        row = tk.Frame(self, bg=DARK_BG)
        row.pack(fill="x", padx=12, pady=8)
        tk.Button(row, text="📋 Copiar", command=self._copy,
                  **BTN_NEUTRAL).pack(side="left")
        tk.Button(row, text="Cerrar", command=self.destroy,
                  **BTN_PRIMARY).pack(side="right")

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.txt.get("1.0", "end"))


# ── Settings Frame ─────────────────────────────────────────────────────────────

class SettingsFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=DARK_BG)
        self._build()

    def _build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=PAD, pady=PAD)

        store_tab = tk.Frame(nb, bg=DARK_BG)
        users_tab = tk.Frame(nb, bg=DARK_BG)
        nb.add(store_tab, text="  🏪 Tienda  ")
        nb.add(users_tab, text="  👤 Usuarios  ")

        self._build_store_settings(store_tab)
        self._build_users_tab(users_tab)

    def _build_store_settings(self, parent):
        from ..database import get_setting, set_setting
        tk.Label(parent, text="Configuración de la Tienda", font=FONT_H2,
                 bg=DARK_BG, fg=TEXT).pack(pady=(16, 8))

        fields = [
            ("Nombre de la tienda", "store_name"),
            ("Dirección", "store_address"),
            ("Teléfono", "store_phone"),
            ("RFC", "store_rfc"),
            ("Tasa IVA (%)", "tax_rate"),
            ("Moneda", "currency"),
            ("Símbolo monetario", "currency_symbol"),
            ("Pie de recibo", "receipt_footer"),
        ]
        form = tk.Frame(parent, bg=DARK_BG)
        form.pack(padx=40, pady=8)

        self._settings_vars = {}
        for label, key in fields:
            row = tk.Frame(form, bg=DARK_BG)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, font=FONT_BODY, bg=DARK_BG,
                     fg=TEXT_DIM, width=22, anchor="w").pack(side="left")
            var = tk.StringVar(value=get_setting(key))
            tk.Entry(row, textvariable=var, font=FONT_BODY, bg=INPUT_BG,
                     fg=TEXT, insertbackground=TEXT, relief="flat", bd=4,
                     width=30).pack(side="left")
            self._settings_vars[key] = var

        def save():
            for key, var in self._settings_vars.items():
                set_setting(key, var.get().strip())
            messagebox.showinfo("Guardado", "Configuración guardada correctamente.")

        tk.Button(parent, text="💾 Guardar configuración", command=save,
                  **BTN_SUCCESS).pack(pady=12)

    def _build_users_tab(self, parent):
        from .. import auth as auth_mod
        tk.Label(parent, text="Gestión de Usuarios", font=FONT_H2,
                 bg=DARK_BG, fg=TEXT).pack(pady=(16, 8))

        toolbar = tk.Frame(parent, bg=DARK_BG)
        toolbar.pack(fill="x", padx=PAD)
        tk.Button(toolbar, text="+ Nuevo usuario",
                  command=lambda: self._new_user(tree),
                  **BTN_PRIMARY).pack(side="left", padx=4)

        cols = ("ID", "Usuario", "Nombre", "Rol", "Activo")
        frame = tk.Frame(parent, bg=DARK_BG)
        frame.pack(fill="both", expand=True, padx=PAD, pady=8)
        style = ttk.Style()
        style.configure("POS.Treeview",
                        background=CARD_BG, foreground=TEXT,
                        fieldbackground=CARD_BG, rowheight=26, font=FONT_BODY)
        style.map("POS.Treeview", background=[("selected", ACCENT)])

        tree = ttk.Treeview(frame, columns=cols, show="headings",
                             style="POS.Treeview")
        for col, w in zip(cols, (40, 120, 200, 80, 60)):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center" if w < 120 else "w")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def load():
            tree.delete(*tree.get_children())
            for u in auth_mod.list_users():
                tree.insert("", "end", iid=str(u["id"]),
                            values=(u["id"], u["username"], u["full_name"],
                                    u["role"], "Sí" if u["active"] else "No"))

        def change_pw():
            sel = tree.selection()
            if not sel:
                return
            uid = int(sel[0])
            pw = simpledialog.askstring("Contraseña",
                                         "Nueva contraseña:", show="*", parent=parent)
            if pw:
                auth_mod.change_password(uid, pw)
                messagebox.showinfo("OK", "Contraseña actualizada.")

        bot = tk.Frame(parent, bg=DARK_BG, padx=PAD)
        bot.pack(fill="x")
        tk.Button(bot, text="🔑 Cambiar contraseña",
                  command=change_pw, **BTN_NEUTRAL).pack(side="left", padx=4)
        tk.Button(bot, text="🔄 Recargar", command=load,
                  **BTN_NEUTRAL).pack(side="left", padx=4)
        load()

    def _new_user(self, tree):
        from .. import auth as auth_mod
        win = tk.Toplevel(self)
        win.title("Nuevo Usuario")
        win.configure(bg=PANEL_BG)
        win.resizable(False, False)
        win.geometry("360x340")
        tk.Label(win, text="Crear Usuario", font=FONT_H2,
                 bg=PANEL_BG, fg=TEXT).pack(pady=(14, 8))
        form = tk.Frame(win, bg=PANEL_BG)
        form.pack(padx=24, fill="x")
        vars_ = {}
        for label, key, show in [
            ("Usuario*", "username", ""), ("Nombre completo*", "full_name", ""),
            ("Contraseña*", "password", "•"), ("Confirmar contraseña", "confirm", "•"),
        ]:
            r = tk.Frame(form, bg=PANEL_BG)
            r.pack(fill="x", pady=4)
            tk.Label(r, text=label, font=FONT_SMALL, bg=PANEL_BG,
                     fg=TEXT_DIM, width=20, anchor="w").pack(side="left")
            v = tk.StringVar()
            tk.Entry(r, textvariable=v, show=show, font=FONT_BODY, bg=INPUT_BG,
                     fg=TEXT, insertbackground=TEXT, relief="flat", bd=4).pack(
                side="left", fill="x", expand=True)
            vars_[key] = v

        role_var = tk.StringVar(value="cashier")
        r = tk.Frame(form, bg=PANEL_BG)
        r.pack(fill="x", pady=4)
        tk.Label(r, text="Rol", font=FONT_SMALL, bg=PANEL_BG,
                 fg=TEXT_DIM, width=20, anchor="w").pack(side="left")
        ttk.Combobox(r, textvariable=role_var, values=["cashier", "admin"],
                     state="readonly", width=14).pack(side="left")

        def save():
            u = vars_["username"].get().strip()
            n = vars_["full_name"].get().strip()
            p = vars_["password"].get()
            c = vars_["confirm"].get()
            if not u or not n or not p:
                messagebox.showerror("Error", "Completa todos los campos.", parent=win)
                return
            if p != c:
                messagebox.showerror("Error", "Las contraseñas no coinciden.", parent=win)
                return
            try:
                auth_mod.create_user(u, p, role_var.get(), n)
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)

        tk.Button(win, text="Crear usuario", command=save,
                  **BTN_PRIMARY).pack(pady=12, padx=24, fill="x")
