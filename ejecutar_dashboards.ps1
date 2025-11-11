#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Ejecutor de Dashboards Formación Sábados 2016-2025
.DESCRIPTION
    Script para ejecutar cualquiera de los 5 dashboards de Formación Sábados
    con cobertura completa de datos históricos (2016-2025)
#>

# Definir colores
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Cyan = "Cyan"
$White = "White"

# Header
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor $Cyan
Write-Host "║     DASHBOARDS FORMACIÓN SÁBADOS 2016-2025              ║" -ForegroundColor $Cyan
Write-Host "║     Cobertura: 7,686 estudiantes | 10 años             ║" -ForegroundColor $Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor $Cyan
Write-Host ""

# Cambiar al directorio del proyecto
$projectPath = "d:\Proyectos Jc Code\Archivos para BD rionegro\Observatorio"
Set-Location $projectPath

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "Dashboards")) {
    Write-Host "❌ ERROR: No se encontró la carpeta 'Dashboards'" -ForegroundColor $Red
    Write-Host "   Ubicación esperada: $projectPath" -ForegroundColor $Red
    exit 1
}

Write-Host "📊 DASHBOARDS DISPONIBLES:" -ForegroundColor $Green
Write-Host ""
Write-Host "1. Estudiantes por Nivel MCER y Sexo" -ForegroundColor $White
Write-Host "   📁 estudiantes_niveles_sabados.py" -ForegroundColor $Cyan
Write-Host ""
Write-Host "2. Estudiantes por Grado y Sexo" -ForegroundColor $White
Write-Host "   📁 estudiantes_grado_sexo_sabados.py" -ForegroundColor $Cyan
Write-Host ""
Write-Host "3. Estado de Estudiantes (Aprobación)" -ForegroundColor $White
Write-Host "   📁 Estado_estudiantes_sabados.py" -ForegroundColor $Cyan
Write-Host ""
Write-Host "4. Asistencia por Institución" -ForegroundColor $White
Write-Host "   📁 asistencia_institucion_sabados.py" -ForegroundColor $Cyan
Write-Host ""
Write-Host "5. Instituciones y Sedes Nodales" -ForegroundColor $White
Write-Host "   📁 instituciones_sedes_sabados.py" -ForegroundColor $Cyan
Write-Host ""
Write-Host "0. Salir" -ForegroundColor $White
Write-Host ""

# Pedir selección
$selection = Read-Host "Selecciona el número del dashboard (0-5)"

switch ($selection) {
    "1" {
        Write-Host ""
        Write-Host "🚀 Ejecutando: Estudiantes por Nivel MCER y Sexo..." -ForegroundColor $Green
        Write-Host "📈 Cobertura: 2016-2025 | 7,686 estudiantes" -ForegroundColor $Green
        Write-Host ""
        & streamlit run Dashboards/estudiantes_niveles_sabados.py
    }
    "2" {
        Write-Host ""
        Write-Host "🚀 Ejecutando: Estudiantes por Grado y Sexo..." -ForegroundColor $Green
        Write-Host "📈 Cobertura: 2016-2025 | 7,686 estudiantes" -ForegroundColor $Green
        Write-Host ""
        & streamlit run Dashboards/estudiantes_grado_sexo_sabados.py
    }
    "3" {
        Write-Host ""
        Write-Host "🚀 Ejecutando: Estado de Estudiantes (Aprobación)..." -ForegroundColor $Green
        Write-Host "📈 Cobertura: 2016-2025 | 7,686 estudiantes" -ForegroundColor $Green
        Write-Host ""
        & streamlit run Dashboards/Estado_estudiantes_sabados.py
    }
    "4" {
        Write-Host ""
        Write-Host "🚀 Ejecutando: Asistencia por Institución..." -ForegroundColor $Green
        Write-Host "📈 Cobertura: 2016-2025 | 7,686 estudiantes" -ForegroundColor $Green
        Write-Host ""
        & streamlit run Dashboards/asistencia_institucion_sabados.py
    }
    "5" {
        Write-Host ""
        Write-Host "🚀 Ejecutando: Instituciones y Sedes Nodales..." -ForegroundColor $Green
        Write-Host "📈 Cobertura: 2016-2025 | 7,686 estudiantes" -ForegroundColor $Green
        Write-Host ""
        & streamlit run Dashboards/instituciones_sedes_sabados.py
    }
    "0" {
        Write-Host ""
        Write-Host "👋 Saliendo..." -ForegroundColor $Yellow
        exit 0
    }
    default {
        Write-Host ""
        Write-Host "❌ Opción inválida. Por favor, selecciona 0-5." -ForegroundColor $Red
        exit 1
    }
}
