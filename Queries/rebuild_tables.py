import pandas as pd
from sqlalchemy import text
import sys
import os
from datetime import datetime

# Añadir el directorio raíz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Base_datos.conexion import engine
from Base_datos.models_rebuild import Base
from logger_config import setup_logging, get_logger

logger = get_logger(__name__)

def create_default_person(engine):
    """Creates or verifies existence of default person for foreign key references"""
    try:
        # Crear la persona por defecto en una transacción separada
        with engine.begin() as conn:
            # Obtener IDs necesarios
            tipo_id = conn.execute(text("SELECT ID FROM Tipo_documentos WHERE TIPO_DOCUMENTO = 'NO TIENE'")).scalar()
            nivel_id = conn.execute(text("SELECT ID FROM Nivel_MCER WHERE NIVEL_MCER = 'SIN DIAGNOSTICO'")).scalar()
            ciudad_id = conn.execute(text("SELECT ID FROM Ciudades WHERE MUNICIPIO = 'NO ESPECIFICADA'")).scalar()

            # Verificar si ya existe la persona por defecto (por ejemplo por NOMBRES2 y APELLIDOS)
            exists_id = conn.execute(text("SELECT ID FROM Personas WHERE NOMBRES2 = 'NO TIENE' AND APELLIDOS = 'NO TIENE' LIMIT 1")).scalar()
            if exists_id:
                default_person_id = exists_id
                logger.info('Default person already exists with ID %s', default_person_id)
            else:
                # Insertar persona por defecto sin NUMERO_DOCUMENTO (NULL) para no colisionar con documentos reales
                conn.execute(text("""
                    INSERT INTO Personas (
                        NOMBRES2, APELLIDOS, TIPO_PERSONA,
                        TIPO_DOCUMENTO_ID, NIVEL_MCER_ID, CIUDAD_ID,
                        CERTIFICADO, TELEFONO1, TELEFONO2,
                        CORREO_ELECTRONICO, DIRECCION, SEXO
                    ) VALUES (
                        'NO TIENE', 'NO TIENE', 'NO ESPECIFICADA',
                        :tipo_id, :nivel_id, :ciudad_id,
                        0, 'NO TIENE', 'NO TIENE',
                        'NO TIENE', 'NO TIENE', 'NO ESPECIFICADO'
                    )
                """), {'tipo_id': tipo_id, 'nivel_id': nivel_id, 'ciudad_id': ciudad_id})

                # Obtener el ID asignado
                default_person_id = conn.execute(text("SELECT ID FROM Personas WHERE NOMBRES2 = 'NO TIENE' AND APELLIDOS = 'NO TIENE' ORDER BY ID DESC LIMIT 1")).scalar()
                if not default_person_id:
                    raise RuntimeError('Could not create default person')
                logger.info('Created default person with ID %s', default_person_id)

            # Retornar los IDs de valores por defecto y el ID de persona por defecto
            return {
                'tipo_id': tipo_id,
                'nivel_id': nivel_id,
                'ciudad_id': ciudad_id,
                'default_person_id': default_person_id
            }
    except Exception as e:
        logger.error(f"Failed to create default person: {e}")
        raise

def drop_tables(engine):
    """Elimina las tablas si existen"""
    tables = ['Sedes_instituciones', 'Cursos', 'Personas', 'Instituciones_educativas', 
              'Ciudades', 'Nivel_MCER', 'Tipo_documentos']
    with engine.begin() as conn:
        for table in tables:
            try:
                conn.execute(text(f'DROP TABLE IF EXISTS {table}'))
                logger.info(f'Dropped {table} if existed')
            except Exception as e:
                logger.warning(f'Could not drop {table}: {e}')

def create_new_tables(engine):
    """Crea las nuevas tablas con tipos correctos y FKs"""
    Base.metadata.create_all(engine)
    logger.info('Created new tables with proper types and constraints')

