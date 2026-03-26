# 📋 Guía de Instalación - NorbackPOS

## Opción 1: Ejecutar con Python (Recomendado para desarrollo)

### Paso 1: Instalar Python
1. Descarga Python 3.8 o superior desde: https://www.python.org/downloads/
2. Durante la instalación, **IMPORTANTE**: marca la casilla **"Add Python to PATH"**
3. Completa la instalación

### Paso 2: Verificar que Python está instalado
Abre una terminal/símbolo del sistema y ejecuta:
```bash
python --version
```
Deberías ver algo como: `Python 3.13.0`

### Paso 3: Ejecutar NorbackPOS
En Windows, haz doble clic en **`run.bat`**  
O desde terminal:
```bash
python pos_system/main.py
```

### Acceso inicial
- Usuario: `admin`
- Contraseña: `admin123`

---

## Opción 2: Usar el ejecutable (EXE)

Si solo quieres usar la aplicación sin tener Python instalado:

### Paso 1: Compilar el EXE
1. Descarga e instala Python (ver Opción 1)
2. En la carpeta del proyecto, haz doble clic en **`build_exe.bat`**
3. Espera que termine (puede tardar 1-2 minutos)
4. El ejecutable estará en la carpeta `dist/NorbackPOS.exe`

### Paso 2: Ejecutar el programa
- Haz doble clic en **`dist/NorbackPOS.exe`**
- La aplicación se abrirá sin necesidad de Python

---

## Solución de problemas

### "Python no reconocido"
- Python no está en PATH
- Reinstala Python y marca **"Add Python to PATH"**

### "Aplicación no inicia"
- Abre terminal en la carpeta del proyecto:
  ```bash
  cd D:\PROGRAMAS\Norbackvc-main
  python test_run.py
  ```
- Esto te mostrará el error exacto

### "No se puede crear el EXE"
- Abre PowerShell y ejecuta:
  ```bash
  python -m pip install --upgrade pip
  python -m pip install PyInstaller pyinstaller-hooks-contrib
  ```
- Luego vuelve a ejecutar `build_exe.bat`

---

## Ubicación de datos

- **Base de datos**: `pos_system/pos_data.db`
- **Recibos**: `pos_system/receipts/`

Estos archivos se crean automáticamente en la primera ejecución.

---

## En Linux/Mac

```bash
# Dar permisos al script
chmod +x run.sh

# Ejecutar
./run.sh

# O desde Python directamente
python3 pos_system/main.py
```

---

¿Problemas? Revisa el README.md para más información.
