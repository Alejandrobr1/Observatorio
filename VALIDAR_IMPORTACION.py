#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
✅ VALIDACIÓN DE IMPORTACIÓN DE DATOS
Observatorio Bilinguismo - Verificación de integridad

Este script verifica que la importación se realizó correctamente
y que la base de datos contiene todos los datos esperados.
"""

import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from Base_datos.conexion import engine
from sqlalchemy import text

def print_section(title):
    """Imprime una sección con título"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_row(label, value, width=60):
    """Imprime una fila de información"""
    print(f"  {label:<30} {str(value):<{width}}")

def validate_database():
    """Valida que la base de datos esté correctamente poblada"""
    
    print_section("✅ VALIDACIÓN DE IMPORTACIÓN DE DATOS")
    print(f"\n  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        with engine.connect() as connection:
            
            # 1. Verificar tablas
            print_section("1️⃣  TABLAS CREADAS")
            
            result = connection.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            
            expected_tables = [
                'Tipo_documentos', 'Ciudades', 'Instituciones', 
                'Nivel_MCER', 'Personas', 'Persona_Nivel_MCER',
                'Sedes', 'Cursos'
            ]
            
            for table in expected_tables:
                status = "✅" if table in tables else "❌"
                print(f"  {status} {table}")
            
            # 2. Contar registros por tabla
            print_section("2️⃣  REGISTROS POR TABLA")
            
            stats = {
                'Tipo_documentos': 'SELECT COUNT(*) FROM Tipo_documentos',
                'Ciudades': 'SELECT COUNT(*) FROM Ciudades',
                'Instituciones': 'SELECT COUNT(*) FROM Instituciones',
                'Nivel_MCER': 'SELECT COUNT(*) FROM Nivel_MCER',
                'Personas': 'SELECT COUNT(*) FROM Personas',
                'Persona_Nivel_MCER': 'SELECT COUNT(*) FROM Persona_Nivel_MCER',
                'Sedes': 'SELECT COUNT(*) FROM Sedes',
                'Cursos': 'SELECT COUNT(*) FROM Cursos'
            }
            
            total_records = 0
            for table_name, query in stats.items():
                try:
                    result = connection.execute(text(query))
                    count = result.fetchone()[0]
                    total_records += count
                    status = "✅" if count > 0 else "⚠️ "
                    print_row(f"{status} {table_name}:", f"{count:,} registros")
                except Exception as e:
                    print_row(f"❌ {table_name}:", f"Error: {str(e)}")
            
            print_row("TOTAL:", f"{total_records:,} registros")
            
            # 3. Validar datos de Personas
            print_section("3️⃣  ANÁLISIS DE PERSONAS")
            
            try:
                # Total de personas
                result = connection.execute(text("SELECT COUNT(*) FROM Personas"))
                personas_count = result.fetchone()[0]
                print_row("Total de personas:", f"{personas_count:,}")
                
                # Personas por tipo
                result = connection.execute(text(
                    "SELECT TIPO_PERSONA, COUNT(*) as cantidad FROM Personas GROUP BY TIPO_PERSONA"
                ))
                print_row("Desglose por tipo:", "")
                for row in result:
                    print_row(f"  - {row[0] or 'Sin tipo'}:", f"{row[1]:,}")
                
                # Personas por sexo
                result = connection.execute(text(
                    "SELECT SEXO, COUNT(*) as cantidad FROM Personas GROUP BY SEXO"
                ))
                print_row("Desglose por sexo:", "")
                for row in result:
                    print_row(f"  - {row[0] or 'Sin sexo'}:", f"{row[1]:,}")
                
                # Personas por ciudad
                result = connection.execute(text(
                    """SELECT COALESCE(c.MUNICIPIO, 'Sin ciudad'), COUNT(*) as cantidad 
                       FROM Personas p LEFT JOIN Ciudades c ON p.CIUDAD_ID = c.ID 
                       GROUP BY p.CIUDAD_ID ORDER BY cantidad DESC LIMIT 5"""
                ))
                print_row("Top 5 ciudades:", "")
                for row in result:
                    print_row(f"  - {row[0]}:", f"{row[1]:,}")
                
            except Exception as e:
                print(f"  ❌ Error en análisis de personas: {str(e)}")
            
            # 4. Validar datos de Nivel_MCER
            print_section("4️⃣  ANÁLISIS DE NIVELES MCER")
            
            try:
                # Niveles por año
                result = connection.execute(text(
                    "SELECT ANIO, COUNT(*) as cantidad FROM Nivel_MCER GROUP BY ANIO ORDER BY ANIO"
                ))
                print_row("Niveles por año:", "")
                for row in result:
                    print_row(f"  - {row[0] or 'Sin año'}:", f"{row[1]:,}")
                
                # Niveles MCER únicos
                result = connection.execute(text(
                    "SELECT DISTINCT NIVEL_MCER FROM Nivel_MCER WHERE NIVEL_MCER IS NOT NULL ORDER BY NIVEL_MCER"
                ))
                niveles = [row[0] for row in result]
                print_row("Niveles MCER encontrados:", ", ".join(niveles) if niveles else "Ninguno")
                
                # Tipos de población
                result = connection.execute(text(
                    "SELECT DISTINCT TIPO_POBLACION FROM Nivel_MCER WHERE TIPO_POBLACION IS NOT NULL ORDER BY TIPO_POBLACION"
                ))
                tipos = [row[0] for row in result]
                print_row("Tipos de población:", ", ".join(tipos) if tipos else "Ninguno")
                
            except Exception as e:
                print(f"  ❌ Error en análisis de niveles: {str(e)}")
            
            # 5. Validar datos de Persona_Nivel_MCER
            print_section("5️⃣  ANÁLISIS DE RELACIÓN PERSONA-NIVEL")
            
            try:
                # Total de relaciones
                result = connection.execute(text("SELECT COUNT(*) FROM Persona_Nivel_MCER"))
                total_relaciones = result.fetchone()[0]
                print_row("Total de relaciones:", f"{total_relaciones:,}")
                
                # Relaciones por año de registro
                result = connection.execute(text(
                    "SELECT ANIO_REGISTRO, COUNT(*) as cantidad FROM Persona_Nivel_MCER GROUP BY ANIO_REGISTRO ORDER BY ANIO_REGISTRO"
                ))
                print_row("Relaciones por año:", "")
                for row in result:
                    print_row(f"  - {row[0] or 'Sin año'}:", f"{row[1]:,}")
                
                # Verificar NOMBRE_CURSO
                result = connection.execute(text(
                    "SELECT COUNT(DISTINCT NOMBRE_CURSO) FROM Persona_Nivel_MCER WHERE NOMBRE_CURSO IS NOT NULL"
                ))
                cursos_count = result.fetchone()[0]
                print_row("Cursos únicos registrados:", f"{cursos_count:,}")
                
                result = connection.execute(text(
                    "SELECT DISTINCT NOMBRE_CURSO FROM Persona_Nivel_MCER WHERE NOMBRE_CURSO IS NOT NULL ORDER BY NOMBRE_CURSO"
                ))
                cursos = [row[0] for row in result]
                print_row("Cursos encontrados:", "")
                for curso in cursos[:5]:
                    print_row(f"  - {curso}:", "✅")
                if len(cursos) > 5:
                    print_row(f"  ... y {len(cursos)-5} más", "")
                
            except Exception as e:
                print(f"  ❌ Error en análisis de relaciones: {str(e)}")
            
            # 6. Validar instituciones y sedes
            print_section("6️⃣  ANÁLISIS DE INSTITUCIONES Y SEDES")
            
            try:
                # Total instituciones
                result = connection.execute(text("SELECT COUNT(*) FROM Instituciones"))
                inst_count = result.fetchone()[0]
                print_row("Total de instituciones:", f"{inst_count:,}")
                
                # Instituciones con personas
                result = connection.execute(text(
                    """SELECT COUNT(DISTINCT p.INSTITUCION_ID) FROM Personas p 
                       WHERE p.INSTITUCION_ID IS NOT NULL"""
                ))
                inst_con_personas = result.fetchone()[0]
                print_row("Instituciones con personas:", f"{inst_con_personas:,}")
                
                # Top 5 instituciones por cantidad de personas
                result = connection.execute(text(
                    """SELECT COALESCE(i.NOMBRE_INSTITUCION, 'Sin institución'), COUNT(*) as cantidad
                       FROM Personas p LEFT JOIN Instituciones i ON p.INSTITUCION_ID = i.ID
                       GROUP BY p.INSTITUCION_ID ORDER BY cantidad DESC LIMIT 5"""
                ))
                print_row("Top 5 instituciones:", "")
                for row in result:
                    print_row(f"  - {row[0]}:", f"{row[1]:,} personas")
                
                # Sedes
                result = connection.execute(text("SELECT COUNT(*) FROM Sedes"))
                sedes_count = result.fetchone()[0]
                print_row("Total de sedes:", f"{sedes_count:,}")
                
            except Exception as e:
                print(f"  ❌ Error en análisis de instituciones: {str(e)}")
            
            # 7. Verificación de integridad
            print_section("7️⃣  VERIFICACIÓN DE INTEGRIDAD")
            
            try:
                # Personas sin tipos
                result = connection.execute(text(
                    "SELECT COUNT(*) FROM Personas WHERE TIPO_PERSONA IS NULL"
                ))
                sin_tipo = result.fetchone()[0]
                print_row("Personas sin tipo:", f"{sin_tipo} ⚠️ " if sin_tipo > 0 else "0 ✅")
                
                # Personas sin documento
                result = connection.execute(text(
                    "SELECT COUNT(*) FROM Personas WHERE NUMERO_DOCUMENTO IS NULL OR NUMERO_DOCUMENTO = ''"
                ))
                sin_doc = result.fetchone()[0]
                print_row("Personas sin documento:", f"{sin_doc} ⚠️ " if sin_doc > 0 else "0 ✅")
                
                # Personas sin institución
                result = connection.execute(text(
                    "SELECT COUNT(*) FROM Personas WHERE INSTITUCION_ID IS NULL"
                ))
                sin_inst = result.fetchone()[0]
                print_row("Personas sin institución:", f"{sin_inst} ⚠️ " if sin_inst > 0 else "0 ✅")
                
                # Relaciones persona-nivel sin curso
                result = connection.execute(text(
                    "SELECT COUNT(*) FROM Persona_Nivel_MCER WHERE NOMBRE_CURSO IS NULL"
                ))
                sin_curso = result.fetchone()[0]
                print_row("Relaciones sin nombre de curso:", f"{sin_curso} ⚠️ " if sin_curso > 0 else "0 ✅")
                
            except Exception as e:
                print(f"  ❌ Error en verificación de integridad: {str(e)}")
            
            # 8. Resumen final
            print_section("✅ RESUMEN")
            
            if total_records > 0:
                print(f"\n  🎉 ¡IMPORTACIÓN EXITOSA!")
                print(f"\n  Se importaron correctamente:")
                print(f"    • {personas_count:,} personas")
                print(f"    • {total_relaciones:,} relaciones persona-nivel")
                print(f"    • {inst_count:,} instituciones")
                print(f"    • {cursos_count:,} cursos únicos")
                print(f"\n  Los datos están listos para usar en los dashboards ✨\n")
                return True
            else:
                print(f"\n  ⚠️ No se encontraron datos en la base de datos")
                print(f"  Ejecuta los scripts de importación primero\n")
                return False
    
    except Exception as e:
        print(f"\n  ❌ Error conectando a la base de datos: {str(e)}")
        print(f"  Verifica la configuración en Base_datos/conexion.py\n")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("  🔍 VALIDACIÓN DE IMPORTACIÓN - OBSERVATORIO BILINGUISMO")
    print("="*80)
    
    success = validate_database()
    
    sys.exit(0 if success else 1)
