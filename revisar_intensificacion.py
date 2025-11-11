#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os

project_root = r"d:\Proyectos Jc Code\Archivos para BD rionegro\Observatorio"
ruta = os.path.join(project_root, "CSVs", "data_2022_intensificacion.csv")

print(f"Leyendo: {ruta}")
df = pd.read_csv(ruta, sep=';', encoding='utf-8-sig')

print("\n" + "=" * 80)
print("INFORMACIÓN - data_2022_intensificacion.csv")
print("=" * 80)
print(f"\nTotal filas: {len(df)}")
print(f"Columnas: {list(df.columns)}")

print("\nCURSOS ÚNICOS:")
cursos = df['NOMBRE CURSO'].unique()
print(f"Total: {len(cursos)}")
for idx, curso in enumerate(cursos, 1):
    print(f"{idx}. {curso}")

# Distribución
print("\n📊 Distribución por curso:")
print(df['NOMBRE CURSO'].value_counts())

# Contar intensificación
intensif_count = df[df['NOMBRE CURSO'].str.contains('intensificacion', case=False, na=False)].shape[0]
print(f"\n🎯 Registros con 'intensificacion': {intensif_count}")
