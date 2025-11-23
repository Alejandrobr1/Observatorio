# 📊 Dashboards Formación Sábados

## Descripción General

Este conjunto de dashboards está filtrado específicamente para **estudiantes del curso "FORMACIÓN SÁBADOS"**.

Todos los dashboards aplicarán automáticamente los siguientes filtros:
- **NOMBRE_CURSO**: `FORMACION SABADOS` (usa LIKE '%formacion sabados%')
- **TIPO_PERSONA**: `Estudiante`

---

## 📈 Dashboards Disponibles

### 1. **estudiantes_niveles_sabados.py**
**Título**: 📊 Estudiantes por Nivel MCER y Genero - FORMACIÓN SÁBADOS

**Descripción**:
- Muestra la distribución de estudiantes de Formación Sábados por nivel MCER (A1, A2, B1, B2, C1, C2)
- Desglosado por genero (Masculino/Femenino)
- Gráfico de barras apiladas y tabla resumen

**Filtros Disponibles**:
- 📅 Año
- 🏫 Institución Educativa (opcional)

**Gráficos**:
- Barras apiladas horizontales por nivel MCER
- Gráfico de pastel con distribución por genero
- Tabla resumen

---

### 2. **estudiantes_grado_genero_sabados.py**
**Título**: 📊 Distribución de Estudiantes por Genero y Grado - FORMACIÓN SÁBADOS

**Descripción**:
- Muestra la distribución de estudiantes de Formación Sábados por grado escolar
- Desglosado por genero (Masculino/Femenino)
- Barras horizontales y verticales apiladas

**Filtros Disponibles**:
- 📅 Año

**Gráficos**:
- Barras horizontales apiladas por grado
- Barras verticales apiladas por grado
- Tabla resumen por grado
- Gráfico de pastel con distribución por genero

---

### 3. **Estado_estudiantes_sabados.py**
**Título**: 📊 Aprobación de Estudiantes por Año - FORMACIÓN SÁBADOS

**Descripción**:
- Muestra el estado de aprobación de estudiantes de Formación Sábados
- Categorización: Aprobó / No Aprobó
- Cálculo automático de tasa de aprobación

**Filtros Disponibles**:
- 📅 Año

**Gráficos**:
- Gráfico de pastel con distribución de aprobación
- Gráfico de barras comparativo
- Tabla resumen
- Indicador de tasa de aprobación (verde/amarillo/rojo según porcentaje)

---

### 4. **asistencia_institucion_sabados.py**
**Título**: 📊 Asistencia por Institución - FORMACIÓN SÁBADOS

**Descripción**:
- Muestra la distribución de asistencia por institución educativa
- Desglosado por tipos de asistencia (Asistió/No Asistió/Justificada/etc.)
- Top 5 instituciones con más estudiantes

**Filtros Disponibles**:
- 📅 Año

**Gráficos**:
- Barras horizontales apiladas por institución
- Gráfico de pastel con distribución por asistencia (por institución seleccionada)
- Tabla completa de todas las instituciones

---

### 5. **instituciones_sedes_sabados.py**
**Título**: 🏫 Distribución de Estudiantes por Institución y Sede Nodal - FORMACIÓN SÁBADOS

**Descripción**:
- Muestra la distribución de estudiantes por institución y sede nodal
- Análisis de cobertura territorial
- Detalles por institución y sede

**Filtros Disponibles**:
- 📅 Año

**Gráficos**:
- Barras horizontales apiladas por institución y sede nodal
- Gráfico de pastel con distribución por sede (por institución seleccionada)
- Tabla completa de instituciones y sedes

---

## 🚀 Cómo Ejecutar los Dashboards

```bash
# Navega a la carpeta de dashboards
cd "Dashboards"

# Ejecuta cualquier dashboard (ejemplo)
streamlit run estudiantes_niveles_sabados.py
```

Todos los dashboards se abrirán en el navegador en `http://localhost:8501`

---

## 🔍 Filtros Comunes

Todos los dashboards incluyen:

### Filtro de Año (📅)
- Automáticamente detecta años disponibles con datos de Formación Sábados
- Permite cambiar entre años para análisis temporal

### Filtro de Institución (🏫) - *Disponible en algunos dashboards*
- Permite filtrar datos de una institución específica
- Opción "TODAS" para ver datos consolidados

---

## 📊 Consultas SQL Base

Todos los dashboards utilizan esta estructura base de filtrado:

```sql
WHERE pnm.ANIO_REGISTRO = :año
AND LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion sabados%'
AND p.TIPO_PERSONA = 'Estudiante'
```

---

## 💾 Conexión a Base de Datos

- **Host**: localhost
- **Puerto**: 3308
- **Usuario**: root
- **Contraseña**: 123456
- **Base de Datos**: observatorio_bilinguismo

---

## ⚠️ Notas Importantes

1. **Filtrado Automático**: Todos los dashboards filtran automáticamente para mostrar SOLO datos de estudiantes en el programa de Formación Sábados.

2. **Datos Historicos**: Los dashboards incluyen datos desde 2021 en adelante (según disponibilidad).

3. **Rendimiento**: Si hay muchas instituciones o sedes, algunos gráficos muestran el TOP 15 para mejor visualización.

4. **Valores Nulos**: Se filtran automáticamente los valores "SIN INFORMACION" y campos nulos.

---

## 📋 Comparación con Dashboards Originales

| Aspecto | Original | Formación Sábados |
|---------|----------|-------------------|
| **Filtro NOMBRE_CURSO** | ❌ No | ✅ Sí (FORMACION SABADOS) |
| **Filtro TIPO_PERSONA** | ❌ No | ✅ Sí (Estudiante) |
| **Cobertura de Datos** | Todos los cursos | Solo Formación Sábados |
| **Precisión** | Mixta | Alta |
| **Casos de Uso** | Análisis general | Análisis específico |

---

## 🎯 Casos de Uso

Estos dashboards son ideales para:

- ✅ Análisis de rendimiento académico de Formación Sábados
- ✅ Evaluación de cobertura geográfica
- ✅ Análisis de asistencia
- ✅ Comparación de resultados entre años
- ✅ Reportes institucionales específicos
- ✅ Evaluación de equidad de género en el programa

---

## 📞 Soporte

Para problemas o inconsistencias en los datos:
1. Verifica que la base de datos esté activa
2. Revisa que el archivo CSV tenga la columna NOMBRE_CURSO
3. Consulta el diagnóstico disponible en cada dashboard (ícono 🔍)

---

**Última actualización**: Noviembre 2025
**Estado**: Operativo ✅
