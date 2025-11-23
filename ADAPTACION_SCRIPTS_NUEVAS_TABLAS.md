# Adaptación de Scripts para Nueva Estructura de Base de Datos

## Resumen de Cambios

Se ha adaptado el proyecto para trabajar con una nueva estructura de base de datos que utiliza **tablas independientes por años** en lugar de tablas universales con campos para todos los años.

### Cambios Principales

#### 1. **Nueva Estructura de Base de Datos (models.py)**
```
Antes:
- Tabla única: Personas
- Tabla única: Persona_Nivel_MCER
- Tabla única: Nivel_MCER

Ahora:
- Tablas independientes: Estudiantes_2016, Estudiantes_2017, etc.
- Estructura simplificada: ID, FECHA, SEDE_NODAL, POBLACION, NIVEL, DIA, JORNADA, MATRICULADOS, ETAPA
- Sin valores nulos ni vacíos
- Campo FECHA contiene el año
```

#### 2. **Scripts de Inserción Adaptados**

##### **insertar_datos_2016.py**
- ✅ Lee datos del archivo `tabla_2016.csv`
- ✅ Limpia automáticamente filas completamente vacías
- ✅ Valida que no haya valores nulos ni vacíos en datos válidos
- ✅ Detecta y evita duplicados
- ✅ Proporciona estadísticas detalladas de inserción
- ✅ Manejo robusto de errores con logging

**Características:**
```python
- Extrae año del CSV o usa parámetro
- Convierte tipos de datos correctamente (int para números, string para texto)
- Verifica duplicados antes de insertar
- Commit cada 100 registros para mejor performance
- Muestra distribución de datos por población, nivel, día
- Calcula total de estudiantes matriculados
```

##### **insertar_datos_generico.py** (NUEVO)
Script reutilizable que puede usarse para cualquier año:

```python
insertar_datos_por_año('tabla_2016.csv', 'Estudiantes_2016', año=2016)
insertar_datos_por_año('tabla_2017.csv', 'Estudiantes_2017', año=2017)
# ... y así sucesivamente
```

**Ventajas:**
- Función genérica reutilizable
- Manejo flexible de años
- Evita duplicación de código
- Fácil de mantener y escalar

### Resultados de Ejecución (tabla_2016.csv)

```
Archivo original: 115 filas
Después de limpieza: 27 filas válidas
Registros insertados: 21
Registros duplicados: 6
Errores: 0

Distribución:
├── Población
│   ├── Inglés Adolescentes: 12 registros
│   └── Inglés Niños: 9 registros
├── Niveles
│   └── Nivel 1: 21 registros
├── Días
│   ├── Sábado: 16 registros
│   ├── Martes y jueves: 3 registros
│   └── Miércoles y viernes: 2 registros
└── Total de matriculados: 337 estudiantes
```

### Características de Validación

1. **Limpieza Automática**
   - Elimina filas completamente vacías
   - Preserva espacios en blanco mínimos
   - No altera datos válidos

2. **Conversión de Tipos**
   - Año: Integer
   - Sede Nodal: String (trimmed)
   - Población: String (trimmed)
   - Nivel: Integer
   - Día: String (trimmed)
   - Jornada: String (trimmed)
   - Matriculados: Integer
   - Etapa: Integer

3. **Detección de Duplicados**
   - Verifica combinación única: FECHA + SEDE_NODAL + POBLACION + NIVEL + DIA + JORNADA + ETAPA
   - Evita inserciones duplicadas
   - Registra duplicados encontrados

4. **Manejo de Errores**
   - Captura errores por fila
   - Registra con logging
   - Continúa procesamiento en otros registros
   - Muestra resumen de errores

### Uso del Script

#### Opción 1: Script Específico
```bash
python Queries/insertar_datos_2016.py
```

#### Opción 2: Script Genérico
```bash
python Queries/insertar_datos_generico.py
```

O modificar el archivo para insertar otros años:
```python
# En el bloque if __name__ == "__main__":
insertar_datos_por_año('tabla_2017.csv', 'Estudiantes_2017', año=2017)
```

### Estadísticas Generadas

El script proporciona información detallada sobre:
- ✅ Total de registros insertados
- ✅ Registros duplicados
- ✅ Registros con error
- ✅ Distribución por población
- ✅ Distribución por nivel
- ✅ Distribución por día
- ✅ Total de estudiantes matriculados

### Archivos CSV Esperados

```
CSVs/
├── tabla_2016.csv (✓ Procesado)
├── tabla_2017.csv (pendiente)
├── tabla_2018.csv (pendiente)
└── tabla_2019.csv (pendiente)
```

### Estructura del CSV

```
Año;Sede Nodal;Población;Nivel;Día;Jornada;Matriculados;Etapa
2016;[Sede];[Población];[Nivel];[Día];[Jornada];[Número];[Etapa]
```

Ejemplo:
```
2016;Gilberto Echeverri Mejía;Inglés Adolescentes;1;Sábado;Tarde;7;1
2016;Josefina Muñoz González;Inglés Adolescentes;1;Sábado;Tarde;20;1
```

### Logging

Todos los procesos se registran en `logs/`:
- Información de conexión
- Estadísticas de inserción
- Errores y excepciones
- Cierre de conexiones

### Consideraciones de Performance

- Commit cada 100 registros
- Detecta duplicados antes de insertar (evita operaciones innecesarias)
- Conexión única reutilizada
- Manejo eficiente de memoria con pandas

### Próximos Pasos

1. ✅ Insertar datos de 2016: `tabla_2016.csv`
2. ⏳ Insertar datos de años subsecuentes (2017-2023)
3. ⏳ Validar integridad de datos en Streamlit dashboards
4. ⏳ Actualizar dashboards para consultar las tablas por año

### Integración con Dashboards

Para actualizar los dashboards para usar esta nueva estructura:

```python
# Antes:
df = pd.read_sql("SELECT * FROM Personas WHERE ANIO = 2016", engine)

# Ahora:
df = pd.read_sql("SELECT * FROM Estudiantes_2016", engine)
```

### Referencias Técnicas

- **Lenguaje**: Python 3.13
- **ORM**: SQLAlchemy
- **Base de Datos**: MySQL
- **Librerías**: pandas, sqlalchemy, mysql-connector-python
- **Manejo de Logs**: logger_config personalizado
