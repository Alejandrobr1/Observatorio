import pandas as pd
import os
import sys
from sqlalchemy import text
import numpy as np
from datetime import datetime


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Base_datos.conexion import engine

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ruta_archivo = os.path.join(project_root, "CSVs", "data_2023_intensificacion.csv")

df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')

print("\n=== DIAGNÓSTICO INICIAL ===")
print(f"Total de filas en CSV: {len(df)}")
print(f"Total de columnas: {len(df.columns)}")

# Función para extraer año
def extraer_anio(fecha):
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

def convertir_fecha_mysql(fecha):
    if pd.isna(fecha):
        return None
    fecha_str = str(fecha).strip()
    if fecha_str.lower() in ['nan', 'none', '']:
        return None
    formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%Y/%m/%d']
    for formato in formatos:
        try:
            fecha_obj = datetime.strptime(fecha_str, formato)
            return fecha_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def limpiar_valor(valor):
    if pd.isna(valor):
        return None
    if isinstance(valor, float) and np.isnan(valor):
        return None
    valor_str = str(valor).strip()
    if valor_str.lower() in ['nan', 'none', '']:
        return None
    return valor_str

# Rellenar valores faltantes
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

print(f"\n✓ Valores faltantes rellenados con 'SIN INFORMACION'")
print(f"  Total de filas: {len(df)}")

df['ANIO'] = df['FECHA'].apply(extraer_anio)

df['NOMBRE_CURSO_PROCESADO'] = df.apply(
    lambda row: 'Formación Docente' if limpiar_valor(row.get('TIPO POBLACION')) == 'Docente' 
    else (limpiar_valor(row.get('NOMBRE CURSO')) if limpiar_valor(row.get('NOMBRE CURSO')) else 'SIN INFORMACION'), 
    axis=1
)

TIPO_DOCUMENTOS_2023 = df[["TIPO DE IDENTIFICACIÓN"]].drop_duplicates().reset_index(drop=True)
TIPO_DOCUMENTOS_2023 = TIPO_DOCUMENTOS_2023[TIPO_DOCUMENTOS_2023["TIPO DE IDENTIFICACIÓN"] != 'SIN INFORMACION']

# Verificar columna GRADO
grado_col = None
for col in df.columns:
    if col.upper() == 'GRADO':
        grado_col = col
        break

if grado_col is None:
    df['GRADO'] = 'SIN INFORMACION'
    grado_col = 'GRADO'
else:
    print(f"\n✓ Columna de grado encontrada: '{grado_col}'")

print(f"  Grados únicos en CSV: {sorted(df[grado_col].unique())}")
print(f"  Distribución de grados:")
print(df[grado_col].value_counts().head(20))

# PREPARAR NIVEL_MCER CON GRADO
NIVEL_MCER_2023 = df[[
    "NIVEL_MCER",
    "TIPO POBLACION",
    "ESTADO ETAPA 2",
    "ANIO",
    "IDIOMA",
    "CERTIFICADO",
    grado_col
]].copy()

if grado_col != 'GRADO':
    NIVEL_MCER_2023 = NIVEL_MCER_2023.rename(columns={grado_col: 'GRADO'})

NIVEL_MCER_2023 = NIVEL_MCER_2023.drop_duplicates().reset_index(drop=True)

print(f"\n✓ NIVEL_MCER_2023 preparado: {len(NIVEL_MCER_2023)} registros únicos")
print(f"  Grados únicos: {sorted(NIVEL_MCER_2023['GRADO'].unique())}")
print(f"  Distribución:")
print(NIVEL_MCER_2023['GRADO'].value_counts())

INSTITUCIONES_2023 = df[["INSTITUCIÓN EDUCATIVA","COLEGIO ABREVIADO PARA LISTADOS"]].drop_duplicates().reset_index(drop=True)
INSTITUCIONES_2023 = INSTITUCIONES_2023[INSTITUCIONES_2023["INSTITUCIÓN EDUCATIVA"] != 'SIN INFORMACION']

CIUDADES_2023 = df[["MUNICIPIO"]].drop_duplicates().reset_index(drop=True)
CIUDADES_2023 = CIUDADES_2023[CIUDADES_2023["MUNICIPIO"] != 'SIN INFORMACION']

