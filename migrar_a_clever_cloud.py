#!/usr/bin/env python3
"""
Script de migración de Base de Datos Local (Docker) a Clever Cloud

Este script realiza la migración de tu BD local corriendo en Docker
a la BD de Clever Cloud.

Uso:
    python3 migrar_a_clever_cloud.py

Requisitos:
    - Docker corriendo con la BD local (puerto 3306 o 3308)
    - mysql-connector-python instalado
    - sqlalchemy instalado
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def print_header(text):
    """Imprime un encabezado formateado"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_step(number, text):
    """Imprime un paso"""
    print(f"\n📍 PASO {number}: {text}")
    print("-" * 70)

def run_command(cmd, description="", shell=False):
    """Ejecuta un comando y verifica si tuvo éxito"""
    if description:
        print(f"   ⏳ {description}...")
    try:
        if shell:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"   ❌ Error: {result.stderr}")
            return False, result.stderr
        else:
            if result.stdout:
                print(f"   ✅ {result.stdout.strip()[:100]}")
            return True, result.stdout
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, str(e)

def main():
    print_header("🚀 MIGRACIÓN DE BD LOCAL (DOCKER) A CLEVER CLOUD")
    
    print("""
Este script migrará tu base de datos desde Docker a Clever Cloud.

Requisitos previos:
  ✓ Docker corriendo con MySQL
  ✓ BD local con datos
  ✓ Credenciales de Clever Cloud
  ✓ Conexión a internet
    """)
    
    # Datos de conexión Clever Cloud
    print_step(1, "Configurar credenciales de Clever Cloud")
    
    clever_config = {
        'user': 'uuoxxbrx6knnwzc6',
        'password': '5fIPyo9KIlulljR0yTdB',
        'host': 'bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com',
        'port': '3306',
        'database': 'bdldn022szfj4gyd9fqn'
    }
    
    print(f"""
   📊 Clever Cloud BD:
      • Host: {clever_config['host']}
      • Base de datos: {clever_config['database']}
      • Usuario: {clever_config['user']}
      • Puerto: {clever_config['port']}
    """)
    
    # Datos de conexión Local (Docker)
    print_step(2, "Configurar BD local en Docker")
    
    docker_config = {
        'user': 'root',
        'password': '123456',
        'host': 'localhost',
        'port': '3308',
        'database': 'observatorio_bilinguismo'
    }
    
    print(f"""
   🐳 Docker BD Local:
      • Host: {docker_config['host']}
      • Base de datos: {docker_config['database']}
      • Usuario: {docker_config['user']}
      • Puerto: {docker_config['port']}
    """)
    
    # Verificar Docker
    print_step(3, "Verificar Docker")
    
    success, output = run_command("docker ps", "Verificando Docker")
    if not success:
        print("❌ Docker no está corriendo o no está instalado.")
        print("   Inicia Docker y ejecuta de nuevo este script.")
        sys.exit(1)
    
    # Verificar MySQL corriendo en Docker
    print_step(4, "Verificar MySQL corriendo en Docker")
    
    containers_output = subprocess.run("docker ps", shell=True, capture_output=True, text=True).stdout
    if 'mysql' in containers_output.lower():
        print("   ✅ MySQL detectado en Docker")
    else:
        print("   ⚠️  MySQL no detectado. Asegúrate de que el contenedor esté corriendo.")
        print("   Contenedores actuales:")
        print(containers_output)
    
    # Opciones de migración
    print_step(5, "Seleccionar método de migración")
    
    print("""
Métodos disponibles:

  1️⃣  Volcado + Restauración (Recomendado - rápido y seguro)
      • Exporta BD local a SQL
      • Importa en Clever Cloud
      
  2️⃣  Sincronización por Python (Alternativo)
      • Lee datos de Docker
      • Inserta en Clever Cloud
      
  3️⃣  Usar solo tablas de Clever Cloud (sin datos)
      • Solo crea estructura
      • No importa datos
    """)
    
    choice = input("\nOpción (1-3): ").strip()
    
    if choice == "1":
        migrate_with_dump(docker_config, clever_config)
    elif choice == "2":
        migrate_with_python(docker_config, clever_config)
    elif choice == "3":
        create_only_schema(clever_config)
    else:
        print("❌ Opción no válida")
        sys.exit(1)

