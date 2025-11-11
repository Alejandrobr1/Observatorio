#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from logger_config import get_logger

logger = get_logger(__name__)

def limpiar_valor(valor):
    """Limpia y normaliza valores de texto"""
    if pd.isna(valor) or valor is None:
        return 'SIN INFORMACION'
    valor = str(valor).strip().upper()
    if valor in ['', 'NAN', 'NONE', 'NULL']:
        return 'SIN INFORMACION'
    return valor

# Conexión a BD
engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3308/observatorio_bilinguismo")

print("=" * 80)
print("POBLANDO NOMBRE_CURSO EN Persona_Nivel_MCER - 2022")
print("=" * 80)

try:
    # Leer CSV 2022
    print("\n1. Leyendo CSV 2022...")
    project_root = os.path.abspath(os.path.dirname(__file__))
    ruta_archivo = os.path.join(project_root, "CSVs", "data_2022.csv")
    
    # Intentar con sep=;
    try:
        df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')
    except Exception:
        # Si falla, intentar con sep=,
        df = pd.read_csv(ruta_archivo, sep=',', encoding='utf-8-sig')
    
    print(f"   Total filas: {len(df)}")
    
    # Crear mapeo numero_doc -> nombre_curso
    print("\n2. Creando mapeo de numero_doc -> NOMBRE_CURSO...")
    nombre_curso_map = {}
    
    for _, row in df.iterrows():
        numero_doc = str(row.get('NÚMERO DE IDENTIFICACIÓN', ''))
        nombre_curso = limpiar_valor(row.get('NOMBRE CURSO', 'SIN INFORMACION'))
        tipo_poblacion = limpiar_valor(row.get('TIPO POBLACION', ''))
        
        # Si es docente, el "curso" es "Formación Docente"
        if tipo_poblacion == 'DOCENTE':
            nombre_curso = 'Formación Docente'
        
        if numero_doc and numero_doc != 'NAN':
            nombre_curso_map[numero_doc] = nombre_curso
    
    print(f"   Mapeos creados: {len(nombre_curso_map)}")
    
    # Conectar y actualizar
    with engine.connect() as connection:
        print("\n3. Actualizando registros en Persona_Nivel_MCER...")
        
        actualizados = 0
        no_encontrados = 0
        
        for numero_doc, nombre_curso in nombre_curso_map.items():
            # Buscar la persona
            persona = connection.execute(text(
                "SELECT ID FROM Personas WHERE NUMERO_DOCUMENTO = :numero_doc"
            ), {'numero_doc': numero_doc}).fetchone()
            
            if not persona:
                no_encontrados += 1
                continue
            
            # Actualizar NOMBRE_CURSO para esta persona
            result = connection.execute(text(
                """UPDATE Persona_Nivel_MCER 
                   SET NOMBRE_CURSO = :nombre_curso 
                   WHERE PERSONA_ID = :persona_id AND ANIO_REGISTRO = 2022"""
            ), {'nombre_curso': nombre_curso, 'persona_id': persona[0]})
            
            actualizados += result.rowcount
        
        connection.commit()
        
        print(f"   ✓ Registros actualizados: {actualizados}")
        print(f"   ⚠️  Personas no encontradas: {no_encontrados}")
        
        # Verificar resultados
        print("\n4. Verificando resultados...")
        stats = connection.execute(text(
            """SELECT 
                   COUNT(*) as total,
                   COUNT(NOMBRE_CURSO) as con_nombre,
                   COUNT(DISTINCT NOMBRE_CURSO) as nombres_unicos
               FROM Persona_Nivel_MCER 
               WHERE ANIO_REGISTRO = 2022"""
        )).fetchone()
        
        print(f"   Total registros 2022: {stats[0]}")
        print(f"   Con NOMBRE_CURSO: {stats[1]}")
        print(f"   Nombres únicos: {stats[2]}")
        
        # Mostrar algunos ejemplos
        print("\n5. Ejemplos de cursos encontrados:")
        ejemplos = connection.execute(text(
            """SELECT DISTINCT NOMBRE_CURSO 
               FROM Persona_Nivel_MCER 
               WHERE ANIO_REGISTRO = 2022 
               AND NOMBRE_CURSO IS NOT NULL 
               LIMIT 10"""
        )).fetchall()
        
        for idx, (curso,) in enumerate(ejemplos, 1):
            print(f"   {idx}. {curso}")
        
        print("\n" + "=" * 80)
        print("✅ POBLACIÓN COMPLETADA - 2022")
        print("=" * 80)
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    engine.dispose()
