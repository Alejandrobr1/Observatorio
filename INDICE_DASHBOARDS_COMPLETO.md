# 📚 ÍNDICE COMPLETO DE DASHBOARDS

## ESTRUCTURA GENERAL

```
Observatorio/
├── Dashboards/
│   ├── FORMACIÓN SÁBADOS (ESTUDIANTES)
│   │   ├── estudiantes_niveles_sabados.py
│   │   ├── estudiantes_grado_sexo_sabados.py
│   │   ├── Estado_estudiantes_sabados.py
│   │   ├── asistencia_institucion_sabados.py
│   │   └── instituciones_sedes_sabados.py
│   │
│   ├── FORMACIÓN DOCENTE (DOCENTES) ⭐ NUEVO
│   │   ├── estudiantes_niveles_docente.py
│   │   ├── estudiantes_grado_sexo_docente.py
│   │   ├── Estado_estudiantes_docente.py
│   │   ├── asistencia_institucion_docente.py
│   │   └── instituciones_sedes_docente.py
│   │
│   └── INTENSIFICACIÓN (para referencia)
│       ├── estudiantes_niveles_intensificacion.py
│       └── Estado_estudiantes_intensificacion.py
│
├── Documentación/
│   ├── DASHBOARDS_FORMACION_DOCENTE.md ⭐ NUEVO
│   ├── TAREA_COMPLETADA_DOCENTES.txt ⭐ NUEVO
│   ├── INDICE.txt
│   ├── RESUMEN_EJECUTIVO.txt
│   ├── GUIA_RAPIDA_DASHBOARDS.md
│   └── INVENTARIO_COMPLETO.md
│
└── Scripts/
    ├── Base_datos/
    │   └── conexion.py
    └── Queries/
        └── csv_2025.py
```

---

## 🎯 ACCESO POR TIPO DE ANÁLISIS

### Análisis de ESTUDIANTES - Formación Sábados
1. **Niveles MCER**: `estudiantes_niveles_sabados.py`
2. **Grado y Sexo**: `estudiantes_grado_sexo_sabados.py`
3. **Estado**: `Estado_estudiantes_sabados.py`
4. **Por Institución**: `asistencia_institucion_sabados.py`
5. **Institución & Sede**: `instituciones_sedes_sabados.py`

### Análisis de DOCENTES - Formación Docente ⭐
1. **Niveles MCER**: `estudiantes_niveles_docente.py`
2. **Grado y Sexo**: `estudiantes_grado_sexo_docente.py`
3. **Estado**: `Estado_estudiantes_docente.py`
4. **Por Institución**: `asistencia_institucion_docente.py`
5. **Institución & Sede**: `instituciones_sedes_docente.py`

---

## 📊 COMPARACIÓN RÁPIDA

| Dashboard | Sábados | Docente | Intensificación |
|-----------|---------|---------|-----------------|
| **Niveles MCER** | ✅ | ✅ ⭐ | ✅ |
| **Grado & Sexo** | ✅ | ✅ ⭐ | ❌ |
| **Estado/Aprobación** | ✅ | ✅ ⭐ | ✅ |
| **Por Institución** | ✅ | ✅ ⭐ | ❌ |
| **Inst. & Sede** | ✅ | ✅ ⭐ | ❌ |

---

## 🔍 DETALLES POR DASHBOARD

### Dashboard 1: NIVELES MCER
```
Tipo de Análisis: Distribución por Nivel de Inglés y Sexo
Gráficos: Barras apiladas, pastel
Tablas: Desglose por nivel, porcentajes
Filtros: Año
Archivos:
  - estudiantes_niveles_sabados.py (Sábados)
  - estudiantes_niveles_docente.py (Docentes) ⭐
  - estudiantes_niveles_intensificacion.py (Intensificación)
```

### Dashboard 2: GRADO & SEXO
```
Tipo de Análisis: Distribución por Grado Escolar y Sexo
Gráficos: Barras horizontales, verticales, pastel
Tablas: Desglose por grado, diagnóstico
Filtros: Año
Archivos:
  - estudiantes_grado_sexo_sabados.py (Sábados)
  - estudiantes_grado_sexo_docente.py (Docentes) ⭐
```

