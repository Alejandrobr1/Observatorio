# 🚀 Guía de Migración: BD Local (Docker) → Clever Cloud

## 📊 Información de Conexión

### Clever Cloud (Remoto)
```
Host:     bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com
Port:     3306
Database: bdldn022szfj4gyd9fqn
User:     uuoxxbrx6knnwzc6
Password: 5fIPyo9KIlulljR0yTdB
```

### Docker Local
```
Host:     localhost
Port:     3308
Database: observatorio_bilinguismo
User:     root
Password: 123456
```

---

## 🎯 Métodos de Migración

### Opción 1: Volcado SQL (Recomendado) ⭐

Más rápido y preserva exactamente la estructura y datos.

#### Paso 1: Exportar BD desde Docker

**Con PowerShell:**
```powershell
# Obtener ID del contenedor MySQL
docker ps | Select-String mysql

# Exportar a archivo SQL
docker exec [CONTAINER_ID] mysqldump -u root -p123456 observatorio_bilinguismo > bd_backup.sql

# Ejemplo completo:
docker exec $(docker ps | Select-String mysql | ForEach-Object {$_ -split ' ' | Select -First 1}) mysqldump -u root -p123456 observatorio_bilinguismo > bd_backup.sql
```

**Con Bash (Linux/Mac):**
```bash
docker exec $(docker ps | grep mysql | awk '{print $1}') mysqldump -u root -p123456 observatorio_bilinguismo > bd_backup.sql
```

#### Paso 2: Importar a Clever Cloud

**Con PowerShell:**
```powershell
$file = Get-Content bd_backup.sql -Raw
$file | mysql -h bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com -u uuoxxbrx6knnwzc6 -p5fIPyo9KIlulljR0yTdB -P 3306 bdldn022szfj4gyd9fqn
```

**Con CMD/Bash:**
```bash
mysql -h bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com -u uuoxxbrx6knnwzc6 -p5fIPyo9KIlulljR0yTdB -P 3306 bdldn022szfj4gyd9fqn < bd_backup.sql
```

#### Paso 3: Verificar migración

```bash
# Contar tablas en Clever Cloud
mysql -h bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com \
      -u uuoxxbrx6knnwzc6 \
      -p5fIPyo9KIlulljR0yTdB \
      -P 3306 \
      bdldn022szfj4gyd9fqn \
      -e "SHOW TABLES;"
```

---

### Opción 2: Script Python (Automático)

Ejecutar el script que genera y ejecuta los comandos automáticamente.

```powershell
# Ejecutar script interactivo
python migrar_a_clever_cloud.py
```

El script te guiará a través de:
1. Conexión a Docker
2. Conexión a Clever Cloud
3. Sincronización de datos

---

### Opción 3: Usando Docker Compose (Si lo tienes)

Si tu BD está en un servicio de Docker Compose:

```bash
# Desde el directorio con docker-compose.yml
docker-compose exec mysql mysqldump -u root -p123456 observatorio_bilinguismo > bd_backup.sql

# Luego importar a Clever Cloud
mysql -h bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com \
      -u uuoxxbrx6knnwzc6 \
      -p5fIPyo9KIlulljR0yTdB \
      -P 3306 \
      bdldn022szfj4gyd9fqn < bd_backup.sql
```

---

## 🔧 Requisitos Previos

### En tu PC (Windows)

1. **MySQL Client instalado**
   ```powershell
   # Verificar si mysql está disponible
   mysql --version
   ```
   
   Si no está instalado:
   - Descarga MySQL Community: https://dev.mysql.com/downloads/mysql/
   - O instala solo el cliente: https://dev.mysql.com/downloads/workbench/

2. **Docker corriendo**
   ```powershell
   docker ps
   ```

3. **Python (opcional, para script automático)**
   ```bash
   python --version
   pip list | Select-String sqlalchemy
   ```

---

## 📋 Pasos Detallados (Método 1 - Recomendado)

### 1. Verificar Docker

```powershell
# Ver contenedores
docker ps

# Debería mostrar algo como:
# CONTAINER ID   IMAGE          STATUS
# abc123...      mysql:8.0      Up 2 hours
```

### 2. Crear archivo de volcado

```powershell
# Windows PowerShell
$containerId = docker ps | Select-String mysql | ForEach-Object {$_ -split ' ' | Select -First 1}
docker exec $containerId mysqldump -u root -p123456 observatorio_bilinguismo > bd_backup.sql

# Verificar que se creó
Get-Item bd_backup.sql
```

### 3. Verificar archivo

```powershell
# Ver primeras líneas del archivo
Get-Content bd_backup.sql -Head 20

# Ver tamaño
$size = (Get-Item bd_backup.sql).Length / 1MB
Write-Host "Tamaño: $([Math]::Round($size, 2)) MB"
```

### 4. Importar a Clever Cloud

```powershell
# Opción A: Usando mysql command line
Get-Content bd_backup.sql -Raw | mysql `
  -h bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com `
  -u uuoxxbrx6knnwzc6 `
  -p5fIPyo9KIlulljR0yTdB `
  -P 3306 `
  bdldn022szfj4gyd9fqn

