"""
Script genérico para insertar datos de cualquier año en las tablas Estudiantes_YYYY
Este script puede adaptarse para diferentes años cambiendo el nombre del archivo CSV
"""

import pandas as pd
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Base_datos.conexion import engine
from logger_config import get_logger

logger = get_logger(__name__)

def insertar_datos_por_año(archivo_csv, tabla_destino, año=None):
    """
    Función genérica para insertar datos de un CSV a una tabla de estudiantes
    
    Parameters:
    -----------
    archivo_csv : str
        Nombre del archivo CSV en la carpeta CSVs
    tabla_destino : str
        Nombre de la tabla de destino (ej: Estudiantes_2016)
    año : int, optional
        Año específico. Si es None, se extrae del CSV
    """
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    ruta_archivo = os.path.join(project_root, "CSVs", archivo_csv)
    
    print("\n" + "="*70)
    print(f"INSERCIÓN DE DATOS - TABLA {tabla_destino}")
    print("="*70)
    
    try:
        # Leer el CSV
        print(f"\n📂 Leyendo archivo: {ruta_archivo}")
        if not os.path.exists(ruta_archivo):
            raise FileNotFoundError(f"Archivo no encontrado: {ruta_archivo}")
        
        df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')
        
        print(f"✓ Archivo cargado exitosamente")
        print(f"   • Total de filas (antes de limpieza): {len(df)}")
        print(f"   • Total de columnas: {len(df.columns)}")
        print(f"   • Columnas: {list(df.columns)}")
        
        # Limpiar filas completamente vacías
        df = df.dropna(how='all')
        print(f"   • Total de filas (después de eliminar filas vacías): {len(df)}")
        
        if len(df) == 0:
            print("⚠️ Advertencia: No hay datos válidos en el CSV después de la limpieza")
            return
        
        # Mostrar sample de datos
        print(f"\n📋 Primeras 5 filas del CSV:")
        print(df.head().to_string())
        
        print(f"\n🔄 Preparando datos para inserción...")
        
        # Crear lista de registros para inserción
        registros = []
        errores = []
        
        for idx, row in df.iterrows():
            try:
                # Extraer y convertir valores
                fecha = int(row['Año']) if pd.notna(row['Año']) else (año if año else None)
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
                        'razon': 'Valores nulos o vacíos'
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
                    'razon': str(e)
                })
                continue
        
        print(f"✓ Datos preparados")
        print(f"   • Registros válidos: {len(registros)}")
        print(f"   • Registros con error: {len(errores)}")
        
        if errores and len(errores) <= 5:
            print(f"\n⚠️ Errores encontrados:")
            for error in errores:
                print(f"   Fila {error['fila']}: {error['razon']}")
        elif errores:
            print(f"\n⚠️ {len(errores)} errores encontrados")
        
        if len(registros) == 0:
            print("❌ No hay registros válidos para insertar")
            return
        
        # Insertar en la base de datos
        print(f"\n💾 Insertando {len(registros)} registros en {tabla_destino}...")
        
        with engine.connect() as connection:
            inseridos = 0
            duplicados = 0
            
            for reg in registros:
                try:
                    # Verificar si el registro ya existe
                    resultado = connection.execute(text(
                        f"""SELECT COUNT(*) FROM {tabla_destino}
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
                        f"""INSERT INTO {tabla_destino}
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
        
        # Verificar resultados
        print(f"\n✓ Inserción completada en la base de datos")
        print(f"\n📊 Estadísticas de inserción:")
        print(f"   • Registros insertados: {inseridos}")
        print(f"   • Registros duplicados: {duplicados}")
        print(f"   • Registros con error: {len(errores)}")
        
        # Mostrar estadísticas de los datos insertados
        with engine.connect() as connection:
            # Total de registros
            total_query = connection.execute(text(f"SELECT COUNT(*) FROM {tabla_destino}"))
            total = total_query.scalar()
            
            print(f"\n📈 Distribución de datos en {tabla_destino}:")
            print(f"   • Total de registros: {total}")
            
            # Distribución por población
            pob_query = connection.execute(text(
                f"SELECT POBLACION, COUNT(*) as cantidad FROM {tabla_destino} GROUP BY POBLACION ORDER BY cantidad DESC"
            ))
            print(f"\n   Población:")
            for row in pob_query:
                print(f"      • {row[0]}: {row[1]}")
            
            # Distribución por nivel
            nivel_query = connection.execute(text(
                f"SELECT NIVEL, COUNT(*) as cantidad FROM {tabla_destino} GROUP BY NIVEL ORDER BY NIVEL"
            ))
            print(f"\n   Niveles:")
            for row in nivel_query:
                print(f"      • Nivel {row[0]}: {row[1]}")
            
            # Distribución por día
            dia_query = connection.execute(text(
                f"SELECT DIA, COUNT(*) as cantidad FROM {tabla_destino} GROUP BY DIA ORDER BY cantidad DESC"
            ))
            print(f"\n   Días:")
            for row in dia_query:
                print(f"      • {row[0]}: {row[1]}")
            
            # Total de estudiantes matriculados
            total_matr = connection.execute(text(
                f"SELECT SUM(MATRICULADOS) FROM {tabla_destino}"
            ))
            total_matriculados = total_matr.scalar()
            print(f"\n   Total de estudiantes matriculados: {total_matriculados}")
        
        print("\n" + "="*70)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("="*70)
        
        logger.info(f"Successfully inserted {inseridos} records into {tabla_destino}")
        
        return {'insertados': inseridos, 'duplicados': duplicados, 'errores': len(errores)}

    except FileNotFoundError as e:
        print(f"\n❌ Error: Archivo no encontrado")
        print(f"   {str(e)}")
        logger.error(f"File not found: {ruta_archivo}", exc_info=True)
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        print(f"   Tipo: {type(e).__name__}")
        logger.error(f"Unexpected error: {e}", exc_info=True)

    finally:
        engine.dispose()


# Ejemplo de uso
if __name__ == "__main__":
    # Insertar datos de 2016
    insertar_datos_por_año('tabla_2016.csv', 'Estudiantes_2016', año=2016)
    
    # Para insertar datos de otros años, simplemente cambiar:
    # insertar_datos_por_año('tabla_2017.csv', 'Estudiantes_2017', año=2017)
    # insertar_datos_por_año('tabla_2018.csv', 'Estudiantes_2018', año=2018)
