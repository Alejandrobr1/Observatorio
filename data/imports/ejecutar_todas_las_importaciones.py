"""
Script principal para ejecutar todos los scripts de importación de datos en un orden específico.
Este script actúa como un orquestador para poblar o actualizar la base de datos completa.
"""

import os
import sys
import subprocess
import time

def ejecutar_importaciones():
    """
    Encuentra y ejecuta todos los scripts de importación en el directorio actual.
    """
    # El directorio donde se encuentra este script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Definir el orden de ejecución de los scripts.
    # Esto es útil si hay dependencias, y asegura un proceso predecible.
    scripts_a_ejecutar = [
      
        "insertar_datos_docentes.py",
        "insertar_datos_estudiantes_2016_2019.py",
        "insertar_datos_escuela_nueva.py",
        "insertar_datos_colombo.py",
        "insertar_datos_2021_2025.py",
        "insertar_grados_2021_2025.py",
        "insertar_instituciones_2021_2025.py",
        "insertar_datos_intensificacion.py",
        "insertar_intensificacion_grados.py",
        "insertar_intensificacion_frances.py",
        "insertar_intensificacion_frances_grados.py",
        "insertar_intensificacion_horas_frances.py",
    ]

    print("="*80)
    print("🚀 INICIANDO PROCESO DE IMPORTACIÓN DE TODOS LOS DATOS")
    print("="*80)
    
    start_time = time.time()
    scripts_exitosos = 0
    scripts_fallidos = 0

    for script_name in scripts_a_ejecutar:
        script_path = os.path.join(script_dir, script_name)
        
        if not os.path.exists(script_path):
            print(f"\n🟡 ADVERTENCIA: El script '{script_name}' no fue encontrado. Omitiendo.")
            continue

        print(f"\n▶️ Ejecutando script: {script_name}")
        print("-" * (20 + len(script_name)))
        
        # Usamos sys.executable para asegurarnos de usar el mismo intérprete de Python
        # que está ejecutando este script.
        # El argumento '-m' es necesario para que las importaciones relativas dentro
        # de los scripts hijos funcionen correctamente.
        module_path = f"data.imports.{script_name.replace('.py', '')}"
        result = subprocess.run([sys.executable, "-m", module_path], capture_output=True, text=True, encoding='utf-8')
        
        print(result.stdout) # Imprimir la salida estándar del script hijo
        
        if result.returncode == 0:
            print(f"✅ Script '{script_name}' finalizado con éxito.")
            scripts_exitosos += 1
        else:
            print(f"❌ ERROR: El script '{script_name}' falló.")
            print("Salida de error:")
            print(result.stderr) # Imprimir la salida de error
            scripts_fallidos += 1

    end_time = time.time()
    duracion_total = end_time - start_time

    print("\n" + "="*80)
    print("🏁 PROCESO DE IMPORTACIÓN FINALIZADO")
    print(f"   - Duración total: {duracion_total:.2f} segundos")
    print(f"   - Scripts exitosos: {scripts_exitosos}")
    print(f"   - Scripts fallidos: {scripts_fallidos}")
    print("="*80)

if __name__ == "__main__":
    ejecutar_importaciones()