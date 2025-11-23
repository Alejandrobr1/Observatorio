import sys
import os

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from conexion import engine
from models import Base
from logger_config import get_logger

logger = get_logger(__name__)
try:
    # Eliminar todas las tablas existentes para asegurar un esquema limpio (opcional pero recomendado si hay cambios)
    logger.info("Eliminando tablas existentes (si las hay)...")
    Base.metadata.drop_all(engine)
    logger.info("Tablas eliminadas.")

    # Crear todas las tablas definidas en los modelos
    logger.info("Iniciando creación de tablas en la base de datos")
    Base.metadata.create_all(engine)
    logger.info("Tablas creadas exitosamente en observatorio_bilinguismo")
    print("Tablas creadas exitosamente en la base de datos observatorio_bilinguismo")
except Exception as e:
    logger.error(f"Error al crear las tablas: {e}", exc_info=True)
    print(f"Error al crear las tablas: {e}")
    raise
finally:
    engine.dispose()
    logger.info("Proceso de creación de tablas finalizado")