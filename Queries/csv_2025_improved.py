import pandas as pd
import os
import sys
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

# Añadir el directorio raíz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Base_datos.conexion import engine
from Base_datos.models import (Tipo_documentos, Nivel_MCER, Ciudades, 
                             Instituciones_educativas, Cursos, Personas, 
                             Sedes_instituciones, NivelMCERType, TipoPersonaType)
from logger_config import setup_logging, get_logger

logger = get_logger(__name__)

class DataValidator:
    def __init__(self, engine):
        self.engine = engine
        self.session = Session(engine)
        self.validation_errors = []

    def validate_foreign_keys(self, df, table_name, fk_mappings):
        """Valida que las foreign keys existan en las tablas padre."""
        valid_mask = pd.Series(True, index=df.index)
        
        for col, (parent_table, parent_col) in fk_mappings.items():
            if col in df.columns:
                # Obtener valores únicos de la columna FK
                fk_values = df[col].dropna().unique()
                
                # Consultar valores existentes en la tabla padre
                query = select(getattr(parent_table, parent_col))
                existing_values = pd.read_sql(query.where(
                    getattr(parent_table, parent_col).in_(fk_values)
                ), self.engine)
                
                # Identificar valores que no existen
                missing_values = set(fk_values) - set(existing_values[parent_col])
                
                if missing_values:
                    error_rows = df[df[col].isin(missing_values)]
                    self.validation_errors.append({
                        'table': table_name,
                        'column': col,
                        'missing_values': missing_values,
                        'affected_rows': error_rows.index.tolist()
                    })
                    valid_mask &= ~df[col].isin(missing_values)
                    
                    logger.error(
                        f"Foreign key validation error in {table_name}.{col}: "
                        f"Values {missing_values} not found in {parent_table.__tablename__}"
                    )
        
        return df[valid_mask]

    def clean_and_validate_personas(self, df):
        """Limpia y valida datos para la tabla Personas."""
        cleaned_df = df.copy()
        invalid_docs = pd.Series(dtype=object)
        invalid_dates = pd.Series(dtype=object)
        
        try:
            # Validar y limpiar cada columna que debería existir
            if 'NUMERO_DOCUMENTO' in cleaned_df.columns:
                cleaned_df['NUMERO_DOCUMENTO'] = cleaned_df['NUMERO_DOCUMENTO'].astype(str).str.replace('.', '', regex=False)
                cleaned_df['NUMERO_DOCUMENTO'] = pd.to_numeric(cleaned_df['NUMERO_DOCUMENTO'], errors='coerce')
                invalid_docs = cleaned_df[pd.isna(cleaned_df['NUMERO_DOCUMENTO'])]['NUMERO_DOCUMENTO']
                if not invalid_docs.empty:
                    logger.warning(f"Documentos inválidos encontrados: {invalid_docs.tolist()}")
            else:
                logger.warning("Columna NUMERO_DOCUMENTO no encontrada")
            
            if 'FECHA_NACIMIENTO' in cleaned_df.columns:
                cleaned_df['FECHA_NACIMIENTO'] = pd.to_datetime(
                    cleaned_df['FECHA_NACIMIENTO'],
                    format='%d/%m/%Y',
                    errors='coerce'
                )
                invalid_dates = cleaned_df[pd.isna(cleaned_df['FECHA_NACIMIENTO'])]['FECHA_NACIMIENTO']
                if not invalid_dates.empty:
                    logger.warning(f"Fechas de nacimiento inválidas encontradas: {invalid_dates.tolist()}")
            else:
                logger.warning("Columna FECHA_NACIMIENTO no encontrada")

            # Validar campos obligatorios
            required_fields = ['NOMBRES2', 'APELLIDOS', 'NUMERO_DOCUMENTO']
            for field in required_fields:
                if field in cleaned_df.columns:
                    missing = cleaned_df[pd.isna(cleaned_df[field])][field]
                    if not missing.empty:
                        logger.error(f"Registros con {field} faltante: {len(missing)}")
                else:
                    logger.error(f"Campo requerido {field} no encontrado en el DataFrame")
            
            # Validar y limpiar correos
            if 'CORREO_ELECTRONICO' in cleaned_df.columns:
                cleaned_df['CORREO_ELECTRONICO'] = cleaned_df['CORREO_ELECTRONICO'].fillna('')
                cleaned_df['CORREO_ELECTRONICO'] = cleaned_df['CORREO_ELECTRONICO'].astype(str).str.lower().str.strip()
                
                mask = ~cleaned_df['CORREO_ELECTRONICO'].str.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
                mask = mask & (cleaned_df['CORREO_ELECTRONICO'] != '')
                invalid_emails = cleaned_df[mask]['CORREO_ELECTRONICO']
                if not invalid_emails.empty:
                    logger.warning(f"Correos electrónicos inválidos encontrados: {invalid_emails.tolist()}")

            # Validar tipo de persona
            if 'TIPO_PERSONA' in cleaned_df.columns:
                def map_tipo_persona(tipo):
                    if pd.isna(tipo) or not tipo:
                        return None
                    tipo = str(tipo).strip().lower()
                    if 'docente' in tipo:
                        return TipoPersonaType.Docente.value
                    elif 'estudiante' in tipo:
                        return TipoPersonaType.Estudiante.value
                    else:
                        logger.warning(f"Tipo de persona no reconocido: {tipo}")
                        return None
                
                cleaned_df['TIPO_PERSONA'] = cleaned_df['TIPO_PERSONA'].map(map_tipo_persona)
            
            # Limpiar teléfonos
            for tel_field in ['TELEFONO1', 'TELEFONO2']:
                if tel_field in cleaned_df.columns:
                    cleaned_df[tel_field] = cleaned_df[tel_field].fillna('')
                    cleaned_df[tel_field] = cleaned_df[tel_field].astype(str).str.replace(r'[^\d+]', '', regex=True)
                    invalid_phones = cleaned_df[
                        (cleaned_df[tel_field].str.len() < 7) & 
                        (cleaned_df[tel_field] != '')
                    ][tel_field]
                    if not invalid_phones.empty:
                        logger.warning(f"Teléfonos inválidos en {tel_field}: {invalid_phones.tolist()}")
            
        except Exception as e:
            logger.error(f"Error durante la limpieza de datos de Personas: {str(e)}")
            raise
        
        return cleaned_df

    def clean_and_validate_sedes(self, df):
        """Limpia y valida datos para la tabla Sedes_instituciones."""
        cleaned_df = df.copy()
        
        try:
            # Convertir fechas
            for fecha_col in ['FECHA_INICIAL', 'FECHA_FINAL']:
                if fecha_col in cleaned_df.columns:
                    cleaned_df[fecha_col] = pd.to_datetime(
                        cleaned_df[fecha_col],
                        format='%d/%m/%Y',
                        errors='coerce'
                    )
                    invalid_dates = cleaned_df[pd.isna(cleaned_df[fecha_col])][fecha_col]
                    if not invalid_dates.empty:
                        logger.warning(f"Fechas inválidas en {fecha_col}: {invalid_dates.tolist()}")
                else:
                    logger.warning(f"Columna {fecha_col} no encontrada")
            
            # Validar foreign keys
            fk_mappings = {
                'CURSO_ID': (Cursos, 'ID'),
                'INSTITUCION_EDUCATIVA_ID': (Instituciones_educativas, 'ID')
            }
            
            return self.validate_foreign_keys(cleaned_df, 'Sedes_instituciones', fk_mappings)
        
        except Exception as e:
            logger.error(f"Error durante la limpieza de datos de Sedes: {str(e)}")
            raise

