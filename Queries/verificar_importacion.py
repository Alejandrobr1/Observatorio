from sqlalchemy import text
import sys
import os

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Base_datos.conexion import engine

print("=" * 70)
print("🔍 VERIFICACIÓN DE DATOS IMPORTADOS")
print("=" * 70)

with engine.connect() as connection:
    # 1. Total personas
    result = connection.execute(text("SELECT COUNT(*) FROM Personas")).fetchone()
    print(f"\n1. Total Personas en BD: {result[0]:,}")
    
    # 2. Total en Nivel_MCER
    result = connection.execute(text("SELECT COUNT(*) FROM Nivel_MCER")).fetchone()
    print(f"2. Total registros en Nivel_MCER: {result[0]:,}")
    
    # 3. Total relaciones
    result = connection.execute(text("SELECT COUNT(*) FROM Persona_Nivel_MCER")).fetchone()
    print(f"3. Total relaciones Persona-Nivel_MCER: {result[0]:,}")
    
    # 4. Niveles MCER únicos (sin "SIN INFORMACION")
    result = connection.execute(text("""
        SELECT DISTINCT NIVEL_MCER 
        FROM Nivel_MCER 
        WHERE NIVEL_MCER IS NOT NULL 
        AND NIVEL_MCER != 'SIN INFORMACION'
        ORDER BY NIVEL_MCER
    """))
    niveles = [row[0] for row in result.fetchall()]
    print(f"\n4. Niveles MCER únicos en BD: {niveles}")
    
    # 5. Años en Persona_Nivel_MCER
    result = connection.execute(text("""
        SELECT DISTINCT ANIO_REGISTRO 
        FROM Persona_Nivel_MCER 
        WHERE ANIO_REGISTRO IS NOT NULL
        ORDER BY ANIO_REGISTRO
    """))
    years = [row[0] for row in result.fetchall()]
    print(f"5. Años registrados en Persona_Nivel_MCER: {years}")
    
    # 6. Personas con nivel MCER por año
    print(f"\n6. Distribución de estudiantes por año:")
    print("-" * 70)
    result = connection.execute(text("""
        SELECT 
            pnm.ANIO_REGISTRO,
            COUNT(DISTINCT pnm.PERSONA_ID) as cantidad
        FROM Persona_Nivel_MCER pnm
        GROUP BY pnm.ANIO_REGISTRO
        ORDER BY pnm.ANIO_REGISTRO
    """))
    for row in result.fetchall():
        print(f"   Año {row[0]}: {row[1]:,} personas con nivel MCER")
    
    # 7. Distribución por nivel MCER para cada año
    result = connection.execute(text("""
        SELECT DISTINCT ANIO_REGISTRO 
        FROM Persona_Nivel_MCER 
        WHERE ANIO_REGISTRO IS NOT NULL
        ORDER BY ANIO_REGISTRO DESC
    """))
    years = [row[0] for row in result.fetchall()]
    
    for year in years:
        print(f"\n7. Distribución por nivel MCER - Año {year}:")
        print("-" * 70)
        result = connection.execute(text("""
            SELECT 
                n.NIVEL_MCER,
                p.SEXO,
                COUNT(DISTINCT p.NUMERO_DOCUMENTO) as cantidad
            FROM Persona_Nivel_MCER pnm
            INNER JOIN Nivel_MCER n ON pnm.NIVEL_MCER_ID = n.ID
            INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
            WHERE pnm.ANIO_REGISTRO = :year
            AND n.NIVEL_MCER IS NOT NULL
            AND n.NIVEL_MCER != 'SIN INFORMACION'
            GROUP BY n.NIVEL_MCER, p.SEXO
            ORDER BY n.NIVEL_MCER, p.SEXO
        """), {'year': year})
        
        data = result.fetchall()
        if data:
            for row in data:
                print(f"   {row[0]} - {row[1]}: {row[2]:,} personas")
        else:
            print(f"   ⚠️ No hay datos con nivel MCER para {year}")
    
    # 8. Entidades disponibles
    print(f"\n8. Entidades en Cursos:")
    print("-" * 70)
    result = connection.execute(text("""
        SELECT DISTINCT ENTIDAD, COUNT(*) as cantidad
        FROM Cursos
        WHERE ENTIDAD IS NOT NULL
        GROUP BY ENTIDAD
        ORDER BY ENTIDAD
    """))
    for row in result.fetchall():
        print(f"   {row[0]}: {row[1]:,} cursos")
    
    # 9. Verificar problemas potenciales
    print(f"\n9. Diagnóstico de problemas:")
    print("-" * 70)
    
    # Personas sin nivel MCER
    result = connection.execute(text("""
        SELECT COUNT(*) 
        FROM Personas p
        LEFT JOIN Persona_Nivel_MCER pnm ON p.ID = pnm.PERSONA_ID
        WHERE pnm.ID IS NULL
        AND p.TIPO_PERSONA = 'Estudiante'
    """))
    sin_nivel = result.fetchone()[0]
    if sin_nivel > 0:
        print(f"   ⚠️ {sin_nivel:,} estudiantes SIN nivel MCER asignado")
    else:
        print(f"   ✓ Todos los estudiantes tienen nivel MCER")
    
    # Niveles MCER sin personas
    result = connection.execute(text("""
        SELECT COUNT(*)
        FROM Nivel_MCER n
        LEFT JOIN Persona_Nivel_MCER pnm ON n.ID = pnm.NIVEL_MCER_ID
        WHERE pnm.ID IS NULL
        AND n.NIVEL_MCER != 'SIN INFORMACION'
    """))
    niveles_sin_uso = result.fetchone()[0]
    if niveles_sin_uso > 0:
        print(f"   ℹ {niveles_sin_uso:,} niveles MCER sin personas asignadas")

print("\n" + "=" * 70)
print("✅ Verificación completada")
print("=" * 70)
