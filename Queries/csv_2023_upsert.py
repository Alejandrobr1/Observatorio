import pandas as pd
import os
import sys
from datetime import datetime
from sqlalchemy import text, select

# Añadir el directorio raíz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Base_datos.conexion import engine
from Base_datos.models import (Tipo_documentos, Nivel_MCER, Ciudades,
                             Instituciones_educativas, Cursos, Personas,
                             Sedes_instituciones, NivelMCERType)
from logger_config import setup_logging, get_logger

logger = get_logger(__name__)

# Funciones auxiliares

def load_csv(path_name):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    ruta = os.path.join(project_root, 'CSVs', path_name)
    logger.info(f"Loading data from {ruta}")
    return pd.read_csv(ruta, sep=';', encoding='utf-8-sig')


def ensure_persona_id_column(engine):
    """Asegura que la columna PERSONA_ID exista en Sedes_instituciones y crea FK si falta."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'Sedes_instituciones'
            AND COLUMN_NAME = 'PERSONA_ID'
        """)).fetchone()
        if result:
            logger.info('PERSONA_ID ya existe en Sedes_instituciones')
            return
    # Crear columna y FK en una transacción
    with engine.begin() as conn:
        try:
            conn.execute(text('ALTER TABLE Sedes_instituciones ADD COLUMN PERSONA_ID INT NULL'))
            conn.execute(text('ALTER TABLE Sedes_instituciones ADD CONSTRAINT fk_sedes_persona FOREIGN KEY (PERSONA_ID) REFERENCES Personas(ID)'))
            logger.info('PERSONA_ID y FK creadas en Sedes_instituciones')
        except Exception as e:
            logger.warning(f'No se pudo crear PERSONA_ID o FK: {e}')


def normalize_mcer(val):
    if pd.isna(val):
        return NivelMCERType.SIN_DIAGNOSTICO.value
    try:
        key = str(val).strip().upper().replace(' ', '_')
        return NivelMCERType[key].value
    except Exception:
        return str(val).strip()


def upsert_reference_table(engine, df_values, table_name, column_name):
    """Inserta valores únicos en una tabla de referencia si no existen."""
    if df_values.empty:
        return 0
    existing = pd.read_sql(text(f"SELECT {column_name} FROM {table_name}"), engine)
    new_vals = df_values[~df_values[column_name].isin(existing[column_name])]
    if new_vals.empty:
        return 0
    # Insertando nuevas filas
    new_vals.to_sql(table_name, engine, if_exists='append', index=False)
    return len(new_vals)


