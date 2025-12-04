import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# --- 1. CONFIGURACIÓN Y CONEXIONES ---

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Añadir el directorio 'src' al path para poder importar los modelos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Importar Base y todos los modelos de la base de datos
from database.models import Base, Docentes, Estudiantes_2016_2019, Escuela_nueva, Estudiantes_Colombo, Estudiantes_2021_2025, Estudiantes_intensificacion

print("="*80)
print("🚀 INICIANDO SCRIPT DE MIGRACIÓN DE BASE DE DATOS 🚀")
print("="*80)

# --- Configuración de la Base de Datos Remota (Origen) ---
remote_db_user = os.getenv('DB_USER')
remote_db_pass = os.getenv('DB_PASS')
remote_db_host = os.getenv('DB_HOST')
remote_db_port = os.getenv('DB_PORT')
remote_db_name = os.getenv('DB_NAME')

remote_conn_str = f"mysql+mysqlconnector://{remote_db_user}:{remote_db_pass}@{remote_db_host}:{remote_db_port}/{remote_db_name}"

# --- Configuración de la Base de Datos Local (Destino) ---
local_db_user = os.getenv('LOCAL_DB_USER')
local_db_pass = os.getenv('LOCAL_DB_PASS')
local_db_host = os.getenv('LOCAL_DB_HOST')
local_db_port = os.getenv('LOCAL_DB_PORT')
local_db_name = os.getenv('LOCAL_DB_NAME')

local_conn_str = f"mysql+mysqlconnector://{local_db_user}:{local_db_pass}@{local_db_host}:{local_db_port}/{local_db_name}"

try:
    print("\n🔌 Conectando a las bases de datos...")
    remote_engine = create_engine(remote_conn_str)
    local_engine = create_engine(local_conn_str)

    # Verificar conexiones
    with remote_engine.connect() as remote_conn, local_engine.connect() as local_conn:
        print("   ✅ Conexión a la BD Remota (Origen) exitosa.")
        print("   ✅ Conexión a la BD Local (Destino) exitosa.")

except Exception as e:
    print(f"\n❌ Error al conectar a una de las bases de datos: {e}")
    print("   Asegúrate de que las credenciales en tu archivo .env son correctas y que el servidor de base de datos local está en ejecución.")
    sys.exit(1) # Detener el script si no se puede conectar


# --- 2. CREACIÓN DE TABLAS EN LA BASE DE DATOS LOCAL ---

try:
    print("\n🏗️  Creando tablas en la base de datos local (si no existen)...")
    # Base.metadata.create_all() crea todas las tablas que heredan de Base
    Base.metadata.create_all(local_engine)
    print("   ✅ Todas las tablas han sido verificadas/creadas en el destino.")

except Exception as e:
    print(f"\n❌ Error al crear las tablas en la base de datos local: {e}")
    sys.exit(1)


# --- 3. TRANSFERENCIA DE DATOS ---

try:
    # Obtener una lista de todas las tablas definidas en models.py
    tables_to_migrate = Base.metadata.sorted_tables

    print("\n🚚 Iniciando transferencia de datos para todas las tablas...")

    for table in tables_to_migrate:
        table_name = table.name
        print(f"\n   -> Procesando tabla: '{table_name}'")

        try:
            # Paso 3.1: Leer todos los datos de la tabla remota usando Pandas
            print(f"      - Leyendo datos desde el origen...")
            df = pd.read_sql_table(table_name, remote_engine)
            print(f"      - {len(df)} filas leídas.")

            if not df.empty:
                # Paso 3.2: Limpiar la tabla local antes de insertar nuevos datos
                print(f"      - Limpiando tabla en el destino...")
                with local_engine.connect() as connection:
                    transaction = connection.begin()
                    # Desactivar temporalmente la revisión de claves foráneas para permitir el borrado
                    connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                    connection.execute(text(f"TRUNCATE TABLE `{table_name}`;"))
                    # Reactivar la revisión
                    connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                    transaction.commit()
                
                # Paso 3.3: Escribir los datos en la tabla local
                print(f"      - Escribiendo {len(df)} filas en el destino...")
                df.to_sql(table_name, local_engine, if_exists='append', index=False, chunksize=1000)
                print(f"      - ✅ Transferencia para '{table_name}' completada.")
            else:
                print(f"      - ⚠️ La tabla '{table_name}' está vacía en el origen. No hay datos para transferir.")

        except Exception as e:
            print(f"      - ❌ Error durante la migración de la tabla '{table_name}': {e}")
            # Continuar con la siguiente tabla en caso de error en una
            continue
finally:
    # Cerrar las conexiones
    remote_engine.dispose()
    local_engine.dispose()
    print("\n🔌 Conexiones a las bases de datos cerradas.")

print("\n" + "="*80)
print("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE 🎉")
print("="*80)