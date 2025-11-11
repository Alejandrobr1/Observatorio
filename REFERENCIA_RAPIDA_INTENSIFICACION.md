# 📋 REFERENCIA RÁPIDA - INTENSIFICACIÓN

## ¿QUÉ CAMBIÓ?

### Problema Original
Los dashboards de intensificación mostraban datos incorrectos porque usaban:
```sql
INNER JOIN Cursos c ON c.INSTITUCION_ID = p.INSTITUCION_ID
```

Esto causaba que si una institución tenía 10 cursos (2 de intensificación, 8 regulares), se mostraban todos los 10 cursos para cada persona.

### Solución Implementada
1. **Agregar columna `NOMBRE_CURSO`** a tabla `Persona_Nivel_MCER`
2. **Guardar el nombre específico del curso** en cada relación persona-nivel
3. **Filtrar directamente por `NOMBRE_CURSO`** en lugar de por institución

```sql
-- Ahora así:
WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%'
```

---

## DATOS DISPONIBLES

### Intensificación
- **2021**: 229 estudiantes
- **2022**: 1,164 estudiantes
- **2023**: 1,114 estudiantes
- **Total**: 2,507 estudiantes

### Otros Cursos
- **Formación Sábados**: 3,218 estudiantes (todos los años)
- **Formación Docente**: 957 estudiantes (todos los años)

---

## DASHBOARDS FUNCIONALES

Todos estos dashboards ahora muestran SOLO datos de intensificación:

1. **Estado_estudiantes_intensificacion.py**
   - Muestra aprobación de estudiantes
   
2. **estudiantes_grado_sexo_intensificacion.py**
   - Distribución por grado y sexo

3. **asistencia_institucion_intensificacion.py**
   - Distribución por institución

4. **estudiantes_niveles_intensificacion.py**
   - Distribución por nivel MCER

5. **instituciones_sedes_intensificacion.py**
   - Sedes nodales y distribución

---

## CÓMO EJECUTAR

```bash
# Opción 1: Con Python
python -m streamlit run Dashboards/Estado_estudiantes_intensificacion.py

# Opción 2: Con Streamlit directo
streamlit run Dashboards/Estado_estudiantes_intensificacion.py

# Opción 3: Main dashboard (todos incluidos)
python main_dashboard.py
```

---

## VERIFICAR DATOS

Para verificar que los datos están correctos, ejecute:

```bash
python prueba_queries_intensificacion.py
```

Debería mostrar:
- ✓ Estudiantes intensificación 2023: 1,114
- ✓ Estudiantes intensificación 2022: 1,164
- ✓ Registros de INTENSIFICACION total: 2,523

---

## ARCHIVOS IMPORTANTES

| Archivo | Propósito |
|---------|----------|
| `Base_datos/models.py` | Definición de modelos - **Contiene NOMBRE_CURSO** |
| `Queries/csv_*.py` | Scripts de importación - **Guardan NOMBRE_CURSO** |
| `Dashboards/*intensificacion.py` | Dashboards específicos de intensificación |
| `prueba_queries_intensificacion.py` | Pruebas unitarias de las queries |
| `verificar_nombre_curso.py` | Verifica integridad de datos en BD |

---

## ESTRUCTURA DE BD

### Tabla: Persona_Nivel_MCER

| Columna | Tipo | Descripción |
|---------|------|-------------|
| ID | BIGINT | Identificador único |
| PERSONA_ID | BIGINT | FK → Personas |
| NIVEL_MCER_ID | BIGINT | FK → Nivel_MCER |
| ANIO_REGISTRO | INT | Año (2022, 2023, 2025) |
| **NOMBRE_CURSO** | VARCHAR(200) | **← NUEVO: Nombre del curso** |

### Valores Posibles para NOMBRE_CURSO

```
• "Intensificacion" (2,523 registros)
• "FORMACION SABADOS" (2,069 registros)
• "Formación Docente" (859 registros)
```

---

## QUERIES DE EJEMPLO

### Contar estudiantes intensificación 2023
```sql
SELECT COUNT(DISTINCT p.ID)
FROM Persona_Nivel_MCER pnm
JOIN Personas p ON pnm.PERSONA_ID = p.ID
WHERE pnm.ANIO_REGISTRO = 2023
AND LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%';
-- Resultado: 1,114 estudiantes
```

### Distribución por sexo
```sql
SELECT p.SEXO, COUNT(DISTINCT p.ID)
FROM Persona_Nivel_MCER pnm
JOIN Personas p ON pnm.PERSONA_ID = p.ID
WHERE pnm.ANIO_REGISTRO = 2023
AND LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%'
GROUP BY p.SEXO;
-- Resultado: M: 601, F: 513
```

---

## SOPORTE

Si necesita:
- Agregar más años de intensificación → `poblar_intensificacion.py`
- Verificar datos → `verificar_nombre_curso.py`
- Probar queries → `prueba_queries_intensificacion.py`
- Regenerar datos → Re-ejecutar archivos CSV

---

**Estado**: ✅ COMPLETADO Y LISTO PARA PRODUCCIÓN

*Última actualización: 10 de Noviembre de 2025*
