"""
Script para poblar NOMBRE_CURSO para los años 2016-2020
Lee los CSVs históricos y actualiza la base de datos
"""

import pandas as pd
from sqlalchemy import create_engine, text

# Conexión a la base de datos
engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3308/observatorio_bilinguismo")

print("=" * 80)
print("📋 POBLANDO NOMBRE_CURSO PARA AÑOS 2016-2020")
print("=" * 80)
print()

# Años a procesar
años_a_procesar = [2016, 2017, 2018, 2019, 2020]

total_actualizados = 0
total_no_encontrados = 0

for año in años_a_procesar:
    print(f"\n{'=' * 80}")
    print(f"📄 Procesando: data_{año}.csv (Año {año})")
    print('=' * 80)
    
    try:
        # Leer el CSV
        df = pd.read_csv(f"CSVs/data_{año}.csv", encoding='utf-8', sep=';')
        
        print(f"✓ Archivo leído: {len(df):,} filas")
        
        # Verificar que existan las columnas necesarias
        if 'NÚMERO DE IDENTIFICACIÓN' not in df.columns and 'NUMERO DE IDENTIFICACION' not in df.columns:
            # Buscar variantes
            id_col = None
            for col in df.columns:
                if 'IDENTIFICACI' in col.upper() and 'NÚMERO' in col.upper():
                    id_col = col
                    break
            if not id_col:
                print(f"❌ No se encontró columna de identificación")
                continue
        else:
            id_col = 'NÚMERO DE IDENTIFICACIÓN' if 'NÚMERO DE IDENTIFICACIÓN' in df.columns else 'NUMERO DE IDENTIFICACION'
        
        if 'NOMBRE CURSO' not in df.columns:
            print(f"❌ No existe columna NOMBRE CURSO en el CSV")
            continue
        
        # Crear mapeo numero_doc -> NOMBRE_CURSO
        mapping = {}
        for idx, row in df.iterrows():
            doc = str(row[id_col]).strip()
            curso = str(row['NOMBRE CURSO']).strip() if pd.notna(row['NOMBRE CURSO']) else None
            
            if doc and curso:
                # Normalizar el nombre del curso
                curso_norm = curso.lower().strip()
                mapping[doc] = curso_norm
        
        print(f"✓ Mapeos creados: {len(mapping):,}")
        
        # Procesar cada mapeo
        actualizados_año = 0
        no_encontrados_año = 0
        
        with engine.connect() as connection:
            for doc, curso in mapping.items():
                try:
                    # Buscar la persona
                    query_persona = text("""
                        SELECT p.ID FROM Personas p 
                        WHERE p.NUMERO_DOCUMENTO = :doc
                    """)
                    result = connection.execute(query_persona, {"doc": doc})
                    persona_row = result.fetchone()
                    
                    if not persona_row:
                        no_encontrados_año += 1
                        continue
                    
                    persona_id = persona_row[0]
                    
                    # Actualizar Persona_Nivel_MCER
                    query_update = text("""
                        UPDATE Persona_Nivel_MCER 
                        SET NOMBRE_CURSO = :curso
                        WHERE PERSONA_ID = :persona_id 
                        AND ANIO_REGISTRO = :año
                        AND (NOMBRE_CURSO IS NULL OR NOMBRE_CURSO = '')
                    """)
                    
                    result = connection.execute(query_update, {
                        "curso": curso,
                        "persona_id": persona_id,
                        "año": año
                    })
                    
                    if result.rowcount > 0:
                        actualizados_año += result.rowcount
                    
                except Exception as e:
                    no_encontrados_año += 1
            
            # Commit
            connection.commit()
        
        print(f"✓ Registros actualizados: {actualizados_año:,}")
        print(f"⚠ Personas no encontradas: {no_encontrados_año:,}")
        
        total_actualizados += actualizados_año
        total_no_encontrados += no_encontrados_año
        
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: data_{año}.csv")
    except Exception as e:
        print(f"❌ Error procesando año {año}: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("📊 RESUMEN FINAL")
print("=" * 80)
print(f"✓ Total registros actualizados: {total_actualizados:,}")
print(f"⚠ Personas no encontradas: {total_no_encontrados:,}")
print()

# Verificación final
print("\n" + "=" * 80)
print("🔍 VERIFICACIÓN: Estado actual de NOMBRE_CURSO por año")
print("=" * 80)

with engine.connect() as connection:
    query = text("""
        SELECT 
            pnm.ANIO_REGISTRO as año,
            COUNT(DISTINCT pnm.PERSONA_ID) as total_registros,
            COUNT(DISTINCT CASE WHEN pnm.NOMBRE_CURSO IS NOT NULL AND pnm.NOMBRE_CURSO != '' THEN pnm.PERSONA_ID END) as con_nombre_curso
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        WHERE p.TIPO_PERSONA = 'Estudiante'
        GROUP BY pnm.ANIO_REGISTRO
        ORDER BY año
    """)
    
    result = connection.execute(query)
    print()
    for row in result:
        año, total, con = row[0], row[1], row[2]
        porcentaje = (con/total*100) if total > 0 else 0
        estado = "✅" if porcentaje >= 90 else "⚠" if porcentaje > 0 else "❌"
        print(f"Año {año}: {con:6,}/{total:6,} ({porcentaje:6.1f}%) {estado}")

print()
print("=" * 80)
