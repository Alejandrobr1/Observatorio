import pandas as pd
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Base_datos.conexion import engine

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ruta_archivo = os.path.join(project_root, "CSVs", "data_2025.csv")

# Leer CSV
df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')

print("🔄 Actualizando relaciones Persona-Nivel_MCER para incluir GRADO...")
print(f"Total registros en CSV: {len(df)}")

actualizaciones = 0
sin_persona = 0
sin_nivel = 0
sin_grado_valido = 0

with engine.connect() as connection:
    
    for idx, row in df.iterrows():
        numero_doc = str(row.get('NÚMERO DE IDENTIFICACIÓN', '')).strip()
        nivel_mcer = str(row.get('NIVEL_MCER', '')).strip().upper()
        tipo_pob = str(row.get('TIPO POBLACION', '')).strip()
        grado = str(row.get('GRADO', '')).strip().upper()
        
        # Validar datos
        if not numero_doc or numero_doc.upper() in ['NAN', 'NONE', 'SIN INFORMACION']:
            continue
        
        if not nivel_mcer or nivel_mcer in ['NAN', 'NONE', '', 'SIN INFORMACION']:
            continue
        
        if not tipo_pob or tipo_pob.upper() in ['NAN', 'NONE', '', 'SIN INFORMACION']:
            continue
        
        if not grado or grado in ['NAN', 'NONE', '', 'NA', 'N/A', 'NULL', 'SIN INFORMACION']:
            sin_grado_valido += 1
            continue
        
        # Buscar ID de la persona
        persona_result = connection.execute(text("""
            SELECT ID FROM Personas 
            WHERE NUMERO_DOCUMENTO = :numero_doc
        """), {'numero_doc': numero_doc}).fetchone()
        
        if not persona_result:
            sin_persona += 1
            continue
        
        persona_id = persona_result[0]
        
        # Buscar ID del Nivel_MCER con GRADO
        nivel_result = connection.execute(text("""
            SELECT ID FROM Nivel_MCER 
            WHERE NIVEL_MCER = :nivel
            AND TIPO_POBLACION = :tipo_pob
            AND GRADO = :grado
        """), {
            'nivel': nivel_mcer,
            'tipo_pob': tipo_pob,
            'grado': grado
        }).fetchone()
        
        if not nivel_result:
            sin_nivel += 1
            continue
        
        nivel_id = nivel_result[0]
        
        # Actualizar o insertar la relación
        # Primero borrar las relaciones existentes de esta persona para 2025
        connection.execute(text("""
            DELETE FROM Persona_Nivel_MCER 
            WHERE PERSONA_ID = :persona_id 
            AND ANIO_REGISTRO = 2025
        """), {'persona_id': persona_id})
        
        # Insertar nueva relación con el Nivel_MCER correcto
        connection.execute(text("""
            INSERT INTO Persona_Nivel_MCER (PERSONA_ID, NIVEL_MCER_ID, ANIO_REGISTRO)
            VALUES (:persona_id, :nivel_id, 2025)
        """), {
            'persona_id': persona_id,
            'nivel_id': nivel_id
        })
        
        actualizaciones += 1
        
        if (idx + 1) % 100 == 0:
            print(f"  Procesados: {idx + 1}/{len(df)} registros...")
    
    connection.commit()

print(f"\n✅ Actualización completada:")
print(f"   - Relaciones actualizadas: {actualizaciones}")
print(f"   - Personas no encontradas: {sin_persona}")
print(f"   - Niveles MCER no encontrados: {sin_nivel}")
print(f"   - Registros sin grado válido: {sin_grado_valido}")
