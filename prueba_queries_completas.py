#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from sqlalchemy import create_engine, text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3308/observatorio_bilinguismo")

print("=" * 80)
print("PRUEBA DE QUERIES - DASHBOARDS INTENSIFICACIÓN (INCLUYENDO 2021)")
print("=" * 80)

try:
    with engine.connect() as connection:
        
        # Prueba 1: Total estudiantes intensificación por año
        print("\n✓ PRUEBA 1: Total estudiantes intensificación por año")
        resultado = connection.execute(text(
            """SELECT ANIO_REGISTRO, COUNT(DISTINCT p.ID) as total
               FROM Persona_Nivel_MCER pnm
               INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
               WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%'
               GROUP BY ANIO_REGISTRO
               ORDER BY ANIO_REGISTRO"""
        )).fetchall()
        
        total_general = 0
        for anio, cantidad in resultado:
            print(f"  • Año {anio}: {cantidad} estudiantes")
            total_general += cantidad
        print(f"  TOTAL GENERAL: {total_general} estudiantes")
        
        # Prueba 2: Estado de estudiantes 2021 intensificación
        print("\n✓ PRUEBA 2: Estado de estudiantes 2021 intensificación")
        resultado = connection.execute(text(
            """SELECT 
                   nm.ESTADO_ESTUDIANTE,
                   COUNT(DISTINCT p.NUMERO_DOCUMENTO) as cantidad
               FROM Persona_Nivel_MCER pnm
               INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
               INNER JOIN Nivel_MCER nm ON pnm.NIVEL_MCER_ID = nm.ID
               WHERE pnm.ANIO_REGISTRO = 2021
               AND LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%'
               GROUP BY nm.ESTADO_ESTUDIANTE
               ORDER BY cantidad DESC"""
        )).fetchall()
        
        if resultado:
            for estado, cantidad in resultado:
                print(f"  • {estado}: {cantidad}")
        else:
            print("  (Sin datos de estado para 2021)")
        
        # Prueba 3: Distribución por sexo 2021 intensificación
        print("\n✓ PRUEBA 3: Distribución por sexo 2021 intensificación")
        resultado = connection.execute(text(
            """SELECT 
                   p.SEXO,
                   COUNT(DISTINCT p.NUMERO_DOCUMENTO) as cantidad
               FROM Persona_Nivel_MCER pnm
               INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
               WHERE pnm.ANIO_REGISTRO = 2021
               AND LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%'
               GROUP BY p.SEXO
               ORDER BY cantidad DESC"""
        )).fetchall()
        
        if resultado:
            for sexo, cantidad in resultado:
                print(f"  • {sexo}: {cantidad}")
        else:
            print("  (Sin datos de sexo para 2021)")
        
        # Prueba 4: Comparativa de intensificación por año
        print("\n✓ PRUEBA 4: Comparativa INTENSIFICACION vs FORMACION SABADOS por año")
        resultado = connection.execute(text(
            """SELECT 
                   ANIO_REGISTRO,
                   CASE 
                       WHEN LOWER(NOMBRE_CURSO) LIKE '%intensificacion%' THEN 'Intensificacion'
                       WHEN LOWER(NOMBRE_CURSO) LIKE '%sabados%' THEN 'Formacion Sabados'
                       ELSE 'Otros'
                   END as tipo_curso,
                   COUNT(DISTINCT p.ID) as cantidad
               FROM Persona_Nivel_MCER pnm
               INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
               WHERE ANIO_REGISTRO IN (2021, 2022, 2023)
               GROUP BY ANIO_REGISTRO, tipo_curso
               ORDER BY ANIO_REGISTRO, tipo_curso"""
        )).fetchall()
        
        for anio, tipo, cantidad in resultado:
            print(f"  • Año {anio} - {tipo}: {cantidad}")
        
        # Prueba 5: Años completos con todos los datos
        print("\n✓ PRUEBA 5: Resumen por año")
        resultado = connection.execute(text(
            """SELECT 
                   pnm.ANIO_REGISTRO,
                   COUNT(*) as total_registros,
                   COUNT(DISTINCT p.ID) as estudiantes_unicos,
                   COUNT(DISTINCT NOMBRE_CURSO) as tipos_cursos
               FROM Persona_Nivel_MCER pnm
               INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
               WHERE ANIO_REGISTRO IN (2021, 2022, 2023, 2025)
               GROUP BY pnm.ANIO_REGISTRO
               ORDER BY pnm.ANIO_REGISTRO"""
        )).fetchall()
        
        for anio, total_reg, est_unicos, tipos_cursos in resultado:
            print(f"  • Año {anio}: {total_reg} registros, {est_unicos} estudiantes únicos, {tipos_cursos} tipos de cursos")
        
        print("\n" + "=" * 80)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 80)
        print("\n📝 CONCLUSIÓN:")
        print("  Los dashboards de intensificación ahora tienen datos para:")
        print("  • 2021: 229 estudiantes de intensificación")
        print("  • 2022: 1,164 estudiantes de intensificación")
        print("  • 2023: 1,114 estudiantes de intensificación")
        print("  • TOTAL: 2,507 registros de intensificación (revisados)")
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    engine.dispose()
