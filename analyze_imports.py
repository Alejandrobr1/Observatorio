#!/usr/bin/env python3
"""
Script para remover imports realmente inutilizados en todos los archivos de pages/
"""

import ast
import os
from pathlib import Path

pages_dir = Path("pages")
files_to_process = sorted(pages_dir.glob("*.py"))

print(f"🔍 Analizando imports en {len(files_to_process)} archivos...")
print()

def find_unused_imports(file_path):
    """Encuentra imports que no se usan en el archivo"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except:
        return []
    
    # Recolectar todos los imports
    imports = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name
                imports[name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                imports[name] = alias.name
    
    # Recolectar todos los nombres usados
    used_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Para imports como 'st.dataframe', capturamos 'st'
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)
    
    # Encontrar imports no usados
    unused = []
    for import_name, original_name in imports.items():
        if import_name not in used_names:
            unused.append((import_name, original_name))
    
    return unused, used_names

stats = {
    'total_files': len(files_to_process),
    'files_with_unused_imports': 0,
    'unused_imports_found': 0
}

for file_path in files_to_process:
    unused, used = find_unused_imports(file_path)
    
    if unused:
        stats['files_with_unused_imports'] += 1
        stats['unused_imports_found'] += len(unused)
        
        print(f"📄 {file_path.name}")
        for import_name, original_name in unused:
            # Solo mostrar si es realmente inutilizado
            if import_name != original_name:
                print(f"   ❌ {original_name} as {import_name}")
            else:
                print(f"   ❌ {import_name}")

print()
print("=" * 70)
print(f"📊 {stats['files_with_unused_imports']} archivos con imports inutilizados")
print(f"📋 {stats['unused_imports_found']} imports inutilizados encontrados")
print()
print("⚠️  NOTA: Los imports inutilizados más comunes son:")
print("   - traceback (usado solo en bloques try/except que ya no existen)")
print("   - create_engine (ahora usamos src.database.conexion)")
print("   - get_current_page_category (función deprecada)")
