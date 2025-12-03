import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Cambiamos las importaciones relativas por absolutas desde la raíz 'src'
from src.database.conexion import engine
from src.database.models import (
    Base,
    Estudiantes_2021_2025,
    Instituciones_2021_2025,
    Grados_2021_2025,
    Estudiantes_intensificacion,
    Grados_intensificacion,
    Frances_intensificacion,
    Grados_intensificacion_Frances
)
from src.config.logger_config import get_logger

logger = get_logger(__name__)

def recrear_tablas_especificas():
    """
    Elimina y vuelve a crear un conjunto específico de tablas 
    (2021-2025 e Intensificación) sin afectar al resto.
    """
    # Lista de modelos de las tablas a gestionar
    modelos_a_gestionar = [
        Estudiantes_2021_2025,
        Instituciones_2021_2025,
        Grados_2021_2025,
        Estudiantes_intensificacion,
        Grados_intensificacion,
        Frances_intensificacion,
        Grados_intensificacion_Frances
    ]
    
    # Obtener los objetos Table de SQLAlchemy para pasarlos a drop_all y create_all
    tablas_a_gestionar = [modelo.__table__ for modelo in modelos_a_gestionar]
    nombres_tablas = [tabla.name for tabla in tablas_a_gestionar]

    try:
        print("="*70)
        print("⚠️ ADVERTENCIA: Este script eliminará y recreará las siguientes tablas:")
        for nombre in nombres_tablas:
            print(f"  - {nombre}")
        print("Las demás tablas NO serán afectadas.")
        print("="*70)
        
        confirm = input("¿Estás seguro de que quieres continuar? (s/n): ").lower().strip()
        if confirm != 's':
            print("❌ Operación cancelada.")
            return
        
        logger.info(f"Eliminando las tablas específicas: {nombres_tablas}")
        Base.metadata.drop_all(engine, tables=tablas_a_gestionar)
        logger.info("Tablas específicas eliminadas.")

        logger.info(f"Creando las tablas específicas: {nombres_tablas}")
        Base.metadata.create_all(engine, tables=tablas_a_gestionar)
        logger.info("✅ Tablas específicas recreadas exitosamente.")
        print("✅ Tablas específicas recreadas exitosamente.")

    except Exception as e:
        logger.error(f"Error durante el proceso de recreación de tablas: {e}", exc_info=True)
        print(f"❌ Error al recrear las tablas: {e}")
    finally:
        engine.dispose()
        logger.info("Proceso de recreación de tablas finalizado.")

if __name__ == "__main__":
    recrear_tablas_especificas()
