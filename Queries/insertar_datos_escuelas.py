"""
Script para insertar datos de tabla_escuelas.csv en la tabla Instituciones.
Verifica si la tabla existe y la crea si es necesario.
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
ruta_archivo = os.path.join(project_root, "CSVs", "tabla_escuelas.csv")

print("\n" + "="*70)
print("INSERCIÓN DE DATOS - TABLA INSTITUCIONES")
print("="*70)

def crear_tabla_si_no_existe(engine):
    """Verifica si la tabla 'Instituciones' existe y la crea si no."""
    create_table_query = text("""
    CREATE TABLE IF NOT EXISTS Instituciones (
        ID_INSTITUCION VARCHAR(255) PRIMARY KEY,
        NOMBRE_INSTITUCION VARCHAR(255) NOT NULL,
        SEDE VARCHAR(255),
        SECTOR VARCHAR(50),
        ZONA VARCHAR(50)
    );
    """)
    try:
        with engine.connect() as connection:
            connection.execute(create_table_query)
            connection.commit()
        print("✓ Tabla 'Instituciones' verificada/creada exitosamente.")
    except Exception as e:
        print(f"❌ Error al crear/verificar la tabla 'Instituciones': {e}")
        raise

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
    
    print(f"\n🔍 Validando datos...")
    
    nulls_por_columna = df.isnull().sum()
    if nulls_por_columna.sum() > 0:
        print("  ⚠️ Advertencia: Se encontraron valores nulos:")
        for col, count in nulls_por_columna[nulls_por_columna > 0].items():
            print(f"     • {col}: {count} valores")
    print(f"\n📋 Primeras 5 filas del CSV:")
    print(df.head().to_string())
    
    print(f"\n🔄 Preparando datos para inserción...")
    
    # Crear lista de registros para inserción
    registros = []
    errores = []
    
    for idx, row in df.iterrows():
        try:
            # Mapeo de las columnas del CSV a las de la tabla
            nombre_institucion = str(row['Institución educativa']).strip() if pd.notna(row['Institución educativa']) else None
            sede = str(row['Sede']).strip() if pd.notna(row['Sede']) else None
            
            # Generar un ID único basado en el nombre y la sede
            id_institucion = f"{nombre_institucion}-{sede}".lower().replace(" ", "-")
            
            # Validar que los campos requeridos tengan valor
            if not nombre_institucion or not sede:
                errores.append({
                    'fila': idx + 2,
                    'razon': 'Valores nulos o vacíos en "Institución educativa" o "Sede"',
                    'valores': {
                        'Institución educativa': nombre_institucion, 'Sede': sede
                    }
                })
                continue
            
            registros.append({
                'ID_INSTITUCION': id_institucion,
                'NOMBRE_INSTITUCION': nombre_institucion,
                'SEDE': sede,
                'SECTOR': 'OFICIAL', # Valor por defecto, ajustar si es necesario
                'ZONA': 'URBANA'     # Valor por defecto, ajustar si es necesario
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
    
    # Crear la tabla si no existe
    crear_tabla_si_no_existe(engine)

    # Insertar en la base de datos
    print(f"\n💾 Insertando {len(registros)} registros en la base de datos...")
    
    with engine.connect() as connection:
        inseridos = 0
        actualizados = 0
        
        for reg in registros:
            try:
                # Verificar si la institución ya existe
                existe_query = text("SELECT ID_INSTITUCION FROM Instituciones WHERE ID_INSTITUCION = :id")
                existe = connection.execute(existe_query, {'id': reg['ID_INSTITUCION']}).fetchone()

                if existe:
                    # Actualizar registro existente
                    update_query = text("""
                        UPDATE Instituciones SET NOMBRE_INSTITUCION = :nombre, SEDE = :sede, SECTOR = :sector, ZONA = :zona
                        WHERE ID_INSTITUCION = :id
                    """)
                    connection.execute(update_query, {'nombre': reg['NOMBRE_INSTITUCION'], 'sede': reg['SEDE'], 'sector': reg['SECTOR'], 'zona': reg['ZONA'], 'id': reg['ID_INSTITUCION']})
                    actualizados += 1
                else:
                    # Insertar nuevo registro
                    insert_query = text("""
                        INSERT INTO Instituciones (ID_INSTITUCION, NOMBRE_INSTITUCION, SEDE, SECTOR, ZONA)
                        VALUES (:id, :nombre, :sede, :sector, :zona)
                    """)
                    connection.execute(insert_query, {'id': reg['ID_INSTITUCION'], 'nombre': reg['NOMBRE_INSTITUCION'], 'sede': reg['SEDE'], 'sector': reg['SECTOR'], 'zona': reg['ZONA']})
                    inseridos += 1
                
                # Commit cada 100 registros
                if (inseridos + actualizados) % 100 == 0:
                    connection.commit()
                    print(f"   ✓ {inseridos + actualizados} registros procesados...")
            
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
    print(f"   • Registros actualizados: {actualizados}")
    print(f"   • Registros con error: {len(errores)}")
    
    # Mostrar estadísticas de los datos insertados
    with engine.connect() as connection:
        # Total de registros
        total_query = connection.execute(text("SELECT COUNT(*) FROM Instituciones"))
        total = total_query.scalar()
        
        print(f"\n📈 Distribución de datos en Instituciones:")
        print(f"   • Total de registros: {total}")
        
        # Distribución por sector
        sector_query = connection.execute(text("SELECT SECTOR, COUNT(*) as cantidad FROM Instituciones GROUP BY SECTOR"))
        print(f"\n   Distribución por Sector:")
        for row in sector_query:
            print(f"      • {row[0]}: {row[1]} instituciones")
    
    print("\n" + "="*70)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*70)
    
    logger.info(f"Successfully inserted {inseridos} and updated {actualizados} records into Instituciones")

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
