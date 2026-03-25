"""
Reports view frame.
"""
import tkinter as tk
from tkinter import ttk
from .. import reports
from .styles import *


class ReportsFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=DARK_BG)
        self._build()
        self.refresh()

    def _build(self):
        toolbar = tk.Frame(self, bg=PANEL_BG, padx=PAD, pady=8)
        toolbar.pack(fill="x")
        tk.Label(toolbar, text="📊  Reportes", font=FONT_H1,
                 bg=PANEL_BG, fg=TEXT).pack(side="left")

        # Period selector
        tk.Label(toolbar, text="Período:", font=FONT_BODY,
                 bg=PANEL_BG, fg=TEXT_DIM).pack(side="right", padx=(0, 4))
        self.period_var = tk.StringVar(value="month")
        for text, val in [("Hoy", "today"), ("Semana", "week"),
                           ("Mes", "month"), ("Año", "year")]:
            tk.Radiobutton(toolbar, text=text, variable=self.period_var,
                           value=val, command=self.refresh,
                           bg=PANEL_BG, fg=TEXT, selectcolor=ACCENT,
                           activebackground=PANEL_BG, font=FONT_SMALL
                           ).pack(side="right", padx=2)

        # Summary cards row
        self.cards_frame = tk.Frame(self, bg=DARK_BG)
        self.cards_frame.pack(fill="x", padx=PAD, pady=8)

        # Notebook for sub-reports
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=PAD, pady=4)

        self.sales_frame  = self._make_list_frame(nb, "Ventas recientes")
        self.top_frame    = self._make_list_frame(nb, "Top productos")
        self.inv_frame    = self._make_list_frame(nb, "Inventario")
        nb.add(self.sales_frame,  text="Ventas recientes")
        nb.add(self.top_frame,    text="Productos más vendidos")
        nb.add(self.inv_frame,    text="Valor de inventario")

    def _make_list_frame(self, parent, title):
        f = tk.Frame(parent, bg=DARK_BG)
        return f

    def refresh(self):
        period = self.period_var.get()

        # Summary cards
        for w in self.cards_frame.winfo_children():
            w.destroy()
        summary = reports.sales_summary(period)
        sym = "$"
        cards = [
            ("Ventas", str(summary["count"]), ACCENT),
            ("Total", f"{sym}{summary['total']:,.2f}", SUCCESS),
            ("IVA",   f"{sym}{summary['tax']:,.2f}", ACCENT2),
            ("Descuentos", f"{sym}{summary['discount']:,.2f}", WARNING),
        ]
        for label, value, color in cards:
            card = tk.Frame(self.cards_frame, bg=CARD_BG, padx=20, pady=10)
            card.pack(side="left", padx=6, fill="y")
            tk.Label(card, text=label, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack()
            tk.Label(card, text=value, font=FONT_H1, bg=CARD_BG, fg=color).pack()

        # Inventory summary card
        inv = reports.inventory_value()
        for label, value, color in [
            ("Productos", str(inv["products"]), TEXT),
            ("Unidades", str(int(inv["units"])), TEXT),
            ("Valor costo", f"{sym}{inv['cost_value']:,.2f}", WARNING),
            ("Valor venta", f"{sym}{inv['sale_value']:,.2f}", SUCCESS),
        ]:
            card = tk.Frame(self.cards_frame, bg=CARD_BG, padx=20, pady=10)
            card.pack(side="right", padx=6, fill="y")
            tk.Label(card, text=label, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack()
            tk.Label(card, text=value, font=FONT_H1, bg=CARD_BG, fg=color).pack()

        # Recent sales table
        self._rebuild_sales_table(period)
        self._rebuild_top_table(period)
        self._rebuild_inv_table()

    def _rebuild_sales_table(self, period):
        for w in self.sales_frame.winfo_children():
            w.destroy()
        cols = ("Folio", "Fecha", "Cliente", "Método", "Total", "Estado")
        tree, _ = self._make_tree(self.sales_frame, cols, (90, 140, 140, 80, 80, 80))
        rows = reports.recent_sales(50)
        for r in rows:
            tree.insert("", "end", values=(
                r["folio"], r["created_at"][:16],
                r.get("customer_name") or "General",
                r["payment_method"], f"${r['total']:.2f}", r["status"]))
        tree.pack(fill="both", expand=True)

    def _rebuild_top_table(self, period):
        for w in self.top_frame.winfo_children():
            w.destroy()
        cols = ("Producto", "Cant. vendida", "Ingresos")
        tree, _ = self._make_tree(self.top_frame, cols, (240, 120, 120))
        for r in reports.top_products(20, period):
            tree.insert("", "end", values=(
                r["product_name"], f"{r['qty_sold']:.0f}", f"${r['revenue']:.2f}"))
        tree.pack(fill="both", expand=True)

    def _rebuild_inv_table(self):
        from .. import inventory
        for w in self.inv_frame.winfo_children():
            w.destroy()
        cols = ("Producto", "Stock", "Mín.", "Costo unit.", "Precio", "Valor stock")
        tree, _ = self._make_tree(self.inv_frame, cols, (200, 60, 60, 80, 80, 100))
        prods = inventory.list_products()
        for p in prods:
            tree.insert("", "end", values=(
                p["name"], p["stock"], p["min_stock"],
                f"${p['cost']:.2f}", f"${p['price']:.2f}",
                f"${p['stock'] * p['cost']:.2f}"))
        tree.pack(fill="both", expand=True)

    def _make_tree(self, parent, cols, widths):
        frame = tk.Frame(parent, bg=DARK_BG)
        frame.pack(fill="both", expand=True, padx=PAD, pady=4)

        style = ttk.Style()
        style.configure("POS.Treeview",
                        background=CARD_BG, foreground=TEXT,
                        fieldbackground=CARD_BG, rowheight=24, font=FONT_SMALL)
        style.configure("POS.Treeview.Heading",
                        background=PANEL_BG, foreground=TEXT_DIM, font=FONT_SMALL)
        style.map("POS.Treeview", background=[("selected", ACCENT)])

        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            style="POS.Treeview", selectmode="browse")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="w" if w > 80 else "center")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        return tree, frame
