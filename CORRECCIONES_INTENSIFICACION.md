# =====================================================
# CORRECCIÓN DE FILTROS DE INTENSIFICACIÓN
# =====================================================

## PROBLEMA IDENTIFICADO
El filtro de intensificación no estaba funcionando correctamente porque:

1. Los dashboards intensificación hacían JOIN a la tabla `Cursos` usando:
   ```sql
   INNER JOIN Cursos c ON c.INSTITUCION_ID = p.INSTITUCION_ID
   WHERE LOWER(c.NOMBRE_CURSO) LIKE '%intensificacion%'
   ```

2. **Problema**: Una institución puede tener múltiples cursos, algunos de intensificación y otros no.
   Por lo tanto, este JOIN incluía a TODAS las personas de esa institución si cualquiera de los cursos era de intensificación.

## SOLUCIÓN IMPLEMENTADA

### 1. Modelo actualizado (`Base_datos/models.py`)
- ✅ Agregada columna `NOMBRE_CURSO` a tabla `Persona_Nivel_MCER`
- Permite almacenar el nombre del curso directamente en la relación persona-nivel

### 2. Migración SQL (`migration_add_nombre_curso.sql`)
- ✅ Creado script para agregar columna a BD
- **ACCIÓN REQUERIDA**: Ejecutar en la base de datos:
  ```sql
  ALTER TABLE Persona_Nivel_MCER ADD COLUMN NOMBRE_CURSO VARCHAR(200) NULL;
  ```

### 3. Scripts de importación CSV actualizados
- ✅ `csv_2022.py`: Ahora incluye `NOMBRE_CURSO` en inserciones a `Persona_Nivel_MCER`
- ✅ `csv_2023.py`: Ahora incluye `NOMBRE_CURSO` en inserciones a `Persona_Nivel_MCER`
- ✅ `csv_2025.py`: Ahora incluye `NOMBRE_CURSO` en inserciones a `Persona_Nivel_MCER`

### 4. Dashboards intensificación corregidos
Cambio de query pattern:

**ANTES (INCORRECTO):**
```sql
INNER JOIN Cursos c ON c.INSTITUCION_ID = p.INSTITUCION_ID
WHERE LOWER(c.NOMBRE_CURSO) LIKE '%intensificacion%'
```

**AHORA (CORRECTO):**
```sql
WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%'
```

**Dashboards ya corregidos:**
- ✅ `Estado_estudiantes_intensificacion.py`
- ✅ `estudiantes_grado_sexo_intensificacion.py`
- ✅ `asistencia_institucion_intensificacion.py`

**Aún requieren corrección:**
- ⏳ `estudiantes_niveles_intensificacion.py` (parcialmente)
- ⏳ `instituciones_sedes_intensificacion.py` (parcialmente)

## PASOS A SEGUIR

### 1. Ejecutar migración en BD
```bash
cd d:\Proyectos Jc Code\Archivos para BD rionegro\Observatorio
mysql -h localhost -P 3308 -u root -p123456 observatorio_bilinguismo < migration_add_nombre_curso.sql
```

### 2. Re-ejecutar scripts de importación CSV
```bash
python Queries/csv_2022.py
python Queries/csv_2023.py
python Queries/csv_2025.py
```

### 3. Verificar datos importados correctamente
```sql
SELECT DISTINCT NOMBRE_CURSO FROM Persona_Nivel_MCER WHERE NOMBRE_CURSO IS NOT NULL LIMIT 10;
SELECT COUNT(*) as total FROM Persona_Nivel_MCER WHERE LOWER(NOMBRE_CURSO) LIKE '%intensificacion%';
```

### 4. Terminar de corregir dashboards pendientes
- `estudiantes_niveles_intensificacion.py`
- `instituciones_sedes_intensificacion.py`

**Pattern a aplicar:**
Reemplazar todos los JOINs a `Cursos` con filtro directo en `pnm.NOMBRE_CURSO`

## VALIDACIÓN POST-CORRECCIÓN

Después de completar los pasos anteriores, probar cada dashboard:

```bash
streamlit run Estado_estudiantes_intensificacion.py
streamlit run estudiantes_grado_sexo_intensificacion.py
streamlit run asistencia_institucion_intensificacion.py
streamlit run estudiantes_niveles_intensificacion.py
streamlit run instituciones_sedes_intensificacion.py
```

Verificar que:
- ✓ Solo aparecen datos de personas en cursos de intensificación
- ✓ Los números coinciden con consulta directa a BD
- ✓ Los filtros de año funcionan correctamente
- ✓ Las visualizaciones se cargan sin errores
