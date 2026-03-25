# 🛒 Punto de Venta (POS) en Python

Sistema de Punto de Venta completo desarrollado en Python puro con interfaz gráfica (Tkinter) y base de datos SQLite — **sin dependencias externas**.

## Requisitos

- Python 3.8 o superior
- Tkinter (incluido con Python; en Linux: `sudo apt install python3-tk`)

## Instalación y ejecución

```bash
git clone https://github.com/Norbackvc/Norbackvc.git
cd Norbackvc
python pos_system/main.py
```

> La base de datos se crea automáticamente en la primera ejecución.  
> **Usuario por defecto:** `admin` | **Contraseña:** `admin123`

## Características

| Módulo | Descripción |
|--------|-------------|
| 🛍 **Punto de Venta** | Búsqueda por nombre/código de barras, carrito, descuentos, IVA, múltiples formas de pago, cambio automático |
| 📦 **Inventario** | CRUD de productos, categorías, ajuste de stock, alertas de stock mínimo |
| 👥 **Clientes** | Registro y gestión de clientes, asociación a ventas |
| 📊 **Reportes** | Ventas por período, productos más vendidos, métodos de pago, valor de inventario |
| 🧾 **Recibos** | Generación automática con folio, detalle de artículos y cambio |
| ⚙ **Configuración** | Datos de la tienda, IVA, moneda, pie de recibo |
| 👤 **Usuarios** | Roles (admin/cajero), contraseñas cifradas (SHA-256), gestión de usuarios |

## Estructura del proyecto

```
pos_system/
├── main.py           # Punto de entrada
├── database.py       # SQLite — tablas e inicialización
├── auth.py           # Autenticación y usuarios
├── inventory.py      # Productos, categorías e inventario
├── sales.py          # Ventas, carrito y clientes
├── receipt.py        # Generación de recibos en texto
├── reports.py        # Consultas para reportes y estadísticas
└── gui/
    ├── login.py          # Pantalla de inicio de sesión
    ├── main_window.py    # Ventana principal + interfaz de venta
    ├── products.py       # Gestión de productos
    ├── customers.py      # Gestión de clientes
    ├── reports_view.py   # Vista de reportes
    └── styles.py         # Tema oscuro / colores y fuentes
```

## Licencia

MIT