def main():
    setup_logging()
    df = load_csv('data_2023.csv')

    logger.info(f'Columnas CSV: {df.columns.tolist()}')

    # Asegurar PERSONA_ID
    ensure_persona_id_column(engine)

    # Tipo_documentos
    if 'TIPO DE IDENTIFICACIÓN' in df.columns:
        tipo_df = df[['TIPO DE IDENTIFICACIÓN']].drop_duplicates().dropna().rename(columns={'TIPO DE IDENTIFICACIÓN':'TIPO_DOCUMENTO'})
        inserted = upsert_reference_table(engine, tipo_df, 'Tipo_documentos', 'TIPO_DOCUMENTO')
        logger.info(f'Inserted {inserted} Tipo_documentos (if any)')

    # Nivel_MCER
    nivel_cols = [c for c in ['NIVEL_MCER','Población 2023','ESTADO MATRÍCULA ETAPA 2'] if c in df.columns]
    if nivel_cols:
        nivel_df = df[nivel_cols].drop_duplicates().copy()
        if 'NIVEL_MCER' in nivel_df.columns:
            nivel_df['NIVEL_MCER'] = nivel_df['NIVEL_MCER'].map(normalize_mcer)
        nivel_df = nivel_df.rename(columns={'Población 2023':'TIPO_POBLACION','ESTADO MATRÍCULA ETAPA 2':'ESTADO_ESTUDIANTE'})
        nivel_df['FECHA_ACTUAL'] = datetime.now().strftime('%Y-%m-%d')
        # Insert only missing by NIVEL_MCER
        existing_nm = pd.read_sql(text('SELECT NIVEL_MCER FROM Nivel_MCER'), engine)
        to_ins = nivel_df[~nivel_df['NIVEL_MCER'].isin(existing_nm['NIVEL_MCER'])]
        if not to_ins.empty:
            to_ins[['NIVEL_MCER','TIPO_POBLACION','ESTADO_ESTUDIANTE','FECHA_ACTUAL']].to_sql('Nivel_MCER', engine, if_exists='append', index=False)
            logger.info(f'Inserted {len(to_ins)} Nivel_MCER')

    # Ciudades
    if 'MUNICIPIO' in df.columns:
        ciu = df[['MUNICIPIO']].drop_duplicates().dropna().rename(columns={'MUNICIPIO':'MUNICIPIO'})
        inserted = upsert_reference_table(engine, ciu, 'Ciudades', 'MUNICIPIO')
        logger.info(f'Inserted {inserted} Ciudades')

    # Instituciones
    inst_cols = [c for c in ['Institución Educativa 2023','COLEGIO ABREVIADO PARA LISTADOS','Grado 2023'] if c in df.columns]
    if inst_cols:
        inst_df = df[inst_cols].drop_duplicates().rename(columns={'Institución Educativa 2023':'INSTITUCION_EDUCATIVA','COLEGIO ABREVIADO PARA LISTADOS':'COLEGIO_ABREVIADO','Grado 2023':'GRADO'})
        # Insert only by INSTITUCION_EDUCATIVA
        existing_inst = pd.read_sql(text('SELECT INSTITUCION_EDUCATIVA FROM Instituciones_educativas'), engine)
        to_ins = inst_df[~inst_df['INSTITUCION_EDUCATIVA'].isin(existing_inst['INSTITUCION_EDUCATIVA'])]
        if not to_ins.empty:
            to_ins.to_sql('Instituciones_educativas', engine, if_exists='append', index=False)
            logger.info(f'Inserted {len(to_ins)} Instituciones_educativas')

    # Cursos - attempt to map Nivel_MCER
    cursos_cols = [c for c in ['ENTIDAD','NOMBRE CURSO','IDIOMA','NIVEL_MCER'] if c in df.columns]
    if cursos_cols:
        cursos_df = df[cursos_cols].drop_duplicates().rename(columns={'NOMBRE CURSO':'NOMBRE_CURSO'})
        nivel_table = pd.read_sql(text('SELECT ID,NIVEL_MCER FROM Nivel_MCER'), engine)
        if 'NIVEL_MCER' in cursos_df.columns:
            cursos_df['NIVEL_MCER'] = cursos_df['NIVEL_MCER'].map(normalize_mcer)
            def map_nm(x):
                m = nivel_table[nivel_table['NIVEL_MCER']==x]
                return int(m['ID'].iloc[0]) if not m.empty else None
            cursos_df['NIVEL_MCER_ID'] = cursos_df['NIVEL_MCER'].map(map_nm)
        cursos_insert = cursos_df[['ENTIDAD','NOMBRE_CURSO','IDIOMA','NIVEL_MCER_ID']].drop_duplicates()
        # Avoid duplicates by ENTIDAD+NOMBRE_CURSO
        existing_cursos = pd.read_sql(text('SELECT ENTIDAD,NOMBRE_CURSO FROM Cursos'), engine)
        merged = cursos_insert.merge(existing_cursos, how='left', on=['ENTIDAD','NOMBRE_CURSO'], indicator=True)
        new_cursos = merged[merged['_merge']=='left_only'].drop(columns=['_merge'])
        if not new_cursos.empty:
            new_cursos.to_sql('Cursos', engine, if_exists='append', index=False)
            logger.info(f'Inserted {len(new_cursos)} Cursos')

    # Personas - insert only new persons
    personas_map = {
        'NOMBRES':'NOMBRES2','APELLIDOS':'APELLIDOS','TELÉFONO 1':'TELEFONO1','TELÉFONO 2':'TELEFONO2',
        'NÚMERO DE IDENTIFICACIÓN':'NUMERO_DOCUMENTO','CORREO ELECTRÓNICO':'CORREO_ELECTRONICO','DIRECCIÓN':'DIRECCION',
        'SEXO':'SEXO','FECHA DE NACIMIENTO':'FECHA_NACIMIENTO','CERTIFICADO':'CERTIFICADO','TIPO POBLACION':'TIPO_PERSONA',
        'MUNICIPIO':'MUNICIPIO','TIPO DE IDENTIFICACIÓN':'TIPO_DOCUMENTO','NIVEL_MCER':'NIVEL_MCER'
    }
    present = {k:v for k,v in personas_map.items() if k in df.columns}
    if present:
        pers = df[list(present.keys())].copy().rename(columns=present)
        # Clean NUMERO_DOCUMENTO
        if 'NUMERO_DOCUMENTO' in pers.columns:
            pers['NUMERO_DOCUMENTO'] = pers['NUMERO_DOCUMENTO'].astype(str).str.replace('.', '', regex=False)
            pers['NUMERO_DOCUMENTO'] = pd.to_numeric(pers['NUMERO_DOCUMENTO'], errors='coerce')
            # get existing
            existing_nums = pd.read_sql(text('SELECT NUMERO_DOCUMENTO FROM Personas'), engine)
            existing_set = set(existing_nums['NUMERO_DOCUMENTO'].dropna().astype(int).tolist())
            new_pers = pers[~pers['NUMERO_DOCUMENTO'].isin(existing_set)].copy()
            if not new_pers.empty:
                # map fks
                tipo_tbl = pd.read_sql(text('SELECT ID,TIPO_DOCUMENTO FROM Tipo_documentos'), engine)
                nivel_tbl = pd.read_sql(text('SELECT ID,NIVEL_MCER FROM Nivel_MCER'), engine)
                ciudad_tbl = pd.read_sql(text('SELECT ID,MUNICIPIO FROM Ciudades'), engine)
                # helper to safely map textual value -> integer ID from a reference table
                def map_id_from_table(tbl, key_col, id_col):
                    def _mapper(v):
                        if pd.isna(v):
                            return None
                        m = tbl[tbl[key_col] == v]
                        if m.empty:
                            return None
                        val = m[id_col].iloc[0]
                        try:
                            return int(val)
                        except Exception:
                            return None
                    return _mapper

                if 'TIPO_DOCUMENTO' in new_pers.columns:
                    new_pers['TIPO_DOCUMENTO_ID'] = new_pers['TIPO_DOCUMENTO'].map(map_id_from_table(tipo_tbl, 'TIPO_DOCUMENTO', 'ID'))
                if 'NIVEL_MCER' in new_pers.columns:
                    new_pers['NIVEL_MCER'] = new_pers['NIVEL_MCER'].map(normalize_mcer)
                    new_pers['NIVEL_MCER_ID'] = new_pers['NIVEL_MCER'].map(map_id_from_table(nivel_tbl, 'NIVEL_MCER', 'ID'))
                if 'MUNICIPIO' in new_pers.columns:
                    new_pers['CIUDAD_ID'] = new_pers['MUNICIPIO'].map(map_id_from_table(ciudad_tbl, 'MUNICIPIO', 'ID'))

                # ensure Personas has the FK columns we will write
                def ensure_column_exists(engine, table, column, sql_type='INT NULL'):
                    with engine.connect() as conn:
                        r = conn.execute(text(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND COLUMN_NAME='{column}'")).fetchone()
                        if not r:
                            logger.info(f"Adding column {column} to {table}")
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"))

                ensure_column_exists(engine, 'Personas', 'TIPO_DOCUMENTO_ID', 'INT NULL')
                ensure_column_exists(engine, 'Personas', 'NIVEL_MCER_ID', 'INT NULL')
                ensure_column_exists(engine, 'Personas', 'CIUDAD_ID', 'INT NULL')

                # select columns compatible with Personas table
                cols = ['NOMBRES2','APELLIDOS','TELEFONO1','TELEFONO2','NUMERO_DOCUMENTO','CORREO_ELECTRONICO','DIRECCION','SEXO','FECHA_NACIMIENTO','CERTIFICADO','TIPO_PERSONA','TIPO_DOCUMENTO_ID','NIVEL_MCER_ID','CIUDAD_ID']
                insert_df = new_pers[[c for c in cols if c in new_pers.columns]].copy()
                # normalize FECHA_NACIMIENTO to datetime (day-first formats like 8/03/2007)
                if 'FECHA_NACIMIENTO' in insert_df.columns:
                    insert_df['FECHA_NACIMIENTO'] = pd.to_datetime(insert_df['FECHA_NACIMIENTO'], dayfirst=True, errors='coerce')
                # CERTIFICADO in DB is numeric (double) in current schema; map common textual values to numeric
                if 'CERTIFICADO' in insert_df.columns:
                    insert_df['CERTIFICADO'] = insert_df['CERTIFICADO'].astype(str).str.strip().str.upper()
                    insert_df['CERTIFICADO'] = insert_df['CERTIFICADO'].replace({
                        'YES': 1,
                        'SI': 1,
                        'S': 1,
                        'Y': 1,
                        'NO': 0,
                        'N': 0,
                        'NONE': None,
                        'NAN': None,
                        '': None
                    })
                    insert_df['CERTIFICADO'] = pd.to_numeric(insert_df['CERTIFICADO'], errors='coerce')

                insert_df.to_sql('Personas', engine, if_exists='append', index=False)
                logger.info(f'Inserted {len(insert_df)} new Personas')
            else:
                logger.info('No hay Personas nuevas')

    logger.info('Upsert process finished')

if __name__ == '__main__':
    main()
