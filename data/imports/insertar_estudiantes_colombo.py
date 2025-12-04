"""
Script para insertar datos de tabla_estudiantes_colombo.csv en la tabla Estudiantes_Colombo.
Permite la inserción de registros duplicados.
"""

import pandas as pd
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.database.conexion import engine
from src.config.logger_config import get_logger

logger = get_logger(__name__)

# Definir la ruta del archivo CSV
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ruta_archivo = os.path.join(project_root, "data", "csv", "Tabla_colombo.csv")

print("\n" + "="*70)
print("INSERCIÓN DE DATOS - TABLA ESTUDIANTES COLOMBO")
print("="*70)

try:
    # Leer el CSV
    print(f"\n📂 Leyendo archivo: {ruta_archivo}")
    df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')
    
    print(f"✓ Archivo cargado exitosamente")
    print(f"   • Total de filas (antes de limpieza): {len(df)}")
    print(f"   • Total de columnas: {len(df.columns)}")
    print(f"   • Columnas: {list(df.columns)}")
    
    # Limpiar filas completamente vacías
    df = df.dropna(how='all')
    print(f"   • Total de filas (después de eliminar filas vacías): {len(df)}")
    
    # Validar que el CSV no tenga valores vacíos ni nulos
    print(f"\n🔍 Validando datos...")
    
    # Verificar valores nulos
    nulls_por_columna = df.isnull().sum()
    if nulls_por_columna.sum() > 0:
        print("  ⚠️ Advertencia: Se encontraron valores nulos:")
        for col, count in nulls_por_columna[nulls_por_columna > 0].items():
            print(f"     • {col}: {count} valores")
    else:
        print("  ✓ No hay valores nulos")
    
    # Verificar valores vacíos (ahora sin usar .astype(str).str que causaba error)
    vacios_por_columna = df.isnull().sum()
    if vacios_por_columna.sum() > 0:
        print("  ⚠️ Advertencia: Se encontraron valores vacíos:")
        for col, count in vacios_por_columna[vacios_por_columna > 0].items():
            print(f"     • {col}: {count} valores")
    else:
        print("  ✓ No hay valores vacíos")
    
    # Mostrar sample de datos
    print(f"\n📋 Primeras 5 filas del CSV:")
    print(df.head().to_string())
    
    print(f"\n🔄 Preparando datos para inserción...")
    
    # Crear lista de registros para inserción
    registros = []
    errores = []
    
    for idx, row in df.iterrows():
        try:
            # Extraer y convertir valores según la estructura de la tabla
            fecha = int(row['FECHA']) if pd.notna(row['FECHA']) else None
            institucion = str(row['INSTITUCIÓN EDUCATIVA']).strip() if pd.notna(row['INSTITUCIÓN EDUCATIVA']) else None
            nivel = str(row['NIVEL_MCER']).strip() if pd.notna(row['NIVEL_MCER']) else None
            
            # Validar que los campos requeridos tengan valor
            if None in [fecha, institucion, nivel] or '' in [institucion, nivel]:
                errores.append({
                    'fila': idx + 2,
                    'razon': 'Valores nulos o vacíos',
                    'valores': {
                        'FECHA': fecha,
                        'INSTITUCION_EDUCATIVA': institucion,
                        'NIVEL': nivel
                    }
                })
                continue
            
            registros.append({
                'FECHA': fecha,
                'INSTITUCION_EDUCATIVA': institucion,
                'NIVEL': nivel
            })
        
        except Exception as e:
            errores.append({
                'fila': idx + 2,
                'razon': str(e),
                'valores': row.to_dict()
            })
            continue
    
    print(f"✓ Datos preparados")
    print(f"   • Registros válidos: {len(registros)}")
    print(f"   • Registros con error: {len(errores)}")
    
    if errores:
        print(f"\n⚠️ Errores encontrados:")
        for error in errores[:5]:
            print(f"   Fila {error['fila']}: {error['razon']}")
        if len(errores) > 5:
            print(f"   ... y {len(errores) - 5} errores más")
    
    # Insertar en la base de datos
    print(f"\n💾 Insertando {len(registros)} registros en la base de datos...")
    
    with engine.connect() as connection:
        inseridos = 0
        omitidos = 0
        
        for reg in registros:
            try:
                # Insertar registro (ahora sin verificar duplicados)
                insert_query = text("""
                    INSERT INTO Estudiantes_Colombo (FECHA, INSTITUCION_EDUCATIVA, NIVEL)
                    VALUES (:fecha, :institucion, :nivel)
                """)
                connection.execute(insert_query, {
                    'fecha': reg['FECHA'], 'institucion': reg['INSTITUCION_EDUCATIVA'], 'nivel': reg['NIVEL']
                })
                
                inseridos += 1
                
                # Commit cada 100 registros
                if (inseridos + omitidos) % 100 == 0:
                    connection.commit()
                    print(f"   ✓ {inseridos + omitidos} registros procesados...")
            
            except Exception as e:
                print(f"   ✗ Error al insertar: {str(e)[:100]}")
                connection.rollback()
                logger.error(f"Error inserting record: {e}", exc_info=True)
        
        # Commit final
        connection.commit()
        print(f"\n✓ Inserción completada en la base de datos")
    
    # Verificar resultados
    print(f"\n📊 Estadísticas de inserción:")
    print(f"   • Registros insertados: {inseridos}")
    print(f"   • Registros omitidos (por error): {omitidos}") # Se mantiene 'omitidos' pero ahora solo cuenta errores lógicos
    print(f"   • Registros con error: {len(errores)}")
    
    # Mostrar estadísticas de los datos insertados
    with engine.connect() as connection:
        # Total de registros
        total_query = connection.execute(text("SELECT COUNT(*) FROM Estudiantes_Colombo"))
        total = total_query.scalar()
        
        # Distribución por año
        print(f"\n📈 Distribución de datos en Estudiantes_Colombo:")
        print(f"   • Total de registros: {total}")
        
        # Verificar año
        año_query = connection.execute(text(
            "SELECT FECHA, COUNT(*) as cantidad FROM Estudiantes_Colombo GROUP BY FECHA ORDER BY FECHA DESC"
        ))
        for row in año_query:
            print(f"   • Año {row[0]}: {row[1]} registros")
        
        # Distribución por nivel
        nivel_query = connection.execute(text(
            "SELECT NIVEL, COUNT(*) as cantidad FROM Estudiantes_Colombo GROUP BY NIVEL ORDER BY cantidad DESC LIMIT 5"
        ))
        print(f"\n   Niveles (top 5):")
        for row in nivel_query:
            print(f"      • Nivel {row[0]}: {row[1]} registros")
    
    print("\n" + "="*70)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*70)
    
    logger.info(f"Successfully inserted {inseridos} records into Estudiantes_Colombo. No duplicate check performed.")

except FileNotFoundError:
    print(f"\n❌ Error: Archivo no encontrado")
    print(f"   Ruta esperada: {ruta_archivo}")
    logger.error(f"File not found: {ruta_archivo}", exc_info=True)
    
except pd.errors.EmptyDataError:
    print(f"\n❌ Error: El archivo CSV está vacío")
    logger.error("Empty CSV file", exc_info=True)
    
except Exception as e:
    print(f"\n❌ Error inesperado: {str(e)}")
    print(f"   Tipo: {type(e).__name__}")
    logger.error(f"Unexpected error: {e}", exc_info=True)

finally:
    engine.dispose()
    logger.info("Database connection closed")
