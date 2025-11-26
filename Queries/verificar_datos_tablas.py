"""
Script para verificar el estado de todas las tablas en la base de datos remota.
Se conecta a la base de datos, obtiene una lista de todas las tablas y
ejecuta una consulta COUNT(*) en cada una para informar si tienen datos.

Requisitos:
- python-dotenv: pip install python-dotenv
- Un archivo .env en la raíz del proyecto con las credenciales de la BD:
  DB_USER="tu_usuario"
  DB_PASS="tu_contraseña"
  DB_HOST="tu_host"
  DB_PORT="tu_puerto"
  DB_NAME="tu_nombre_de_bd"
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Añadir el directorio raíz del proyecto a sys.path para encontrar el .env
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# Obtener credenciales de la base de datos desde las variables de entorno
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

# Validar que todas las variables de entorno estén presentes
if not all([db_user, db_pass, db_host, db_port, db_name]):
    print("\n❌ Error: Faltan variables de entorno para la conexión a la base de datos.")
    print("   Asegúrate de tener un archivo .env en la raíz del proyecto con DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME.")
    sys.exit(1)

# Crear la cadena de conexión y el motor de SQLAlchemy
connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
engine = create_engine(connection_string, pool_pre_ping=True)

def verificar_tablas():
    print("\n" + "="*70)
    print("VERIFICACIÓN DE DATOS EN TABLAS DE LA BASE DE DATOS REMOTA")
    print("="*70)
    
    try:
        print("\n📡 Conectando a la base de datos remota...")
        with engine.connect() as connection:
            print("✅ Conexión exitosa.")
            
            inspector = inspect(engine)
            tables = sorted(inspector.get_table_names())
            
            if not tables:
                print("\n⚠️ No se encontraron tablas en la base de datos.")
                return

            print("\n📋 Reporte de estado de las tablas:")
            for table_name in tables:
                count_query = text(f"SELECT COUNT(*) FROM `{table_name}`")
                row_count = connection.execute(count_query).scalar()
                
                if row_count > 0:
                    print(f"  ✅ Tabla '{table_name}': {row_count:,} registros.")
                else:
                    print(f"  ⚠️ Tabla '{table_name}': 0 registros (vacía).")

    except Exception as e:
        print(f"\n❌ Error durante la verificación: {e}")
    finally:
        engine.dispose()
        print("\n🔌 Conexión a la base de datos cerrada.")
        print("="*70)

if __name__ == "__main__":
    verificar_tablas()