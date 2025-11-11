#!/bin/bash
# Script para ejecutar los dashboards de Formación Sábados

echo "=================================="
echo "📊 Dashboards Formación Sábados"
echo "=================================="
echo ""
echo "Selecciona un dashboard para ejecutar:"
echo ""
echo "1️⃣  Estudiantes por Nivel MCER y Sexo"
echo "2️⃣  Estudiantes por Grado y Sexo"
echo "3️⃣  Aprobación de Estudiantes"
echo "4️⃣  Asistencia por Institución"
echo "5️⃣  Instituciones y Sedes Nodales"
echo "6️⃣  Ejecutar todos (en puertos diferentes)"
echo "0️⃣  Salir"
echo ""
read -p "Ingresa la opción (0-6): " option

case $option in
    1)
        echo "🚀 Iniciando: Estudiantes por Nivel MCER y Sexo..."
        streamlit run estudiantes_niveles_sabados.py
        ;;
    2)
        echo "🚀 Iniciando: Estudiantes por Grado y Sexo..."
        streamlit run estudiantes_grado_sexo_sabados.py
        ;;
    3)
        echo "🚀 Iniciando: Aprobación de Estudiantes..."
        streamlit run Estado_estudiantes_sabados.py
        ;;
    4)
        echo "🚀 Iniciando: Asistencia por Institución..."
        streamlit run asistencia_institucion_sabados.py
        ;;
    5)
        echo "🚀 Iniciando: Instituciones y Sedes Nodales..."
        streamlit run instituciones_sedes_sabados.py
        ;;
    6)
        echo "🚀 Iniciando todos los dashboards..."
        echo "  • Puerto 8501: Nivel MCER"
        streamlit run estudiantes_niveles_sabados.py --server.port 8501 &
        sleep 2
        echo "  • Puerto 8502: Grado y Sexo"
        streamlit run estudiantes_grado_sexo_sabados.py --server.port 8502 &
        sleep 2
        echo "  • Puerto 8503: Aprobación"
        streamlit run Estado_estudiantes_sabados.py --server.port 8503 &
        sleep 2
        echo "  • Puerto 8504: Asistencia"
        streamlit run asistencia_institucion_sabados.py --server.port 8504 &
        sleep 2
        echo "  • Puerto 8505: Instituciones y Sedes"
        streamlit run instituciones_sedes_sabados.py --server.port 8505 &
        echo ""
        echo "✅ Todos los dashboards iniciados:"
        echo "  1. http://localhost:8501 - Nivel MCER y Sexo"
        echo "  2. http://localhost:8502 - Grado y Sexo"
        echo "  3. http://localhost:8503 - Aprobación"
        echo "  4. http://localhost:8504 - Asistencia"
        echo "  5. http://localhost:8505 - Instituciones y Sedes"
        ;;
    0)
        echo "👋 Adiós!"
        exit 0
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac
