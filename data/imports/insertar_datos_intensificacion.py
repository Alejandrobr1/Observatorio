"""
Script para insertar datos de Tabla_datos_intensificacion.csv en la tabla Estudiantes_intensificacion
"""

import pandas as pd
import os
import sys
from sqlalchemy import text



# Añadir el directorio raíz del proyecto ('Observatorio') al path de Python
# Se suben dos niveles desde 'data/imports' para llegar a la raíz.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.database.conexion import engine
from src.config.logger_config import get_logger

logger = get_logger(__name__)

# Definir la ruta del archivo CSV de forma robusta desde la raíz del proyecto
# El script está en 'data/imports', así que subimos dos niveles para llegar a 'Observatorio'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ruta_archivo = os.path.join(project_root, "data", "csv", "Tabla_intensificacion.csv")

print("\n" + "="*70)
print("INSERCIÓN DE DATOS - TABLA ESTUDIANTES_INTENSIFICACION")
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
            institucion_educativa = str(row['Institución Educativa']).strip() if pd.notna(row['Institución Educativa']) else None
            poblacion = str(row['Población']).strip() if pd.notna(row['Población']) else None
            grado = str(row['Grado']).strip() if pd.notna(row['Grado']) else None
            jornada = str(row['Jornada']).strip() if pd.notna(row['Jornada']) else None
            nivel_mcer = str(row['NIVEL_MCER']).strip() if pd.notna(row['NIVEL_MCER']) else None
            idioma = str(row['IDIOMA']).strip() if pd.notna(row['IDIOMA']) else None
            
            registros.append({
                'FECHA': fecha,
                'INSTITUCION_EDUCATIVA': institucion_educativa,
                'POBLACION': poblacion,
                'GRADO': grado,
                'JORNADA': jornada,
                'NIVEL_MCER': nivel_mcer,
                'IDIOMA': idioma
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
        
        for reg in registros:
            try:
                # Insertar registro sin verificar duplicados
                # Se permiten valores duplicados tal como vienen en el Excel
                connection.execute(text(
                    """INSERT INTO Estudiantes_intensificacion 
                       (FECHA, INSTITUCION_EDUCATIVA, POBLACION, GRADO, JORNADA, NIVEL_MCER, IDIOMA)
                       VALUES (:fecha, :institucion_educativa, :poblacion, :grado, :jornada, :nivel_mcer, :idioma)"""
                ), {
                    'fecha': reg['FECHA'],
                    'institucion_educativa': reg['INSTITUCION_EDUCATIVA'],
                    'poblacion': reg['POBLACION'],
                    'grado': reg['GRADO'],
                    'jornada': reg['JORNADA'],
                    'nivel_mcer': reg['NIVEL_MCER'],
                    'idioma': reg['IDIOMA']
                })
                
                inseridos += 1
                
                # Commit cada 100 registros
                if inseridos % 100 == 0:
                    connection.commit()
                    print(f"   ✓ {inseridos} registros procesados...")
            
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
    print(f"   • Registros con error: {len(errores)}")
    
    # Mostrar estadísticas de los datos insertados
    with engine.connect() as connection:
        # Total de registros
        total_query = connection.execute(text("SELECT COUNT(*) FROM Estudiantes_intensificacion"))
        total = total_query.scalar()
        
        # Distribución por año
        print(f"\n📈 Distribución de datos en Estudiantes_intensificacion:")
        print(f"   • Total de registros: {total}")
        
        # Verificar año
        año_query = connection.execute(text(
            "SELECT DISTINCT FECHA, COUNT(*) as cantidad FROM Estudiantes_intensificacion GROUP BY FECHA"
        ))
        for row in año_query:
            print(f"   • Año {row[0]}: {row[1]} registros")
        
        # Distribución por población
        pob_query = connection.execute(text(
            "SELECT POBLACION, COUNT(*) as cantidad FROM Estudiantes_intensificacion GROUP BY POBLACION ORDER BY cantidad DESC LIMIT 5"
        ))
        print(f"\n   Población (top 5):")
        for i, row in enumerate(pob_query):
            print(f"      • {row[0]}: {row[1]}")
        
        # Distribución por grado
        grado_query = connection.execute(text(
            "SELECT GRADO, COUNT(*) as cantidad FROM Estudiantes_intensificacion GROUP BY GRADO ORDER BY GRADO"
        ))
        print(f"\n   Grados:")
        for row in grado_query:
            print(f"      • Grado {row[0]}: {row[1]} registros")
        
        # Distribución por jornada
        jornada_query = connection.execute(text(
            "SELECT JORNADA, COUNT(*) as cantidad FROM Estudiantes_intensificacion GROUP BY JORNADA ORDER BY cantidad DESC"
        ))
        print(f"\n   Jornadas:")
        for row in jornada_query:
            print(f"      • {row[0]}: {row[1]}")
    
    print("\n" + "="*70)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*70)
    
    logger.info(f"Successfully inserted {inseridos} records into Estudiantes_intensificacion")

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
