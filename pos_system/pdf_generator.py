"""
PDF Receipt generator using reportlab.
Generates professional boletas (receipts) as PDFs.
"""
import os
from pathlib import Path
from typing import Dict
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
except ImportError:
    raise ImportError(
        "reportlab es requerido para generar PDFs. "
        "Instala con: pip install reportlab"
    )

from .database import get_setting


def _get_receipts_folder() -> Path:
    """Get or create receipts folder."""
    if getattr(__import__('sys'), 'frozen', False):
        # PyInstaller executable
        base_dir = Path(__import__('sys').executable).resolve().parent
    else:
        # Script mode
        base_dir = Path(__file__).resolve().parent
    
    receipts_dir = base_dir / "receipts"
    receipts_dir.mkdir(exist_ok=True)
    return receipts_dir


def generate_pdf_receipt(sale: Dict) -> str:
    """
    Generate a PDF receipt for a sale and save to receipts/ folder.
    Returns the path to the PDF file.
    """
    receipts_dir = _get_receipts_folder()
    filename = f"boleta_{sale['folio'].replace('/', '_')}.pdf"
    filepath = receipts_dir / filename
    
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#1a1a1a'),
        alignment=TA_CENTER,
    )
    
    # Build elements
    elements = []
    
    # Store header
    store_name = get_setting("store_name", "NORVATECH STORE")
    store_address = get_setting("store_address", "")
    store_phone = get_setting("store_phone", "")
    store_rfc = get_setting("store_rfc", "")
    
    elements.append(Paragraph(store_name, title_style))
    if store_address:
        elements.append(Paragraph(store_address, normal_style))
    if store_phone:
        elements.append(Paragraph(f"Tel: {store_phone}", normal_style))
    if store_rfc:
        elements.append(Paragraph(f"RUC: {store_rfc}", normal_style))
    
    elements.append(Spacer(1, 0.15 * inch))
    
    # Receipt info
    created_at = sale.get("created_at", "")
    if created_at:
        created_at_str = str(created_at)
    else:
        created_at_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    elements.append(Paragraph(f"<b>BOLETA DE VENTA</b>", title_style))
    elements.append(Paragraph(f"Folio: {sale['folio']}", normal_style))
    elements.append(Paragraph(f"Fecha: {created_at_str}", normal_style))
    
    # Items table
    sym = get_setting("currency_symbol", "$")
    
    items_data = [["Artículo", "Cant.", "P.U.", "Importe"]]
    for item in sale.get("items", []):
        name = item["product_name"][:35]
        qty = f"{item['quantity']:.0f}"
        pu = f"{sym}{item['unit_price']:.2f}"
        subtotal = f"{sym}{item['subtotal']:.2f}"
        items_data.append([name, qty, pu, subtotal])
        
        if item["discount"] > 0:
            items_data.append([
                f"  Descuento {item['discount']:.0f}%",
                "",
                "",
                f"-{sym}{item['subtotal'] * item['discount'] / 100:.2f}"
            ])
    
    items_table = Table(items_data, colWidths=[2.8*inch, 0.8*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a1a1a')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 0.1 * inch))
    
    # Totals
    totals_data = [
        ["Subtotal:", f"{sym}{sale['subtotal']:.2f}"],
    ]
    if sale["discount"] > 0:
        totals_data.append(["Descuento:", f"-{sym}{sale['discount']:.2f}"])
    
    tax_rate = get_setting("tax_rate", "16")
    totals_data.extend([
        [f"IVA ({tax_rate}%):", f"{sym}{sale['tax']:.2f}"],
        ["TOTAL:", f"{sym}{sale['total']:.2f}"],
    ])
    
    totals_table = Table(totals_data, colWidths=[4*inch, 1.6*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (1, -1), 9),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
    ]))
    
    elements.append(totals_table)
    elements.append(Spacer(1, 0.1 * inch))
    
    # Payment info
    payment_data = [
        ["Forma de pago:", sale["payment_method"].upper()],
        ["Monto recibido:", f"{sym}{sale['amount_paid']:.2f}"],
        ["Cambio:", f"{sym}{sale['change_due']:.2f}"],
    ]
    
    payment_table = Table(payment_data, colWidths=[4*inch, 1.6*inch])
    payment_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (1, -1), 8),
    ]))
    
    elements.append(payment_table)
    elements.append(Spacer(1, 0.15 * inch))
    
    # Footer
    footer = get_setting("receipt_footer", "¡Gracias por su compra!")
    elements.append(Paragraph(f"<i>{footer}</i>", normal_style))
    
    elements.append(Spacer(1, 0.05 * inch))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(f"Generado: {now}", normal_style))
    
    # Build PDF
    doc.build(elements)
    
    return str(filepath)
