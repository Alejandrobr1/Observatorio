# 📖 GUÍA DE DOCUMENTACIÓN

## 📚 Archivos de Documentación Disponibles

### 🚀 Para Comenzar Rápido
- **`00_INICIO_RAPIDO.md`** ← **LEER PRIMERO**
  - Resumen ejecutivo
  - Cómo ejecutar el proyecto
  - Estado actual

### 📋 Documentación Detallada
- **`README_ESTRUCTURA.md`**
  - Explicación completa de la estructura
  - Módulos y componentes
  - Importaciones

- **`ESTRUCTURA_FINAL.md`**
  - Visualización de carpetas
  - Archivos en cada ubicación
  - Cambios realizados

- **`REORGANIZACION_RESUMEN.md`**
  - Detalles de cambios
  - Archivos movidos
  - Checklist de verificación

### 🧹 Limpieza Opcional
- **`cleanup_old_structure.py`**
  - Script para eliminar carpetas antiguas
  - Uso después de verificar que todo funciona
  - Confirmación antes de eliminar

### 🔧 Scripts de Utilidad
- **`migrate_imports.py`**
  - Actualiza imports automáticamente
  - Ya ha sido ejecutado
  - Puede reutilizarse si es necesario

---

## 🗂️ Estructura de Directorios

```
Observatorio/
│
├── 📖 DOCUMENTACIÓN
│   ├── 00_INICIO_RAPIDO.md          ← LEER PRIMERO
│   ├── README_ESTRUCTURA.md
│   ├── ESTRUCTURA_FINAL.md
│   ├── REORGANIZACION_RESUMEN.md
│   ├── GUIA_DOCUMENTACION.md         ← Estás aquí
│   │
│   ├── migrate_imports.py            (Script ya ejecutado)
│   └── cleanup_old_structure.py      (Script opcional)
│
├── 🔵 CÓDIGO PRINCIPAL
│   ├── app.py                        (Punto de entrada)
│   ├── dashboard_config.py           (Configuración)
│   └── requirements.txt              (Dependencias)
│
├── 🟣 MÓDULOS (src/)
│   ├── src/config/                  (Configuración)
│   ├── src/database/                (Base de datos)
│   └── src/utils/                   (Utilidades)
│
├── 🟠 DATOS (data/)
│   ├── data/csv/                    (Archivos fuente)
│   ├── data/imports/                (Scripts import)
│   ├── data/exports/                (Generado)
│   └── data/verify/                 (Validación)
│
├── 🟢 DASHBOARDS
│   ├── pages/                       (Activos 1p-11p)
│   └── dashboards_archive/          (Backup 1-10)
│
└── 🟤 OTROS
    ├── assets/                      (Logos, recursos)
    ├── logs/                        (Registros)
    ├── env/                         (Virtual env)
    └── .streamlit/                  (Config)
```

---

## ⚡ Quick Start

```bash
# 1. Activar entorno
.\env\Scripts\Activate.ps1

# 2. Ejecutar
streamlit run app.py

# 3. Abrir en navegador
# http://localhost:8501
```

---

## 📊 Mapeo de Cambios

### Archivos Movidos a `src/database/`
- ✓ `Base_datos/conexion.py`
- ✓ `Base_datos/models.py`
- ✓ `Base_datos/crear_tablas.py`
- ✓ `Base_datos/crear_tabla_especifica.py`

### Archivos Movidos a `src/config/`
- ✓ `logger_config.py`

### Archivos Movidos a `data/imports/`
- ✓ `Queries/insertar_datos_2016_2019.py`
- ✓ `Queries/insertar_datos_2021_2025.py`
- ✓ `Queries/insertar_docentes.py`
- ✓ `Queries/insertar_escuela_nueva.py`
- ✓ `Queries/insertar_estudiantes_colombo.py`
- ✓ `Queries/verificar_datos_tablas.py`

### Archivos Movidos a `data/csv/`
- ✓ Todos los archivos de `CSVs/`

### Archivos Movidos a `dashboards_archive/`
- ✓ Todos los archivos de `Dashboards/` (10 archivos)

---

## 🔍 Navegación Rápida

**¿Quiero saber...?**

- ✓ Cómo ejecutar → Ver `00_INICIO_RAPIDO.md`
- ✓ Estructura del proyecto → Ver `README_ESTRUCTURA.md`
- ✓ Archivos movidos → Ver `ESTRUCTURA_FINAL.md`
- ✓ Detalles técnicos → Ver `REORGANIZACION_RESUMEN.md`
- ✓ Eliminar carpetas antiguas → Ejecutar `cleanup_old_structure.py`

---

## 💾 Base de Datos

**Módulo:** `src/database/`

- `conexion.py` - Conexión MySQL
- `models.py` - Modelos SQLAlchemy
- `crear_tablas.py` - Script de creación

**Tablas:**
- Docentes
- Estudiantes_2016_2019
- Estudiantes_2021_2025
- Estudiantes_Colombo
- Escuela_nueva

---

## 📊 Dashboards

**Activos:** `pages/` (11 dashboards)
```
1p-11p: Dashboards en uso
```

**Archivo:** `dashboards_archive/` (10 dashboards)
```
1-9: Versiones antiguas
```

---

## 🎯 Funcionalidades

✅ Base de datos MySQL operativa
✅ Importación de datos CSV
✅ 11 dashboards interactivos
✅ Sistema de filtros por población
✅ Exportación de datos
✅ Logging centralizado

---

## 📞 Soporte

Si encuentras problemas:

1. Verifica que `streamlit run app.py` funciona
2. Revisa `logs/` para errores
3. Consulta `README_ESTRUCTURA.md`
4. Ejecuta `python -c "from src.database.conexion import engine; print('✓')"`

---

## 📅 Información

- **Fecha:** 29 de Noviembre de 2025
- **Estado:** ✅ Operativo
- **Estructura:** ✅ Optimizada
- **Documentación:** ✅ Completa

---

**¡Proyecto listo para usar!** 🚀

Comienza leyendo: `00_INICIO_RAPIDO.md`
