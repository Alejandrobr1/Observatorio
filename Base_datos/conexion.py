import sys
import os
from sqlalchemy import create_engine
import pandas as pd

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger_config import get_logger


logger = get_logger(__name__)
engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3308/observatorio_bilinguismo")

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
