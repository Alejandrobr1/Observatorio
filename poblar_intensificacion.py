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
print("POBLANDO NOMBRE_CURSO EN Persona_Nivel_MCER - INTENSIFICACIÓN (2022/2023)")
print("=" * 80)

try:
    archivos_intensif = [
        ("CSVs/data_2022_intensificacion.csv", 2022),
        ("CSVs/data_2023_intensificacion.csv", 2023),
    ]
    
    total_actualizados = 0
    
    for archivo, anio in archivos_intensif:
        print(f"\n📂 Procesando: {archivo} (Año {anio})")
        
        project_root = os.path.abspath(os.path.dirname(__file__))
        ruta_archivo = os.path.join(project_root, archivo)
        
        if not os.path.exists(ruta_archivo):
            print(f"   ⚠️  Archivo no encontrado: {ruta_archivo}")
            continue
        
        # Leer CSV
        print(f"   1. Leyendo archivo...")
        try:
            df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')
        except Exception:
            df = pd.read_csv(ruta_archivo, sep=',', encoding='utf-8-sig')
        
        print(f"      Total filas: {len(df)}")
        
        # Crear mapeo numero_doc -> nombre_curso (siempre "Intensificacion" para estos archivos)
        print(f"   2. Creando mapeo...")
        nombre_curso_map = {}
        
        for _, row in df.iterrows():
            numero_doc = str(row.get('NÚMERO DE IDENTIFICACIÓN', ''))
            nombre_curso = limpiar_valor(row.get('NOMBRE CURSO', 'Intensificacion'))
            
            if numero_doc and numero_doc != 'NAN':
                nombre_curso_map[numero_doc] = nombre_curso
        
        print(f"      Mapeos creados: {len(nombre_curso_map)}")
        
        # Conectar y actualizar
        with engine.connect() as connection:
            print(f"   3. Actualizando registros...")
            
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
                    f"""UPDATE Persona_Nivel_MCER 
                       SET NOMBRE_CURSO = :nombre_curso 
                       WHERE PERSONA_ID = :persona_id AND ANIO_REGISTRO = {anio}"""
                ), {'nombre_curso': nombre_curso, 'persona_id': persona[0]})
                
                actualizados += result.rowcount
            
            connection.commit()
            
            print(f"      ✓ Registros actualizados: {actualizados}")
            if no_encontrados > 0:
                print(f"      ⚠️  Personas no encontradas: {no_encontrados}")
            
            total_actualizados += actualizados
    
    # Verificar resultados globales
    with engine.connect() as connection:
        print("\n" + "=" * 80)
        print("📊 ESTADÍSTICAS FINALES")
        print("=" * 80)
        
        stats = connection.execute(text(
            """SELECT 
                   ANIO_REGISTRO,
                   COUNT(*) as total,
                   COUNT(NOMBRE_CURSO) as con_nombre,
                   COUNT(DISTINCT NOMBRE_CURSO) as nombres_unicos
               FROM Persona_Nivel_MCER 
               WHERE ANIO_REGISTRO IN (2022, 2023)
               GROUP BY ANIO_REGISTRO
               ORDER BY ANIO_REGISTRO"""
        )).fetchall()
        
        for anio, total, con_nombre, nombres_unicos in stats:
            print(f"\n📅 Año {anio}:")
            print(f"   • Total registros: {total}")
            print(f"   • Con NOMBRE_CURSO: {con_nombre}")
            print(f"   • Nombres únicos: {nombres_unicos}")
        
        # Contar intensificaciones
        print("\n🎯 INTENSIFICACIONES:")
        intensif = connection.execute(text(
            """SELECT COUNT(*) as total 
               FROM Persona_Nivel_MCER 
               WHERE LOWER(NOMBRE_CURSO) LIKE '%intensificacion%'"""
        )).fetchone()
        print(f"   Total registros con 'intensificacion': {intensif[0]}")
        
        print("\n" + "=" * 80)
        print("✅ POBLACIÓN DE INTENSIFICACIONES COMPLETADA")
        print("=" * 80)
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    engine.dispose()
