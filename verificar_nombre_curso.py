#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from sqlalchemy import create_engine, text
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Conexión a BD
engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3308/observatorio_bilinguismo")

print("=" * 80)
print("VERIFICACIÓN DE DATOS - NOMBRE_CURSO EN Persona_Nivel_MCER")
print("=" * 80)

try:
    with engine.connect() as connection:
        # Verificar total de registros con NOMBRE_CURSO
        result = connection.execute(text(
            """SELECT COUNT(*) as total, 
                      COUNT(DISTINCT NOMBRE_CURSO) as cursos_unicos 
               FROM Persona_Nivel_MCER 
               WHERE NOMBRE_CURSO IS NOT NULL"""
        )).fetchone()
        
        print(f"\n✓ Total registros con NOMBRE_CURSO: {result[0]}")
        print(f"✓ Cursos únicos encontrados: {result[1]}")
        
        # Mostrar los cursos únicos
        print("\n📚 Cursos encontrados:")
        cursos_result = connection.execute(text(
            """SELECT DISTINCT NOMBRE_CURSO 
               FROM Persona_Nivel_MCER 
               WHERE NOMBRE_CURSO IS NOT NULL 
               ORDER BY NOMBRE_CURSO 
               LIMIT 30"""
        )).fetchall()
        
        for idx, (curso,) in enumerate(cursos_result, 1):
            print(f"   {idx:2d}. {curso}")
        
        # Contar intensificación
        intensif_result = connection.execute(text(
            """SELECT COUNT(*) as total 
               FROM Persona_Nivel_MCER 
               WHERE LOWER(NOMBRE_CURSO) LIKE '%intensificacion%'"""
        )).fetchone()
        
        print(f"\n🎯 Registros de INTENSIFICACIÓN: {intensif_result[0]}")
        
        # Verificar estructura de la tabla
        print("\n📋 Estructura de Persona_Nivel_MCER:")
        structure = connection.execute(text(
            """SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE 
               FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'Persona_Nivel_MCER' 
               AND TABLE_SCHEMA = 'observatorio_bilinguismo'
               ORDER BY ORDINAL_POSITION"""
        )).fetchall()
        
        for col_name, col_type, nullable in structure:
            null_str = "NULL" if nullable == "YES" else "NOT NULL"
            print(f"   • {col_name}: {col_type} [{null_str}]")
        
        print("\n" + "=" * 80)
        print("✅ VERIFICACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 80)
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    engine.dispose()
