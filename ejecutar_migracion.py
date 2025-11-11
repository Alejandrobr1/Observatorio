#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from sqlalchemy import create_engine, text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Conexión a BD
engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3308/observatorio_bilinguismo")

print("=" * 80)
print("EJECUTANDO MIGRACIÓN - AGREGAR NOMBRE_CURSO A Persona_Nivel_MCER")
print("=" * 80)

try:
    with engine.connect() as connection:
        # Leer el archivo SQL
        with open("migration_add_nombre_curso.sql", "r", encoding="utf-8") as f:
            sql_content = f.read()
        
        # Dividir las consultas por punto y coma
        queries = [q.strip() for q in sql_content.split(';') if q.strip()]
        
        print(f"\n📝 Se encontraron {len(queries)} comandos SQL\n")
        
        for idx, query in enumerate(queries, 1):
            # Saltar comentarios
            if query.startswith('--'):
                continue
                
            print(f"[{idx}] Ejecutando: {query[:60]}...")
            try:
                connection.execute(text(query))
                connection.commit()
                print(f"     ✅ OK\n")
            except Exception as e:
                # Algunos errores son esperados (ej: columna ya existe)
                if "Duplicate column name" in str(e) or "already exists" in str(e):
                    print(f"     ℹ️  (Columna ya existe - OK)\n")
                else:
                    print(f"     ⚠️  {str(e)}\n")
        
        print("\n" + "=" * 80)
        print("✅ MIGRACIÓN EJECUTADA")
        print("=" * 80)
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    engine.dispose()
