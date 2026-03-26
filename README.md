# 🛒 Punto de Venta (POS) en Python

Sistema de Punto de Venta completo desarrollado en Python puro con interfaz gráfica (Tkinter) y base de datos SQLite — **sin dependencias externas en el código**.

## Requisitos

- **Python 3.8 o superior** ([Descargar](https://www.python.org/downloads/))
- **Tkinter** (incluido con Python; en Linux instala: `sudo apt install python3-tk`)

## 🚀 Ejecución rápida

### En Windows:
Haz doble clic en **`run.bat`** o ejecuta:
```bash
run.bat
```

### En Linux/Mac:
```bash
chmod +x run.sh
./run.sh
```

### O desde terminal (cualquier SO):
```bash
python pos_system/main.py
```

## Datos de acceso por defecto

- **Usuario:** `admin`
- **Contraseña:** `admin123`

> ⚠️ **Importante:** Cambia la contraseña del admin en la sección de Configuración después del primer inicio.

## 📦 Compilar EXE (opcional)

Si quieres crear un ejecutable standalone (no requiere Python instalado):

### Windows:
1. Instala PyInstaller:
   ```bash
   pip install PyInstaller pyinstaller-hooks-contrib
   ```

2. Ejecuta el script de compilación:
   ```bash
   build_exe.bat
   ```

3. El EXE estará en la carpeta `dist/`:
   ```bash
   dist/NorbackPOS.exe
   ```

### Linux/Mac:
```bash
pip install -r requirements-build.txt
python -m PyInstaller --onefile --windowed --name NorbackPOS pos_system/main.py
```



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

Todos los Derechos reservados @norbackvc 2026
