import sys
import os

# Añadir el directorio raíz del proyecto ('Observatorio') al path de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar los componentes necesarios
from src.database.conexion import engine
from src.database.models import (
    Base,
    Frances_intensificacion,
    Frances_intensificacion_horas
)
from src.config.logger_config import get_logger

logger = get_logger(__name__)

def recrear_tablas_frances():
    """
    Elimina y vuelve a crear específicamente las tablas relacionadas con 'Francés'.
    - Frances_intensificacion
    - Frances_intensificacion_horas
    """
    # Lista de modelos de las tablas a gestionar
    modelos_a_gestionar = [
        Frances_intensificacion,
        Frances_intensificacion_horas
    ]
    
    # Obtener los objetos Table de SQLAlchemy para pasarlos a drop_all y create_all
    tablas_a_gestionar = [modelo.__table__ for modelo in modelos_a_gestionar]
    nombres_tablas = [tabla.name for tabla in tablas_a_gestionar]

    try:
        print("="*70)
        print("⚠️  ADVERTENCIA: Este script eliminará y recreará las siguientes tablas de FRANCÉS:")
        for nombre in nombres_tablas:
            print(f"  - {nombre}")
        print("Las demás tablas NO serán afectadas.")
        print("="*70)
        
        confirm = input("¿Estás seguro de que quieres continuar? (s/n): ").lower().strip()
        if confirm != 's':
            print("❌ Operación cancelada.")
            return
        
        logger.info(f"Eliminando las tablas de Francés: {nombres_tablas}")
        Base.metadata.drop_all(engine, tables=tablas_a_gestionar, checkfirst=True)
        logger.info("Tablas de Francés eliminadas.")

        logger.info(f"Creando las tablas de Francés: {nombres_tablas}")
        Base.metadata.create_all(engine, tables=tablas_a_gestionar)
        logger.info("✅ Tablas de Francés recreadas exitosamente.")
        print("\n✅ Tablas de Francés recreadas exitosamente.")

    except Exception as e:
        logger.error(f"Error durante el proceso de recreación de tablas de Francés: {e}", exc_info=True)
        print(f"❌ Error al recrear las tablas: {e}")
    finally:
        engine.dispose()
        logger.info("Proceso de recreación de tablas de Francés finalizado.")

if __name__ == "__main__":
    recrear_tablas_frances()