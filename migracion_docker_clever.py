#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Migración: Docker → Clever Cloud
"""
from sqlalchemy import create_engine, text
import pandas as pd

print("\n" + "=" * 80)
print("🚀 MIGRACIÓN BD DOCKER → CLEVER CLOUD")
print("=" * 80)

try:
    # Conexión Docker
    print("\n📡 Conectando a BD local (Docker)...")
    docker_engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3308/observatorio_bilinguismo")
    
    # Conexión Clever Cloud
    print("📡 Conectando a Clever Cloud...")
    clever_engine = create_engine("mysql+mysqlconnector://uuoxxbrx6knnwzc6:5fIPyo9KIlulljR0yTdB@bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com:3306/bdldn022szfj4gyd9fqn")
    
    # Obtener tablas
    print("\n📋 Obteniendo lista de tablas...")
    with docker_engine.connect() as conn:
        result = conn.execute(text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='observatorio_bilinguismo'"))
        tables = [row[0] for row in result]
    
    print(f"✅ {len(tables)} tablas encontradas: {', '.join(tables)}\n")
    
    # Migrar
    total = 0
    for tabla in tables:
        print(f"🔄 {tabla}...", end=" ")
        df = pd.read_sql(f"SELECT * FROM `{tabla}`", docker_engine)
        df.to_sql(tabla, clever_engine, if_exists='replace', index=False)
        print(f"✅ {len(df)} registros")
        total += len(df)
    
    # Verificar
    print("\n✨ MIGRACIÓN COMPLETADA")
    print(f"📊 Total: {total} registros en {len(tables)} tablas")
    
    print("\n🔍 Verificando Clever Cloud...")
    with clever_engine.connect() as conn:
        result = conn.execute(text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='bdldn022szfj4gyd9fqn'"))
        clever_tables = [row[0] for row in result]
    
    print(f"✅ Clever Cloud tiene {len(clever_tables)} tablas")
    
    print("\n" + "=" * 80)
    print("✅ ¡MIGRACIÓN EXITOSA!")
    print("=" * 80 + "\n")
    
except Exception as e:
    print(f"\n❌ Error: {e}\n")
