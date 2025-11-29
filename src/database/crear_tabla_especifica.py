import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from .conexion import engine
from .models import Estudiantes_2021_2025
from src.config.logger_config import get_logger

logger = get_logger(__name__)

def crear_tabla_especifica():
    """
    Crea una tabla específica en la base de datos si no existe,
    sin afectar a las demás tablas.
    """
    try:
        table_name = Estudiantes_2021_2025.__tablename__
        logger.info(f"Verificando y creando la tabla '{table_name}' si no existe...")
        
        # El argumento checkfirst=True asegura que no se intente crear si ya existe.
        Estudiantes_2021_2025.__table__.create(bind=engine, checkfirst=True)
        
        logger.info(f"✓ Tabla '{table_name}' verificada/creada exitosamente.")
        print(f"✓ Tabla '{table_name}' verificada/creada exitosamente.")

    except Exception as e:
        logger.error(f"Error al crear la tabla: {e}", exc_info=True)
        print(f"❌ Error al crear la tabla: {e}")
    finally:
        engine.dispose()
        logger.info("Proceso de creación de tabla finalizado.")

if __name__ == "__main__":
    crear_tabla_especifica()
