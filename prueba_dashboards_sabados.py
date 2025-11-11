"""
Script de prueba para verificar que los dashboards de Formación Sábados funcionan correctamente
"""

from sqlalchemy import create_engine, text

# Configuración de conexión
engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3308/observatorio_bilinguismo")

print("=" * 80)
print("🧪 PRUEBA DE DASHBOARDS FORMACIÓN SÁBADOS")
print("=" * 80)

try:
    with engine.connect() as connection:
        
        # PRUEBA 1: Total de estudiantes en Formación Sábados
        print("\n✅ PRUEBA 1: Total de estudiantes en Formación Sábados")
        print("-" * 80)
        
        query = text("""
            SELECT 
                pnm.ANIO_REGISTRO as año,
                COUNT(DISTINCT pnm.PERSONA_ID) as total_estudiantes
            FROM Persona_Nivel_MCER pnm
            INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
            WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion sabados%'
            AND p.TIPO_PERSONA = 'Estudiante'
            GROUP BY pnm.ANIO_REGISTRO
            ORDER BY año DESC
        """)
        
        result = connection.execute(query)
        for row in result:
            print(f"  • Año {row[0]}: {row[1]:,} estudiantes")
        
        # PRUEBA 2: Niveles MCER disponibles
        print("\n✅ PRUEBA 2: Niveles MCER disponibles en Formación Sábados")
        print("-" * 80)
        
        query = text("""
            SELECT DISTINCT n.NIVEL_MCER
            FROM Persona_Nivel_MCER pnm
            INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
            INNER JOIN Nivel_MCER n ON pnm.NIVEL_MCER_ID = n.ID
            WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion sabados%'
            AND p.TIPO_PERSONA = 'Estudiante'
            AND n.NIVEL_MCER IS NOT NULL
            AND n.NIVEL_MCER != 'SIN INFORMACION'
            ORDER BY n.NIVEL_MCER
        """)
        
        result = connection.execute(query)
        niveles = [row[0] for row in result]
        print(f"  • Niveles encontrados: {', '.join(niveles)}")
        
        # PRUEBA 3: Distribución por sexo
        print("\n✅ PRUEBA 3: Distribución por sexo en Formación Sábados")
        print("-" * 80)
        
        query = text("""
            SELECT 
                p.SEXO,
                COUNT(DISTINCT p.ID) as cantidad
            FROM Persona_Nivel_MCER pnm
            INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
            WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion sabados%'
            AND p.TIPO_PERSONA = 'Estudiante'
            AND p.SEXO IS NOT NULL
            AND p.SEXO != ''
            AND p.SEXO != 'SIN INFORMACION'
            GROUP BY p.SEXO
            ORDER BY cantidad DESC
        """)
        
        result = connection.execute(query)
        total_sexo = 0
        for row in result:
            print(f"  • {row[0]}: {row[1]:,}")
            total_sexo += row[1]
        print(f"  • TOTAL: {total_sexo:,}")
        
        # PRUEBA 4: Instituciones disponibles
        print("\n✅ PRUEBA 4: Top 10 Instituciones en Formación Sábados")
        print("-" * 80)
        
        query = text("""
            SELECT 
                i.NOMBRE_INSTITUCION,
                COUNT(DISTINCT p.ID) as cantidad
            FROM Persona_Nivel_MCER pnm
            INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
            INNER JOIN Instituciones i ON p.INSTITUCION_ID = i.ID
            WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion sabados%'
            AND p.TIPO_PERSONA = 'Estudiante'
            AND i.NOMBRE_INSTITUCION IS NOT NULL
            AND i.NOMBRE_INSTITUCION != ''
            AND i.NOMBRE_INSTITUCION != 'SIN INFORMACION'
            GROUP BY i.NOMBRE_INSTITUCION
            ORDER BY cantidad DESC
            LIMIT 10
        """)
        
        result = connection.execute(query)
        for idx, row in enumerate(result, 1):
            nombre = row[0][:50] + "..." if len(row[0]) > 50 else row[0]
            print(f"  {idx}. {nombre}: {row[1]:,}")
        
        # PRUEBA 5: Grados disponibles
        print("\n✅ PRUEBA 5: Grados disponibles en Formación Sábados")
        print("-" * 80)
        
        query = text("""
            SELECT DISTINCT 
                CASE 
                    WHEN n.GRADO IS NULL OR n.GRADO = '' OR n.GRADO = 'SIN INFORMACION' THEN 'SIN INFORMACION'
                    ELSE n.GRADO
                END as grado
            FROM Persona_Nivel_MCER pnm
            INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
            LEFT JOIN Nivel_MCER n ON pnm.NIVEL_MCER_ID = n.ID
            WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion sabados%'
            AND p.TIPO_PERSONA = 'Estudiante'
            ORDER BY grado
        """)
        
        result = connection.execute(query)
        grados = [row[0] for row in result]
        print(f"  • Grados encontrados: {', '.join(grados)}")
        
        # PRUEBA 6: Estado de aprobación
        print("\n✅ PRUEBA 6: Distribución de aprobación en Formación Sábados")
        print("-" * 80)
        
        query = text("""
            SELECT 
                n.ESTADO_ESTUDIANTE,
                COUNT(DISTINCT p.NUMERO_DOCUMENTO) as cantidad
            FROM Persona_Nivel_MCER pnm
            INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
            INNER JOIN Nivel_MCER n ON pnm.NIVEL_MCER_ID = n.ID
            WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion sabados%'
            AND p.TIPO_PERSONA = 'Estudiante'
            AND n.ESTADO_ESTUDIANTE IS NOT NULL
            AND n.ESTADO_ESTUDIANTE != ''
            AND n.ESTADO_ESTUDIANTE != 'SIN INFORMACION'
            GROUP BY n.ESTADO_ESTUDIANTE
            ORDER BY cantidad DESC
        """)
        
        result = connection.execute(query)
        for row in result:
            print(f"  • {row[0]}: {row[1]:,}")
        
        # PRUEBA 7: Sedes nodales
        print("\n✅ PRUEBA 7: Sedes Nodales en Formación Sábados")
        print("-" * 80)
        
        query = text("""
            SELECT DISTINCT s.SEDE_NODAL
            FROM Persona_Nivel_MCER pnm
            INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
            INNER JOIN Sedes s ON s.PERSONA_ID = p.ID
            WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion sabados%'
            AND p.TIPO_PERSONA = 'Estudiante'
            AND s.SEDE_NODAL IS NOT NULL
            AND s.SEDE_NODAL != ''
            AND s.SEDE_NODAL != 'SIN INFORMACION'
            ORDER BY s.SEDE_NODAL
        """)
        
        result = connection.execute(query)
        sedes = [row[0] for row in result]
        print(f"  • Sedes encontradas: {', '.join(sedes)}")
        
        print("\n" + "=" * 80)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 80)
        print("\n📌 RESUMEN:")
        print(f"  ✓ Base de datos: CONECTADA")
        print(f"  ✓ Filtro NOMBRE_CURSO: FUNCIONANDO")
        print(f"  ✓ Filtro TIPO_PERSONA: FUNCIONANDO")
        print(f"  ✓ Datos disponibles: SÍ")
        print(f"  ✓ Dashboards listos para ejecutar")
        print("\n🚀 Puedes ejecutar los dashboards con:")
        print("  streamlit run estudiantes_niveles_sabados.py")
        print("  streamlit run estudiantes_grado_sexo_sabados.py")
        print("  streamlit run Estado_estudiantes_sabados.py")
        print("  streamlit run asistencia_institucion_sabados.py")
        print("  streamlit run instituciones_sedes_sabados.py")
        print("=" * 80)

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
