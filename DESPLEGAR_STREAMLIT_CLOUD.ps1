# Script para desplegar Observatorio Bilinguismo en Streamlit Cloud
# Ejecución en PowerShell en Windows

Write-Host "🚀 DESPLIEGUE EN STREAMLIT CLOUD - GUÍA RÁPIDA" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Git
Write-Host "✅ Paso 1: Verificar Git" -ForegroundColor Green
$gitVersion = & git --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   $gitVersion" -ForegroundColor Green
} else {
    Write-Host "   ❌ Git no está instalado. Descárgalo desde: https://git-scm.com/" -ForegroundColor Red
    exit 1
}

# Cambiar a directorio del proyecto
$projectDir = Get-Location
Write-Host ""
Write-Host "✅ Paso 2: Ubicación del proyecto" -ForegroundColor Green
Write-Host "   📁 $projectDir" -ForegroundColor Green

# Inicializar Git si no existe
Write-Host ""
Write-Host "✅ Paso 3: Inicializar repositorio Git" -ForegroundColor Green
if (-not (Test-Path ".git")) {
    git init
    git config user.email "desarrollo@observatorio.local"
    git config user.name "Observatorio"
    Write-Host "   ✅ Repositorio inicializado" -ForegroundColor Green
} else {
    Write-Host "   ✅ Repositorio ya existe" -ForegroundColor Green
}

# Verificar requirements.txt
Write-Host ""
Write-Host "✅ Paso 4: Verificar requirements.txt" -ForegroundColor Green
if (Test-Path "requirements.txt") {
    $packageCount = (Get-Content "requirements.txt" | Where-Object { $_ -and -not $_.StartsWith("#") }).Count
    Write-Host "   ✅ Encontrado ($packageCount paquetes)" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  requirements.txt no encontrado" -ForegroundColor Yellow
}

# Ver estado Git
Write-Host ""
Write-Host "✅ Paso 5: Estado del repositorio" -ForegroundColor Green
$status = & git status --short 2>&1
if ($status) {
    $changeCount = ($status | Measure-Object -Line).Lines
    Write-Host "   📝 $changeCount cambios detectados" -ForegroundColor Yellow
    Write-Host ""
    Write-Host $status -ForegroundColor Gray
} else {
    Write-Host "   ✅ Sin cambios" -ForegroundColor Green
}

# Mostrar instrucciones
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "📋 INSTRUCCIONES PARA DESPLEGAR EN STREAMLIT CLOUD" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1️⃣  SUBIR CÓDIGO A GITHUB:" -ForegroundColor Yellow
Write-Host "    # Agregar cambios" -ForegroundColor Gray
Write-Host "    git add ." -ForegroundColor White
Write-Host ""
Write-Host "    # Hacer commit" -ForegroundColor Gray
Write-Host "    git commit -m `"Preparar para Streamlit Cloud`"" -ForegroundColor White
Write-Host ""
Write-Host "    # Crear rama main (si no existe)" -ForegroundColor Gray
Write-Host "    git branch -M main" -ForegroundColor White
Write-Host ""
Write-Host "    # Agregar remoto de GitHub (copia la URL de tu repo)" -ForegroundColor Gray
Write-Host "    git remote add origin https://github.com/TU_USUARIO/observatorio-bilinguismo.git" -ForegroundColor White
Write-Host ""
Write-Host "    # Empujar a GitHub" -ForegroundColor Gray
Write-Host "    git push -u origin main" -ForegroundColor White
Write-Host ""

Write-Host "2️⃣  PREPARAR BASE DE DATOS EN LA NUBE:" -ForegroundColor Yellow
Write-Host "    Opciones:" -ForegroundColor Gray
Write-Host "    • AWS RDS: https://aws.amazon.com/rds/" -ForegroundColor Gray
Write-Host "    • Clever Cloud: https://clever-cloud.com/" -ForegroundColor Gray
Write-Host "    • Digital Ocean: https://digitalocean.com/" -ForegroundColor Gray
Write-Host ""

Write-Host "3️⃣  DESPLEGAR EN STREAMLIT CLOUD:" -ForegroundColor Yellow
Write-Host "    1. Ve a https://share.streamlit.io" -ForegroundColor Gray
Write-Host "    2. Inicia sesión con tu cuenta de GitHub" -ForegroundColor Gray
Write-Host "    3. Haz clic en 'New app'" -ForegroundColor Gray
Write-Host "    4. Selecciona:" -ForegroundColor Gray
Write-Host "       • Repository: observatorio-bilinguismo" -ForegroundColor Gray
Write-Host "       • Branch: main" -ForegroundColor Gray
Write-Host "       • Main file path: Dashboards/main_dashboard.py" -ForegroundColor Gray
Write-Host ""

Write-Host "4️⃣  CONFIGURAR SECRETOS:" -ForegroundColor Yellow
Write-Host "    1. En Streamlit Cloud, ve a 'App settings' → 'Secrets'" -ForegroundColor Gray
Write-Host "    2. Copia y pega lo siguiente (con tus valores):" -ForegroundColor Gray
Write-Host ""
Write-Host "    DB_USER = `"tu_usuario`"" -ForegroundColor White
Write-Host "    DB_PASS = `"tu_contraseña`"" -ForegroundColor White
Write-Host "    DB_HOST = `"tu_host.rds.amazonaws.com`"" -ForegroundColor White
Write-Host "    DB_PORT = `"3306`"" -ForegroundColor White
Write-Host "    DB_NAME = `"observatorio_bilinguismo`"" -ForegroundColor White
Write-Host ""

Write-Host "5️⃣  IMPORTAR DATOS:" -ForegroundColor Yellow
Write-Host "    • Conecta a la BD remota con MySQL Workbench" -ForegroundColor Gray
Write-Host "    • Ejecuta: Base_datos/crear_tablas.py" -ForegroundColor Gray
Write-Host "    • Importa datos: Queries/CSV_GENERAL.py" -ForegroundColor Gray
Write-Host ""

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "🎉 ¡TU APP ESTARÁ EN LÍNEA EN POCOS MINUTOS!" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "URL de la aplicación: https://observatorio-bilinguismo.streamlit.app/" -ForegroundColor Green
Write-Host ""

# Opciones
Write-Host "¿QUÉ DESEAS HACER?" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Agregar cambios (git add .)" -ForegroundColor Gray
Write-Host "2. Ver status de Git" -ForegroundColor Gray
Write-Host "3. Abrir documentación" -ForegroundColor Gray
Write-Host "4. Salir" -ForegroundColor Gray
Write-Host ""

$option = Read-Host "Selecciona una opción (1-4)"

switch ($option) {
    "1" {
        Write-Host ""
        Write-Host "Agregando cambios..." -ForegroundColor Cyan
        git add .
        $message = Read-Host "Mensaje de commit (ej: 'Preparar para Streamlit Cloud')"
        if ([string]::IsNullOrEmpty($message)) {
            $message = "Preparar para Streamlit Cloud"
        }
        git commit -m $message
        Write-Host "✅ Cambios confirmados" -ForegroundColor Green
        Write-Host "Ahora ejecuta: git push -u origin main" -ForegroundColor Yellow
    }
    "2" {
        Write-Host ""
        git status
    }
    "3" {
        Write-Host "Abriendo documentación..." -ForegroundColor Cyan
        Start-Process "DESPLIEGUE_STREAMLIT_CLOUD.md"
    }
    "4" {
        Write-Host "¡Hasta luego!" -ForegroundColor Cyan
    }
    default {
        Write-Host "Opción no válida" -ForegroundColor Red
    }
}
