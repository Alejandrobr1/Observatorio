"""
Script para migrar datos de las tablas Estudiantes_YYYY a Estudiantes_escuela
"""

import sys
import os
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Base_datos.conexion import engine
from logger_config import get_logger

logger = get_logger(__name__)

print("\n" + "="*70)
print("MIGRACIÓN DE DATOS - ESTUDIANTES_ESCUELA")
print("="*70)

try:
    with engine.connect() as connection:
        # Primero, limpiar la tabla Estudiantes_escuela
        print("\n🗑️  Limpiando tabla Estudiantes_escuela...")
        connection.execute(text("DELETE FROM Estudiantes_escuela"))
        connection.commit()
        print("✅ Tabla limpiada")
        
        # Migrar datos de cada año
        años = [2016, 2017, 2018, 2019]
        total_inseridos = 0
        
        for año in años:
            tabla_origen = f"Estudiantes_{año}"
            
            # Verificar si la tabla existe y tiene datos
            try:
                resultado = connection.execute(text(f"SELECT COUNT(*) FROM {tabla_origen}"))
                count = resultado.scalar()
                
                if count == 0:
                    print(f"\n⏭️  {tabla_origen}: No tiene datos, se omite")
                    continue
                
                print(f"\n📂 Migrando datos de {tabla_origen} ({count} registros)...")
                
                # Insertar datos
                # Agregar por SEDE_NODAL como SEDE
                query = text(f"""
                    INSERT INTO Estudiantes_escuela (FECHA, SEDE, GRUPO_1, GRUPO_2, GRUPO_3, MATRICULADOS)
                    SELECT 
                        FECHA as FECHA,
                        SEDE_NODAL as SEDE,
                        0 as GRUPO_1,
                        0 as GRUPO_2,
                        0 as GRUPO_3,
                        MATRICULADOS as MATRICULADOS
                    FROM {tabla_origen}
                    WHERE SEDE_NODAL IS NOT NULL AND SEDE_NODAL != ''
                """)
                
                connection.execute(query)
                connection.commit()
                
                # Contar registros insertados
                resultado = connection.execute(text(f"SELECT COUNT(*) FROM Estudiantes_escuela WHERE FECHA = {año}"))
                inseridos = resultado.scalar()
                total_inseridos += inseridos
                print(f"✅ {inseridos} registros insertados para el año {año}")
                
            except Exception as e:
                print(f"⚠️  Error al procesar {tabla_origen}: {str(e)}")
                logger.error(f"Error migrating {tabla_origen}: {e}", exc_info=True)
                continue
        
        print(f"\n📊 Estadísticas de migración:")
        print(f"   • Total registros insertados: {total_inseridos}")
        
        # Verificar resultado
        resultado = connection.execute(text("SELECT DISTINCT FECHA FROM Estudiantes_escuela ORDER BY FECHA"))
        fechas = [row[0] for row in resultado.fetchall()]
        print(f"   • Años disponibles: {fechas}")
    
    print("\n" + "="*70)
    print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("="*70)
    
    logger.info(f"Successfully migrated {total_inseridos} records to Estudiantes_escuela")

except Exception as e:
    print(f"\n❌ Error durante la migración: {str(e)}")
    logger.error(f"Migration error: {e}", exc_info=True)

finally:
    engine.dispose()
    logger.info("Database connection closed")
