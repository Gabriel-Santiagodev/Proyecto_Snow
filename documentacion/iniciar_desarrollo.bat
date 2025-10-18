@echo off
echo 🚀 Iniciando Sistema de Vigilancia SNOW - Modo Desarrollo
echo ========================================================

REM Verificar que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado o no está en el PATH
    pause
    exit /b 1
)

REM Verificar que los archivos necesarios existan
if not exist "sistema_desarrollo.py" (
    echo ❌ Archivo sistema_desarrollo.py no encontrado
    pause
    exit /b 1
)

if not exist "best.pt" (
    echo ❌ Archivo best.pt no encontrado
    pause
    exit /b 1
)

if not exist "config_sistema.json" (
    echo ❌ Archivo config_sistema.json no encontrado
    pause
    exit /b 1
)

echo ✅ Archivos verificados correctamente
echo.
echo 🎯 Iniciando sistema de vigilancia...
echo 📋 Presiona Ctrl+C para detener el sistema
echo.

REM Ejecutar el sistema
python sistema_desarrollo.py

echo.
echo ⚠️  Sistema detenido
pause
