"""
Script para insertar datos de Tabla_grados_2021_2025.csv en la tabla Grados_2021_2025
"""

import pandas as pd
import os
import sys
from sqlalchemy import text

# Añadir el directorio raíz del proyecto ('Observatorio') al path de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.database.conexion import engine
from src.config.logger_config import get_logger

logger = get_logger(__name__)

# Definir la ruta del archivo CSV
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ruta_archivo = os.path.join(project_root, "data", "csv", "Tabla_grados_2021_2025.csv")

print("\n" + "="*70)
print("INSERCIÓN DE DATOS - TABLA GRADOS_2021_2025")
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
    
    nulls_por_columna = df.isnull().sum()
    if nulls_por_columna.sum() > 0:
        print("  ⚠️ Advertencia: Se encontraron valores nulos:")
        for col, count in nulls_por_columna[nulls_por_columna > 0].items():
            print(f"     • {col}: {count} valores")
    else:
        print("  ✓ No hay valores nulos")
    
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
            etapa = int(row['Etapa']) if pd.notna(row['Etapa']) else None
            grado = str(row['Grado']).strip() if pd.notna(row['Grado']) else None
            matriculados = int(row['Matriculados']) if pd.notna(row['Matriculados']) else None
            
            registros.append({
                'FECHA': fecha,
                'ETAPA': etapa,
                'GRADO': grado,
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
    
    # --- INICIO: Eliminar datos existentes ---
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            print(f"   • Limpiando datos antiguos de la tabla 'Grados_2021_2025'...")
            connection.execute(text("DELETE FROM Grados_2021_2025"))
            transaction.commit()
            print(f"   ✓ Datos antiguos eliminados.")
        except Exception as e:
            transaction.rollback()
            print(f"   ✗ Error al limpiar la tabla: {e}")
            raise
    # --- FIN: Eliminar datos existentes ---

    with engine.connect() as connection:
        inseridos = 0
        
        for reg in registros:
            try:
                # Insertar registro
                connection.execute(text(
                    """INSERT INTO Grados_2021_2025 
                       (FECHA, ETAPA, GRADO, MATRICULADOS)
                       VALUES (:fecha, :etapa, :grado, :matriculados)"""
                ), {
                    'fecha': reg['FECHA'],
                    'etapa': reg['ETAPA'],
                    'grado': reg['GRADO'],
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
        total_query = connection.execute(text("SELECT COUNT(*) FROM Grados_2021_2025"))
        total = total_query.scalar()
        
        print(f"\n📈 Distribución de datos en Grados_2021_2025:")
        print(f"   • Total de registros: {total}")
        
        año_query = connection.execute(text(
            "SELECT FECHA, SUM(MATRICULADOS) as total_matriculados FROM Grados_2021_2025 GROUP BY FECHA"
        ))
        for row in año_query:
            print(f"   • Año {row[0]}: {row[1]:,} matriculados")
        
        grado_query = connection.execute(text(
            "SELECT GRADO, SUM(MATRICULADOS) as total_matriculados FROM Grados_2021_2025 GROUP BY GRADO ORDER BY total_matriculados DESC LIMIT 5"
        ))
        print(f"\n   Grados con más matriculados (top 5):")
        for row in grado_query:
            print(f"      • Grado {row[0]}: {row[1]:,} matriculados")
    
    print("\n" + "="*70)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*70)
    
    logger.info(f"Successfully inserted {inseridos} records into Grados_2021_2025")

except FileNotFoundError:
    print(f"\n❌ Error: Archivo no encontrado")
    print(f"   Ruta esperada: {ruta_archivo}")
    logger.error(f"File not found: {ruta_archivo}", exc_info=True)
    
except Exception as e:
    print(f"\n❌ Error inesperado: {str(e)}")
    print(f"   Tipo: {type(e).__name__}")
    logger.error(f"Unexpected error: {e}", exc_info=True)

finally:
    engine.dispose()
    logger.info("Database connection closed")