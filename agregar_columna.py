#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from sqlalchemy import create_engine, text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Conexión a BD
engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3308/observatorio_bilinguismo")

print("=" * 80)
print("AGREGANDO COLUMNA NOMBRE_CURSO A Persona_Nivel_MCER")
print("=" * 80)

try:
    with engine.connect() as connection:
        # Verificar si la columna ya existe
        print("\n1. Verificando estructura actual...")
        result = connection.execute(text(
            """SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'Persona_Nivel_MCER' 
               AND TABLE_SCHEMA = 'observatorio_bilinguismo'"""
        )).fetchall()
        
        columns = [row[0] for row in result]
        print(f"   Columnas actuales: {columns}")
        
        if 'NOMBRE_CURSO' in columns:
            print("   ✓ La columna NOMBRE_CURSO ya existe")
        else:
            print("   ✗ La columna NOMBRE_CURSO NO existe - agregando...")
            connection.execute(text(
                "ALTER TABLE Persona_Nivel_MCER ADD COLUMN NOMBRE_CURSO VARCHAR(200) NULL"
            ))
            connection.commit()
            print("   ✅ Columna agregada exitosamente")
        
        # Verificar nuevamente
        print("\n2. Verificando después de la migración...")
        result = connection.execute(text(
            """SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'Persona_Nivel_MCER' 
               AND TABLE_SCHEMA = 'observatorio_bilinguismo'"""
        )).fetchall()
        
        columns = [row[0] for row in result]
        print(f"   Columnas actuales: {columns}")
        
        # Verificar estadísticas
        print("\n3. Estadísticas de la tabla...")
        stats = connection.execute(text(
            """SELECT COUNT(*) as total_registros,
                      COUNT(NOMBRE_CURSO) as registros_con_nombre_curso
               FROM Persona_Nivel_MCER"""
        )).fetchone()
        
        print(f"   • Total registros: {stats[0]}")
        print(f"   • Registros con NOMBRE_CURSO: {stats[1]}")
        
        print("\n" + "=" * 80)
        print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 80)
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    engine.dispose()