def insert_default_values(engine):
    """Inserta valores por defecto en tablas de referencia"""
    with engine.begin() as conn:
        # Tipo_documentos default
        conn.execute(text("INSERT INTO Tipo_documentos (TIPO_DOCUMENTO) VALUES ('NO TIENE')"))
        logger.info('Inserted default value into Tipo_documentos')

        # Nivel_MCER default
        conn.execute(text("""
            INSERT INTO Nivel_MCER 
            (NIVEL_MCER, TIPO_POBLACION, ESTADO_ESTUDIANTE, FECHA_ACTUAL) 
            VALUES 
            ('SIN DIAGNOSTICO', 'NO ESPECIFICADA', 'NO ESPECIFICADO', :fecha)
        """), {'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        logger.info('Inserted default value into Nivel_MCER')

        # Ciudades default
        conn.execute(text("INSERT INTO Ciudades (MUNICIPIO) VALUES ('NO ESPECIFICADA')"))
        logger.info('Inserted default value into Ciudades')

def clean_numeric(val):
    """Limpia valores numéricos eliminando puntos y espacios"""
    if pd.isna(val):
        return None
    try:
        # Eliminar puntos, espacios, guiones y convertir a int
        cleaned = str(val).replace('.', '').replace(' ', '').replace('-', '')
        return int(cleaned) if cleaned.isdigit() else None
    except Exception:
        return None

def migrate_data(engine, default_ids):
    """Migra datos desde tablas _old a nuevas tablas, limpiando y mapeando valores"""
    # 1. Migrar datos de tablas de referencia primero
    # Tipo_documentos - Eliminar IDs existentes para evitar conflictos
    old_tipos = pd.read_sql('SELECT DISTINCT TIPO_DOCUMENTO FROM Tipo_documentos_old', engine)
    old_tipos.to_sql('Tipo_documentos', engine, if_exists='append', index=False)
    logger.info(f'Migrated {len(old_tipos)} Tipo_documentos')

    # Nivel_MCER - Eliminar IDs y fechas inválidas
    old_nivel = pd.read_sql('SELECT DISTINCT NIVEL_MCER, TIPO_POBLACION, ESTADO_ESTUDIANTE FROM Nivel_MCER_old', engine)
    old_nivel['FECHA_ACTUAL'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    old_nivel.to_sql('Nivel_MCER', engine, if_exists='append', index=False)
    logger.info(f'Migrated {len(old_nivel)} Nivel_MCER')

    # Ciudades - Solo migrar MUNICIPIO
    old_ciudades = pd.read_sql('SELECT DISTINCT MUNICIPIO FROM Ciudades_old', engine)
    old_ciudades.to_sql('Ciudades', engine, if_exists='append', index=False)
    logger.info(f'Migrated {len(old_ciudades)} Ciudades')

    # Actualizar mapeos después de la migración
    tipo_map = pd.read_sql('SELECT ID, TIPO_DOCUMENTO FROM Tipo_documentos', engine).set_index('TIPO_DOCUMENTO')['ID'].to_dict()
    nivel_map = pd.read_sql('SELECT ID, NIVEL_MCER FROM Nivel_MCER', engine).set_index('NIVEL_MCER')['ID'].to_dict()
    ciudad_map = pd.read_sql('SELECT ID, MUNICIPIO FROM Ciudades', engine).set_index('MUNICIPIO')['ID'].to_dict()

    # Instituciones_educativas - Migrar sin IDs
    old_inst = pd.read_sql('''
        SELECT DISTINCT INSTITUCION_EDUCATIVA, COLEGIO_ABREVIADO, GRADO 
        FROM Instituciones_educativas_old
    ''', engine)
    old_inst.to_sql('Instituciones_educativas', engine, if_exists='append', index=False)
    logger.info(f'Migrated {len(old_inst)} Instituciones_educativas')

    # 2. Migrar Personas limpiando datos
    old_pers = pd.read_sql('SELECT * FROM Personas_old', engine)
    # Limpiar NUMERO_DOCUMENTO
    old_pers['NUMERO_DOCUMENTO'] = old_pers['NUMERO_DOCUMENTO'].apply(clean_numeric)
    old_pers = old_pers.dropna(subset=['NUMERO_DOCUMENTO'])  # Eliminar registros sin número de documento
    
    # Mapear o usar default ID para valores no encontrados
    if 'TIPO_DOCUMENTO' in old_pers.columns:
        old_pers['TIPO_DOCUMENTO_ID'] = old_pers['TIPO_DOCUMENTO'].map(tipo_map).fillna(default_ids['tipo_id'])
    else:
        old_pers['TIPO_DOCUMENTO_ID'] = default_ids['tipo_id']
        
    if 'NIVEL_MCER' in old_pers.columns:
        old_pers['NIVEL_MCER_ID'] = old_pers['NIVEL_MCER'].map(nivel_map).fillna(default_ids['nivel_id'])
    else:
        old_pers['NIVEL_MCER_ID'] = default_ids['nivel_id']
        
    if 'MUNICIPIO' in old_pers.columns:
        old_pers['CIUDAD_ID'] = old_pers['MUNICIPIO'].map(ciudad_map).fillna(default_ids['ciudad_id'])
    else:
        old_pers['CIUDAD_ID'] = default_ids['ciudad_id']
    
    # Convertir CERTIFICADO a numérico
    if 'CERTIFICADO' in old_pers.columns:
        old_pers['CERTIFICADO'] = old_pers['CERTIFICADO'].astype(str).str.upper()
        old_pers['CERTIFICADO'] = old_pers['CERTIFICADO'].map({'YES': 1, 'SI': 1, 'S': 1, 'Y': 1,
                                                              'NO': 0, 'N': 0}).fillna(0)
    else:
        old_pers['CERTIFICADO'] = 0
    
    # Seleccionar columnas válidas y migrar
    valid_cols = ['NOMBRES2', 'APELLIDOS', 'TELEFONO1', 'TELEFONO2', 'NUMERO_DOCUMENTO',
                  'CORREO_ELECTRONICO', 'DIRECCION', 'SEXO', 'FECHA_NACIMIENTO', 'CERTIFICADO',
                  'TIPO_PERSONA', 'TIPO_DOCUMENTO_ID', 'NIVEL_MCER_ID', 'CIUDAD_ID']
    to_migrate = old_pers[[c for c in valid_cols if c in old_pers.columns]]
    
    # Asegurar que no haya duplicados en NUMERO_DOCUMENTO
    to_migrate = to_migrate.drop_duplicates(subset=['NUMERO_DOCUMENTO'], keep='first')
    
    # Migrar personas en bloques para evitar problemas de memoria
    CHUNK_SIZE = 100
    for i in range(0, len(to_migrate), CHUNK_SIZE):
        chunk = to_migrate.iloc[i:i+CHUNK_SIZE]
        chunk.to_sql('Personas', engine, if_exists='append', index=False)
    logger.info(f'Migrated {len(to_migrate)} Personas')

    # Construir mapeo NUMERO_DOCUMENTO -> Personas.ID para usar en Sedes_instituciones
    persona_map_df = pd.read_sql('SELECT ID, NUMERO_DOCUMENTO FROM Personas WHERE NUMERO_DOCUMENTO IS NOT NULL', engine)
    persona_map = dict(zip(persona_map_df['NUMERO_DOCUMENTO'], persona_map_df['ID']))

    # 3. Migrar Cursos
    old_cursos = pd.read_sql('SELECT ENTIDAD, NOMBRE_CURSO, IDIOMA FROM Cursos_old', engine)
    old_cursos['NIVEL_MCER_ID'] = default_ids['nivel_id']  # Usar default para todos
    old_cursos.to_sql('Cursos', engine, if_exists='append', index=False)
    logger.info(f'Migrated {len(old_cursos)} Cursos')

    # 4. Migrar Sedes_instituciones
    old_sedes = pd.read_sql('''
        SELECT GRUPO, JORNADA, FECHA_INICIAL, FECHA_FINAL, SEDE,
               INSTITUCION_EDUCATIVA, PERSONA_ID 
        FROM Sedes_instituciones_old
    ''', engine)
    
    # Limpiar PERSONA_ID y mapear desde NUMERO_DOCUMENTO -> Personas.ID
    old_sedes['PERSONA_ID'] = old_sedes['PERSONA_ID'].apply(clean_numeric)
    default_person_id = default_ids.get('default_person_id')
    # Map the document number to person ID, fallback to default_person_id
    old_sedes['PERSONA_ID'] = old_sedes['PERSONA_ID'].apply(lambda x: persona_map.get(x, default_person_id))
    
    # Migrar por bloques
    CHUNK_SIZE = 100
    for i in range(0, len(old_sedes), CHUNK_SIZE):
        chunk = old_sedes.iloc[i:i+CHUNK_SIZE]
        chunk.to_sql('Sedes_instituciones', engine, if_exists='append', index=False)
    logger.info(f'Migrated {len(old_sedes)} Sedes_instituciones')

def verify_constraints(engine):
    """Verifica que las relaciones estén correctas"""
    checks = [
        ("Personas sin TIPO_DOCUMENTO_ID válido", 
         "SELECT COUNT(*) as cnt FROM Personas p LEFT JOIN Tipo_documentos t ON p.TIPO_DOCUMENTO_ID = t.ID WHERE t.ID IS NULL"),
        ("Personas sin NIVEL_MCER_ID válido",
         "SELECT COUNT(*) as cnt FROM Personas p LEFT JOIN Nivel_MCER n ON p.NIVEL_MCER_ID = n.ID WHERE n.ID IS NULL"),
        ("Personas sin CIUDAD_ID válido",
         "SELECT COUNT(*) as cnt FROM Personas p LEFT JOIN Ciudades c ON p.CIUDAD_ID = c.ID WHERE c.ID IS NULL"),
        ("Cursos sin NIVEL_MCER_ID válido",
         "SELECT COUNT(*) as cnt FROM Cursos c LEFT JOIN Nivel_MCER n ON c.NIVEL_MCER_ID = n.ID WHERE n.ID IS NULL"),
    ("Sedes_instituciones con PERSONA_ID inválido",
     "SELECT COUNT(*) as cnt FROM Sedes_instituciones s LEFT JOIN Personas p ON s.PERSONA_ID = p.ID WHERE p.ID IS NULL")
    ]
    
    with engine.connect() as conn:
        for desc, query in checks:
            result = conn.execute(text(query)).fetchone()[0]
            logger.info(f"{desc}: {result} registros")

def main():
    setup_logging()
    logger.info("Starting database rebuild process...")
    
    # 1. Drop existing tables (if any)
    drop_tables(engine)
    
    # 2. Crear nuevas tablas con estructura correcta
    create_new_tables(engine)
    
    # 3. Insertar valores por defecto
    insert_default_values(engine)
    
    # 4. Crear persona por defecto y obtener IDs
    default_ids = create_default_person(engine)
    
    # 5. Migrar datos desde _old
    migrate_data(engine, default_ids)
    
    # 6. Verificar constraints
    verify_constraints(engine)
    
    logger.info("Database rebuild complete")

if __name__ == '__main__':
    main()