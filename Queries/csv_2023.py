import pandas as pd
import os
import sys
from sqlalchemy import text
import numpy as np
from datetime import datetime

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Base_datos.conexion import engine

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ruta_archivo = os.path.join(project_root, "CSVs", "data_2023.csv")

# Leer CSV
df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')

# Función para extraer año de diferentes formatos
def extraer_anio(fecha):
    """Extrae el año de diferentes formatos de fecha"""
    if pd.isna(fecha):
        return None
    
    fecha_str = str(fecha).strip()
    
    if fecha_str.isdigit() and len(fecha_str) == 4:
        return int(fecha_str)
    
    try:
        fecha_parsed = pd.to_datetime(fecha_str, errors='coerce')
        if not pd.isna(fecha_parsed):
            return fecha_parsed.year
    except:
        pass
    
    import re
    match = re.search(r'\b(19|20)\d{2}\b', fecha_str)
    if match:
        return int(match.group())
    
    return None

# Función para convertir fecha a formato MySQL
def convertir_fecha_mysql(fecha):
    """Convierte fecha a formato MySQL (YYYY-MM-DD)"""
    if pd.isna(fecha):
        return None
    
    fecha_str = str(fecha).strip()
    
    if fecha_str.lower() in ['nan', 'none', '']:
        return None
    
    formatos = [
        '%d/%m/%Y',
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%m/%d/%Y',
        '%Y/%m/%d',
    ]
    
    for formato in formatos:
        try:
            fecha_obj = datetime.strptime(fecha_str, formato)
            return fecha_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None

# Función para limpiar valores NaN
def limpiar_valor(valor):
    """Convierte NaN a None para SQL"""
    if pd.isna(valor):
        return None
    if isinstance(valor, float) and np.isnan(valor):
        return None
    valor_str = str(valor).strip()
    if valor_str.lower() in ['nan', 'none', '']:
        return None
    return valor_str

# ==========================================
# RELLENAR VALORES FALTANTES CON "SIN INFORMACION"
# ==========================================

columnas_texto = [
    'TIPO DE IDENTIFICACIÓN', 'NOMBRES', 'APELLIDOS', 'TELÉFONO 1', 'TELÉFONO 2',
    'CORREO ELECTRÓNICO', 'DIRECCIÓN', 'SEXO', 'TIPO POBLACION', 'NIVEL_MCER',
    'POBLACIÓN', 'ESTADO ETAPA 2', 'IDIOMA', 'CERTIFICADO', 'MUNICIPIO',
    'INSTITUCIÓN EDUCATIVA', 'COLEGIO ABREVIADO PARA LISTADOS', 'GRADO',
    'GRUPO', 'JORNADA', 'SEDE NODAL', 'ENTIDAD', 'NOMBRE CURSO'
]

for columna in columnas_texto:
    if columna in df.columns:
        df[columna] = df[columna].fillna('SIN INFORMACION')

print(f"✓ Valores faltantes rellenados con 'SIN INFORMACION'")
print(f"  Total de filas preservadas: {len(df)}")

# ==========================================
# PREPARACIÓN DE DATOS
# ==========================================

df['ANIO'] = df['FECHA'].apply(extraer_anio)

df['NOMBRE_CURSO_PROCESADO'] = df.apply(
    lambda row: 'Formación Docente' if limpiar_valor(row.get('TIPO POBLACION')) == 'Docente' 
    else (limpiar_valor(row.get('NOMBRE CURSO')) if limpiar_valor(row.get('NOMBRE CURSO')) else 'SIN INFORMACION'), 
    axis=1
)

TIPO_DOCUMENTOS_2023 = df[["TIPO DE IDENTIFICACIÓN"]].drop_duplicates().reset_index(drop=True)
TIPO_DOCUMENTOS_2023 = TIPO_DOCUMENTOS_2023[TIPO_DOCUMENTOS_2023["TIPO DE IDENTIFICACIÓN"] != 'SIN INFORMACION']

NIVEL_MCER_2023 = df[["NIVEL_MCER","TIPO POBLACION","ESTADO ETAPA 2","ANIO","IDIOMA","CERTIFICADO","GRADO"]].drop_duplicates().reset_index(drop=True)

