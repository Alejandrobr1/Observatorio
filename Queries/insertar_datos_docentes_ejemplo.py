"""
Script para insertar datos de ejemplo en la tabla Docentes
"""

import pandas as pd
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Base_datos.conexion import engine
from logger_config import get_logger

logger = get_logger(__name__)

print("\n" + "="*70)
print("INSERCIÓN DE DATOS - TABLA DOCENTES")
print("="*70)

try:
    # Definir datos de ejemplo
    docentes_data = [
        # 2016
        {'FECHA': 2016, 'INSTITUCION_EDUCATIVA': 'Gilberto Echeverri Mejía', 'NOMBRES': 'Juan García', 'NIVEL': '1', 'IDIOMA': 'Inglés'},
        {'FECHA': 2016, 'INSTITUCION_EDUCATIVA': 'Gilberto Echeverri Mejía', 'NOMBRES': 'María López', 'NIVEL': '1', 'IDIOMA': 'Inglés'},
        {'FECHA': 2016, 'INSTITUCION_EDUCATIVA': 'Josefina Muñoz González', 'NOMBRES': 'Carlos Pérez', 'NIVEL': '1', 'IDIOMA': 'Inglés'},
        {'FECHA': 2016, 'INSTITUCION_EDUCATIVA': 'Josefina Muñoz González', 'NOMBRES': 'Ana Rodríguez', 'NIVEL': '2', 'IDIOMA': 'Inglés'},
        {'FECHA': 2016, 'INSTITUCION_EDUCATIVA': 'Concejo Municipal El Porvenir', 'NOMBRES': 'David Martínez', 'NIVEL': '1', 'IDIOMA': 'Inglés'},
        
        # 2017
        {'FECHA': 2017, 'INSTITUCION_EDUCATIVA': 'Gilberto Echeverri Mejía', 'NOMBRES': 'Juan García', 'NIVEL': '1', 'IDIOMA': 'Inglés'},
        {'FECHA': 2017, 'INSTITUCION_EDUCATIVA': 'Gilberto Echeverri Mejía', 'NOMBRES': 'Laura González', 'NIVEL': '2', 'IDIOMA': 'Inglés'},
        {'FECHA': 2017, 'INSTITUCION_EDUCATIVA': 'Josefina Muñoz González', 'NOMBRES': 'Carlos Pérez', 'NIVEL': '1', 'IDIOMA': 'Inglés'},
        {'FECHA': 2017, 'INSTITUCION_EDUCATIVA': 'Josefina Muñoz González', 'NOMBRES': 'Patricia Sánchez', 'NIVEL': '3', 'IDIOMA': 'Inglés'},
        {'FECHA': 2017, 'INSTITUCION_EDUCATIVA': 'Concejo Municipal El Porvenir', 'NOMBRES': 'Roberto Díaz', 'NIVEL': '1', 'IDIOMA': 'Inglés'},
        {'FECHA': 2017, 'INSTITUCION_EDUCATIVA': 'Técnico Industrial Santiago de Arma', 'NOMBRES': 'Carmen Ruiz', 'NIVEL': '2', 'IDIOMA': 'Inglés'},
        
        # 2019
        {'FECHA': 2019, 'INSTITUCION_EDUCATIVA': 'Gilberto Echeverri Mejía', 'NOMBRES': 'Juan García', 'NIVEL': '1', 'IDIOMA': 'Inglés'},
        {'FECHA': 2019, 'INSTITUCION_EDUCATIVA': 'Gilberto Echeverri Mejía', 'NOMBRES': 'Sofía Torres', 'NIVEL': '2', 'IDIOMA': 'Inglés'},
        {'FECHA': 2019, 'INSTITUCION_EDUCATIVA': 'Josefina Muñoz González', 'NOMBRES': 'Carlos Pérez', 'NIVEL': '1', 'IDIOMA': 'Inglés'},
        {'FECHA': 2019, 'INSTITUCION_EDUCATIVA': 'Josefina Muñoz González', 'NOMBRES': 'Valeria Morales', 'NIVEL': '3', 'IDIOMA': 'Inglés'},
        {'FECHA': 2019, 'INSTITUCION_EDUCATIVA': 'Concejo Municipal El Porvenir', 'NOMBRES': 'Héctor Flores', 'NIVEL': '1', 'IDIOMA': 'Inglés'},
        {'FECHA': 2019, 'INSTITUCION_EDUCATIVA': 'Técnico Industrial Santiago de Arma', 'NOMBRES': 'Isabel Vargas', 'NIVEL': '2', 'IDIOMA': 'Inglés'},
        {'FECHA': 2019, 'INSTITUCION_EDUCATIVA': 'Técnico Industrial Santiago de Arma', 'NOMBRES': 'Gustavo Ramírez', 'NIVEL': '1', 'IDIOMA': 'Inglés'},
    ]
    
    df = pd.DataFrame(docentes_data)
    
    print(f"\n📊 Datos a insertar:")
    print(f"   • Total registros: {len(df)}")
    print(f"   • Años: {sorted(df['FECHA'].unique())}")
    print(f"   • Instituciones: {sorted(df['INSTITUCION_EDUCATIVA'].unique())}")
    print(f"\n📋 Primeros 5 registros:")
    print(df.head().to_string())
    
    print(f"\n💾 Insertando datos en la base de datos...")
    
    with engine.connect() as connection:
        inseridos = 0
        errores = 0
        
        for idx, row in df.iterrows():
            try:
                insert_query = text("""
                    INSERT INTO Docentes (FECHA, INSTITUCION_EDUCATIVA, NOMBRES, NIVEL, IDIOMA)
                    VALUES (:fecha, :institucion, :nombres, :nivel, :idioma)
                """)
                connection.execute(insert_query, {
                    'fecha': int(row['FECHA']),
                    'institucion': str(row['INSTITUCION_EDUCATIVA']),
                    'nombres': str(row['NOMBRES']),
                    'nivel': str(row['NIVEL']),
                    'idioma': str(row['IDIOMA'])
                })
                inseridos += 1
                
                if inseridos % 5 == 0:
                    connection.commit()
                    print(f"   ✓ {inseridos} registros procesados...")
            
            except Exception as e:
                errores += 1
                print(f"   ✗ Error al procesar fila {idx + 1}: {str(e)[:100]}")
                logger.error(f"Error processing row: {e}", exc_info=True)
        
        connection.commit()
        print(f"\n✓ Inserción completada")
    
    print(f"\n📊 Estadísticas de inserción:")
    print(f"   • Registros insertados: {inseridos}")
    print(f"   • Errores: {errores}")
    
    with engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM Docentes"))
        total = result.scalar()
        print(f"\n📈 Datos en la tabla Docentes:")
        print(f"   • Total de registros: {total}")
        
        result = connection.execute(text("SELECT DISTINCT FECHA FROM Docentes ORDER BY FECHA"))
        fechas = [row[0] for row in result.fetchall()]
        print(f"   • Años disponibles: {fechas}")
    
    print("\n" + "="*70)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*70)
    
    logger.info(f"Successfully inserted {inseridos} records into Docentes")

except Exception as e:
    print(f"\n❌ Error inesperado: {str(e)}")
    logger.error(f"Unexpected error: {e}", exc_info=True)

finally:
    engine.dispose()
    logger.info("Database connection closed")
