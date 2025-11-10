from sqlalchemy import text
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Base_datos.conexion import engine

print("🔧 Corrigiendo campo TIPO_PERSONA...")

with engine.connect() as connection:
    # Actualizar todos los registros de Adolescentes, Infantil y Adultos a "Estudiante"
    query_update = text("""
        UPDATE Personas 
        SET TIPO_PERSONA = 'Estudiante'
        WHERE TIPO_PERSONA IN ('Adolescentes', 'Infantil', 'Adultos')
    """)
    
    result = connection.execute(query_update)
    connection.commit()
    
    print(f"✅ Actualizados {result.rowcount} registros a 'Estudiante'")
    
    # Verificar el resultado
    query_verify = text("""
        SELECT DISTINCT TIPO_PERSONA, COUNT(*) as cantidad
        FROM Personas
        GROUP BY TIPO_PERSONA
        ORDER BY TIPO_PERSONA
    """)
    
    result_verify = connection.execute(query_verify)
    print("\n📊 Distribución actual de TIPO_PERSONA:")
    for row in result_verify:
        print(f"  - {row[0]}: {row[1]} personas")

print("\n✅ Corrección completada")
