# Script de migración BD Local (Docker) a Clever Cloud
# Ejecución en PowerShell en Windows

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        🚀 MIGRACIÓN BD DOCKER → CLEVER CLOUD 🚀               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Credenciales Clever Cloud
$cleverUser = "uuoxxbrx6knnwzc6"
$cleverPass = "5fIPyo9KIlulljR0yTdB"
$cleverHost = "bdldn022szfj4gyd9fqn-mysql.services.clever-cloud.com"
$cleverPort = "3306"
$cleverDB = "bdldn022szfj4gyd9fqn"

# Credenciales Docker Local
$dockerUser = "root"
$dockerPass = "123456"
$dockerHost = "localhost"
$dockerPort = "3308"
$dockerDB = "observatorio_bilinguismo"

# Mostrar información
Write-Host "📊 CONFIGURACIÓN" -ForegroundColor Green
Write-Host "════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "🐳 DOCKER (Local):" -ForegroundColor Blue
Write-Host "   Host: $dockerHost" -ForegroundColor White
Write-Host "   Puerto: $dockerPort" -ForegroundColor White
Write-Host "   BD: $dockerDB" -ForegroundColor White
Write-Host ""
Write-Host "☁️  CLEVER CLOUD (Remoto):" -ForegroundColor Blue
Write-Host "   Host: $cleverHost" -ForegroundColor White
Write-Host "   Puerto: $cleverPort" -ForegroundColor White
Write-Host "   BD: $cleverDB" -ForegroundColor White
Write-Host ""

# Paso 1: Verificar Docker
Write-Host "✅ PASO 1: Verificar Docker" -ForegroundColor Green
Write-Host "════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

$dockerCheck = & docker ps 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Docker está corriendo" -ForegroundColor Green
    Write-Host ""
    Write-Host "   Contenedores activos:" -ForegroundColor Gray
    docker ps | Select-Object -First 5 | Format-Table
} else {
    Write-Host "   ❌ Docker no está corriendo o no está instalado" -ForegroundColor Red
    Write-Host "   Por favor, inicia Docker e intenta de nuevo" -ForegroundColor Red
    exit 1
}

# Paso 2: Verificar MySQL en Docker
Write-Host ""
Write-Host "✅ PASO 2: Verificar MySQL en Docker" -ForegroundColor Green
Write-Host "════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

$mysqlContainer = & docker ps | Select-String -Pattern "mysql"
if ($mysqlContainer) {
    Write-Host "   ✅ MySQL detectado en Docker" -ForegroundColor Green
    $containerID = ($mysqlContainer -split ' ')[0]
    Write-Host "   Container ID: $containerID" -ForegroundColor Gray
} else {
    Write-Host "   ⚠️  MySQL no detectado en Docker" -ForegroundColor Yellow
    Write-Host "   Asegúrate de que el contenedor esté corriendo" -ForegroundColor Yellow
}

# Paso 3: Seleccionar método
Write-Host ""
Write-Host "✅ PASO 3: Seleccionar método de migración" -ForegroundColor Green
Write-Host "════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Métodos disponibles:" -ForegroundColor Gray
Write-Host "  1️⃣  Volcado SQL + Restauración (Recomendado)" -ForegroundColor White
Write-Host "  2️⃣  Sincronización por Python" -ForegroundColor White
Write-Host "  3️⃣  Solo crear estructura (sin datos)" -ForegroundColor White
Write-Host ""

$option = Read-Host "Selecciona una opción (1-3)"