INSTITUCIONES_2023 = df[["INSTITUCIÓN EDUCATIVA","COLEGIO ABREVIADO PARA LISTADOS"]].drop_duplicates().reset_index(drop=True)
INSTITUCIONES_2023 = INSTITUCIONES_2023[INSTITUCIONES_2023["INSTITUCIÓN EDUCATIVA"] != 'SIN INFORMACION']

CIUDADES_2023 = df[["MUNICIPIO"]].drop_duplicates().reset_index(drop=True)
CIUDADES_2023 = CIUDADES_2023[CIUDADES_2023["MUNICIPIO"] != 'SIN INFORMACION']

CURSOS_2023 = df[["ENTIDAD","IDIOMA","INSTITUCIÓN EDUCATIVA","NOMBRE_CURSO_PROCESADO","TIPO POBLACION"]].copy()
CURSOS_2023 = CURSOS_2023[CURSOS_2023["INSTITUCIÓN EDUCATIVA"] != 'SIN INFORMACION'].drop_duplicates().reset_index(drop=True)

PERSONAS_2023 = df[["NOMBRES","APELLIDOS","TELÉFONO 1","TELÉFONO 2","NÚMERO DE IDENTIFICACIÓN","CORREO ELECTRÓNICO",
                    "DIRECCIÓN","SEXO","FECHA DE NACIMIENTO","TIPO POBLACION","TIPO DE IDENTIFICACIÓN",
                    "MUNICIPIO","INSTITUCIÓN EDUCATIVA"]].copy()

PERSONA_NIVEL_2023 = df[["NÚMERO DE IDENTIFICACIÓN","NIVEL_MCER","TIPO POBLACION","ANIO"]].copy()

# DEBUG: Información de NIVEL_MCER
print(f"\n🔍 DEBUG - Datos de NIVEL_MCER en CSV:")
print(f"  - Total filas: {len(PERSONA_NIVEL_2023)}")
print(f"  - Con NIVEL_MCER != 'SIN INFORMACION': {len(PERSONA_NIVEL_2023[PERSONA_NIVEL_2023['NIVEL_MCER'] != 'SIN INFORMACION'])}")
print(f"  - Niveles únicos: {sorted(PERSONA_NIVEL_2023['NIVEL_MCER'].unique())}")
print(f"  - Años únicos: {sorted(PERSONA_NIVEL_2023['ANIO'].unique())}")

SEDES_2023 = df[["GRUPO","JORNADA","SEDE NODAL","NÚMERO DE IDENTIFICACIÓN"]].copy()

PERSONAS_2023['NÚMERO DE IDENTIFICACIÓN'] = PERSONAS_2023['NÚMERO DE IDENTIFICACIÓN'].apply(
    lambda x: 'Sin información' if pd.isna(x) or str(x).strip().lower() in ['nan', 'none', '', 'sin informacion'] else str(x).strip()
)

PERSONA_NIVEL_2023['NÚMERO DE IDENTIFICACIÓN'] = PERSONA_NIVEL_2023['NÚMERO DE IDENTIFICACIÓN'].apply(
    lambda x: 'Sin información' if pd.isna(x) or str(x).strip().lower() in ['nan', 'none', '', 'sin informacion'] else str(x).strip()
)

SEDES_2023['NÚMERO DE IDENTIFICACIÓN'] = SEDES_2023['NÚMERO DE IDENTIFICACIÓN'].apply(
    lambda x: 'Sin información' if pd.isna(x) or str(x).strip().lower() in ['nan', 'none', '', 'sin informacion'] else str(x).strip()
)

print("\nIniciando inserción de datos...")
print(f"Total personas a procesar: {len(PERSONAS_2023)}")
print(f"\nVerificando columna ANIO:")
print(f"  - Valores únicos: {sorted(df['ANIO'].dropna().unique())}")
print(f"  - Valores nulos: {df['ANIO'].isna().sum()}")

