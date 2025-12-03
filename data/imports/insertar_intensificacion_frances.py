"""
Script para insertar datos de Tabla_intensificacion_frances.csv en la tabla Frances_intensificacion
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
ruta_archivo = os.path.join(project_root, "data", "csv", "Tabla_intensificacion_frances.csv")

print("\n" + "="*70)
print("INSERCIÓN DE DATOS - TABLA FRANCES_INTENSIFICACION")
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

    # Rellenar valores NaN para evitar errores de conversión
    # Columnas numéricas
    numeric_cols = ['Año', 'Horas', 'Matriculados']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    # Columnas de texto
    text_cols = ['Sede Nodal', 'Sede', 'Grado', 'Idioma', 'Nivel MCER', 'Día', 'Jornada', 'Nivel']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna('')
    
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
            def clean_text(value):
                if pd.isna(value) or str(value).strip().upper() in ['', 'SIN INFORMACION', 'NAN']:
                    return None
                return str(value).strip()

            def clean_int(value):
                if pd.isna(value):
                    return 0
                return int(value)

            fecha = clean_int(row.get('Año', 0))
            sede_nodal = clean_text(row.get('Sede Nodal'))
            sede = clean_text(row.get('Sede'))
            grado = clean_text(row.get('Grado'))
            idioma = clean_text(row.get('Idioma'))
            nivel_mcer = clean_text(row.get('Nivel MCER'))
            horas = clean_int(row.get('Horas', 0))
            dia = clean_text(row.get('Día'))
            jornada = clean_text(row.get('Jornada'))
            matriculados = clean_int(row.get('Matriculados', 0))
            nivel = clean_text(row.get('Nivel'))
            
            registros.append({
                'FECHA': fecha,
                'SEDE_NODAL': sede_nodal,
                'SEDE': sede,
                'GRADO': grado,
                'IDIOMA': idioma,
                'NIVEL_MCER': nivel_mcer,
                'HORAS': horas,
                'DIA': dia,
                'JORNADA': jornada,
                'MATRICULADOS': matriculados,
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
    
    # --- INICIO: Eliminar datos existentes ---
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            print(f"   • Limpiando datos antiguos de la tabla 'Frances_intensificacion'...")
            connection.execute(text("DELETE FROM Frances_intensificacion"))
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
                    """INSERT INTO Frances_intensificacion 
                       (FECHA, SEDE_NODAL, SEDE, GRADO, IDIOMA, NIVEL_MCER, HORAS, DIA, JORNADA, MATRICULADOS, NIVEL)
                       VALUES (:fecha, :sede_nodal, :sede, :grado, :idioma, :nivel_mcer, :horas, :dia, :jornada, :matriculados, :nivel)"""
                ), {
                    'fecha': reg['FECHA'],
                    'sede_nodal': reg['SEDE_NODAL'],
                    'sede': reg['SEDE'],
                    'grado': reg['GRADO'],
                    'idioma': reg['IDIOMA'],
                    'nivel_mcer': reg['NIVEL_MCER'],
                    'horas': reg['HORAS'],
                    'dia': reg['DIA'],
                    'jornada': reg['JORNADA'],
                    'matriculados': reg['MATRICULADOS'],
                    'nivel': reg['NIVEL']
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
        total_query = connection.execute(text("SELECT COUNT(*) FROM Frances_intensificacion"))
        total = total_query.scalar()
        
        print(f"\n📈 Distribución de datos en Frances_intensificacion:")
        print(f"   • Total de registros: {total}")
        
        año_query = connection.execute(text(
            "SELECT FECHA, SUM(MATRICULADOS) as total_matriculados FROM Frances_intensificacion GROUP BY FECHA"
        ))
        for row in año_query:
            print(f"   • Año {row[0]}: {row[1]:,} matriculados")
        
        idioma_query = connection.execute(text(
            "SELECT IDIOMA, SUM(MATRICULADOS) as total_matriculados FROM Frances_intensificacion GROUP BY IDIOMA ORDER BY total_matriculados DESC"
        ))
        print(f"\n   Matriculados por Idioma:")
        for row in idioma_query:
            print(f"      • {row[0]}: {row[1]:,} matriculados")
    
    print("\n" + "="*70)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*70)
    
    logger.info(f"Successfully inserted {inseridos} records into Frances_intensificacion")

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