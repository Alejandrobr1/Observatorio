import sys
import os
from sqlalchemy import create_engine
import pandas as pd
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger_config import get_logger


logger = get_logger(__name__)

# Credenciales desde variables de entorno
# Clever Cloud en producción, Docker en desarrollo
db_user = os.getenv('DB_USER', 'root')
db_pass = os.getenv('DB_PASS', '123456')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '3308')
db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')

# Construir connection string
connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
engine = create_engine(connection_string)

try:
    with engine.connect() as connection:
        logger.info("Conexión exitosa a MySQL en puerto 3308")
        print("Conexión exitosa a MySQL en puerto 3308")
        df = pd.read_sql("SHOW DATABASES;", connection)
        logger.debug(f"Bases de datos encontradas: {df.to_dict()}")
        print(df)
except Exception as e:
    logger.error(f"Error al conectar a la base de datos: {e}", exc_info=True)
    print(f"Error al conectar: {e}")
    raise
finally:
    engine.dispose()
    logger.info("Conexión a base de datos cerrada")
