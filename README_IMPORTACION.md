# 🎯 GUÍA RÁPIDA - IMPORTACIÓN DE DATOS

## ¿Qué hacer para importar los datos en otro PC?

### **3 pasos simples:**

#### **1️⃣ Preparar el ambiente**

```powershell
# En la carpeta Observatorio, ejecutar en PowerShell:
python -m venv env
.\env\Scripts\Activate.ps1
pip install pandas sqlalchemy mysql-connector-python
```

#### **2️⃣ Configurar la conexión a MySQL**

Editar: `Base_datos/conexion.py`

```python
DB_USER = "root"
DB_PASSWORD = "tu_contraseña"
DB_HOST = "localhost"
DB_PORT = 3308  # ← Puerto de tu MySQL
DB_NAME = "observatorio_bilinguismo"
```

#### **3️⃣ Crear tablas e importar datos**

```powershell
# Crear el esquema de base de datos
python Base_datos/crear_tablas.py

# Ejecutar importación COMPLETA (automática)
python EJECUTAR_IMPORTACION.py
```

---

## 📂 Estructura de carpetas requerida

```
Observatorio/
├── Base_datos/
│   ├── conexion.py
│   ├── crear_tablas.py
│   ├── models.py
│   └── __pycache__/
├── CSVs/
│   ├── data_2016.csv
│   ├── data_2017.csv
│   └── ... data_2025.csv
├── Queries/
│   ├── CSV_GENERAL.py
│   ├── CSV_GENERAL_INTENSIFICACION.py
│   └── ...
├── Dashboards/
│   └── (archivos .py de dashboards)
├── env/
└── EJECUTAR_IMPORTACION.py  ← Ejecuta esto
```

---

## 🚀 Datos que se importan

Automáticamente se importan:

✅ **Programas Sábados** (años 2016-2025)
- Estudiantes regulares
- Datos de niveles MCER
- Instituciones y sedes

✅ **Programas Intensificación** (años 2016-2025)
- Estudiantes de programas intensivos
- Datos específicos por intensificación

✅ **Docentes (Formación Docente)**
- Se detectan automáticamente (TIPO_PERSONA = 'Docente')

---

## ❓ Preguntas frecuentes

### ¿Qué pasa si tengo errores de conexión?

1. Verifica que MySQL esté corriendo en puerto **3308**
2. Verifica usuario y contraseña en `Base_datos/conexion.py`
3. Si necesitas cambiar el puerto, actualiza `conexion.py` y `crear_tablas.py`

### ¿Puedo importar solo un año?

Sí, edita el archivo `Queries/CSV_GENERAL.py` y cambia la línea:

```python
# Original:
años = range(2016, 2026)

# Cambiar a:
años = range(2025, 2026)  # Solo 2025
```

### ¿Qué tablas se crean?

- `Tipo_documentos`
- `Ciudades`
- `Instituciones`
- `Nivel_MCER`
- `Personas`
- `Persona_Nivel_MCER` ← Con NOMBRE_CURSO
- `Sedes`
- `Cursos`

### ¿Cuánto tiempo tarda?

Depende de:
- Cantidad de CSVs (años 2016-2025)
- Cantidad de registros por CSV
- Velocidad de conexión a MySQL

Típicamente: **5-15 minutos** para todos los años

---

## ✅ Verificación

Cuando la importación termina, deberías ver:

```
======================================================================
📊 RESUMEN DE EJECUCIÓN
======================================================================
  CSV_GENERAL.py: ✅ ÉXITO
  CSV_GENERAL_INTENSIFICACION.py: ✅ ÉXITO

✅ IMPORTACIÓN COMPLETADA EXITOSAMENTE

📈 Los datos están listos para usar en los dashboards:
  • Dashboards Sábados
  • Dashboards Intensificación
  • Dashboards Formación Docente
```

---

## 🔧 Scripts principales

| Script | Propósito |
|--------|-----------|
| `EJECUTAR_IMPORTACION.py` | **USA ESTE** - Automatiza todo |
| `Queries/CSV_GENERAL.py` | Importa datos Sábados (2016-2025) |
| `Queries/CSV_GENERAL_INTENSIFICACION.py` | Importa datos Intensificación (2016-2025) |
| `Base_datos/crear_tablas.py` | Crea el esquema de BD |

---

**Versión:** 2.1  
**Última actualización:** Noviembre 2025  
**Estado:** ✅ Listo para producción
