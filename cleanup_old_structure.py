#!/usr/bin/env python3
"""
Script de Limpieza Opcional
Elimina carpetas antiguas después de verificar que todo funciona

⚠️ USAR SOLO DESPUÉS DE VERIFICAR QUE EL PROYECTO FUNCIONA CORRECTAMENTE
"""

import os
import shutil
from pathlib import Path

def confirm_deletion(path):
    """Solicita confirmación antes de eliminar"""
    print(f"\n⚠️  ¿Eliminar: {path}?")
    response = input("   (s/n): ").lower().strip()
    return response == 's'

def cleanup_old_structure():
    """Elimina las carpetas antiguas"""
    
    project_root = Path(__file__).parent
    
    # Carpetas y archivos que pueden ser eliminados
    old_items = [
        'Base_datos',           # → src/database/
        'Queries',              # → data/imports/
        'CSVs',                 # → data/csv/
        'Dashboards',           # → dashboards_archive/
        'logger_config.py',     # → src/config/logger_config.py
    ]
    
    print("=" * 70)
    print("🧹 SCRIPT DE LIMPIEZA - ESTRUCTURA ANTIGUA")
    print("=" * 70)
    print("\n⚠️  IMPORTANTE: Ejecutar SOLO después de verificar que:")
    print("   ✓ El proyecto funciona correctamente")
    print("   ✓ Los dashboards cargan sin errores")
    print("   ✓ Se ha hecho commit en git")
    print()
    
    input("Presiona Enter para continuar...")
    
    deleted_count = 0
    
    for item in old_items:
        item_path = project_root / item
        
        if item_path.exists():
            print(f"\n📁 {item}")
            
            if not confirm_deletion(item):
                print("   ✗ Omitido")
                continue
            
            try:
                if item_path.is_file():
                    os.remove(item_path)
                    print(f"   ✓ Archivo eliminado: {item}")
                else:
                    shutil.rmtree(item_path)
                    print(f"   ✓ Carpeta eliminada: {item}")
                deleted_count += 1
            except Exception as e:
                print(f"   ✗ Error al eliminar: {e}")
        else:
            print(f"   - No existe: {item}")
    
    print("\n" + "=" * 70)
    print(f"✅ Limpieza completada: {deleted_count} elementos eliminados")
    print("=" * 70)
    
    print(f"\n📁 Estructura final:")
    print("""
    src/             ← Código fuente (nuevo)
    data/            ← Datos y scripts (nuevo)
    pages/           ← Dashboards activos
    dashboards_archive/  ← Respaldo de versiones antiguas
    assets/          ← Recursos
    logs/            ← Registros
    """)
    
    print("\n✨ Proyecto optimizado y limpio")

if __name__ == '__main__':
    cleanup_old_structure()
