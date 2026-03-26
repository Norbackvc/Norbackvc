#!/bin/bash
# Script para ejecutar NorbackPOS en Linux/Mac

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Si existe el ejecutable compilado, usarlo
if [ -f "dist/NorbackPOS" ]; then
    echo "Ejecutando NorbackPOS..."
    ./dist/NorbackPOS &
    exit 0
fi

# Si no, ejecutar desde Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 no encontrado."
    echo "Instala Python desde: https://www.python.org"
    exit 1
fi

echo "Ejecutando NorbackPOS con Python..."
python3 pos_system/main.py