CURSOS_2023 = df[["ENTIDAD","IDIOMA","INSTITUCIÓN EDUCATIVA","NOMBRE_CURSO_PROCESADO","TIPO POBLACION"]].copy()
CURSOS_2023 = CURSOS_2023[CURSOS_2023["INSTITUCIÓN EDUCATIVA"] != 'SIN INFORMACION'].drop_duplicates().reset_index(drop=True)

PERSONAS_2023 = df[["NOMBRES","APELLIDOS","TELÉFONO 1","TELÉFONO 2","NÚMERO DE IDENTIFICACIÓN","CORREO ELECTRÓNICO",
                    "DIRECCIÓN","SEXO","FECHA DE NACIMIENTO","TIPO POBLACION","TIPO DE IDENTIFICACIÓN",
                    "MUNICIPIO","INSTITUCIÓN EDUCATIVA"]].copy()

# PREPARAR PERSONA_NIVEL CON GRADO INCLUIDO
PERSONA_NIVEL_2023 = df[["NÚMERO DE IDENTIFICACIÓN","NIVEL_MCER","TIPO POBLACION","ANIO","GRADO"]].copy()

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

print("\n" + "="*60)
print("INICIANDO INSERCIÓN DE DATOS")
print("="*60)

with engine.connect() as connection:
    
    print("\n1. Procesando Tipo_documentos...")
    for _, row in TIPO_DOCUMENTOS_2023.iterrows():
        tipo_doc = row['TIPO DE IDENTIFICACIÓN']
        if tipo_doc == 'SIN INFORMACION':
            continue
        result = connection.execute(text("SELECT ID FROM Tipo_documentos WHERE TIPO_DOCUMENTO = :tipo_doc"), {'tipo_doc': tipo_doc})
        if result.fetchone() is None:
            connection.execute(text("INSERT INTO Tipo_documentos (TIPO_DOCUMENTO) VALUES (:tipo_doc)"), {'tipo_doc': tipo_doc})
    connection.commit()
    print("✓ Tipo_documentos actualizado")
    
    print("\n2. Procesando Ciudades...")
    for _, row in CIUDADES_2023.iterrows():
        municipio = row['MUNICIPIO']
        if municipio == 'SIN INFORMACION':
            continue
        result = connection.execute(text("SELECT ID FROM Ciudades WHERE MUNICIPIO = :municipio"), {'municipio': municipio})
        if result.fetchone() is None:
            connection.execute(text("INSERT INTO Ciudades (MUNICIPIO) VALUES (:municipio)"), {'municipio': municipio})
    connection.commit()
    print("✓ Ciudades actualizado")
    
    print("\n3. Procesando Instituciones...")
    for _, row in INSTITUCIONES_2023.iterrows():
        nombre = row['INSTITUCIÓN EDUCATIVA']
        colegio_abrev = row['COLEGIO ABREVIADO PARA LISTADOS']
        if nombre == 'SIN INFORMACION':
            continue
        colegio_abrev = None if colegio_abrev == 'SIN INFORMACION' else colegio_abrev
        result = connection.execute(text("SELECT ID FROM Instituciones WHERE NOMBRE_INSTITUCION = :nombre"), {'nombre': nombre})
        if result.fetchone() is None:
            connection.execute(text("INSERT INTO Instituciones (NOMBRE_INSTITUCION, COLEGIO_ABREVIADO) VALUES (:nombre, :colegio_abrev)"), 
                             {'nombre': nombre, 'colegio_abrev': colegio_abrev})
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
        
        nivel = None if nivel == 'SIN INFORMACION' else nivel
        tipo_pob = None if tipo_pob == 'SIN INFORMACION' else tipo_pob
        estado = None if estado == 'SIN INFORMACION' else estado
        idioma = None if idioma == 'SIN INFORMACION' else idioma
        certificado = None if certificado == 'SIN INFORMACION' else certificado
        grado = None if grado == 'SIN INFORMACION' else grado
        
        if nivel is None and tipo_pob is None and grado is None:
            continue
        
        # CAMBIO CLAVE: Buscar con GRADO incluido
        result = connection.execute(text(
            """SELECT ID FROM Nivel_MCER 
               WHERE (NIVEL_MCER <=> :nivel) 
               AND (TIPO_POBLACION <=> :tipo_pob) 
               AND (ANIO <=> :anio)
               AND (GRADO <=> :grado)"""
        ), {'nivel': nivel, 'tipo_pob': tipo_pob, 'anio': anio, 'grado': grado})
        
        if result.fetchone() is None:
            connection.execute(text(
                """INSERT INTO Nivel_MCER (NIVEL_MCER, TIPO_POBLACION, ESTADO_ESTUDIANTE, ANIO, IDIOMA, CERTIFICADO, GRADO) 
                   VALUES (:nivel, :tipo_pob, :estado, :anio, :idioma, :certificado, :grado)"""
            ), {'nivel': nivel, 'tipo_pob': tipo_pob, 'estado': estado, 'anio': anio, 'idioma': idioma, 'certificado': certificado, 'grado': grado})
            niveles_insertados += 1
    
    connection.commit()
    print(f"✓ Nivel_MCER: {niveles_insertados} registros insertados")
    
    # Verificar grados insertados
    result_grados = connection.execute(text(
        """SELECT DISTINCT GRADO, COUNT(*) as cantidad 
           FROM Nivel_MCER 
           WHERE GRADO IS NOT NULL 
           GROUP BY GRADO 
           ORDER BY CASE WHEN GRADO REGEXP '^[0-9]+$' THEN CAST(GRADO AS UNSIGNED) ELSE 999 END, GRADO"""
    ))
    print(f"  Grados en BD:")
    for row in result_grados:
        print(f"    • Grado {row[0]}: {row[1]} registros")
    
    print("\n5. Procesando Personas...")
    personas_nuevas = 0
    personas_actualizadas = 0
    
    for idx, row in PERSONAS_2023.iterrows():
        numero_doc = row['NÚMERO DE IDENTIFICACIÓN']
        tipo_doc_valor = limpiar_valor(row['TIPO DE IDENTIFICACIÓN'])
        if tipo_doc_valor == 'SIN INFORMACION':
            tipo_doc_valor = None
        municipio_valor = limpiar_valor(row['MUNICIPIO'])
        institucion_valor = limpiar_valor(row['INSTITUCIÓN EDUCATIVA'])
        municipio_valor = None if municipio_valor == 'SIN INFORMACION' else municipio_valor
        institucion_valor = None if institucion_valor == 'SIN INFORMACION' else institucion_valor
        
        tipo_doc_id = None
        if tipo_doc_valor:
            tipo_doc_id = connection.execute(text("SELECT ID FROM Tipo_documentos WHERE TIPO_DOCUMENTO = :tipo_doc"), 
                                            {'tipo_doc': tipo_doc_valor}).fetchone()
        ciudad_id = None
        if municipio_valor:
            ciudad_id = connection.execute(text("SELECT ID FROM Ciudades WHERE MUNICIPIO = :municipio"), 
                                          {'municipio': municipio_valor}).fetchone()
        institucion_id = None
        if institucion_valor:
            institucion_id = connection.execute(text("SELECT ID FROM Instituciones WHERE NOMBRE_INSTITUCION = :nombre"), 
                                               {'nombre': institucion_valor}).fetchone()
        
        persona_existe = connection.execute(text("SELECT ID FROM Personas WHERE NUMERO_DOCUMENTO = :numero_doc"), 
                                           {'numero_doc': numero_doc}).fetchone()
        
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
                """UPDATE Personas SET NOMBRES = :nombres, APELLIDOS = :apellidos, TELEFONO1 = :telefono1, 
                   TELEFONO2 = :telefono2, CORREO_ELECTRONICO = :correo, DIRECCION = :direccion, SEXO = :sexo,
                   FECHA_NACIMIENTO = :fecha_nac, TIPO_PERSONA = :tipo_persona, TIPO_DOCUMENTO_ID = :tipo_doc_id,
                   CIUDAD_ID = :ciudad_id, INSTITUCION_ID = :institucion_id WHERE NUMERO_DOCUMENTO = :numero_doc"""
            ), datos_persona)
            personas_actualizadas += 1
        else:
            connection.execute(text(
                """INSERT INTO Personas (NOMBRES, APELLIDOS, TELEFONO1, TELEFONO2, NUMERO_DOCUMENTO, CORREO_ELECTRONICO,
                   DIRECCION, SEXO, FECHA_NACIMIENTO, TIPO_PERSONA, TIPO_DOCUMENTO_ID, CIUDAD_ID, INSTITUCION_ID)
                   VALUES (:nombres, :apellidos, :telefono1, :telefono2, :numero_doc, :correo, :direccion, :sexo,
                   :fecha_nac, :tipo_persona, :tipo_doc_id, :ciudad_id, :institucion_id)"""
            ), datos_persona)
            personas_nuevas += 1
    
    connection.commit()
    print(f"✓ Personas: {personas_nuevas} nuevas, {personas_actualizadas} actualizadas")
    
    print("\n5.5. Procesando relaciones Persona-Nivel_MCER...")
    relaciones_nuevas = 0
    niveles_no_encontrados = 0
    
    # Crear un mapeo de NUMERO_DOCUMENTO a NOMBRE_CURSO desde el DataFrame original
    nombre_curso_map = dict(zip(df["NÚMERO DE IDENTIFICACIÓN"], df["NOMBRE_CURSO_PROCESADO"]))
    
    for _, row in PERSONA_NIVEL_2023.iterrows():
        numero_doc = row['NÚMERO DE IDENTIFICACIÓN']
        nivel_mcer_valor = limpiar_valor(row['NIVEL_MCER'])
        poblacion_valor = limpiar_valor(row['TIPO POBLACION'])
        anio_registro = int(row['ANIO']) if pd.notna(row['ANIO']) else None
        grado_valor = limpiar_valor(row['GRADO'])  # INCLUIR GRADO
        nombre_curso_valor = limpiar_valor(nombre_curso_map.get(numero_doc, 'SIN INFORMACION'))
        
        nivel_mcer_valor = None if nivel_mcer_valor == 'SIN INFORMACION' else nivel_mcer_valor
        poblacion_valor = None if poblacion_valor == 'SIN INFORMACION' else poblacion_valor
        grado_valor = None if grado_valor == 'SIN INFORMACION' else grado_valor
        nombre_curso_valor = None if nombre_curso_valor == 'SIN INFORMACION' else nombre_curso_valor
        
        persona_id = connection.execute(text("SELECT ID FROM Personas WHERE NUMERO_DOCUMENTO = :numero_doc"), 
                                       {'numero_doc': numero_doc}).fetchone()
        
        if persona_id is None:
            continue
        
        # BUSCAR CON GRADO Y AÑO INCLUIDOS
        nivel_id = connection.execute(text(
            """SELECT ID FROM Nivel_MCER 
               WHERE (NIVEL_MCER <=> :nivel) 
               AND (TIPO_POBLACION <=> :tipo_pob)
               AND (ANIO <=> :anio)
               AND (GRADO <=> :grado)
               LIMIT 1"""
        ), {'nivel': nivel_mcer_valor, 'tipo_pob': poblacion_valor, 'anio': anio_registro, 'grado': grado_valor}).fetchone()
        
        if nivel_id is None:
            niveles_no_encontrados += 1
            continue
        
        relacion_existe = connection.execute(text(
            """SELECT ID FROM Persona_Nivel_MCER 
               WHERE PERSONA_ID = :persona_id AND NIVEL_MCER_ID = :nivel_id 
               AND (ANIO_REGISTRO <=> :anio)"""
        ), {'persona_id': persona_id[0], 'nivel_id': nivel_id[0], 'anio': anio_registro}).fetchone()
        
        if relacion_existe is None:
            connection.execute(text(
                """INSERT INTO Persona_Nivel_MCER (PERSONA_ID, NIVEL_MCER_ID, ANIO_REGISTRO, NOMBRE_CURSO)
                   VALUES (:persona_id, :nivel_id, :anio, :nombre_curso)"""
            ), {'persona_id': persona_id[0], 'nivel_id': nivel_id[0], 'anio': anio_registro, 'nombre_curso': nombre_curso_valor})
            relaciones_nuevas += 1
    
    connection.commit()
    print(f"✓ Relaciones Persona-Nivel_MCER: {relaciones_nuevas} nuevas")
    if niveles_no_encontrados > 0:
        print(f"  ⚠️ {niveles_no_encontrados} niveles no encontrados")
    
    print("\n6. Procesando Sedes...")
    sedes_nuevas = 0
    for _, row in SEDES_2023.iterrows():
        numero_doc = row['NÚMERO DE IDENTIFICACIÓN']
        persona_id = connection.execute(text("SELECT ID FROM Personas WHERE NUMERO_DOCUMENTO = :numero_doc"), 
                                       {'numero_doc': numero_doc}).fetchone()
        if persona_id is None:
            continue
        grupo = limpiar_valor(row['GRUPO'])
        jornada = limpiar_valor(row['JORNADA'])
        sede = limpiar_valor(row['SEDE NODAL'])
        grupo = None if grupo == 'SIN INFORMACION' else grupo
        jornada = None if jornada == 'SIN INFORMACION' else jornada
        sede = None if sede == 'SIN INFORMACION' else sede
        
        sede_existe = connection.execute(text(
            "SELECT ID FROM Sedes WHERE PERSONA_ID = :persona_id AND (GRUPO <=> :grupo) AND (JORNADA <=> :jornada)"
        ), {'persona_id': persona_id[0], 'grupo': grupo, 'jornada': jornada}).fetchone()
        
        if sede_existe is None:
            connection.execute(text("INSERT INTO Sedes (GRUPO, JORNADA, SEDE_NODAL, PERSONA_ID) VALUES (:grupo, :jornada, :sede, :persona_id)"), 
                             {'grupo': grupo, 'jornada': jornada, 'sede': sede, 'persona_id': persona_id[0]})
            sedes_nuevas += 1
    connection.commit()
    print(f"✓ Sedes: {sedes_nuevas} nuevas")

    print("\n7. Procesando Cursos...")
    cursos_nuevos = 0
    for _, row in CURSOS_2023.iterrows():
        entidad = limpiar_valor(row['ENTIDAD'])
        idioma = limpiar_valor(row['IDIOMA'])
        institucion = limpiar_valor(row['INSTITUCIÓN EDUCATIVA'])
        nombre_curso = limpiar_valor(row['NOMBRE_CURSO_PROCESADO'])
        
        if institucion is None or institucion == 'SIN INFORMACION':
            continue
        entidad = None if entidad == 'SIN INFORMACION' else entidad
        idioma = None if idioma == 'SIN INFORMACION' else idioma
        nombre_curso = None if nombre_curso == 'SIN INFORMACION' else nombre_curso
        
        institucion_id = connection.execute(text("SELECT ID FROM Instituciones WHERE NOMBRE_INSTITUCION = :nombre"), 
                                           {'nombre': institucion}).fetchone()
        if institucion_id is None:
            continue
        
        curso_existe = connection.execute(text(
            "SELECT ID FROM Cursos WHERE INSTITUCION_ID = :inst_id AND (NOMBRE_CURSO <=> :nombre) AND (ENTIDAD <=> :ent) AND (IDIOMA <=> :idioma)"
        ), {'inst_id': institucion_id[0], 'nombre': nombre_curso, 'ent': entidad, 'idioma': idioma}).fetchone()
        
        if curso_existe is None:
            connection.execute(text("INSERT INTO Cursos (ENTIDAD, IDIOMA, INSTITUCION_ID, NOMBRE_CURSO) VALUES (:entidad, :idioma, :inst_id, :nombre)"), 
                             {'entidad': entidad, 'idioma': idioma, 'inst_id': institucion_id[0], 'nombre': nombre_curso})
            cursos_nuevos += 1
    connection.commit()
    print(f"✓ Cursos: {cursos_nuevos} nuevos")

print("\n" + "="*60)
print("✅ PROCESO COMPLETADO")
print("="*60)
print(f"   - Personas nuevas: {personas_nuevas}")
print(f"   - Personas actualizadas: {personas_actualizadas}")
print(f"   - Niveles MCER nuevos: {niveles_insertados}")
print(f"   - Relaciones Persona-Nivel_MCER: {relaciones_nuevas}")
print(f"   - Sedes nuevas: {sedes_nuevas}")
print(f"   - Cursos nuevos: {cursos_nuevos}")
print("="*60)
