"""
Script para insertar datos de tabla_docentes.csv en la tabla Docentes.
Verifica la existencia del docente por ID antes de insertar o actualizar.
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
ruta_archivo = os.path.join(project_root, "CSVs", "tabla_docentes.csv")

print("\n" + "="*70)
print("INSERCIÓN DE DATOS - TABLA DOCENTES")
print("="*70)

try:
    # Leer el CSV
    print(f"\n📂 Leyendo archivo: {ruta_archivo}")
    df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig', dtype={'ID_DOCENTE': str, 'ID_INSTITUCION': str})
    
    print(f"✓ Archivo cargado exitosamente")
    print(f"   • Total de filas (antes de limpieza): {len(df)}")
    print(f"   • Total de columnas: {len(df.columns)}")
    print(f"   • Columnas: {list(df.columns)}")
    
    df = df.dropna(how='all')
    print(f"   • Total de filas (después de eliminar filas vacías): {len(df)}")
    
    print(f"\n🔍 Validando datos...")
    
    nulls_por_columna = df.isnull().sum()
    if nulls_por_columna.sum() > 0:
        print("  ⚠️ Advertencia: Se encontraron valores nulos:")
        for col, count in nulls_por_columna[nulls_por_columna > 0].items():
            print(f"     • {col}: {count} valores")
    else:
        print("  ✓ No hay valores nulos")

    print(f"\n📋 Primeras 5 filas del CSV:")
    print(df.head().to_string())
    
    print(f"\n🔄 Preparando datos para inserción...")
    
    registros = []
    errores = []
    
    for idx, row in df.iterrows():
        try:
            id_docente = str(row['ID_DOCENTE']).strip() if pd.notna(row['ID_DOCENTE']) else None
            nombre = str(row['NOMBRE']).strip() if pd.notna(row['NOMBRE']) else None
            apellido = str(row['APELLIDO']).strip() if pd.notna(row['APELLIDO']) else None
            email = str(row['EMAIL']).strip() if pd.notna(row['EMAIL']) else None
            id_institucion = str(row['ID_INSTITUCION']).strip() if pd.notna(row['ID_INSTITUCION']) else None
            
            if None in [id_docente, nombre, apellido, email, id_institucion]:
                errores.append({
                    'fila': idx + 2,
                    'razon': 'Valores nulos o vacíos en campos requeridos',
                    'valores': row.to_dict()
                })
                continue
            
            registros.append({
                'ID_DOCENTE': id_docente,
                'NOMBRE': nombre,
                'APELLIDO': apellido,
                'EMAIL': email,
                'ID_INSTITUCION': id_institucion
            })
        
        except Exception as e:
            errores.append({'fila': idx + 2, 'razon': str(e), 'valores': row.to_dict()})
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
    
    print(f"\n💾 Insertando {len(registros)} registros en la base de datos...")
    
    with engine.connect() as connection:
        inseridos = 0
        actualizados = 0
        
        for reg in registros:
            try:
                existe_query = text("SELECT ID_DOCENTE FROM Docentes WHERE ID_DOCENTE = :id")
                existe = connection.execute(existe_query, {'id': reg['ID_DOCENTE']}).fetchone()

                if existe:
                    update_query = text("""
                        UPDATE Docentes SET NOMBRE = :nombre, APELLIDO = :apellido, EMAIL = :email, ID_INSTITUCION = :id_inst
                        WHERE ID_DOCENTE = :id
                    """)
                    connection.execute(update_query, {'nombre': reg['NOMBRE'], 'apellido': reg['APELLIDO'], 'email': reg['EMAIL'], 'id_inst': reg['ID_INSTITUCION'], 'id': reg['ID_DOCENTE']})
                    actualizados += 1
                else:
                    insert_query = text("""
                        INSERT INTO Docentes (ID_DOCENTE, NOMBRE, APELLIDO, EMAIL, ID_INSTITUCION)
                        VALUES (:id, :nombre, :apellido, :email, :id_inst)
                    """)
                    connection.execute(insert_query, {'id': reg['ID_DOCENTE'], 'nombre': reg['NOMBRE'], 'apellido': reg['APELLIDO'], 'email': reg['EMAIL'], 'id_inst': reg['ID_INSTITUCION']})
                    inseridos += 1
                
                if (inseridos + actualizados) % 100 == 0:
                    connection.commit()
                    print(f"   ✓ {inseridos + actualizados} registros procesados...")
            
            except Exception as e:
                print(f"   ✗ Error al procesar registro: {str(e)[:100]}")
                connection.rollback()
                logger.error(f"Error processing record: {e}", exc_info=True)
        
        connection.commit()
        print(f"\n✓ Proceso completado en la base de datos")
    
    print(f"\n📊 Estadísticas de inserción:")
    print(f"   • Registros insertados: {inseridos}")
    print(f"   • Registros actualizados: {actualizados}")
    print(f"   • Registros con error: {len(errores)}")
    
    with engine.connect() as connection:
        total = connection.execute(text("SELECT COUNT(*) FROM Docentes")).scalar()
        print(f"\n📈 Datos en la tabla Docentes:")
        print(f"   • Total de registros: {total}")
    
    print("\n" + "="*70)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*70)
    
    logger.info(f"Successfully inserted {inseridos} and updated {actualizados} records into Docentes")

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