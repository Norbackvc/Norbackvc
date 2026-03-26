"""
Reports view frame.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

try:
    from tkcalendar import DateEntry
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False

from .. import auth
from .. import reports
from ..receipt import build_receipt
from ..pdf_generator import generate_pdf_receipt
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
        self.date_var = tk.StringVar(value=date.today().isoformat())
        
        # Use DateEntry if available, otherwise use Entry
        if HAS_CALENDAR:
            self.date_entry = DateEntry(
                toolbar,
                textvariable=self.date_var,
                font=FONT_SMALL,
                background=INPUT_BG,
                foreground=TEXT,
                fieldbackground=INPUT_BG,
                headersformatfunction=lambda x: x.strftime('%B %Y').upper(),
                relief="flat",
                bd=4,
                width=12,
            )
        else:
            self.date_entry = tk.Entry(
                toolbar,
                textvariable=self.date_var,
                font=FONT_SMALL,
                bg=INPUT_BG,
                fg=TEXT,
                insertbackground=TEXT,
                relief="flat",
                bd=4,
                width=12,
            )
        
        self.today_btn = tk.Button(
            toolbar,
            text="Hoy",
            command=self._set_today,
            **BTN_NEUTRAL,
        )
        for text, val in [("Hoy", "today"), ("Semana", "week"),
                           ("Mes", "month"), ("Año", "year"), ("Por fecha", "date")]:
            tk.Radiobutton(toolbar, text=text, variable=self.period_var,
                           value=val, command=self._on_period_change,
                           bg=PANEL_BG, fg=TEXT, selectcolor=ACCENT,
                           activebackground=PANEL_BG, font=FONT_SMALL
                           ).pack(side="right", padx=2)

        # Bind Enter key for manual date entry (if not using calendar widget)
        if not HAS_CALENDAR:
            self.date_entry.bind("<Return>", lambda _e: self.refresh())
        else:
            self.date_entry.bind("<<Change>>", lambda _e: self.refresh())

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

        self._on_period_change()

    def _make_list_frame(self, parent, title):
        f = tk.Frame(parent, bg=DARK_BG)
        return f

    def refresh(self):
        period = self.period_var.get()
        selected_date = self.date_var.get().strip()

        if period == "date" and not self._is_valid_date(selected_date):
            messagebox.showwarning("Fecha inválida", "Usa formato YYYY-MM-DD.", parent=self)
            return

        # Summary cards
        for w in self.cards_frame.winfo_children():
            w.destroy()
        summary = reports.sales_summary(period, selected_date=selected_date)
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
        self._rebuild_top_table(period, selected_date)
        self._rebuild_inv_table()

    def _on_period_change(self):
        show_date = self.period_var.get() == "date"
        if show_date:
            self.today_btn.pack(side="right", padx=(2, 2))
            self.date_entry.pack(side="right", padx=(2, 10))
        else:
            self.today_btn.pack_forget()
            self.date_entry.pack_forget()
        self.refresh()

    def _set_today(self):
        self.date_var.set(date.today().isoformat())
        self.refresh()

    def _is_valid_date(self, value: str) -> bool:
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False

    def _rebuild_sales_table(self, period):
        for w in self.sales_frame.winfo_children():
            w.destroy()

        actions = tk.Frame(self.sales_frame, bg=DARK_BG)
        actions.pack(fill="x", padx=PAD, pady=(4, 2))

        cols = ("Folio", "Fecha", "Cliente", "Método", "Total", "Estado")
        tree, _ = self._make_tree(self.sales_frame, cols, (90, 140, 140, 80, 80, 80))
        rows = reports.recent_sales(50)
        for r in rows:
            tree.insert("", "end", values=(
                r["folio"], r["created_at"][:16],
                r.get("customer_name") or "General",
                r["payment_method"], f"${r['total']:.2f}", r["status"]))
        tree.bind("<Double-1>", lambda e: self._open_selected_receipt(tree))
        tree.pack(fill="both", expand=True)

        if auth.can("delete_receipts"):
            tk.Button(
                actions,
                text="🗑 Eliminar boleta seleccionada",
                command=lambda: self._delete_selected_sale(tree),
                **BTN_DANGER,
            ).pack(side="left", padx=(0, 6))
        if auth.can("delete_all_receipts"):
            tk.Button(
                actions,
                text="⚠ Eliminar TODAS las boletas",
                command=self._delete_all_sales,
                **BTN_DANGER,
            ).pack(side="left")

    def _delete_selected_sale(self, tree):
        if not auth.can("delete_receipts"):
            messagebox.showwarning("Sin permiso", "No tienes permiso para eliminar boletas.", parent=self)
            return
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Eliminar boleta", "Selecciona una boleta primero.", parent=self)
            return
        vals = tree.item(sel[0], "values")
        if not vals:
            return
        folio = vals[0]
        ok = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar la boleta {folio}?\n\nEsta acción no se puede deshacer.",
            parent=self,
        )
        if not ok:
            return
        try:
            deleted = reports.delete_sale_by_folio(folio)
            if deleted:
                messagebox.showinfo("Boleta eliminada", f"Se eliminó la boleta {folio}.", parent=self)
            else:
                messagebox.showwarning("No encontrada", "La boleta ya no existe.", parent=self)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar la boleta.\n\n{e}", parent=self)

    def _delete_all_sales(self):
        if not auth.can("delete_all_receipts"):
            messagebox.showwarning("Sin permiso", "No tienes permiso para eliminar todas las boletas.", parent=self)
            return
        ok = messagebox.askyesno(
            "Confirmar eliminación total",
            "¿Eliminar TODAS las boletas?\n\nEsta acción no se puede deshacer.",
            parent=self,
        )
        if not ok:
            return
        ok2 = messagebox.askyesno(
            "Confirmación final",
            "Esta acción borrará todas las ventas e items de venta.\n\n¿Deseas continuar?",
            parent=self,
        )
        if not ok2:
            return
        try:
            count = reports.delete_all_sales()
            messagebox.showinfo("Boletas eliminadas", f"Se eliminaron {count} boletas.", parent=self)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron eliminar las boletas.\n\n{e}", parent=self)

    def _open_selected_receipt(self, tree):
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0], "values")
        if not vals:
            return
        folio = vals[0]
        sale = reports.get_sale_by_folio(folio)
        if not sale:
            messagebox.showerror("Boleta", "No se encontró la venta seleccionada.", parent=self)
            return
        receipt_text = build_receipt(sale)

        # Reuse receipt windows from main_window to keep UX consistent.
        from .main_window import ReceiptWindow, ReceiptPDFWindow
        try:
            pdf_path = generate_pdf_receipt(sale)
            ReceiptPDFWindow(self.winfo_toplevel(), receipt_text, pdf_path)
        except Exception:
            ReceiptWindow(self.winfo_toplevel(), receipt_text)

    def _rebuild_top_table(self, period, selected_date=None):
        for w in self.top_frame.winfo_children():
            w.destroy()
        cols = ("Producto", "Cant. vendida", "Ingresos")
        tree, _ = self._make_tree(self.top_frame, cols, (240, 120, 120))
        for r in reports.top_products(20, period, selected_date=selected_date):
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
