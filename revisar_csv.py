#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os

project_root = "d:\Proyectos Jc Code\Archivos para BD rionegro\Observatorio"
ruta = os.path.join(project_root, "CSVs", "data_2025.csv")

print(f"Leyendo: {ruta}")
df = pd.read_csv(ruta, sep=';', encoding='utf-8-sig')

print("\n" + "=" * 80)
print("CURSOS ÚNICOS EN data_2025.csv")
print("=" * 80)

cursos = df['NOMBRE CURSO'].unique()
print(f"\nTotal cursos únicos: {len(cursos)}")
print("\nLista completa:")
for idx, curso in enumerate(cursos, 1):
    print(f"{idx:2d}. {curso}")

# Contar intensificación
intensif_count = df[df['NOMBRE CURSO'].str.contains('intensificacion', case=False, na=False)].shape[0]
print(f"\n🎯 Registros con 'intensificacion': {intensif_count}")

# Mostrar distribución
print("\n📊 Distribución por curso:")
print(df['NOMBRE CURSO'].value_counts())
