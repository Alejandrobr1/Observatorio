#!/usr/bin/env python3
"""
Script de migración para actualizar imports en archivos
de la nueva estructura src/

Uso: python migrate_imports.py
"""

import os
import re
from pathlib import Path

def update_file_imports(file_path):
    """Actualiza los imports en un archivo"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Reemplazos de imports
    replacements = [
        (r'from Base_datos\.conexion import', 'from src.database.conexion import'),
        (r'from Base_datos\.models import', 'from src.database.models import'),
        (r'from logger_config import', 'from src.config.logger_config import'),
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    # Actualizar sys.path si es necesario
    if 'sys.path.append' in content and '../' in content:
        # Solo actualizar si necesita ser relativo a src
        pass
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def migrate_structure():
    """Migra la estructura del proyecto"""
    project_root = Path(__file__).parent
    
    # Directorio src (actualizar imports si existen)
    src_files = list((project_root / 'data' / 'imports').glob('*.py'))
    src_files.extend(list((project_root / 'src').rglob('*.py')))
    
    updated_count = 0
    for file_path in src_files:
        if update_file_imports(str(file_path)):
            print(f"✓ Actualizado: {file_path.relative_to(project_root)}")
            updated_count += 1
    
    print(f"\n✅ Migración completada: {updated_count} archivos actualizados")
    
    # Mostrar estructura
    print("\n📁 Estructura del proyecto organizada:")
    print("""
    src/
    ├── config/
    │   ├── __init__.py
    │   └── logger_config.py
    ├── database/
    │   ├── __init__.py
    │   ├── conexion.py
    │   ├── models.py
    │   ├── crear_tablas.py
    │   └── crear_tabla_especifica.py
    └── utils/
        └── __init__.py
    
    data/
    ├── csv/
    ├── imports/
    ├── exports/
    └── verify/
    
    pages/              (activos)
    dashboards_archive/ (respaldo)
    """)

if __name__ == '__main__':
    migrate_structure()
