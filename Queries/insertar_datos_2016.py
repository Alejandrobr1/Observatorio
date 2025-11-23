"""
Script para insertar datos de tabla_2016.csv en la tabla Estudiantes_2016
Nueva estructura: Tablas independientes por años sin valores vacíos ni nulos
"""

import pandas as pd
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Base_datos.conexion import engine
from logger_config import get_logger

logger = get_logger(__name__)

# Definir la ruta del archivo CSV
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ruta_archivo = os.path.join(project_root, "CSVs", "tabla_2016.csv")

print("\n" + "="*70)
print("INSERCIÓN DE DATOS - TABLA ESTUDIANTES_2016")
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
            fecha = int(row['Año']) if pd.notna(row['Año']) else None
            sede_nodal = str(row['Sede Nodal']).strip() if pd.notna(row['Sede Nodal']) else None
            poblacion = str(row['Población']).strip() if pd.notna(row['Población']) else None
            nivel = int(row['Nivel']) if pd.notna(row['Nivel']) else None
            dia = str(row['Día']).strip() if pd.notna(row['Día']) else None
            jornada = str(row['Jornada']).strip() if pd.notna(row['Jornada']) else None
            matriculados = int(row['Matriculados']) if pd.notna(row['Matriculados']) else None
            etapa = int(row['Etapa']) if pd.notna(row['Etapa']) else None
            
            # Validar que los campos requeridos tengan valor
            if None in [fecha, sede_nodal, poblacion, nivel, dia, jornada, matriculados, etapa]:
                errores.append({
                    'fila': idx + 2,
                    'razon': 'Valores nulos o vacíos',
                    'valores': {
                        'FECHA': fecha,
                        'SEDE_NODAL': sede_nodal,
                        'POBLACION': poblacion,
                        'NIVEL': nivel,
                        'DIA': dia,
                        'JORNADA': jornada,
                        'MATRICULADOS': matriculados,
                        'ETAPA': etapa
                    }
                })
                continue
            
            registros.append({
                'FECHA': fecha,
                'SEDE_NODAL': sede_nodal,
                'POBLACION': poblacion,
                'NIVEL': nivel,
                'DIA': dia,
                'JORNADA': jornada,
                'MATRICULADOS': matriculados,
                'ETAPA': etapa
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
        duplicados = 0
        
        for reg in registros:
            try:
                # Verificar si el registro ya existe
                resultado = connection.execute(text(
                    """SELECT COUNT(*) FROM Estudiantes_2016 
                       WHERE FECHA = :fecha 
                       AND SEDE_NODAL = :sede_nodal 
                       AND POBLACION = :poblacion 
                       AND NIVEL = :nivel 
                       AND DIA = :dia 
                       AND JORNADA = :jornada 
                       AND ETAPA = :etapa"""
                ), {
                    'fecha': reg['FECHA'],
                    'sede_nodal': reg['SEDE_NODAL'],
                    'poblacion': reg['POBLACION'],
                    'nivel': reg['NIVEL'],
                    'dia': reg['DIA'],
                    'jornada': reg['JORNADA'],
                    'etapa': reg['ETAPA']
                })
                
                count = resultado.scalar()
                
                if count > 0:
                    duplicados += 1
                    continue
                
                # Insertar nuevo registro
                connection.execute(text(
                    """INSERT INTO Estudiantes_2016 
                       (FECHA, SEDE_NODAL, POBLACION, NIVEL, DIA, JORNADA, MATRICULADOS, ETAPA)
                       VALUES (:fecha, :sede_nodal, :poblacion, :nivel, :dia, :jornada, :matriculados, :etapa)"""
                ), {
                    'fecha': reg['FECHA'],
                    'sede_nodal': reg['SEDE_NODAL'],
                    'poblacion': reg['POBLACION'],
                    'nivel': reg['NIVEL'],
                    'dia': reg['DIA'],
                    'jornada': reg['JORNADA'],
                    'matriculados': reg['MATRICULADOS'],
                    'etapa': reg['ETAPA']
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
    print(f"   • Registros duplicados: {duplicados}")
    print(f"   • Registros con error: {len(errores)}")
    
    # Mostrar estadísticas de los datos insertados
    with engine.connect() as connection:
        # Total de registros
        total_query = connection.execute(text("SELECT COUNT(*) FROM Estudiantes_2016"))
        total = total_query.scalar()
        
        # Distribución por año
        print(f"\n📈 Distribución de datos en Estudiantes_2016:")
        print(f"   • Total de registros: {total}")
        
        # Verificar año
        año_query = connection.execute(text(
            "SELECT DISTINCT FECHA, COUNT(*) as cantidad FROM Estudiantes_2016 GROUP BY FECHA"
        ))
        for row in año_query:
            print(f"   • Año {row[0]}: {row[1]} registros")
        
        # Distribución por población
        pob_query = connection.execute(text(
            "SELECT POBLACION, COUNT(*) as cantidad FROM Estudiantes_2016 GROUP BY POBLACION ORDER BY cantidad DESC LIMIT 5"
        ))
        print(f"\n   Población (top 5):")
        for i, row in enumerate(pob_query):
            print(f"      • {row[0]}: {row[1]}")
        
        # Distribución por nivel
        nivel_query = connection.execute(text(
            "SELECT NIVEL, COUNT(*) as cantidad FROM Estudiantes_2016 GROUP BY NIVEL ORDER BY NIVEL"
        ))
        print(f"\n   Niveles:")
        for row in nivel_query:
            print(f"      • Nivel {row[0]}: {row[1]} registros")
        
        # Distribución por día
        dia_query = connection.execute(text(
            "SELECT DIA, COUNT(*) as cantidad FROM Estudiantes_2016 GROUP BY DIA ORDER BY cantidad DESC"
        ))
        print(f"\n   Días:")
        for row in dia_query:
            print(f"      • {row[0]}: {row[1]}")
    
    print("\n" + "="*70)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*70)
    
    logger.info(f"Successfully inserted {inseridos} records into Estudiantes_2016")

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