# Opción B: Usar archivos (más confiable)
mysql -h bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com `
      -u uuoxxbrx6knnwzc6 `
      -p5fIPyo9KIlulljR0yTdB `
      -P 3306 `
      bdldn022szfj4gyd9fqn < bd_backup.sql
```

### 5. Verificar importación

```bash
mysql -h bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com \
      -u uuoxxbrx6knnwzc6 \
      -p5fIPyo9KIlulljR0yTdB \
      -P 3306 \
      bdldn022szfj4gyd9fqn \
      -e "SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema='bdldn022szfj4gyd9fqn';"
```

---

## 🔍 Verificaciones Post-Migración

### 1. Contar tablas

```bash
mysql -h bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com \
      -u uuoxxbrx6knnwzc6 \
      -p5fIPyo9KIlulljR0yTdB \
      -P 3306 \
      bdldn022szfj4gyd9fqn \
      -e "SHOW TABLES;"
```

### 2. Contar registros por tabla

```bash
mysql -h bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com \
      -u uuoxxbrx6knnwzc6 \
      -p5fIPyo9KIlulljR0yTdB \
      -P 3306 \
      bdldn022szfj4gyd9fqn \
      -e "
SELECT TABLE_NAME, TABLE_ROWS 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'bdldn022szfj4gyd9fqn'
ORDER BY TABLE_ROWS DESC;
      "
```

### 3. Verificar estructura de tabla

```bash
mysql -h bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com \
      -u uuoxxbrx6knnwzc6 \
      -p5fIPyo9KIlulljR0yTdB \
      -P 3306 \
      bdldn022szfj4gyd9fqn \
      -e "DESCRIBE Personas;"
```

---

## 🔄 Actualizar Conexión en el Proyecto

### Opción A: Usar variables de entorno (Recomendado)

1. **Crear archivo `.env`:**
   ```env
   DB_USER=uuoxxbrx6knnwzc6
   DB_PASS=5fIPyo9KIlulljR0yTdB
   DB_HOST=bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com
   DB_PORT=3306
   DB_NAME=bdldn022szfj4gyd9fqn
   ```

2. **Actualizar `Base_datos/conexion.py`:**
   ```python
   import os
   from sqlalchemy import create_engine

   db_user = os.getenv('DB_USER', 'uuoxxbrx6knnwzc6')
   db_pass = os.getenv('DB_PASS', '5fIPyo9KIlulljR0yTdB')
   db_host = os.getenv('DB_HOST', 'bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com')
   db_port = os.getenv('DB_PORT', '3306')
   db_name = os.getenv('DB_NAME', 'bdldn022szfj4gyd9fqn')

   engine = create_engine(
       f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
   )
   ```

### Opción B: Actualizar directamente la URL

```python
# Base_datos/conexion.py
engine = create_engine(
    "mysql+mysqlconnector://uuoxxbrx6knnwzc6:5fIPyo9KIlulljR0yTdB@bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com:3306/bdldn022szfj4gyd9fqn"
)
```

---

## 📥 Actualizar Streamlit Cloud

1. Actualiza `.streamlit/secrets.toml` en Streamlit Cloud:

```toml
DB_USER = "uuoxxbrx6knnwzc6"
DB_PASS = "5fIPyo9KIlulljR0yTdB"
DB_HOST = "bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com"
DB_PORT = "3306"
DB_NAME = "bdldn022szfj4gyd9fqn"
```

2. Haz `git push` para redeploy automático

---

## 🆘 Troubleshooting

### Error: "Can't connect to MySQL server"

```bash
# Verificar conectividad a Clever Cloud
telnet bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com 3306

# O con PowerShell
Test-NetConnection -ComputerName bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com -Port 3306
```

### Error: "Access denied for user"

```bash
# Verificar credenciales
mysql -h bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com \
      -u uuoxxbrx6knnwzc6 \
      -p5fIPyo9KIlulljR0yTdB \
      -P 3306 \
      -e "SELECT USER();"
```

### Error: "Unknown database"

```bash
# Listar bases de datos disponibles
mysql -h bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com \
      -u uuoxxbrx6knnwzc6 \
      -p5fIPyo9KIlulljR0yTdB \
      -P 3306 \
      -e "SHOW DATABASES;"
```

---

## 📊 Comparativa

| Aspecto | Docker Local | Clever Cloud |
|---------|-------------|--------------|
| Host | localhost | bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com |
| Puerto | 3308 | 3306 |
| Usuario | root | uuoxxbrx6knnwzc6 |
| Acceso | Local solo | Desde internet |
| Costo | Gratis | Incluido en Clever Cloud |
| Disponibilidad | Mientras Docker corre | 24/7 |

---

## ✅ Checklist

- [ ] Docker está corriendo
- [ ] MySQL client instalado
- [ ] Archivo de volcado creado (bd_backup.sql)
- [ ] Credenciales Clever Cloud verificadas
- [ ] Importación completada
- [ ] Tablas verificadas en Clever Cloud
- [ ] Registros migrados correctamente
- [ ] Conexión actualizada en el proyecto
- [ ] Secretos actualizados en Streamlit Cloud
- [ ] App redeployada

---

**¿Necesitas ayuda?** Revisa los logs o contacta al soporte de Clever Cloud.