switch ($option) {
    "1" {
        # Método 1: mysqldump
        Write-Host ""
        Write-Host "✅ PASO 4: Migración con mysqldump" -ForegroundColor Green
        Write-Host "════════════════════════════════════════════" -ForegroundColor Green
        Write-Host ""
        
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $dumpFile = "bd_backup_$timestamp.sql"
        
        Write-Host "   📁 Archivo de volcado: $dumpFile" -ForegroundColor Gray
        Write-Host ""
        
        # Obtener ID del contenedor
        $containerID = & docker ps | Select-String -Pattern "mysql" | ForEach-Object { ($_ -split ' ')[0] }
        
        if ($containerID) {
            Write-Host "   ⏳ Exportando BD desde Docker..." -ForegroundColor Yellow
            
            $exportCmd = "docker exec $containerID mysqldump -u $dockerUser -p$dockerPass $dockerDB"
            $dumpContent = & $exportCmd 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                $dumpContent | Out-File -FilePath $dumpFile -Encoding UTF8
                $fileSize = (Get-Item $dumpFile).Length / 1MB
                Write-Host "   ✅ Volcado completado: $([Math]::Round($fileSize, 2)) MB" -ForegroundColor Green
                
                Write-Host ""
                Write-Host "   ⏳ Importando en Clever Cloud..." -ForegroundColor Yellow
                
                # Importar a Clever Cloud
                $importCmd = "mysql -h $cleverHost -u $cleverUser -p$cleverPass -P $cleverPort $cleverDB"
                $content = Get-Content $dumpFile -Raw
                $content | & $importCmd 2>&1
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "   ✅ Importación completada en Clever Cloud" -ForegroundColor Green
                    
                    Write-Host ""
                    Write-Host "✅ MIGRACIÓN COMPLETADA" -ForegroundColor Green
                    Write-Host "════════════════════════════════════════════" -ForegroundColor Green
                    Write-Host ""
                    Write-Host "   📊 Datos migrados:" -ForegroundColor Gray
                    Write-Host "      • Base de datos: $cleverDB" -ForegroundColor White
                    Write-Host "      • Host: $cleverHost" -ForegroundColor White
                    Write-Host "      • Tamaño: $([Math]::Round($fileSize, 2)) MB" -ForegroundColor White
                } else {
                    Write-Host "   ❌ Error al importar en Clever Cloud" -ForegroundColor Red
                }
            } else {
                Write-Host "   ❌ Error al exportar desde Docker" -ForegroundColor Red
            }
            
            # Preguntar si guardar el archivo
            Write-Host ""
            $keepFile = Read-Host "¿Guardar archivo de volcado? (s/n)"
            
            if ($keepFile -eq 'n') {
                Remove-Item $dumpFile
                Write-Host "   ✅ Archivo eliminado" -ForegroundColor Green
            } else {
                $fullPath = (Get-Item $dumpFile).FullName
                Write-Host "   ✅ Archivo guardado en: $fullPath" -ForegroundColor Green
            }
        } else {
            Write-Host "   ❌ No se encontró contenedor MySQL" -ForegroundColor Red
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "✅ PASO 4: Migración con Python" -ForegroundColor Green
        Write-Host "════════════════════════════════════════════" -ForegroundColor Green
        Write-Host ""
        Write-Host "   ⏳ Ejecutando script Python..." -ForegroundColor Yellow
        
        # Ejecutar el script Python
        python migrar_a_clever_cloud.py
    }
    
    "3" {
        Write-Host ""
        Write-Host "✅ PASO 4: Crear solo estructura" -ForegroundColor Green
        Write-Host "════════════════════════════════════════════" -ForegroundColor Green
        Write-Host ""
        Write-Host "   ⏳ Creando tablas en Clever Cloud..." -ForegroundColor Yellow
        
        $createCmd = "mysql -h $cleverHost -u $cleverUser -p$cleverPass -P $cleverPort $cleverDB"
        
        # Script SQL para crear tablas
        $sqlScript = @"
CREATE TABLE IF NOT EXISTS Tipo_documentos (
    ID INT PRIMARY KEY AUTO_INCREMENT,
    TIPO_DOC VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS Ciudades (
    ID INT PRIMARY KEY AUTO_INCREMENT,
    NOMBRE_CIUDAD VARCHAR(100) NOT NULL
);

-- Agrega más tablas según sea necesario
"@
        
        $sqlScript | & $createCmd 2>&1
        
        Write-Host "   ✅ Estructura creada en Clever Cloud" -ForegroundColor Green
    }
    
    default {
        Write-Host "   ❌ Opción no válida" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "════════════════════════════════════════════" -ForegroundColor Green
Write-Host "🎉 Proceso finalizado" -ForegroundColor Green
Write-Host "════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