def migrate_with_dump(docker_config, clever_config):
    """Migración usando mysqldump (recomendado)"""
    
    print_step(6, "Migración con mysqldump")
    
    # Archivo de volcado
    dump_file = f"bd_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    print(f"\n   📁 Archivo de volcado: {dump_file}")
    
    # Comando mysqldump desde Docker
    print_step(7, "Exportar BD desde Docker")
    
    docker_dump_cmd = f"""docker exec $(docker ps | grep mysql | awk '{{print $1}}') mysqldump -u {docker_config['user']} -p{docker_config['password']} {docker_config['database']} > {dump_file}"""
    
    print(f"   Comando: {docker_dump_cmd}")
    success, output = run_command(docker_dump_cmd, "Exportando base de datos desde Docker", shell=True)
    
    if success:
        file_size = os.path.getsize(dump_file)
        print(f"   ✅ Volcado completado: {file_size / 1024 / 1024:.2f} MB")
    else:
        print(f"   ❌ Error en volcado: {output}")
        return
    
    # Importar en Clever Cloud
    print_step(8, "Importar BD en Clever Cloud")
    
    mysql_import_cmd = f"""mysql -h {clever_config['host']} -u {clever_config['user']} -p{clever_config['password']} -P {clever_config['port']} {clever_config['database']} < {dump_file}"""
    
    print(f"   ⏳ Importando en Clever Cloud...")
    print(f"   Host: {clever_config['host']}")
    print(f"   BD: {clever_config['database']}")
    
    success, output = run_command(mysql_import_cmd, "Importando datos en Clever Cloud", shell=True)
    
    if success:
        print(f"   ✅ Importación completada en Clever Cloud")
    else:
        print(f"   ❌ Error en importación: {output}")
        return
    
    # Verificar
    print_step(9, "Verificar migración")
    
    verify_cmd = f"""mysql -h {clever_config['host']} -u {clever_config['user']} -p{clever_config['password']} -P {clever_config['port']} {clever_config['database']} -e "SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema='{clever_config['database']}';" """
    
    success, output = run_command(verify_cmd, "Verificando tablas en Clever Cloud", shell=True)
    
    if success:
        print(f"   ✅ Verificación exitosa")
        print("\n✅ MIGRACIÓN COMPLETADA CON ÉXITO")
        print(f"\n📊 Datos migrados:")
        print(f"   • Base de datos: {clever_config['database']}")
        print(f"   • Host: {clever_config['host']}")
        print(f"   • Tamaño del volcado: {file_size / 1024 / 1024:.2f} MB")
    
    # Limpiar
    print_step(10, "Limpiar archivos temporales")
    
    keep = input(f"\n¿Mantener archivo de volcado ({dump_file})? (s/n): ").strip().lower()
    if keep != 's':
        os.remove(dump_file)
        print(f"   ✅ Archivo eliminado")
    else:
        print(f"   ✅ Archivo guardado en: {os.path.abspath(dump_file)}")

def migrate_with_python(docker_config, clever_config):
    """Migración usando Python (alternativa)"""
    
    print_step(6, "Migración con Python")
    
    try:
        from sqlalchemy import create_engine, text, inspect
        import pandas as pd
    except ImportError:
        print("❌ Se requieren sqlalchemy y pandas")
        print("   Instala con: pip install sqlalchemy pandas mysql-connector-python")
        sys.exit(1)
    
    print("\n   Conectando a BD local (Docker)...")
    docker_engine = create_engine(
        f"mysql+mysqlconnector://{docker_config['user']}:{docker_config['password']}"
        f"@{docker_config['host']}:{docker_config['port']}/{docker_config['database']}"
    )
    
    print("   Conectando a Clever Cloud...")
    clever_engine = create_engine(
        f"mysql+mysqlconnector://{clever_config['user']}:{clever_config['password']}"
        f"@{clever_config['host']}:{clever_config['port']}/{clever_config['database']}"
    )
    
    # Obtener tablas
    print("\n   📋 Obtener estructura de tablas...")
    inspector = inspect(docker_engine)
    tables = inspector.get_table_names()
    
    print(f"   ✅ Se encontraron {len(tables)} tablas")
    
    # Copiar datos
    print("\n   📊 Copiar datos de tablas...")
    
    try:
        for i, table in enumerate(tables, 1):
            print(f"      {i}/{len(tables)} - Copiando tabla: {table}...", end=" ")
            
            # Leer datos
            df = pd.read_sql(f"SELECT * FROM {table}", docker_engine)
            
            # Escribir en Clever Cloud
            df.to_sql(table, clever_engine, if_exists='append', index=False)
            
            print(f"✅ ({len(df)} registros)")
    
    except Exception as e:
        print(f"\n   ❌ Error: {e}")
        return
    
    print("\n✅ MIGRACIÓN COMPLETADA CON ÉXITO")
    print(f"\n📊 Datos migrados:")
    print(f"   • Tablas: {len(tables)}")
    print(f"   • Base de datos: {clever_config['database']}")
    print(f"   • Host: {clever_config['host']}")

def create_only_schema(clever_config):
    """Crear solo la estructura sin datos"""
    
    print_step(6, "Crear solo estructura en Clever Cloud")
    
    print(f"""
   Solo se crearán las tablas sin importar datos.
   
   BD Clever Cloud:
      • Host: {clever_config['host']}
      • Base de datos: {clever_config['database']}
    """)
    
    try:
        from sqlalchemy import create_engine
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        
        # Crear engine para Clever Cloud
        clever_engine = create_engine(
            f"mysql+mysqlconnector://{clever_config['user']}:{clever_config['password']}"
            f"@{clever_config['host']}:{clever_config['port']}/{clever_config['database']}"
        )
        
        # Importar modelos
        from Base_datos.models import Base
        
        print("\n   Creando tablas en Clever Cloud...")
        Base.metadata.create_all(clever_engine)
        print("   ✅ Tablas creadas exitosamente")
        
        print("\n✅ ESTRUCTURA CREADA EN CLEVER CLOUD")
        print(f"\n📊 Información:")
        print(f"   • Base de datos: {clever_config['database']}")
        print(f"   • Host: {clever_config['host']}")
        print(f"   • Tablas vacías, lista para importar datos")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

if __name__ == "__main__":
    main()
