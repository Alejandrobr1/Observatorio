# 📋 INSTRUCCIONES DE IMPORTACIÓN DE DATOS - OBSERVATORIO BILINGUISMO

## 🎯 Objetivo
Importar datos desde archivos CSV a la base de datos MySQL en cualquier PC. Solo se requieren dos archivos Python para realizar todo el proceso.

---

## 📂 ARCHIVOS NECESARIOS

### **En el PC de destino, necesitas:**

```
Observatorio/
├── Base_datos/
│   ├── conexion.py          ⬅️ Configuración de conexión a BD
│   ├── crear_tablas.py      ⬅️ Crear esquema de BD
│   ├── models.py            ⬅️ Modelos SQLAlchemy
│   └── __pycache__/
├── CSVs/
│   ├── data_2016.csv        ⬅️ Archivos CSV de datos
│   ├── data_2017.csv
│   ├── data_2018.csv
│   └── ... data_2025.csv
├── Queries/
│   ├── CSV_GENERAL.py                    ⬅️ **ARCHIVO 1**
│   ├── CSV_GENERAL_INTENSIFICACION.py    ⬅️ **ARCHIVO 2**
│   └── ...
├── env/                     ⬅️ Virtual environment (o crear uno)
└── logger_config.py         ⬅️ Configuración de logs
```

---

## 🔧 PASO A PASO - PREPARACIÓN

### **1. Configurar la conexión a la base de datos**

Editar el archivo: `Base_datos/conexion.py`

```python
from sqlalchemy import create_engine

# 🔴 AJUSTA ESTOS VALORES según tu configuración
DB_USER = "root"           # Usuario MySQL
DB_PASSWORD = "tu_contraseña"  # Contraseña MySQL
DB_HOST = "localhost"      # Host del servidor (local: localhost)
DB_PORT = 3308             # Puerto MySQL (generalmente 3306 o 3308)
DB_NAME = "observatorio_bilinguismo"  # Nombre de la BD

# Crear conexión
engine = create_engine(
    f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
    echo=False
)
```

### **2. Crear el esquema de base de datos**

Abrir terminal/PowerShell en la carpeta `Observatorio` y ejecutar:

```bash
# Si no tienes virtual environment, créalo primero:
python -m venv env

# Activar el ambiente virtual
.\env\Scripts\Activate.ps1

# Instalar dependencias requeridas
pip install pandas sqlalchemy mysql-connector-python

# Crear las tablas en la base de datos
python Base_datos/crear_tablas.py
```

**Resultado esperado:**
```
✓ Tablas creadas exitosamente en observatorio_bilinguismo
```

---

## 🚀 PASO 3: IMPORTAR LOS DATOS

### **Opción A: Importar TODOS los programas (Sábados + Intensificación + Docentes)**

```bash
# En la carpeta Observatorio, ejecutar:
python Queries/CSV_GENERAL.py
python Queries/CSV_GENERAL_INTENSIFICACION.py
```

**O ejecutar ambos en secuencia:**

```bash
python Queries/CSV_GENERAL.py && python Queries/CSV_GENERAL_INTENSIFICACION.py
```

### **Opción B: Importar solo un año específico**

Si solo necesitas importar un año (ej: 2025), modifica el archivo:

**En `CSV_GENERAL.py`, cambia la línea:**

```python
# Línea actual (al final del archivo):
años = range(2016, 2026)  # 2016 hasta 2025 inclusive

# Cambiar a:
años = range(2025, 2026)  # Solo 2025
```

---

## 📊 FLUJO DE DATOS

```
CSV_GENERAL.py
├── Lee: data_2016.csv ... data_2025.csv
├── Procesa:
│   ├── 1. Tipo_documentos
│   ├── 2. Ciudades
│   ├── 3. Instituciones
│   ├── 4. Nivel_MCER
│   ├── 5. Personas
│   ├── 6. Persona_Nivel_MCER (con NOMBRE_CURSO)
│   ├── 7. Sedes
│   └── 8. Cursos
└── Inserta en BD MySQL

CSV_GENERAL_INTENSIFICACION.py
├── Lee: data_2016_intensificacion.csv ... data_2025_intensificacion.csv
├── Mismo flujo anterior
└── Inserta en BD MySQL
```

