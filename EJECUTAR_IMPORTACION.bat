@echo off
REM ============================================================
REM SCRIPT DE INSTALACIÓN Y EJECUCIÓN RÁPIDA
REM Observatorio Bilinguismo - Importación de Datos
REM Para Windows (Batch + PowerShell)
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  OBSERVATORIO BILINGUISMO - IMPORTACIÓN DE DATOS
echo ============================================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no está instalado o no está en el PATH
    echo Descarga Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python detectado
python --version

REM Verificar si estamos en la carpeta correcta
if not exist "Base_datos\conexion.py" (
    echo.
    echo ❌ ERROR: No estás en la carpeta correcta
    echo Navega a: D:\Proyectos Jc Code\Archivos para BD rionegro\Observatorio
    pause
    exit /b 1
)

echo ✅ Carpeta verificada
echo.

REM Crear virtual environment si no existe
if not exist "env\" (
    echo 📦 Creando virtual environment...
    python -m venv env
    echo ✅ Virtual environment creado
) else (
    echo ✅ Virtual environment ya existe
)

echo.
echo 📦 Instalando dependencias requeridas...
call env\Scripts\activate.bat

REM Instalar paquetes
pip install --upgrade pip -q
pip install pandas sqlalchemy mysql-connector-python -q

echo ✅ Dependencias instaladas

echo.
echo ============================================================
echo  ANTES DE CONTINUAR:
echo ============================================================
echo.
echo ⚠️  Verifica que hayas configurado:
echo    1. Base_datos\conexion.py con los datos de MySQL
echo    2. Los archivos CSV en la carpeta CSVs\
echo.
echo ¿Continuar? (S/N)
set /p continuar="Respuesta: "

if /i not "%continuar%"=="S" (
    echo Proceso cancelado.
    pause
    exit /b 0
)

echo.
echo ============================================================
echo  CREANDO ESQUEMA DE BASE DE DATOS
echo ============================================================
echo.

python Base_datos\crear_tablas.py

if errorlevel 1 (
    echo.
    echo ❌ ERROR: No se pudo crear el esquema
    echo Verifica la configuración de MySQL
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  IMPORTANDO DATOS (Esto puede tomar 5-15 minutos)
echo ============================================================
echo.

python EJECUTAR_IMPORTACION.py

if errorlevel 1 (
    echo.
    echo ❌ ERROR: La importación falló
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  ✅ IMPORTACIÓN COMPLETADA
echo ============================================================
echo.
echo 📊 ¿Deseas validar que los datos se importaron correctamente?
echo (S/N)
set /p validar="Respuesta: "

if /i "%validar%"=="S" (
    echo.
    python VALIDAR_IMPORTACION.py
)

echo.
echo 🎉 ¡PROCESO COMPLETADO!
echo.
echo Los datos están listos para usar en los dashboards:
echo   • Dashboards Sábados
echo   • Dashboards Intensificación
echo   • Dashboards Formación Docente
echo.

pause
