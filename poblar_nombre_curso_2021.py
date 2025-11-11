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
print("POBLANDO NOMBRE_CURSO EN Persona_Nivel_MCER - 2021")
print("=" * 80)

try:
    # Procesar archivo regular de 2021
    print("\n📂 PARTE 1: Datos regulares de 2021 (data_2021.csv)")
    
    project_root = os.path.abspath(os.path.dirname(__file__))
    ruta_archivo = os.path.join(project_root, "CSVs", "data_2021.csv")
    
    if os.path.exists(ruta_archivo):
        print(f"   Leyendo archivo...")
        try:
            df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')
        except Exception:
            df = pd.read_csv(ruta_archivo, sep=',', encoding='utf-8-sig')
        
        print(f"   Total filas: {len(df)}")
        
        # Crear mapeo numero_doc -> nombre_curso
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
            print(f"   Actualizando registros...")
            
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
                       WHERE PERSONA_ID = :persona_id AND ANIO_REGISTRO = 2021"""
                ), {'nombre_curso': nombre_curso, 'persona_id': persona[0]})
                
                actualizados += result.rowcount
            
            connection.commit()
            
            print(f"   ✓ Registros actualizados: {actualizados}")
            if no_encontrados > 0:
                print(f"   ⚠️  Personas no encontradas: {no_encontrados}")
    else:
        print(f"   ⚠️  Archivo no encontrado: {ruta_archivo}")
    
    # Procesar archivo de intensificación de 2021
    print("\n📂 PARTE 2: Datos de intensificación 2021 (data_2021_intensificacion.csv)")
    
    ruta_archivo = os.path.join(project_root, "CSVs", "data_2021_intensificacion.csv")
    
    if os.path.exists(ruta_archivo):
        print(f"   Leyendo archivo...")
        try:
            df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')
        except Exception:
            df = pd.read_csv(ruta_archivo, sep=',', encoding='utf-8-sig')
        
        print(f"   Total filas: {len(df)}")
        
        # Crear mapeo numero_doc -> nombre_curso (siempre "Intensificacion")
        nombre_curso_map = {}
        
        for _, row in df.iterrows():
            numero_doc = str(row.get('NÚMERO DE IDENTIFICACIÓN', ''))
            nombre_curso = limpiar_valor(row.get('NOMBRE CURSO', 'Intensificacion'))
            
            if numero_doc and numero_doc != 'NAN':
                nombre_curso_map[numero_doc] = nombre_curso
        
        print(f"   Mapeos creados: {len(nombre_curso_map)}")
        
        # Conectar y actualizar
        with engine.connect() as connection:
            print(f"   Actualizando registros...")
            
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
                       WHERE PERSONA_ID = :persona_id AND ANIO_REGISTRO = 2021"""
                ), {'nombre_curso': nombre_curso, 'persona_id': persona[0]})
                
                actualizados += result.rowcount
            
            connection.commit()
            
            print(f"   ✓ Registros actualizados: {actualizados}")
            if no_encontrados > 0:
                print(f"   ⚠️  Personas no encontradas: {no_encontrados}")
    else:
        print(f"   ⚠️  Archivo no encontrado: {ruta_archivo}")
    
    # Verificar resultados
    with engine.connect() as connection:
        print("\n" + "=" * 80)
        print("📊 ESTADÍSTICAS FINALES - AÑO 2021")
        print("=" * 80)
        
        stats = connection.execute(text(
            """SELECT 
                   COUNT(*) as total,
                   COUNT(NOMBRE_CURSO) as con_nombre,
                   COUNT(DISTINCT NOMBRE_CURSO) as nombres_unicos
               FROM Persona_Nivel_MCER 
               WHERE ANIO_REGISTRO = 2021"""
        )).fetchone()
        
        print(f"\n📅 Año 2021:")
        print(f"   • Total registros: {stats[0]}")
        print(f"   • Con NOMBRE_CURSO: {stats[1]}")
        print(f"   • Nombres únicos: {stats[2]}")
        
        # Mostrar distribución
        print(f"\n📚 Distribución por tipo de curso:")
        distribucion = connection.execute(text(
            """SELECT NOMBRE_CURSO, COUNT(*) as cantidad
               FROM Persona_Nivel_MCER 
               WHERE ANIO_REGISTRO = 2021
               AND NOMBRE_CURSO IS NOT NULL
               GROUP BY NOMBRE_CURSO
               ORDER BY cantidad DESC"""
        )).fetchall()
        
        for curso, cantidad in distribucion:
            print(f"   • {curso}: {cantidad}")
        
        # Contar intensificaciones
        intensif = connection.execute(text(
            """SELECT COUNT(*) as total 
               FROM Persona_Nivel_MCER 
               WHERE ANIO_REGISTRO = 2021
               AND LOWER(NOMBRE_CURSO) LIKE '%intensificacion%'"""
        )).fetchone()
        print(f"\n🎯 Total intensificación 2021: {intensif[0]}")
        
        print("\n" + "=" * 80)
        print("✅ POBLACIÓN COMPLETADA - AÑO 2021")
        print("=" * 80)
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    engine.dispose()
