"""
Script para crear las tablas necesarias en la base de datos.
Ejecutar este script después de resetear la base de datos.
"""
import sys
import os
from sqlalchemy import text

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Base_datos.conexion import engine

def crear_tablas():
    """Crea las tablas de estudiantes para cada año."""
    
    # Lista de años para los que se crearán tablas
    años = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
    
    with engine.connect() as connection:
        print("Iniciando creación de tablas...")
        
        for año in años:
            nombre_tabla = f"Estudiantes_{año}"
            
            # Sentencia SQL para crear la tabla
            create_table_sql = text(f"""
            CREATE TABLE IF NOT EXISTS {nombre_tabla} (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                FECHA YEAR(4),
                SEDE_NODAL VARCHAR(255),
                POBLACION VARCHAR(255),
                NIVEL INT,
                DIA VARCHAR(50),
                JORNADA VARCHAR(50),
                MATRICULADOS INT,
                ETAPA INT
            );
            """)
            
            try:
                connection.execute(create_table_sql)
                print(f"✓ Tabla '{nombre_tabla}' creada o ya existente.")
            except Exception as e:
                print(f"✗ Error al crear la tabla '{nombre_tabla}': {e}")
        
        connection.commit()
        print("\n✅ Proceso de creación de tablas completado.")

if __name__ == "__main__":
    crear_tablas()