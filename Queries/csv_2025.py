import pandas as pd
import os
import sys

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Base_datos.conexion import engine, text



project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ruta_archivo = os.path.join(project_root, "CSVs", "data_2025.csv")

df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')
"""print(df[["TIPO DE IDENTIFICACIÓN","LUGAR DE EXPEDICIÓN","NÚMERO DE IDENTIFICACIÓN","NOMBRES2","APELLIDOS","FECHA DE NACIMIENTO",
          "TELÉFONO 1","TELÉFONO 2","CORREO ELECTRÓNICO","MUNICIPIO","DIRECCIÓN","INSTITUCIÓN EDUCATIVA 2025","SEDE 2025",
          "COLEGIO ABREVIADO PARA LISTADOS","GRADO 2025","SEDE NODAL 2025","POBLACIÓN","JORNADA ETAPA 2025","DOCENTE - 2025","GRUPO - 2025",
          "ESTADO DEL ESTUDIANTE 2025","ESTADO MATRÍCULA 2025","ESTADO ETAPA 2","CERTIFICADO 2025"]])"""

# Clean and prepare data for lookup tables, creating a primary key 'ID'
TIPO_DOCUMENTOS_2025 = df[["TIPO DE IDENTIFICACIÓN"]].drop_duplicates().dropna().reset_index(drop=True).reset_index().rename(columns={'index': 'ID'})
TIPO_DOCUMENTOS_2025['ID'] += 1 # Start IDs from 1

NIVEL_MCER_2025 = df[["NIVEL_MCER","POBLACIÓN","ESTADO ETAPA 2","FECHA ACTUAL"]].drop_duplicates().dropna(subset=["NIVEL_MCER"]).reset_index(drop=True).reset_index().rename(columns={'index': 'ID'})
NIVEL_MCER_2025['ID'] += 1

INSTITUCIONES_2025 = df[["INSTITUCIÓN EDUCATIVA 2025","COLEGIO ABREVIADO PARA LISTADOS"]].drop_duplicates().dropna().reset_index(drop=True).reset_index().rename(columns={'index': 'ID'})
INSTITUCIONES_2025['ID'] += 1

CIUDADES_2025 = df[["MUNICIPIO"]].drop_duplicates().dropna().reset_index(drop=True).reset_index().rename(columns={'index': 'ID'})
CIUDADES_2025['ID'] += 1

CURSOS_2025 = df[["ENTIDAD","NOMBRE CURSO","IDIOMA"]].drop_duplicates().dropna().reset_index(drop=True).reset_index().rename(columns={'index': 'ID'})
CURSOS_2025['ID'] += 1

# Prepare data for main tables
PERSONAS_2025 = df[["NOMBRES2","APELLIDOS","TELÉFONO 1","TELÉFONO 2","NÚMERO DE IDENTIFICACIÓN","CORREO ELECTRÓNICO",
                    "DIRECCIÓN","SEXO","FECHA DE NACIMIENTO","CERTIFICADO 2025","TIPO POBLACION"]]
SEDE_INSTITUCIONES_2025 = df[["GRUPO - 2025","JORNADA ETAPA 2025","FECHA INICIAL","FECHA FINAL"]]




print(PERSONAS_2025.head())
print(TIPO_DOCUMENTOS_2025.head())
print(NIVEL_MCER_2025.head())
print(CURSOS_2025.head())
print(SEDE_INSTITUCIONES_2025.head())
print(INSTITUCIONES_2025.head())
print(CIUDADES_2025.head())


with engine.connect() as connection:
    # Temporarily disable foreign key checks
    connection.execute(text('SET FOREIGN_KEY_CHECKS = 0;'))

    # Drop tables in the correct order to respect foreign key constraints
    # Note: PERSONAS_2025 and SEDE_INSTITUCIONES_2025 are not ready to be inserted yet
    # as they are missing the foreign key ID columns. This will be the next step.
    # PERSONAS_2025.to_sql("Personas", connection, if_exists='replace', index=False)
    # SEDE_INSTITUCIONES_2025.to_sql("Sede_Instituciones", connection, if_exists='replace', index=False)
    CURSOS_2025.to_sql("Cursos", connection, if_exists='replace', index=False)
    INSTITUCIONES_2025.to_sql("Instituciones_Educativas", connection, if_exists='replace', index=False)
    NIVEL_MCER_2025.to_sql("Nivel_MCER", connection, if_exists='replace', index=False)
    TIPO_DOCUMENTOS_2025.to_sql("Tipo_Documentos", connection, if_exists='replace', index=False)
    CIUDADES_2025.to_sql("Ciudades", connection, if_exists='replace', index=False)

    # Re-enable foreign key checks
    connection.execute(text('SET FOREIGN_KEY_CHECKS = 1;'))
