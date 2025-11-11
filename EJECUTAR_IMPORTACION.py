#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 SCRIPT MAESTRO DE IMPORTACIÓN DE DATOS
Observatorio Bilinguismo - Base de Datos

Este script facilita la importación de datos desde CSVs a la base de datos MySQL.
Solo ejecuta este archivo y el resto se hace automáticamente.
"""

import os
import sys
import subprocess
import time
from datetime import datetime

# Añadir ruta al proyecto
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Colores para terminal (Windows compatible)
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header():
    """Imprime encabezado"""
    print("\n" + "="*80)
    print(f"{Colors.HEADER}{Colors.BOLD}🚀  OBSERVATORIO BILINGUISMO - IMPORTACIÓN DE DATOS{Colors.ENDC}")
    print("="*80)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

def print_success(message):
    """Imprime mensaje de éxito"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_info(message):
    """Imprime mensaje de información"""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")

def print_warning(message):
    """Imprime mensaje de advertencia"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")

def print_error(message):
    """Imprime mensaje de error"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    print_info("Verificando dependencias...")
    
    try:
        import pandas
        print_success("pandas está instalado")
    except ImportError:
        print_error("pandas NO está instalado")
        print("  Ejecutar: pip install pandas")
        return False
    
    try:
        import sqlalchemy
        print_success("sqlalchemy está instalado")
    except ImportError:
        print_error("sqlalchemy NO está instalado")
        print("  Ejecutar: pip install sqlalchemy")
        return False
    
    try:
        import mysql.connector
        print_success("mysql-connector-python está instalado")
    except ImportError:
        print_error("mysql-connector-python NO está instalado")
        print("  Ejecutar: pip install mysql-connector-python")
        return False
    
    return True

def check_database_connection():
    """Verifica la conexión a la base de datos"""
    print_info("Verificando conexión a base de datos...")
    
    try:
        from Base_datos.conexion import engine
        with engine.connect() as connection:
            connection.execute("SELECT 1")
            print_success("✓ Conexión a MySQL establecida exitosamente")
            return True
    except Exception as e:
        print_error(f"No se pudo conectar a MySQL: {str(e)}")
        print("\n📋 Verificar:")
        print("  1. MySQL está corriendo en puerto 3308")
        print("  2. Configuración en Base_datos/conexion.py")
        print("  3. Usuario/contraseña correctos")
        return False

def check_csvs():
    """Verifica que los archivos CSV existan"""
    print_info("Verificando archivos CSV...")
    
    csv_folder = os.path.join(project_root, "CSVs")
    
    if not os.path.exists(csv_folder):
        print_error(f"Carpeta CSVs no encontrada: {csv_folder}")
        return False
    
    csv_files = []
    for year in range(2016, 2026):
        csv_file = os.path.join(csv_folder, f"data_{year}.csv")
        if os.path.exists(csv_file):
            csv_files.append(year)
    
    if not csv_files:
        print_warning(f"No se encontraron archivos CSV en {csv_folder}")
        print("  Archivos esperados: data_2016.csv, data_2017.csv, ..., data_2025.csv")
        return False
    
    print_success(f"Se encontraron {len(csv_files)} años: {', '.join(map(str, csv_files))}")
    return True

def check_tables():
    """Verifica que las tablas existan en la base de datos"""
    print_info("Verificando esquema de base de datos...")
    
    try:
        from Base_datos.conexion import engine
        from sqlalchemy import text
        
        with engine.connect() as connection:
            result = connection.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            
            required_tables = [
                'Tipo_documentos', 'Ciudades', 'Instituciones', 
                'Nivel_MCER', 'Personas', 'Persona_Nivel_MCER',
                'Sedes', 'Cursos'
            ]
            
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                print_warning(f"Tablas faltantes: {', '.join(missing_tables)}")
                print_info("Creando esquema de base de datos...")
                
                try:
                    from Base_datos.crear_tablas import Base
                    from Base_datos.models import Base as Models_Base
                    
                    Models_Base.metadata.create_all(engine)
                    print_success("Esquema de base de datos creado exitosamente")
                    return True
                except Exception as e:
                    print_error(f"Error al crear tablas: {str(e)}")
                    return False
            else:
                print_success(f"✓ Se encontraron todas las tablas requeridas")
                return True
    
    except Exception as e:
        print_error(f"Error verificando tablas: {str(e)}")
        return False

