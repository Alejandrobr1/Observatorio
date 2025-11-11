# 🚀 Despliegue en Streamlit Cloud

## Instrucciones para desplegar el Observatorio de Bilingüismo en Streamlit Cloud

### Paso 1: Preparar el repositorio en GitHub

1. **Crear un repositorio en GitHub** (si no lo tienes)
   - Ve a [github.com/new](https://github.com/new)
   - Nombre: `observatorio-bilinguismo`
   - Descripción: "Sistema de Monitoreo de Programas Educativos de Bilingüismo"
   - Haz que sea **público**

2. **Subir el código a GitHub**
   ```bash
   cd "d:\Proyectos Jc Code\Archivos para BD rionegro\Observatorio"
   
   git init
   git add .
   git commit -m "Initial commit: Observatorio Bilinguismo"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/observatorio-bilinguismo.git
   git push -u origin main
   ```

### Paso 2: Configurar la base de datos en la nube

Para Streamlit Cloud, necesitas una base de datos MySQL en la nube. Opciones:

#### Opción A: AWS RDS (Recomendado)
1. Ve a [aws.amazon.com/rds](https://aws.amazon.com/rds)
2. Crea una instancia MySQL 8.0
3. Configura seguridad para permitir conexiones remotas
4. Anota: `host`, `puerto`, `usuario`, `contraseña`, `nombre BD`

#### Opción B: Clever Cloud
1. Ve a [clever-cloud.com](https://clever-cloud.com)
2. Crea una aplicación MySQL
3. Obtén la cadena de conexión

#### Opción C: Digital Ocean
1. Ve a [digitalocean.com](https://digitalocean.com)
2. Crea una base de datos MySQL
3. Obtén las credenciales de conexión

### Paso 3: Preparar secrets en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Haz clic en "New app"
3. Conecta tu repositorio de GitHub
4. Una vez creada la app, ve a "App settings" → "Secrets"
5. Agrega los siguientes secrets:

```toml
DB_USER = "tu_usuario_mysql"
DB_PASS = "tu_contraseña_mysql"
DB_HOST = "tu_host_rds.amazonaws.com"
DB_PORT = "3306"
DB_NAME = "observatorio_bilinguismo"
```

**IMPORTANTE:** 
- Los secrets en Streamlit Cloud son privados y seguros
- Nunca incluyas credenciales en el código

### Paso 4: Preparar la base de datos en la nube

1. **Conectar a la base de datos remota** usando MySQL Workbench o similar
2. **Ejecutar el script de creación de tablas:**
   ```
   Ejecuta: Base_datos/crear_tablas.py (adaptado a la BD remota)
   ```
3. **Importar datos iniciales:**
   ```
   Ejecuta: Queries/CSV_GENERAL.py (adaptado a la BD remota)
   ```

### Paso 5: Desplegar en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Haz clic en "New app"
3. Selecciona tu repositorio, rama `main` y archivo `Dashboards/main_dashboard.py`
4. Haz clic en "Deploy"

Espera 2-3 minutos mientras Streamlit construye la aplicación.

### Paso 6: Verificar el despliegue

Tu app estará disponible en:
```
https://observatorio-bilinguismo.streamlit.app/
```

## 📁 Estructura de archivos para Streamlit Cloud

```
observatorio-bilinguismo/
├── .streamlit/
│   └── config.toml           # Configuración de Streamlit
├── pages/
│   ├── 1_📊_Estudiantes_Sabados.py
│   ├── 2_👥_Sexo_Grado_Sabados.py
│   └── ...
├── Base_datos/
│   ├── conexion.py
│   ├── crear_tablas.py
│   ├── models.py
│   └── __pycache__/
├── Dashboards/
│   └── main_dashboard.py     # Página principal
├── Queries/
│   ├── CSV_GENERAL.py
│   └── CSV_GENERAL_INTENSIFICACION.py
├── .gitignore
├── requirements.txt
├── logger_config.py
└── README.md
```

## 🔧 Adaptaciones necesarias

### 1. Archivo: `Base_datos/conexion.py`
Actualiza la conexión para usar variables de entorno:

```python
import os
from sqlalchemy import create_engine

def get_engine():
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', '123456')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3308')
    db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')
    
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)

engine = get_engine()
```

### 2. Archivo: `logger_config.py`
Asegúrate de que funcione en la nube:

```python
import logging
import os
from datetime import datetime

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Solo crear handler si no existen
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
```

## 🔐 Seguridad

- ✅ Nunca incluyas contraseñas en GitHub
- ✅ Usa secretos de Streamlit Cloud para credenciales
- ✅ Configura firewall en la BD para solo permitir conexiones desde Streamlit
- ✅ Usa HTTPS (automático en Streamlit Cloud)
- ✅ Limita permisos de base de datos

## 📊 Características de la app desplegada

- 🏠 **Página de inicio** con métricas y descripción
- 📈 **Múltiples dashboards** (Sábados, Docentes, Intensificación)
- 📥 **Descargas** de datos en ZIP y CSV
- 🎨 **Interfaz moderna** con Streamlit
- 🔄 **Caché** para mejor rendimiento

## 🆘 Troubleshooting

### Error: "No se pudo conectar a la base de datos"
- Verifica que los secrets estén correctamente configurados
- Comprueba que el firewall permite conexiones desde Streamlit Cloud
- Verifica las credenciales de la BD

### Error: "Module not found"
- Asegúrate de que todos los módulos estén en `requirements.txt`
- Ejecuta: `pip install -r requirements.txt` localmente para verificar

### La app es lenta
- Usa `@st.cache_data` para cachear datos
- Limita el número de registros mostrados
- Optimiza las queries SQL

## 📝 Notas importantes

1. **Variables de entorno en local**: Crea un archivo `.env` local (NO subas a GitHub):
   ```
   DB_USER=root
   DB_PASS=tu_contraseña
   DB_HOST=localhost
   DB_PORT=3308
   DB_NAME=observatorio_bilinguismo
   ```

2. **Para desarrollo local**:
   ```bash
   streamlit run Dashboards/main_dashboard.py
   ```

3. **Para sincronizar con el servidor**: Solo necesitas hacer `git push` y Streamlit Cloud se actualiza automáticamente.

## 🎯 Próximos pasos

- [ ] Configurar BD en la nube (AWS RDS, Clever Cloud, etc.)
- [ ] Obtener credenciales de BD
- [ ] Subir código a GitHub
- [ ] Crear app en Streamlit Cloud
- [ ] Configurar secrets
- [ ] Importar datos iniciales
- [ ] Verificar despliegue
- [ ] Compartir URL con usuarios

---

¿Necesitas ayuda? Consulta la [documentación de Streamlit Cloud](https://docs.streamlit.io/streamlit-community-cloud/get-started)
