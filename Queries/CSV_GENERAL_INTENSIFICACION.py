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

# ==========================================
# LEER Y COMBINAR MÚLTIPLES ARCHIVOS CSV
# ==========================================

# Lista de años a procesar (de 2016 a 2025)
years = range(2016, 2026)  # 2016 hasta 2025
dfs_list = []

print("Leyendo archivos CSV...")
for year in years:
    ruta_archivo = os.path.join(project_root, "CSVs", f"data_{year}_intensificacion.csv")
    
    # Verificar si el archivo existe
    if os.path.exists(ruta_archivo):
        try:
            df_temp = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')
            dfs_list.append(df_temp)
            print(f"  ✓ Archivo data_{year}.csv cargado ({len(df_temp)} registros)")
        except Exception as e:
            print(f"  ⚠ Error al leer data_{year}.csv: {e}")
    else:
        print(f"  ⚠ Archivo data_{year}.csv no encontrado, se omite")

# Combinar todos los DataFrames en uno solo
if len(dfs_list) == 0:
    print("Error: No se encontraron archivos CSV para procesar")
    sys.exit(1)

df = pd.concat(dfs_list, ignore_index=True)
print(f"\n✓ Total de registros combinados: {len(df)}")

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

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
# PREPARACIÓN DE DATOS
# ==========================================

df['ANIO'] = df['FECHA'].apply(extraer_anio)

TIPO_DOCUMENTOS_2025 = df[["TIPO DE IDENTIFICACIÓN"]].drop_duplicates().dropna().reset_index(drop=True)
NIVEL_MCER_2025 = df[["NIVEL_MCER","POBLACIÓN","ESTADO ETAPA 2","ANIO","IDIOMA","CERTIFICADO"]].drop_duplicates().dropna(subset=["NIVEL_MCER"]).reset_index(drop=True)
INSTITUCIONES_2025 = df[["INSTITUCIÓN EDUCATIVA","COLEGIO ABREVIADO PARA LISTADOS","GRADO"]].drop_duplicates().dropna().reset_index(drop=True)
CIUDADES_2025 = df[["MUNICIPIO"]].drop_duplicates().dropna().reset_index(drop=True)
CURSOS_2025 = df[["ENTIDAD","IDIOMA","INSTITUCIÓN EDUCATIVA"]].drop_duplicates().dropna().reset_index(drop=True)

PERSONAS_2025 = df[["NOMBRES","APELLIDOS","TELÉFONO 1","TELÉFONO 2","NÚMERO DE IDENTIFICACIÓN","CORREO ELECTRÓNICO",
                    "DIRECCIÓN","SEXO","FECHA DE NACIMIENTO","TIPO POBLACION","TIPO DE IDENTIFICACIÓN",
                    "NIVEL_MCER","POBLACIÓN","ESTADO ETAPA 2","ANIO","MUNICIPIO","INSTITUCIÓN EDUCATIVA"]].copy()

SEDES_2025 = df[["GRUPO","JORNADA","SEDE NODAL","NÚMERO DE IDENTIFICACIÓN"]].copy()

PERSONAS_2025['NÚMERO DE IDENTIFICACIÓN'] = PERSONAS_2025['NÚMERO DE IDENTIFICACIÓN'].apply(
    lambda x: 'Sin información' if pd.isna(x) or str(x).strip().lower() in ['nan', 'none', ''] else str(x).strip()
)

SEDES_2025['NÚMERO DE IDENTIFICACIÓN'] = SEDES_2025['NÚMERO DE IDENTIFICACIÓN'].apply(
    lambda x: 'Sin información' if pd.isna(x) or str(x).strip().lower() in ['nan', 'none', ''] else str(x).strip()
)

print("Iniciando inserción de datos...")
print(f"Total personas a procesar: {len(PERSONAS_2025)}")
print(f"\nVerificando columna ANIO:")
print(f"  - Valores únicos: {sorted(PERSONAS_2025['ANIO'].dropna().unique())}")
print(f"  - Valores nulos: {PERSONAS_2025['ANIO'].isna().sum()}")

# ==========================================
# INSERCIÓN EN BASE DE DATOS
# ==========================================