def run_import_script(script_name, display_name):
    """Ejecuta un script de importación"""
    print("\n" + "-"*80)
    print_info(f"Iniciando importación: {display_name}")
    print("-"*80)
    
    script_path = os.path.join(project_root, "Queries", script_name)
    
    if not os.path.exists(script_path):
        print_error(f"Script no encontrado: {script_path}")
        return False
    
    try:
        # Ejecutar el script
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=project_root,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print_success(f"{display_name} completó exitosamente")
            return True
        else:
            print_error(f"{display_name} terminó con error (código {result.returncode})")
            return False
    
    except Exception as e:
        print_error(f"Error ejecutando {display_name}: {str(e)}")
        return False

def print_summary(results):
    """Imprime resumen final"""
    print("\n" + "="*80)
    print(f"{Colors.BOLD}📊 RESUMEN DE EJECUCIÓN{Colors.ENDC}")
    print("="*80)
    
    for script_name, success in results.items():
        status = f"{Colors.OKGREEN}✅ ÉXITO{Colors.ENDC}" if success else f"{Colors.FAIL}❌ FALLO{Colors.ENDC}"
        print(f"  {script_name}: {status}")
    
    all_success = all(results.values())
    
    print("\n" + "-"*80)
    if all_success:
        print_success("IMPORTACIÓN COMPLETADA EXITOSAMENTE")
        print("\n📈 Los datos están listos para usar en los dashboards:")
        print("  • Dashboards Sábados")
        print("  • Dashboards Intensificación")
        print("  • Dashboards Formación Docente")
    else:
        print_warning("IMPORTACIÓN COMPLETADA CON ERRORES")
        print("\nRevisa los mensajes anteriores para más detalles")
    
    print(f"\nFin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

def main():
    """Función principal"""
    print_header()
    
    # PASO 1: Verificar dependencias
    print(f"{Colors.BOLD}📦 PASO 1: Verificando dependencias...{Colors.ENDC}")
    if not check_dependencies():
        print_error("Instala las dependencias y vuelve a intentar")
        sys.exit(1)
    
    print()
    
    # PASO 2: Verificar conexión a BD
    print(f"{Colors.BOLD}🔌 PASO 2: Verificando conexión a base de datos...{Colors.ENDC}")
    if not check_database_connection():
        print_error("No se puede conectar a la base de datos")
        sys.exit(1)
    
    print()
    
    # PASO 3: Verificar CSVs
    print(f"{Colors.BOLD}📂 PASO 3: Verificando archivos CSV...{Colors.ENDC}")
    if not check_csvs():
        print_warning("Algunos archivos CSV podrían estar faltando")
    
    print()
    
    # PASO 4: Verificar tablas
    print(f"{Colors.BOLD}🗄️  PASO 4: Verificando esquema de base de datos...{Colors.ENDC}")
    if not check_tables():
        print_error("No se pudo crear el esquema de base de datos")
        sys.exit(1)
    
    # PASO 5: Ejecutar importaciones
    print(f"\n{Colors.BOLD}🚀 PASO 5: Iniciando importación de datos...{Colors.ENDC}\n")
    
    results = {}
    
    # Importar datos generales
    print(f"{Colors.BOLD}GRUPO 1: Programas Sábados{Colors.ENDC}")
    results['CSV_GENERAL.py'] = run_import_script(
        'CSV_GENERAL.py',
        'Importación de datos - Sábados/Intensificación regular'
    )
    
    time.sleep(2)  # Pausa entre importaciones
    
    # Importar datos intensificación
    print(f"\n{Colors.BOLD}GRUPO 2: Programas Intensificación{Colors.ENDC}")
    results['CSV_GENERAL_INTENSIFICACION.py'] = run_import_script(
        'CSV_GENERAL_INTENSIFICACION.py',
        'Importación de datos - Programas Intensificación'
    )
    
    # Mostrar resumen
    print_summary(results)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}⚠️  Proceso interrumpido por el usuario{Colors.ENDC}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n{Colors.FAIL}❌ Error inesperado: {str(e)}{Colors.ENDC}\n")
        sys.exit(1)
