import pandas as pd
import os


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ruta_archivo = os.path.join(project_root, "CSVs", "data_2023.csv")

df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')
"""print(df[["TIPO DE IDENTIFICACIÓN","LUGAR DE EXPEDICIÓN","NÚMERO DE IDENTIFICACIÓN","NOMBRES2","APELLIDOS","FECHA DE NACIMIENTO",
          "TELÉFONO 1","TELÉFONO 2","CORREO ELECTRÓNICO","MUNICIPIO","DIRECCIÓN","INSTITUCIÓN EDUCATIVA 2025","SEDE 2025",
          "COLEGIO ABREVIADO PARA LISTADOS","GRADO 2025","SEDE NODAL 2025","POBLACIÓN","JORNADA ETAPA 2025","DOCENTE - 2025","GRUPO - 2025",
          "ESTADO DEL ESTUDIANTE 2025","ESTADO MATRÍCULA 2025","ESTADO ETAPA 2","CERTIFICADO 2025"]])"""

# Clean and prepare data for lookup tables, creating a primary key 'ID'
TIPO_DOCUMENTOS_2025 = df[["TIPO DE IDENTIFICACIÓN"]].drop_duplicates().dropna().reset_index(drop=True).reset_index().rename(columns={'index': 'ID'})

NIVEL_MCER_2025 = df[["NIVEL_MCER","Población 2023","ESTADO MATRÍCULA ETAPA 2","FECHA ACTUAL"]].drop_duplicates().dropna(subset=["NIVEL_MCER"]).reset_index(drop=True).reset_index().rename(columns={'index': 'ID'})


INSTITUCIONES_2025 = df[["Institución Educativa 2023","COLEGIO ABREVIADO PARA LISTADOS","Grado 2023"]].drop_duplicates().dropna().reset_index(drop=True).reset_index().rename(columns={'index': 'ID'})


CIUDADES_2025 = df[["MUNICIPIO"]].drop_duplicates().dropna().reset_index(drop=True).reset_index().rename(columns={'index': 'ID'})


CURSOS_2025 = df[["ENTIDAD","NOMBRE CURSO","IDIOMA"]].drop_duplicates().dropna().reset_index(drop=True).reset_index().rename(columns={'index': 'ID'})


# Prepare data for main tables
PERSONAS_2025 = df[["NOMBRES","APELLIDOS","TELÉFONO 1","TELÉFONO 2","NÚMERO DE IDENTIFICACIÓN","CORREO ELECTRÓNICO",
                    "DIRECCIÓN","SEXO","FECHA DE NACIMIENTO","CERTIFICADO","TIPO POBLACION"]]
SEDE_INSTITUCIONES_2025 = df[["GRUPO","Jornada 2023","FECHA INICIAL","FECHA FINAL"]]




print(PERSONAS_2025.head())
print(TIPO_DOCUMENTOS_2025.head())
print(NIVEL_MCER_2025.head())
print(CURSOS_2025.head())
print(SEDE_INSTITUCIONES_2025.head())
print(INSTITUCIONES_2025.head())
print(CIUDADES_2025.head())


