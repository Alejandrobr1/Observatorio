#!/usr/bin/env python3
"""
Script para preparar y desplegar el Observatorio Bilinguismo en Streamlit Cloud

Uso:
    python3 desplegar_streamlit_cloud.py
"""

import os
import subprocess
import sys
from pathlib import Path

def print_header(text):
    """Imprime un encabezado formateado"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def print_step(number, text):
    """Imprime un paso"""
    print(f"\n📍 PASO {number}: {text}")
    print("-" * 50)

def run_command(cmd, description=""):
    """Ejecuta un comando y verifica si tuvo éxito"""
    if description:
        print(f"   ⏳ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   ❌ Error: {result.stderr}")
            return False
        else:
            if result.stdout:
                print(f"   ✅ {result.stdout.strip()}")
            return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print_header("🚀 DESPLIEGUE EN STREAMLIT CLOUD")
    print("""
Este script te guiará a través de los pasos para desplegar
el Observatorio de Bilingüismo en Streamlit Cloud.

Requisitos previos:
  ✓ Cuenta en GitHub
  ✓ Cuenta en Streamlit Cloud (share.streamlit.io)
  ✓ Base de datos MySQL en la nube (AWS RDS, Clever Cloud, etc.)
  ✓ Git instalado localmente
    """)
    
    # Paso 1: Verificar Git
    print_step(1, "Verificar Git")
    if not run_command("git --version", "Verificando Git"):
        print("❌ Git no está instalado. Descárgalo desde: https://git-scm.com/")
        sys.exit(1)
    
    # Paso 2: Inicializar repositorio
    print_step(2, "Inicializar repositorio Git")
    
    root_dir = Path(__file__).parent.absolute()
    os.chdir(root_dir)
    
    if not (root_dir / ".git").exists():
        print("   📁 Inicializando nuevo repositorio...")
        run_command("git init", "Inicializando Git")
        run_command('git config user.email "desarrollo@observatorio.local"', "Configurando email")
        run_command('git config user.name "Observatorio"', "Configurando nombre")
    else:
        print("   ✅ Repositorio Git ya existe")
    
    # Paso 3: Configurar .gitignore
    print_step(3, "Verificar .gitignore")
    gitignore = root_dir / ".gitignore"
    if gitignore.exists():
        print("   ✅ .gitignore configurado")
    else:
        print("   ⚠️  .gitignore no encontrado")
    
    # Paso 4: Verificar requirements.txt
    print_step(4, "Verificar requirements.txt")
    reqs = root_dir / "requirements.txt"
    if reqs.exists():
        print("   ✅ requirements.txt encontrado")
        with open(reqs) as f:
            packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            print(f"   📦 Paquetes incluidos: {len(packages)}")
    else:
        print("   ❌ requirements.txt no encontrado")
    
    # Paso 5: Verificar estructura
    print_step(5, "Verificar estructura de directorios")
    
    required_dirs = [
        ("Dashboards", "Dashboard principal"),
        ("pages", "Páginas de Streamlit"),
        ("Base_datos", "Conexión a BD"),
        (".streamlit", "Configuración Streamlit"),
    ]
    
    for dir_name, description in required_dirs:
        dir_path = root_dir / dir_name
        if dir_path.exists():
            print(f"   ✅ {description} ({dir_name}/)")
        else:
            print(f"   ⚠️  {description} no encontrado ({dir_name}/)")
    
    # Paso 6: Configurar remoto de GitHub
    print_step(6, "Configurar repositorio remoto")
    
    # Verificar si ya tiene remoto
    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    
    if "origin" in result.stdout:
        print("   ✅ Remoto 'origin' ya configurado:")
        print(f"      {result.stdout.strip()}")
    else:
        print("   📝 Necesitas agregar el remoto de GitHub:")
        print("      1. Crea un repositorio en: https://github.com/new")
        print("      2. Copia la URL de tu repositorio")
        print("      3. Ejecuta:")
        print("         git remote add origin https://github.com/TU_USUARIO/observatorio-bilinguismo.git")
    
    # Paso 7: Verificar cambios
    print_step(7, "Revisar cambios pendientes")
    result = subprocess.run("git status --short", shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("   📝 Cambios detectados:")
        lines = result.stdout.strip().split("\n")
        for line in lines[:10]:  # Mostrar máximo 10 líneas
            print(f"      {line}")
        if len(lines) > 10:
            print(f"      ... y {len(lines) - 10} más")
    else:
        print("   ✅ No hay cambios pendientes")
    
    # Paso 8: Instrucciones finales
    print_header("📋 INSTRUCCIONES FINALES")
    
    print("""
1️⃣  Agregar cambios a Git:
    git add .

2️⃣  Hacer commit:
    git commit -m "Preparar proyecto para Streamlit Cloud"

3️⃣  Empujar a GitHub (si tienes remoto configurado):
    git push -u origin main

4️⃣  En Streamlit Cloud (share.streamlit.io):
    • Haz clic en "New app"
    • Conecta tu repositorio de GitHub
    • Selecciona rama: main
    • Selecciona archivo: Dashboards/main_dashboard.py

5️⃣  Configurar secrets en Streamlit Cloud:
    • Ve a "App settings" → "Secrets"
    • Agrega estas variables:
    
    DB_USER = "tu_usuario"
    DB_PASS = "tu_contraseña"
    DB_HOST = "tu_host_rds.amazonaws.com"
    DB_PORT = "3306"
    DB_NAME = "observatorio_bilinguismo"

6️⃣  Preparar base de datos en la nube:
    • Conectar con credenciales
    • Ejecutar: Base_datos/crear_tablas.py
    • Importar datos: Queries/CSV_GENERAL.py

📚 Recursos útiles:
   • Documentación Streamlit Cloud: https://docs.streamlit.io/streamlit-community-cloud
   • AWS RDS: https://aws.amazon.com/rds/
   • Clever Cloud: https://clever-cloud.com/
   • Digital Ocean: https://digitalocean.com/

🎉 ¡Tu aplicación estará en línea en pocos minutos!
    """)
    
    # Ofrecer opciones
    print("\n¿Qué deseas hacer?")
    print("  1. Agregar cambios y hacer commit")
    print("  2. Ver el estado del repositorio")
    print("  3. Salir")
    
    choice = input("\nOpción (1-3): ").strip()
    
    if choice == "1":
        print("\n   📝 Agregando cambios...")
        run_command("git add .", "Agregando archivos a staging")
        
        message = input("   ¿Mensaje de commit? (ej: 'Preparar para Streamlit Cloud'): ").strip()
        if not message:
            message = "Preparar para Streamlit Cloud"
        
        run_command(f'git commit -m "{message}"', f"Haciendo commit: {message}")
        
        print("\n✅ Cambios confirmados. Ahora:")
        print("   1. Configura tu remoto en GitHub si no lo has hecho")
        print("   2. Ejecuta: git push -u origin main")
        print("   3. Ve a Streamlit Cloud y crea una nueva aplicación")
    
    elif choice == "2":
        print("\n   📊 Estado del repositorio:")
        run_command("git status", "")
    
    print_header("✨ ¡Listo para desplegar!")

if __name__ == "__main__":
    main()
