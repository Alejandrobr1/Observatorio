import pandas as pd
import os
import sys
from sqlalchemy import text
import numpy as np
from datetime import datetime


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Base_datos.conexion import engine

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

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
    formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%Y/%m/%d']
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
# FUNCIÓN PRINCIPAL DE IMPORTACIÓN
# ==========================================

def procesar_csv_anio(anio):
    """Procesa el CSV de un año específico"""
    
    print(f"\n{'='*70}")
    print(f"PROCESANDO AÑO {anio}")
    print(f"{'='*70}")
    
    # Buscar archivo CSV del año
    ruta_archivo = os.path.join(project_root, "CSVs", f"data_{anio}_intensificacion.csv")
    
    if not os.path.exists(ruta_archivo):
        print(f"⚠️ Archivo no encontrado: {ruta_archivo}")
        return False
    
    try:
        df = pd.read_csv(ruta_archivo, sep=';', encoding='utf-8-sig')
    except Exception as e:
        print(f"❌ Error al leer CSV: {e}")
        return False
    
    print(f"✓ CSV leído: {len(df)} filas, {len(df.columns)} columnas")
    
    # Rellenar valores faltantes
    columnas_texto = [
        'TIPO DE IDENTIFICACIÓN', 'NOMBRES', 'APELLIDOS', 'TELÉFONO 1', 'TELÉFONO 2',
        'CORREO ELECTRÓNICO', 'DIRECCIÓN', 'GENERO', 'TIPO POBLACION', 'NIVEL_MCER',
        'POBLACIÓN', 'ESTADO ETAPA 2', 'IDIOMA', 'MUNICIPIO',
        'INSTITUCIÓN EDUCATIVA', 'COLEGIO ABREVIADO PARA LISTADOS', 'GRADO',
        'GRUPO', 'JORNADA', 'SEDE NODAL', 'ENTIDAD', 'NOMBRE CURSO'
    ]
    
    for columna in columnas_texto:
        if columna in df.columns:
            df[columna] = df[columna].fillna('SIN INFORMACION')
    
    df['ANIO'] = df['FECHA'].apply(extraer_anio) if 'FECHA' in df.columns else anio
    
    # Si no hay columna FECHA, usar el año del archivo
    if 'ANIO' not in df.columns or df['ANIO'].isna().all():
        df['ANIO'] = anio
    
    df['NOMBRE_CURSO_PROCESADO'] = df.apply(
        lambda row: 'Formación Docente' if limpiar_valor(row.get('TIPO POBLACION')) == 'Docente' 
        else (limpiar_valor(row.get('NOMBRE CURSO')) if limpiar_valor(row.get('NOMBRE CURSO')) else 'SIN INFORMACION'), 
        axis=1
    )
    
    # Verificar columna GRADO
    grado_col = None
    for col in df.columns:
        if col.upper() == 'GRADO':
            grado_col = col
            break
    
    if grado_col is None:
        df['GRADO'] = 'SIN INFORMACION'
        grado_col = 'GRADO'
    
    print(f"  - Grados únicos: {sorted(df[grado_col].unique())[:15]}")
    
    # Preparar DataFrames
    TIPO_DOCUMENTOS = df[["TIPO DE IDENTIFICACIÓN"]].drop_duplicates().reset_index(drop=True)
    TIPO_DOCUMENTOS = TIPO_DOCUMENTOS[TIPO_DOCUMENTOS["TIPO DE IDENTIFICACIÓN"] != 'SIN INFORMACION']
    
    NIVEL_MCER_DF = df[[
        "NIVEL_MCER", "TIPO POBLACION", "ESTADO ETAPA 2", "ANIO", "IDIOMA", grado_col
    ]].copy()
    
    if grado_col != 'GRADO':
        NIVEL_MCER_DF = NIVEL_MCER_DF.rename(columns={grado_col: 'GRADO'})
    
    NIVEL_MCER_DF = NIVEL_MCER_DF.drop_duplicates().reset_index(drop=True)
    
    INSTITUCIONES = df[["INSTITUCIÓN EDUCATIVA","COLEGIO ABREVIADO PARA LISTADOS"]].drop_duplicates().reset_index(drop=True)
    INSTITUCIONES = INSTITUCIONES[INSTITUCIONES["INSTITUCIÓN EDUCATIVA"] != 'SIN INFORMACION']
    
    CIUDADES = df[["MUNICIPIO"]].drop_duplicates().reset_index(drop=True)
    CIUDADES = CIUDADES[CIUDADES["MUNICIPIO"] != 'SIN INFORMACION']
    
    CURSOS = df[["ENTIDAD","IDIOMA","INSTITUCIÓN EDUCATIVA","NOMBRE_CURSO_PROCESADO","TIPO POBLACION"]].copy()
    CURSOS = CURSOS[CURSOS["INSTITUCIÓN EDUCATIVA"] != 'SIN INFORMACION'].drop_duplicates().reset_index(drop=True)
    
    PERSONAS = df[["NOMBRES","APELLIDOS","TELÉFONO 1","TELÉFONO 2","NÚMERO DE IDENTIFICACIÓN","CORREO ELECTRÓNICO",
                        "DIRECCIÓN","GENERO","FECHA DE NACIMIENTO","TIPO POBLACION","TIPO DE IDENTIFICACIÓN",
                        "MUNICIPIO","INSTITUCIÓN EDUCATIVA"]].copy()
    
    PERSONA_NIVEL = df[["NÚMERO DE IDENTIFICACIÓN","NIVEL_MCER","TIPO POBLACION","ANIO","GRADO","NOMBRE_CURSO_PROCESADO"]].copy()
    
    SEDES = df[["GRUPO","JORNADA","SEDE NODAL","NÚMERO DE IDENTIFICACIÓN"]].copy()
    
    # Limpiar números de documento
    for df_temp in [PERSONAS, PERSONA_NIVEL, SEDES]:
        df_temp['NÚMERO DE IDENTIFICACIÓN'] = df_temp['NÚMERO DE IDENTIFICACIÓN'].apply(
            lambda x: 'Sin información' if pd.isna(x) or str(x).strip().lower() in ['nan', 'none', '', 'sin informacion'] else str(x).strip()
        )
    
    # ==========================================
    # INSERCIÓN EN BASE DE DATOS
    # ==========================================
    
    estadisticas = {
        'tipo_docs': 0,
        'ciudades': 0,
        'instituciones': 0,
        'niveles': 0,
        'personas_nuevas': 0,
        'personas_actualizadas': 0,
        'relaciones': 0,
        'sedes': 0,
        'cursos': 0
    }
    
    with engine.connect() as connection:
        
        # 1. Tipo_documentos
        for _, row in TIPO_DOCUMENTOS.iterrows():
            tipo_doc = row['TIPO DE IDENTIFICACIÓN']
            if tipo_doc == 'SIN INFORMACION':
                continue
            result = connection.execute(text("SELECT ID FROM Tipo_documentos WHERE TIPO_DOCUMENTO = :tipo_doc"), {'tipo_doc': tipo_doc})
            if result.fetchone() is None:
                connection.execute(text("INSERT INTO Tipo_documentos (TIPO_DOCUMENTO) VALUES (:tipo_doc)"), {'tipo_doc': tipo_doc})
                estadisticas['tipo_docs'] += 1
        connection.commit()
        
        # 2. Ciudades
        for _, row in CIUDADES.iterrows():
            municipio = row['MUNICIPIO']
            if municipio == 'SIN INFORMACION':
                continue
            result = connection.execute(text("SELECT ID FROM Ciudades WHERE MUNICIPIO = :municipio"), {'municipio': municipio})
            if result.fetchone() is None:
                connection.execute(text("INSERT INTO Ciudades (MUNICIPIO) VALUES (:municipio)"), {'municipio': municipio})
                estadisticas['ciudades'] += 1
        connection.commit()
        
        # 3. Instituciones
        for _, row in INSTITUCIONES.iterrows():
            nombre = row['INSTITUCIÓN EDUCATIVA']
            colegio_abrev = row['COLEGIO ABREVIADO PARA LISTADOS']
            if nombre == 'SIN INFORMACION':
                continue
            colegio_abrev = None if colegio_abrev == 'SIN INFORMACION' else colegio_abrev
            result = connection.execute(text("SELECT ID FROM Instituciones WHERE NOMBRE_INSTITUCION = :nombre"), {'nombre': nombre})
            if result.fetchone() is None:
                connection.execute(text("INSERT INTO Instituciones (NOMBRE_INSTITUCION, COLEGIO_ABREVIADO) VALUES (:nombre, :colegio_abrev)"), 
                                 {'nombre': nombre, 'colegio_abrev': colegio_abrev})
                estadisticas['instituciones'] += 1
        connection.commit()
        
        # 4. Nivel_MCER
        for _, row in NIVEL_MCER_DF.iterrows():
            nivel = limpiar_valor(row['NIVEL_MCER'])
            tipo_pob = limpiar_valor(row['TIPO POBLACION'])
            estado = limpiar_valor(row['ESTADO ETAPA 2'])
            anio_val = int(row['ANIO']) if pd.notna(row['ANIO']) else None
            idioma = limpiar_valor(row.get('IDIOMA'))
            grado = limpiar_valor(row.get('GRADO'))
            
            nivel = None if nivel == 'SIN INFORMACION' else nivel
            tipo_pob = None if tipo_pob == 'SIN INFORMACION' else tipo_pob
            estado = None if estado == 'SIN INFORMACION' else estado
            idioma = None if idioma == 'SIN INFORMACION' else idioma
            grado = None if grado == 'SIN INFORMACION' else grado
            
            if nivel is None and tipo_pob is None and grado is None:
                continue
            
            result = connection.execute(text(
                """SELECT ID FROM Nivel_MCER 
                   WHERE (NIVEL_MCER <=> :nivel) AND (TIPO_POBLACION <=> :tipo_pob) 
                   AND (ANIO <=> :anio) AND (GRADO <=> :grado)"""
            ), {'nivel': nivel, 'tipo_pob': tipo_pob, 'anio': anio_val, 'grado': grado})
            
            if result.fetchone() is None:
                connection.execute(text(
                    """INSERT INTO Nivel_MCER (NIVEL_MCER, TIPO_POBLACION, ESTADO_ESTUDIANTE, ANIO, IDIOMA, GRADO) 
                       VALUES (:nivel, :tipo_pob, :estado, :anio, :idioma, :grado)"""
                ), {'nivel': nivel, 'tipo_pob': tipo_pob, 'estado': estado, 'anio': anio_val, 'idioma': idioma, 'grado': grado})
                estadisticas['niveles'] += 1
        connection.commit()
        
        # 5. Personas
        for idx, row in PERSONAS.iterrows():
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
                'genero': None if limpiar_valor(row['GENERO']) == 'SIN INFORMACION' else limpiar_valor(row['GENERO']),
                'fecha_nac': convertir_fecha_mysql(row['FECHA DE NACIMIENTO']),
                'tipo_persona': None if limpiar_valor(row['TIPO POBLACION']) == 'SIN INFORMACION' else limpiar_valor(row['TIPO POBLACION']),
                'tipo_doc_id': tipo_doc_id[0] if tipo_doc_id else None,
                'ciudad_id': ciudad_id[0] if ciudad_id else None,
                'institucion_id': institucion_id[0] if institucion_id else None
            }
            
            if persona_existe:
                connection.execute(text(
                    """UPDATE Personas SET NOMBRES = :nombres, APELLIDOS = :apellidos, TELEFONO1 = :telefono1, 
                       TELEFONO2 = :telefono2, CORREO_ELECTRONICO = :correo, DIRECCION = :direccion, GENERO = :genero,
                       FECHA_NACIMIENTO = :fecha_nac, TIPO_PERSONA = :tipo_persona, TIPO_DOCUMENTO_ID = :tipo_doc_id,
                       CIUDAD_ID = :ciudad_id, INSTITUCION_ID = :institucion_id WHERE NUMERO_DOCUMENTO = :numero_doc"""
                ), datos_persona)
                estadisticas['personas_actualizadas'] += 1
            else:
                connection.execute(text(
                    """INSERT INTO Personas (NOMBRES, APELLIDOS, TELEFONO1, TELEFONO2, NUMERO_DOCUMENTO, CORREO_ELECTRONICO,
                       DIRECCION, GENERO, FECHA_NACIMIENTO, TIPO_PERSONA, TIPO_DOCUMENTO_ID, CIUDAD_ID, INSTITUCION_ID)
                       VALUES (:nombres, :apellidos, :telefono1, :telefono2, :numero_doc, :correo, :direccion, :genero,
                       :fecha_nac, :tipo_persona, :tipo_doc_id, :ciudad_id, :institucion_id)"""
                ), datos_persona)
                estadisticas['personas_nuevas'] += 1
        connection.commit()
        
        # 6. Persona_Nivel_MCER
        for _, row in PERSONA_NIVEL.iterrows():
            numero_doc = row['NÚMERO DE IDENTIFICACIÓN']
            nivel_mcer_valor = limpiar_valor(row['NIVEL_MCER'])
            poblacion_valor = limpiar_valor(row['TIPO POBLACION'])
            anio_registro = int(row['ANIO']) if pd.notna(row['ANIO']) else None
            grado_valor = limpiar_valor(row['GRADO'])
            nombre_curso_valor = limpiar_valor(row['NOMBRE_CURSO_PROCESADO'])
            
            nivel_mcer_valor = None if nivel_mcer_valor == 'SIN INFORMACION' else nivel_mcer_valor
            poblacion_valor = None if poblacion_valor == 'SIN INFORMACION' else poblacion_valor
            grado_valor = None if grado_valor == 'SIN INFORMACION' else grado_valor
            nombre_curso_valor = None if nombre_curso_valor == 'SIN INFORMACION' else nombre_curso_valor
            
            persona_id = connection.execute(text("SELECT ID FROM Personas WHERE NUMERO_DOCUMENTO = :numero_doc"), 
                                           {'numero_doc': numero_doc}).fetchone()
            
            if persona_id is None:
                continue
            
            nivel_id = connection.execute(text(
                """SELECT ID FROM Nivel_MCER 
                   WHERE (NIVEL_MCER <=> :nivel) AND (TIPO_POBLACION <=> :tipo_pob)
                   AND (ANIO <=> :anio) AND (GRADO <=> :grado) LIMIT 1"""
            ), {'nivel': nivel_mcer_valor, 'tipo_pob': poblacion_valor, 'anio': anio_registro, 'grado': grado_valor}).fetchone()
            
            if nivel_id is None:
                continue
            
            relacion_existe = connection.execute(text(
                """SELECT ID FROM Persona_Nivel_MCER 
                   WHERE PERSONA_ID = :persona_id AND NIVEL_MCER_ID = :nivel_id AND (ANIO_REGISTRO <=> :anio) AND (NOMBRE_CURSO <=> :nombre_curso)"""
            ), {'persona_id': persona_id[0], 'nivel_id': nivel_id[0], 'anio': anio_registro, 'nombre_curso': nombre_curso_valor}).fetchone()
            
            if relacion_existe is None:
                connection.execute(text(
                    """INSERT INTO Persona_Nivel_MCER (PERSONA_ID, NIVEL_MCER_ID, ANIO_REGISTRO, NOMBRE_CURSO)
                       VALUES (:persona_id, :nivel_id, :anio, :nombre_curso)"""
                ), {'persona_id': persona_id[0], 'nivel_id': nivel_id[0], 'anio': anio_registro, 'nombre_curso': nombre_curso_valor})
                estadisticas['relaciones'] += 1
        connection.commit()
        
        # 7. Sedes
        for _, row in SEDES.iterrows():
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
                estadisticas['sedes'] += 1
        connection.commit()
        
        # 8. Cursos
        for _, row in CURSOS.iterrows():
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
                estadisticas['cursos'] += 1
        connection.commit()
    
    # Mostrar resumen
    print(f"\n✅ AÑO {anio} COMPLETADO:")
    print(f"   - Tipo documentos: {estadisticas['tipo_docs']}")
    print(f"   - Ciudades: {estadisticas['ciudades']}")
    print(f"   - Instituciones: {estadisticas['instituciones']}")
    print(f"   - Niveles MCER: {estadisticas['niveles']}")
    print(f"   - Personas nuevas: {estadisticas['personas_nuevas']}")
    print(f"   - Personas actualizadas: {estadisticas['personas_actualizadas']}")
    print(f"   - Relaciones Persona-Nivel: {estadisticas['relaciones']}")
    print(f"   - Sedes: {estadisticas['sedes']}")
    print(f"   - Cursos: {estadisticas['cursos']}")
    
    return True


# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("IMPORTACIÓN MASIVA DE CSVs 2016-2025")
    print("="*70)
    
    años = range(2016, 2026)  # 2016 hasta 2025 inclusive
    
    resultados = {}
    
    for anio in años:
        exito = procesar_csv_anio(anio)
        resultados[anio] = exito
    
    # Resumen final
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)
    
    exitosos = sum(1 for v in resultados.values() if v)
    fallidos = sum(1 for v in resultados.values() if not v)
    
    print(f"\n✅ Años procesados exitosamente: {exitosos}")
    print(f"❌ Años no procesados: {fallidos}")
    
    if fallidos > 0:
        print("\nAños no procesados:")
        for anio, exito in resultados.items():
            if not exito:
                print(f"   - {anio}")
    
    print("\n" + "="*70)
    print("PROCESO COMPLETADO")
    print("="*70)
