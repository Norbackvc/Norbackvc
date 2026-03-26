@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

REM Priorizar Python del entorno virtual del proyecto
if exist "%~dp0.venv\Scripts\python.exe" (
    set PYTHON_EXE=%~dp0.venv\Scripts\python.exe
)

REM Si no hay venv, buscar Python en PATH (evitando alias de Microsoft Store)
if "!PYTHON_EXE!"=="" (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        echo %%i | find /i "WindowsApps" >nul
        if errorlevel 1 (
            set PYTHON_EXE=%%i
            goto :python_found
        )
    )
)

:python_found

REM Si no se encontró en PATH, buscar en ubicaciones comunes
if "!PYTHON_EXE!"=="" (
    if exist "C:\Python313\python.exe" set PYTHON_EXE=C:\Python313\python.exe
    if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
)

if "!PYTHON_EXE!"=="" (
    echo Error: Python no encontrado. Instala Python desde https://www.python.org
    pause
    exit /b 1
)

echo [1/3] Verificando Python en: !PYTHON_EXE!
"!PYTHON_EXE!" --version || goto :error

echo [2/4] Instalando/actualizando dependencias de build...
"!PYTHON_EXE!" -m pip install --upgrade pip || goto :error
if exist "requirements-build.txt" (
    "!PYTHON_EXE!" -m pip install -r requirements-build.txt || goto :error
) else (
    echo Aviso: requirements-build.txt no encontrado. Continuando...
)
"!PYTHON_EXE!" -m pip install --upgrade pyinstaller || goto :error

echo [3/4] Compilando EXE...
"!PYTHON_EXE!" -m PyInstaller --noconfirm --clean --onefile --windowed --name NorbackPOS pos_system\main.py || goto :error

echo [4/4] Compilacion finalizada.

echo.
echo Listo. EXE generado en: dist\NorbackPOS.exe
exit /b 0

:error
echo.
echo Ocurrio un error durante la compilacion.
exit /b 1