---

## 🔍 VALIDAR QUE LOS DATOS IMPORTARON CORRECTAMENTE

Después de ejecutar los scripts, deberías ver algo como:

```
======================================================================
PROCESANDO AÑO 2025
======================================================================
✓ CSV leído: 1500 filas, 23 columnas
  - Grados únicos: ['Primero', 'Segundo', 'Tercero', ...]

✅ AÑO 2025 COMPLETADO:
   - Tipo documentos: 5
   - Ciudades: 12
   - Instituciones: 8
   - Niveles MCER: 25
   - Personas nuevas: 1200
   - Personas actualizadas: 100
   - Relaciones Persona-Nivel: 1500
   - Sedes: 450
   - Cursos: 35
```

---

## 📝 CAMBIOS REALIZADOS A LOS SCRIPTS (Actualización 2025)

### **✅ Ajustes de modelo**

1. **Tabla `Persona_Nivel_MCER`** ahora incluye:
   - `NOMBRE_CURSO` (nuevo campo)
   - Se usa para filtrar datos por tipo de curso en dashboards

2. **Campo `GRADO` movido** de `Instituciones` → `Nivel_MCER`

3. **Mejora en detección de duplicados:**
   - Ahora verifica: `NOMBRE_CURSO` + `ANIO_REGISTRO` + `NIVEL_MCER_ID`
   - Evita duplicados cuando hay múltiples cursos por persona

### **🔧 Scripts actualizados**

- ✅ `CSV_GENERAL.py` - Procesa años 2016-2025 (Sábados/Intensificación regular)
- ✅ `CSV_GENERAL_INTENSIFICACION.py` - Procesa años 2016-2025 (Datos de intensificación)

---

## ⚠️ PROBLEMAS COMUNES Y SOLUCIONES

### **Error: "No module named 'pandas'"**
```bash
pip install pandas sqlalchemy mysql-connector-python
```

### **Error: "Can't connect to MySQL server"**
- Verifica que MySQL esté corriendo: `localhost:3308`
- Verifica usuario/contraseña en `conexion.py`
- Verifica que la base de datos `observatorio_bilinguismo` exista

### **Error: "Table already exists"**
- El script sobrescribe automáticamente
- Si prefieres limpiar primero, ejecuta:
  ```bash
  python Base_datos/crear_tablas.py
  ```

### **Error: "File not found data_2025.csv"**
- Verifica que los CSVs estén en la carpeta `CSVs/`
- Los nombres deben ser: `data_AAAA.csv` o `data_AAAA_intensificacion.csv`

---

## ✅ CHECKLIST FINAL

- [ ] MySQL configurado en `Base_datos/conexion.py`
- [ ] Virtual environment creado y activado
- [ ] Dependencias instaladas: `pip install pandas sqlalchemy mysql-connector-python`
- [ ] Tablas creadas: `python Base_datos/crear_tablas.py`
- [ ] CSVs copiados en carpeta `CSVs/`
- [ ] Ejecutar: `python Queries/CSV_GENERAL.py`
- [ ] Ejecutar: `python Queries/CSV_GENERAL_INTENSIFICACION.py`
- [ ] ✅ Datos importados correctamente en BD

---

## 📞 NOTAS IMPORTANTES

1. **ANIO_REGISTRO**: Se extrae automáticamente del nombre del archivo (AAAA en `data_AAAA.csv`)
2. **NOMBRE_CURSO**: Se asigna automáticamente según `TIPO POBLACION` (Docente → "Formación Docente")
3. **Relaciones**: La tabla `Persona_Nivel_MCER` ahora almacena `NOMBRE_CURSO` para filtrado en dashboards
4. **Idempotencia**: Los scripts verifica duplicados antes de insertar (no duplica datos si se ejecuta varias veces)

---

**Última actualización:** Noviembre 2025  
**Versión:** 2.1 (Con soporte para NOMBRE_CURSO en Persona_Nivel_MCER)
