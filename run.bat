@echo off
REM Script para ejecutar NorbackPOS fácilmente

cd /d "%~dp0"

REM Si existe el EXE compilado, usarlo
if exist "dist\NorbackPOS.exe" (
    echo Ejecutando NorbackPOS...
    start dist\NorbackPOS.exe
    exit /b
)

REM Si no, ejecutar desde Python
for /f "delims=" %%i in ('where python 2^>nul') do set PYTHON_EXE=%%i

if "!PYTHON_EXE!"=="" (
    if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
)

if "!PYTHON_EXE!"=="" (
    echo Error: Python no encontrado.
    echo Instala Python desde: https://www.python.org
    pause
    exit /b 1
)

echo Ejecutando NorbackPOS con Python...
"!PYTHON_EXE!" pos_system/main.py