with engine.connect() as connection:
    
    print("\n1. Procesando Tipo_documentos...")
    for _, row in TIPO_DOCUMENTOS_2025.iterrows():
        tipo_doc = row['TIPO DE IDENTIFICACIÓN']
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
    for _, row in CIUDADES_2025.iterrows():
        municipio = row['MUNICIPIO']
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
    for _, row in INSTITUCIONES_2025.iterrows():
        nombre = row['INSTITUCIÓN EDUCATIVA']
        colegio_abrev = row['COLEGIO ABREVIADO PARA LISTADOS']
        grado = row.get('GRADO')
        
        result = connection.execute(text(
            "SELECT ID FROM Instituciones WHERE NOMBRE_INSTITUCION = :nombre"
        ), {'nombre': nombre})
        
        if result.fetchone() is None:
            connection.execute(text(
                "INSERT INTO Instituciones (NOMBRE_INSTITUCION, COLEGIO_ABREVIADO, GRADO) "
                "VALUES (:nombre, :colegio_abrev, :grado)"
            ), {'nombre': nombre, 'colegio_abrev': colegio_abrev, 'grado': grado})
    
    connection.commit()
    print("✓ Instituciones actualizado")
    
    print("\n4. Procesando Nivel_MCER...")
    for _, row in NIVEL_MCER_2025.iterrows():
        nivel = limpiar_valor(row['NIVEL_MCER'])
        tipo_pob = limpiar_valor(row['POBLACIÓN'])
        estado = limpiar_valor(row['ESTADO ETAPA 2'])
        anio = int(row['ANIO']) if pd.notna(row['ANIO']) else None
        idioma = limpiar_valor(row.get('IDIOMA'))
        certificado = limpiar_valor(row.get('CERTIFICADO'))
        
        if nivel is None or tipo_pob is None:
            continue
        
        result = connection.execute(text(
            "SELECT ID FROM Nivel_MCER WHERE NIVEL_MCER = :nivel AND TIPO_POBLACION = :tipo_pob"
        ), {'nivel': nivel, 'tipo_pob': tipo_pob})
        
        if result.fetchone() is None:
            connection.execute(text(
                "INSERT INTO Nivel_MCER (NIVEL_MCER, TIPO_POBLACION, ESTADO_ESTUDIANTE, ANIO, IDIOMA, CERTIFICADO) "
                "VALUES (:nivel, :tipo_pob, :estado, :anio, :idioma, :certificado)"
            ), {'nivel': nivel, 'tipo_pob': tipo_pob, 'estado': estado, 'anio': anio, 'idioma': idioma, 'certificado': certificado})
    
    connection.commit()
    print("✓ Nivel_MCER actualizado")
    
    print("\n5. Procesando Personas...")
    personas_nuevas = 0
    personas_actualizadas = 0
    personas_sin_doc = 0
    personas_saltadas = 0
    
    for idx, row in PERSONAS_2025.iterrows():
        numero_doc = row['NÚMERO DE IDENTIFICACIÓN']
        
        if numero_doc == 'Sin información':
            personas_sin_doc += 1
        
        tipo_doc_valor = limpiar_valor(row['TIPO DE IDENTIFICACIÓN'])
        if tipo_doc_valor is None:
            personas_saltadas += 1
            continue
        
        nivel_mcer_valor = limpiar_valor(row['NIVEL_MCER'])
        poblacion_valor = limpiar_valor(row['POBLACIÓN'])
        municipio_valor = limpiar_valor(row['MUNICIPIO'])
        institucion_valor = limpiar_valor(row['INSTITUCIÓN EDUCATIVA'])
        
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
        
        nivel_id = None
        if nivel_mcer_valor and poblacion_valor:
            nivel_id = connection.execute(text(
                "SELECT ID FROM Nivel_MCER WHERE NIVEL_MCER = :nivel AND TIPO_POBLACION = :tipo_pob"
            ), {'nivel': nivel_mcer_valor, 'tipo_pob': poblacion_valor}).fetchone()
        
        institucion_id = None
        if institucion_valor:
            institucion_id = connection.execute(text(
                "SELECT ID FROM Instituciones WHERE NOMBRE_INSTITUCION = :nombre"
            ), {'nombre': institucion_valor}).fetchone()
        
        persona_existe = connection.execute(text(
            "SELECT ID FROM Personas WHERE NUMERO_DOCUMENTO = :numero_doc"
        ), {'numero_doc': numero_doc}).fetchone()
        
        datos_persona = {
            'nombres': limpiar_valor(row['NOMBRES']),
            'apellidos': limpiar_valor(row['APELLIDOS']),
            'telefono1': limpiar_valor(row['TELÉFONO 1']),
            'telefono2': limpiar_valor(row['TELÉFONO 2']),
            'numero_doc': numero_doc,
            'correo': limpiar_valor(row['CORREO ELECTRÓNICO']),
            'direccion': limpiar_valor(row['DIRECCIÓN']),
            'sexo': limpiar_valor(row['SEXO']),
            'fecha_nac': convertir_fecha_mysql(row['FECHA DE NACIMIENTO']),
            'tipo_persona': limpiar_valor(row['TIPO POBLACION']),
            'tipo_doc_id': tipo_doc_id[0] if tipo_doc_id else None,
            'nivel_id': nivel_id[0] if nivel_id else None,
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
                   NIVEL_MCER_ID = :nivel_id,
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
                    TIPO_DOCUMENTO_ID, NIVEL_MCER_ID, CIUDAD_ID, INSTITUCION_ID)
                   VALUES (:nombres, :apellidos, :telefono1, :telefono2, :numero_doc, :correo,
                           :direccion, :sexo, :fecha_nac, :tipo_persona,
                           :tipo_doc_id, :nivel_id, :ciudad_id, :institucion_id)"""
            ), datos_persona)
            personas_nuevas += 1
    
    connection.commit()
    print(f"✓ Personas procesadas: {personas_nuevas} nuevas, {personas_actualizadas} actualizadas")
    if personas_sin_doc > 0:
        print(f"  ℹ {personas_sin_doc} personas con 'Sin información' como número de documento")
    if personas_saltadas > 0:
        print(f"  ⚠ {personas_saltadas} personas saltadas por datos incompletos")
    
    print("\n6. Procesando Sedes...")
    sedes_nuevas = 0
    
    for _, row in SEDES_2025.iterrows():
        numero_doc = row['NÚMERO DE IDENTIFICACIÓN']
        
        persona_id = connection.execute(text(
            "SELECT ID FROM Personas WHERE NUMERO_DOCUMENTO = :numero_doc"
        ), {'numero_doc': numero_doc}).fetchone()
        
        if persona_id is None:
            continue
        
        grupo = limpiar_valor(row['GRUPO'])
        jornada = limpiar_valor(row['JORNADA'])
        sede = limpiar_valor(row['SEDE NODAL'])
        
        sede_existe = connection.execute(text(
            """SELECT ID FROM Sedes 
               WHERE PERSONA_ID = :persona_id AND GRUPO = :grupo AND JORNADA = :jornada"""
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
    
    for _, row in CURSOS_2025.iterrows():
        entidad = limpiar_valor(row['ENTIDAD'])
        idioma = limpiar_valor(row['IDIOMA'])
        institucion = limpiar_valor(row['INSTITUCIÓN EDUCATIVA'])
        
        institucion_id = None
        if institucion:
            institucion_id = connection.execute(text(
                "SELECT ID FROM Instituciones WHERE NOMBRE_INSTITUCION = :nombre"
            ), {'nombre': institucion}).fetchone()
        
        if institucion_id is None:
            continue
        
        curso_existe = connection.execute(text(
            """SELECT ID FROM Cursos 
               WHERE ENTIDAD = :entidad AND IDIOMA = :idioma AND INSTITUCION_ID = :institucion_id"""
        ), {
            'entidad': entidad,
            'idioma': idioma,
            'institucion_id': institucion_id[0]
        }).fetchone()
        
        if curso_existe is None:
            connection.execute(text(
                """INSERT INTO Cursos (ENTIDAD, IDIOMA, INSTITUCION_ID)
                   VALUES (:entidad, :idioma, :institucion_id)"""
            ), {
                'entidad': entidad,
                'idioma': idioma,
                'institucion_id': institucion_id[0]
            })
            cursos_nuevos += 1
    
    connection.commit()
    print(f"✓ Cursos procesados: {cursos_nuevos} nuevos")

print("\n✅ Proceso completado exitosamente")
print(f"   - Archivos procesados: {len(dfs_list)}")
print(f"   - Personas nuevas: {personas_nuevas}")
print(f"   - Personas actualizadas: {personas_actualizadas}")
print(f"   - Sedes nuevas: {sedes_nuevas}")
print(f"   - Cursos nuevos: {cursos_nuevos}")
