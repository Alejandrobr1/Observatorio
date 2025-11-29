"""
Script para insertar datos de tabla_escuela_nueva.csv en la tabla Escuela_nueva.
Permite la inserción de registros duplicados.
"""

import pandas as pd
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.conexion import engine
from src.config.logger_config import get_logger

logger = get_logger(__name__)

# Definir la ruta del archivo CSV
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ruta_archivo = os.path.join(project_root, "CSVs", "Tabla_escuelas.csv")

print("\n" + "="*70)
print("INSERCIÓN DE DATOS - TABLA ESCUELA_NUEVA")
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

    # Rellenar valores vacíos (NaN) con 0
    df = df.fillna(0)
    print(f"   • Valores vacíos rellenados con 0.")
    
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
            sede = str(row['Sede']).strip() if pd.notna(row['Sede']) else None
            institucion = str(row['Institución educativa']).strip() if pd.notna(row['Institución educativa']) else None
            grupo_1 = int(row['Grupo 1']) if pd.notna(row['Grupo 1']) else None
            grupo_2 = int(row['Grupo 2']) if pd.notna(row['Grupo 2']) else None
            grupo_3 = int(row['Grupo 3']) if pd.notna(row['Grupo 3']) else None
            matriculados = int(row['Matriculados']) if pd.notna(row['Matriculados']) else None
            
            # Validar que los campos requeridos tengan valor
            if None in [fecha, sede, institucion, grupo_1, grupo_2, grupo_3, matriculados] or '' in [sede, institucion]:
                errores.append({
                    'fila': idx + 2,
                    'razon': 'Valores nulos o vacíos',
                    'valores': {
                        'FECHA': fecha,
                        'SEDE': sede,
                        'INSTITUCION_EDUCATIVA': institucion,
                        'GRUPO_1': grupo_1,
                        'GRUPO_2': grupo_2,
                        'GRUPO_3': grupo_3,
                        'MATRICULADOS': matriculados
                    }
                })
                continue
            
            registros.append({
                'FECHA': fecha,
                'SEDE': sede,
                'INSTITUCION_EDUCATIVA': institucion,
                'GRUPO_1': grupo_1,
                'GRUPO_2': grupo_2,
                'GRUPO_3': grupo_3,
                'MATRICULADOS': matriculados
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
                    """INSERT INTO Escuela_nueva 
                       (FECHA, SEDE, INSTITUCION_EDUCATIVA, GRUPO_1, GRUPO_2, GRUPO_3, MATRICULADOS)
                       VALUES (:fecha, :sede, :institucion, :g1, :g2, :g3, :matriculados)"""
                ), {
                    'fecha': reg['FECHA'],
                    'sede': reg['SEDE'],
                    'institucion': reg['INSTITUCION_EDUCATIVA'],
                    'g1': reg['GRUPO_1'],
                    'g2': reg['GRUPO_2'],
                    'g3': reg['GRUPO_3'],
                    'matriculados': reg['MATRICULADOS']
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
        total_query = connection.execute(text("SELECT COUNT(*) FROM Escuela_nueva"))
        total = total_query.scalar()
        
        # Distribución por año
        print(f"\n📈 Distribución de datos en Escuela_nueva:")
        print(f"   • Total de registros: {total}")
        
        # Verificar año
        año_query = connection.execute(text(
            "SELECT FECHA, COUNT(*) as cantidad FROM Escuela_nueva GROUP BY FECHA ORDER BY FECHA DESC"
        ))
        for row in año_query:
            print(f"   • Año {row[0]}: {row[1]} registros")
            
        # Mostrar todas las filas insertadas en la base de datos
        print("\n📋 Filas en la tabla Escuela_nueva:")
        select_all_query = text("SELECT * FROM Escuela_nueva")
        result = connection.execute(select_all_query)
        
        # Obtener nombres de columnas y mostrarlos como encabezado
        column_names = result.keys()
        header = " | ".join([f"{name:<25}" for name in column_names])
        print(header)
        print("-" * len(header))
        
        # Mostrar cada fila
        for row in result:
            print(" | ".join([f"{str(value):<25}" for value in row]))
    
    print("\n" + "="*70)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*70)
    
    logger.info(f"Successfully inserted {inseridos} records into Escuela_nueva. No duplicate check performed.")

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