def load_data():
    """Carga y procesa los datos del CSV."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    ruta_archivo = os.path.join(project_root, "CSVs", "data_2025.csv")
    
    logger.info(f"Loading data from {ruta_archivo}")
    return pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')

def main():
    try:
        # Configurar logging
        setup_logging()
        
        # Cargar datos
        df = load_data()
        validator = DataValidator(engine)
        
        # Mostrar columnas disponibles para diagnóstico
        logger.info(f"Columnas disponibles en el DataFrame: {df.columns.tolist()}")
        
        logger.info("Processing reference tables...")
        
        # Tipo_documentos
        tipo_docs_mapping = {
            'TIPO DE IDENTIFICACIÓN': 'TIPO_DOCUMENTO'
        }
        tipo_docs = df[list(tipo_docs_mapping.keys())].drop_duplicates().dropna()
        tipo_docs = tipo_docs.rename(columns=tipo_docs_mapping)
        tipo_docs['ID'] = range(1, len(tipo_docs) + 1)
        
        # Nivel_MCER
        nivel_mcer_mapping = {
            'NIVEL_MCER': 'NIVEL_MCER',
            'POBLACIÓN': 'TIPO_POBLACION',
            'ESTADO DEL ESTUDIANTE 2025': 'ESTADO_ESTUDIANTE'
        }
        nivel_mcer = df[list(nivel_mcer_mapping.keys())].drop_duplicates().copy()
        nivel_mcer = nivel_mcer.rename(columns=nivel_mcer_mapping)
        nivel_mcer['ID'] = range(1, len(nivel_mcer) + 1)
        nivel_mcer['FECHA_ACTUAL'] = datetime.now().strftime('%Y-%m-%d')
        
        # Convertir MCER a enum
        def convert_to_mcer(x):
            if pd.isna(x):
                return "SIN DIAGNOSTICO"
            try:
                x_clean = str(x).strip().upper().replace(' ', '_')
                return NivelMCERType[x_clean].value
            except KeyError:
                logger.warning(f"Valor MCER no reconocido: {x}, usando SIN DIAGNOSTICO")
                return "SIN DIAGNOSTICO"
        
        nivel_mcer['NIVEL_MCER'] = nivel_mcer['NIVEL_MCER'].map(convert_to_mcer)
        
        # Ciudades
        ciudades_mapping = {
            'MUNICIPIO': 'MUNICIPIO'
        }
        ciudades = df[list(ciudades_mapping.keys())].drop_duplicates().dropna()
        ciudades = ciudades.rename(columns=ciudades_mapping)
        ciudades['ID'] = range(1, len(ciudades) + 1)
        
        # Instituciones
        inst_mapping = {
            'INSTITUCIÓN EDUCATIVA 2025': 'INSTITUCION_EDUCATIVA',
            'COLEGIO ABREVIADO PARA LISTADOS': 'COLEGIO_ABREVIADO',
            'GRADO 2025': 'GRADO'
        }
        instituciones = df[list(inst_mapping.keys())].drop_duplicates()
        instituciones = instituciones.rename(columns=inst_mapping)
        instituciones['ID'] = range(1, len(instituciones) + 1)
        
        logger.info("Processing main tables...")
        
        # Cursos
        cursos_mapping = {
            'ENTIDAD': 'ENTIDAD',
            'NOMBRE CURSO': 'NOMBRE_CURSO',
            'IDIOMA': 'IDIOMA',
            'NIVEL_MCER': 'NIVEL_MCER_ID'  # Se necesitará mapear con el ID correcto
        }
        cursos = df[list(cursos_mapping.keys())].drop_duplicates().copy()
        cursos = cursos.rename(columns=cursos_mapping)
        cursos['ID'] = range(1, len(cursos) + 1)
        
        # Personas
        personas_mapping = {
            'NOMBRES2': 'NOMBRES2',
            'APELLIDOS': 'APELLIDOS',
            'TELÉFONO 1': 'TELEFONO1',
            'TELÉFONO 2': 'TELEFONO2',
            'NÚMERO DE IDENTIFICACIÓN': 'NUMERO_DOCUMENTO',
            'CORREO ELECTRÓNICO': 'CORREO_ELECTRONICO',
            'DIRECCIÓN': 'DIRECCION',
            'SEXO': 'SEXO',
            'FECHA DE NACIMIENTO': 'FECHA_NACIMIENTO',
            'CERTIFICADO 2025': 'CERTIFICADO',
            'TIPO POBLACION': 'TIPO_PERSONA'
        }
        
        columnas_existentes = {k: v for k, v in personas_mapping.items() if k in df.columns}
        personas = df[list(columnas_existentes.keys())].copy()
        personas = personas.rename(columns=columnas_existentes)
        personas = validator.clean_and_validate_personas(personas)
        
        # Sedes_instituciones
       # En la sección de Sedes_instituciones, agregar el mapeo de persona
        sedes_mapping = {
            'GRUPO - 2025': 'GRUPO',
            'JORNADA ETAPA 2025': 'JORNADA',
            'FECHA INICIAL': 'FECHA_INICIAL',
            'FECHA FINAL': 'FECHA_FINAL',
            'SEDE 2025': 'SEDE',
            'INSTITUCIÓN EDUCATIVA 2025': 'INSTITUCION_EDUCATIVA',
            'NÚMERO DE IDENTIFICACIÓN': 'PERSONA_ID'  # AÑADIR ESTA LÍNEA
        }

        
        columnas_existentes = {k: v for k, v in sedes_mapping.items() if k in df.columns}
        sedes = df[list(columnas_existentes.keys())].copy()
        sedes = sedes.rename(columns=columnas_existentes)
        sedes = validator.clean_and_validate_sedes(sedes)
        
        # Insertar datos en orden correcto
        with engine.begin() as connection:
            logger.info("Inserting data into database...")
            
            for table, data in [
                (Tipo_documentos.__table__, tipo_docs),
                (Nivel_MCER.__table__, nivel_mcer),
                (Ciudades.__table__, ciudades),
                (Instituciones_educativas.__table__, instituciones),
                (Cursos.__table__, cursos),
                (Personas.__table__, personas),
                (Sedes_instituciones.__table__, sedes)
            ]:
                try:
                    data.to_sql(
                        table.name,
                        connection,
                        if_exists='append',
                        index=False
                    )
                    logger.info(f"Successfully inserted {len(data)} rows into {table.name}")
                except Exception as e:
                    logger.error(f"Error inserting data into {table.name}: {str(e)}")
                    raise
        
        # Reportar errores de validación
        if validator.validation_errors:
            logger.warning("Validation errors occurred during import:")
            for error in validator.validation_errors:
                logger.warning(f"Table: {error['table']}, Column: {error['column']}")
                logger.warning(f"Missing values: {error['missing_values']}")
                logger.warning(f"Affected rows: {error['affected_rows']}")
    
    except Exception as e:
        logger.error(f"Fatal error during data import: {str(e)}")
        raise

if __name__ == "__main__":
    main()