### Dashboard 3: ESTADO/APROBACIÓN
```
Tipo de Análisis: Tasa de Aprobación
Gráficos: Pastel, barras, indicadores
Tablas: Estado, porcentajes
Filtros: Año
Archivos:
  - Estado_estudiantes_sabados.py (Sábados)
  - Estado_estudiantes_docente.py (Docentes) ⭐
  - Estado_estudiantes_intensificacion.py (Intensificación)
```

### Dashboard 4: POR INSTITUCIÓN
```
Tipo de Análisis: Distribución por Institución Educativa
Gráficos: Barras horizontales, pastel (top 10)
Tablas: Todas las instituciones, top 5
Filtros: Año
Archivos:
  - asistencia_institucion_sabados.py (Sábados)
  - asistencia_institucion_docente.py (Docentes) ⭐
```

### Dashboard 5: INSTITUCIÓN & SEDE NODAL
```
Tipo de Análisis: Distribución por Institución y Sede Nodal
Gráficos: Barras apiladas, pastel por institución
Tablas: Detallada, selector interactivo
Filtros: Año, selector de institución
Archivos:
  - instituciones_sedes_sabados.py (Sábados)
  - instituciones_sedes_docente.py (Docentes) ⭐
```

---

## 🔐 CONFIGURACIÓN DE CONEXIÓN

**Base de Datos**: observatorio_bilinguismo
**Host**: localhost:3308
**Usuario**: root
**Contraseña**: 123456 (configurado en código)

⚠️ Nota: Considerar mover credenciales a archivo .env en producción

---

## 📈 COBERTURA DE DATOS

### Estudiantes - Formación Sábados
- Años: 2016-2025
- Total: ~7,686 estudiantes
- Tipo: Estudiante
- Curso: Formación Sábados

### Docentes - Formación Docente ⭐
- Años: 2016-2025 (si disponible)
- Total: Por determinar
- Tipo: Docente
- Curso: Formación Docente

### Intensificación
- Años: 2016-2025
- Tipo: Estudiante
- Curso: Intensificación

---

## 🚀 EJECUCIÓN RÁPIDA

### Ejecutar un dashboard individual
```bash
cd Dashboards/
streamlit run estudiantes_niveles_docente.py
```

### Ejecutar todos (en tabs separadas del terminal)
```bash
# Terminal 1
streamlit run estudiantes_niveles_docente.py

# Terminal 2
streamlit run estudiantes_grado_sexo_docente.py

# Terminal 3
streamlit run Estado_estudiantes_docente.py

# etc...
```

### Crear multipage app (recomendado)
```bash
# Añadir a páginas: Inicio > Sábados > Docentes > Intensificación
```

---

## 📋 CHECKLIST DE USO

- [ ] Verificar conexión a BD
- [ ] Seleccionar año en sidebar
- [ ] Esperar a que carguen datos
- [ ] Revisar estadísticas en sidebar
- [ ] Explorar gráficos interactivos
- [ ] Expandir secciones adicionales
- [ ] Descargar datos si es necesario
- [ ] Comparar entre Sábados y Docentes

---

## 🔧 MANTENIMIENTO

### Cambios frecuentes
1. Actualizar conexión a BD si cambia IP/puerto
2. Revisar nuevos años disponibles
3. Sincronizar cambios entre versiones

### Cambios extraordinarios
1. Actualizar filtros de NOMBRE_CURSO
2. Cambiar estructura de gráficos
3. Añadir nuevos KPIs

---

## 📞 SOPORTE

### Si hay errores "No hay datos":
1. Verificar año seleccionado
2. Confirmar existencia de datos en BD
3. Revisar filtros (NOMBRE_CURSO, TIPO_PERSONA)

### Si hay problemas de conexión:
1. Verificar MySQL está corriendo
2. Confirmar credenciales
3. Revisar firewall

### Para nuevas funcionalidades:
1. Duplicar dashboard existente
2. Adaptar filtros
3. Ajustar título y mensajes

---

**Versión**: 1.0
**Última actualización**: Noviembre 10, 2025
**Documentación**: Completa
**Estado**: ✅ Operacional