with engine.connect() as connection:
    
    print("\n1. Procesando Tipo_documentos...")
    for _, row in TIPO_DOCUMENTOS_2023.iterrows():
        tipo_doc = row['TIPO DE IDENTIFICACIÓN']
        
        if tipo_doc == 'SIN INFORMACION':
            continue
            
        result = connection.execute(text(
            "SELECT ID FROM Tipo_documentos WHERE TIPO_DOCUMENTO = :tipo_doc"
        ), {'tipo_doc': tipo_doc})
        
        if result.fetchone() is None:
            connection.execute(text(
                "INSERT INTO Tipo_documentos (TIPO_DOCUMENTO) VALUES (:tipo_doc)"
            ), {'tipo_doc': tipo_doc})
    
    connection.commit()
    print("✓ Tipo_documentos actualizado")
    
    print("\n2. Procesando Ciudades...")
    for _, row in CIUDADES_2023.iterrows():
        municipio = row['MUNICIPIO']
        
        if municipio == 'SIN INFORMACION':
            continue
            
        result = connection.execute(text(
            "SELECT ID FROM Ciudades WHERE MUNICIPIO = :municipio"
        ), {'municipio': municipio})
        
        if result.fetchone() is None:
            connection.execute(text(
                "INSERT INTO Ciudades (MUNICIPIO) VALUES (:municipio)"
            ), {'municipio': municipio})
    
    connection.commit()
    print("✓ Ciudades actualizado")
    
    print("\n3. Procesando Instituciones...")
    for _, row in INSTITUCIONES_2023.iterrows():
        nombre = row['INSTITUCIÓN EDUCATIVA']
        colegio_abrev = row['COLEGIO ABREVIADO PARA LISTADOS']
        
        if nombre == 'SIN INFORMACION':
            continue
        
        colegio_abrev = None if colegio_abrev == 'SIN INFORMACION' else colegio_abrev
        
        result = connection.execute(text(
            "SELECT ID FROM Instituciones WHERE NOMBRE_INSTITUCION = :nombre"
        ), {'nombre': nombre})
        
        if result.fetchone() is None:
            connection.execute(text(
                "INSERT INTO Instituciones (NOMBRE_INSTITUCION, COLEGIO_ABREVIADO) "
                "VALUES (:nombre, :colegio_abrev)"
            ), {'nombre': nombre, 'colegio_abrev': colegio_abrev})
    
    connection.commit()
    print("✓ Instituciones actualizado")
    
    print("\n4. Procesando Nivel_MCER...")
    niveles_insertados = 0
    for _, row in NIVEL_MCER_2023.iterrows():
        nivel = limpiar_valor(row['NIVEL_MCER'])
        tipo_pob = limpiar_valor(row['TIPO POBLACION'])
        estado = limpiar_valor(row['ESTADO ETAPA 2'])
        anio = int(row['ANIO']) if pd.notna(row['ANIO']) else None
        idioma = limpiar_valor(row.get('IDIOMA'))
        certificado = limpiar_valor(row.get('CERTIFICADO'))
        grado = limpiar_valor(row.get('GRADO'))
        
        if (nivel == 'SIN INFORMACION' or nivel is None) and (tipo_pob == 'SIN INFORMACION' or tipo_pob is None):
            continue
        
        estado = None if estado == 'SIN INFORMACION' else estado
        idioma = None if idioma == 'SIN INFORMACION' else idioma
        certificado = None if certificado == 'SIN INFORMACION' else certificado
        grado = None if grado == 'SIN INFORMACION' else grado
        
        result = connection.execute(text(
            "SELECT ID FROM Nivel_MCER WHERE NIVEL_MCER = :nivel AND TIPO_POBLACION = :tipo_pob"
        ), {'nivel': nivel, 'tipo_pob': tipo_pob})
        
        if result.fetchone() is None:
            connection.execute(text(
                "INSERT INTO Nivel_MCER (NIVEL_MCER, TIPO_POBLACION, ESTADO_ESTUDIANTE, ANIO, IDIOMA, CERTIFICADO, GRADO) "
                "VALUES (:nivel, :tipo_pob, :estado, :anio, :idioma, :certificado, :grado)"
            ), {'nivel': nivel, 'tipo_pob': tipo_pob, 'estado': estado, 'anio': anio, 'idioma': idioma, 'certificado': certificado, 'grado': grado})
            niveles_insertados += 1
    
    connection.commit()
    print(f"✓ Nivel_MCER actualizado - {niveles_insertados} registros nuevos")
    
    print("\n5. Procesando Personas...")
    personas_nuevas = 0
    personas_actualizadas = 0
    personas_sin_doc = 0
    
    for idx, row in PERSONAS_2023.iterrows():
        numero_doc = row['NÚMERO DE IDENTIFICACIÓN']
        
        if numero_doc == 'Sin información':
            personas_sin_doc += 1
        
        tipo_doc_valor = limpiar_valor(row['TIPO DE IDENTIFICACIÓN'])
        
        if tipo_doc_valor == 'SIN INFORMACION':
            tipo_doc_valor = None
        
        municipio_valor = limpiar_valor(row['MUNICIPIO'])
        institucion_valor = limpiar_valor(row['INSTITUCIÓN EDUCATIVA'])
        
        municipio_valor = None if municipio_valor == 'SIN INFORMACION' else municipio_valor
        institucion_valor = None if institucion_valor == 'SIN INFORMACION' else institucion_valor
        
        tipo_doc_id = None
        if tipo_doc_valor:
            tipo_doc_id = connection.execute(text(
                "SELECT ID FROM Tipo_documentos WHERE TIPO_DOCUMENTO = :tipo_doc"
            ), {'tipo_doc': tipo_doc_valor}).fetchone()
        
        ciudad_id = None
        if municipio_valor:
            ciudad_id = connection.execute(text(
                "SELECT ID FROM Ciudades WHERE MUNICIPIO = :municipio"
            ), {'municipio': municipio_valor}).fetchone()
        
        institucion_id = None
        if institucion_valor:
            institucion_id = connection.execute(text(
                "SELECT ID FROM Instituciones WHERE NOMBRE_INSTITUCION = :nombre"
            ), {'nombre': institucion_valor}).fetchone()
        
        persona_existe = connection.execute(text(
            "SELECT ID FROM Personas WHERE NUMERO_DOCUMENTO = :numero_doc"
        ), {'numero_doc': numero_doc}).fetchone()
        
        datos_persona = {
            'nombres': None if limpiar_valor(row['NOMBRES']) == 'SIN INFORMACION' else limpiar_valor(row['NOMBRES']),
            'apellidos': None if limpiar_valor(row['APELLIDOS']) == 'SIN INFORMACION' else limpiar_valor(row['APELLIDOS']),
            'telefono1': None if limpiar_valor(row['TELÉFONO 1']) == 'SIN INFORMACION' else limpiar_valor(row['TELÉFONO 1']),
            'telefono2': None if limpiar_valor(row['TELÉFONO 2']) == 'SIN INFORMACION' else limpiar_valor(row['TELÉFONO 2']),
            'numero_doc': numero_doc,
            'correo': None if limpiar_valor(row['CORREO ELECTRÓNICO']) == 'SIN INFORMACION' else limpiar_valor(row['CORREO ELECTRÓNICO']),
            'direccion': None if limpiar_valor(row['DIRECCIÓN']) == 'SIN INFORMACION' else limpiar_valor(row['DIRECCIÓN']),
            'sexo': None if limpiar_valor(row['SEXO']) == 'SIN INFORMACION' else limpiar_valor(row['SEXO']),
            'fecha_nac': convertir_fecha_mysql(row['FECHA DE NACIMIENTO']),
            'tipo_persona': None if limpiar_valor(row['TIPO POBLACION']) == 'SIN INFORMACION' else limpiar_valor(row['TIPO POBLACION']),
            'tipo_doc_id': tipo_doc_id[0] if tipo_doc_id else None,
            'ciudad_id': ciudad_id[0] if ciudad_id else None,
            'institucion_id': institucion_id[0] if institucion_id else None
        }
        
        if persona_existe:
            connection.execute(text(
                """UPDATE Personas SET 
                   NOMBRES = :nombres,
                   APELLIDOS = :apellidos,
                   TELEFONO1 = :telefono1,
                   TELEFONO2 = :telefono2,
                   CORREO_ELECTRONICO = :correo,
                   DIRECCION = :direccion,
                   SEXO = :sexo,
                   FECHA_NACIMIENTO = :fecha_nac,
                   TIPO_PERSONA = :tipo_persona,
                   TIPO_DOCUMENTO_ID = :tipo_doc_id,
                   CIUDAD_ID = :ciudad_id,
                   INSTITUCION_ID = :institucion_id
                   WHERE NUMERO_DOCUMENTO = :numero_doc"""
            ), datos_persona)
            personas_actualizadas += 1
        else:
            connection.execute(text(
                """INSERT INTO Personas 
                   (NOMBRES, APELLIDOS, TELEFONO1, TELEFONO2, NUMERO_DOCUMENTO, CORREO_ELECTRONICO,
                    DIRECCION, SEXO, FECHA_NACIMIENTO, TIPO_PERSONA,
                    TIPO_DOCUMENTO_ID, CIUDAD_ID, INSTITUCION_ID)
                   VALUES (:nombres, :apellidos, :telefono1, :telefono2, :numero_doc, :correo,
                           :direccion, :sexo, :fecha_nac, :tipo_persona,
                           :tipo_doc_id, :ciudad_id, :institucion_id)"""
            ), datos_persona)
            personas_nuevas += 1
    
    connection.commit()
    print(f"✓ Personas procesadas: {personas_nuevas} nuevas, {personas_actualizadas} actualizadas")
    if personas_sin_doc > 0:
        print(f"  ℹ {personas_sin_doc} personas con 'Sin información' como número de documento")
    
    print("\n5.5. Procesando relaciones Persona-Nivel_MCER...")
    relaciones_nuevas = 0
    personas_sin_nivel = 0
    niveles_no_encontrados = 0
    
    for _, row in PERSONA_NIVEL_2023.iterrows():
        numero_doc = row['NÚMERO DE IDENTIFICACIÓN']
        nivel_mcer_valor = limpiar_valor(row['NIVEL_MCER'])
        poblacion_valor = limpiar_valor(row['TIPO POBLACION'])
        anio_registro = int(row['ANIO']) if pd.notna(row['ANIO']) else None
        
        nivel_mcer_valor = None if nivel_mcer_valor == 'SIN INFORMACION' else nivel_mcer_valor
        poblacion_valor = None if poblacion_valor == 'SIN INFORMACION' else poblacion_valor
        
        if not nivel_mcer_valor or not poblacion_valor:
            personas_sin_nivel += 1
            continue
        
        persona_id = connection.execute(text(
            "SELECT ID FROM Personas WHERE NUMERO_DOCUMENTO = :numero_doc"
        ), {'numero_doc': numero_doc}).fetchone()
        
        if persona_id is None:
            continue
        
        nivel_id = connection.execute(text(
            "SELECT ID FROM Nivel_MCER WHERE NIVEL_MCER = :nivel AND TIPO_POBLACION = :tipo_pob"
        ), {'nivel': nivel_mcer_valor, 'tipo_pob': poblacion_valor}).fetchone()
        
        if nivel_id is None:
            niveles_no_encontrados += 1
            continue
        
        relacion_existe = connection.execute(text(
            """SELECT ID FROM Persona_Nivel_MCER 
               WHERE PERSONA_ID = :persona_id AND NIVEL_MCER_ID = :nivel_id 
               AND (ANIO_REGISTRO = :anio OR (ANIO_REGISTRO IS NULL AND :anio IS NULL))"""
        ), {'persona_id': persona_id[0], 'nivel_id': nivel_id[0], 'anio': anio_registro}).fetchone()
        
        if relacion_existe is None:
            connection.execute(text(
                """INSERT INTO Persona_Nivel_MCER (PERSONA_ID, NIVEL_MCER_ID, ANIO_REGISTRO)
                   VALUES (:persona_id, :nivel_id, :anio)"""
            ), {'persona_id': persona_id[0], 'nivel_id': nivel_id[0], 'anio': anio_registro})
            relaciones_nuevas += 1
    
    connection.commit()
    print(f"✓ Relaciones Persona-Nivel_MCER procesadas: {relaciones_nuevas} nuevas")
    if personas_sin_nivel > 0:
        print(f"  ℹ {personas_sin_nivel} personas sin nivel MCER asignado")
    if niveles_no_encontrados > 0:
        print(f"  ⚠️ {niveles_no_encontrados} niveles MCER no encontrados en la BD")
    
    print("\n6. Procesando Sedes...")
    sedes_nuevas = 0
    
    for _, row in SEDES_2023.iterrows():
        numero_doc = row['NÚMERO DE IDENTIFICACIÓN']
        
        persona_id = connection.execute(text(
            "SELECT ID FROM Personas WHERE NUMERO_DOCUMENTO = :numero_doc"
        ), {'numero_doc': numero_doc}).fetchone()
        
        if persona_id is None:
            continue
        
        grupo = limpiar_valor(row['GRUPO'])
        jornada = limpiar_valor(row['JORNADA'])
        sede = limpiar_valor(row['SEDE NODAL'])
        
        grupo = None if grupo == 'SIN INFORMACION' else grupo
        jornada = None if jornada == 'SIN INFORMACION' else jornada
        sede = None if sede == 'SIN INFORMACION' else sede
        
        sede_existe = connection.execute(text(
            """SELECT ID FROM Sedes 
               WHERE PERSONA_ID = :persona_id 
               AND (GRUPO = :grupo OR (GRUPO IS NULL AND :grupo IS NULL))
               AND (JORNADA = :jornada OR (JORNADA IS NULL AND :jornada IS NULL))"""
        ), {'persona_id': persona_id[0], 'grupo': grupo, 'jornada': jornada}).fetchone()
        
        if sede_existe is None:
            connection.execute(text(
                """INSERT INTO Sedes (GRUPO, JORNADA, SEDE_NODAL, PERSONA_ID)
                   VALUES (:grupo, :jornada, :sede, :persona_id)"""
            ), {'grupo': grupo, 'jornada': jornada, 'sede': sede, 'persona_id': persona_id[0]})
            sedes_nuevas += 1
    
    connection.commit()
    print(f"✓ Sedes procesadas: {sedes_nuevas} nuevas")

    print("\n7. Procesando Cursos...")
    cursos_nuevos = 0
    docentes_procesados = 0
    
    for _, row in CURSOS_2023.iterrows():
        entidad = limpiar_valor(row['ENTIDAD'])
        idioma = limpiar_valor(row['IDIOMA'])
        institucion = limpiar_valor(row['INSTITUCIÓN EDUCATIVA'])
        nombre_curso = limpiar_valor(row['NOMBRE_CURSO_PROCESADO'])
        tipo_poblacion = limpiar_valor(row.get('TIPO POBLACION'))
        
        if institucion is None or institucion == 'SIN INFORMACION':
            continue
        
        entidad = None if entidad == 'SIN INFORMACION' else entidad
        idioma = None if idioma == 'SIN INFORMACION' else idioma
        nombre_curso = None if nombre_curso == 'SIN INFORMACION' else nombre_curso
        
        institucion_id = connection.execute(text(
            "SELECT ID FROM Instituciones WHERE NOMBRE_INSTITUCION = :nombre"
        ), {'nombre': institucion}).fetchone()
        
        if institucion_id is None:
            continue
        
        curso_existe = connection.execute(text(
            """SELECT ID FROM Cursos 
               WHERE INSTITUCION_ID = :institucion_id 
               AND (NOMBRE_CURSO = :nombre_curso OR (NOMBRE_CURSO IS NULL AND :nombre_curso IS NULL))
               AND (ENTIDAD = :entidad OR (ENTIDAD IS NULL AND :entidad IS NULL))
               AND (IDIOMA = :idioma OR (IDIOMA IS NULL AND :idioma IS NULL))"""
        ), {
            'institucion_id': institucion_id[0],
            'nombre_curso': nombre_curso,
            'entidad': entidad,
            'idioma': idioma
        }).fetchone()
        
        if curso_existe is None:
            connection.execute(text(
                """INSERT INTO Cursos (ENTIDAD, IDIOMA, INSTITUCION_ID, NOMBRE_CURSO)
                   VALUES (:entidad, :idioma, :institucion_id, :nombre_curso)"""
            ), {
                'entidad': entidad,
                'idioma': idioma,
                'institucion_id': institucion_id[0],
                'nombre_curso': nombre_curso
            })
            cursos_nuevos += 1
            
            if tipo_poblacion == 'Docente':
                docentes_procesados += 1
    
    connection.commit()
    print(f"✓ Cursos procesados: {cursos_nuevos} nuevos")
    if docentes_procesados > 0:
        print(f"  ℹ {docentes_procesados} cursos de Formación Docente creados")

print("\n✅ Proceso completado exitosamente")
print(f"   - Personas nuevas: {personas_nuevas}")
print(f"   - Personas actualizadas: {personas_actualizadas}")
print(f"   - Relaciones Persona-Nivel_MCER: {relaciones_nuevas}")
print(f"   - Sedes nuevas: {sedes_nuevas}")
print(f"   - Cursos nuevos: {cursos_nuevos}")
print(f"   - Total de filas del CSV preservadas: {len(df)}")
