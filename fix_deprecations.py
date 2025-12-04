#!/usr/bin/env python3
"""
Script para corregir deprecaciones y errores en todos los archivos de pages/
- use_container_width=True -> width='stretch'
- use_container_width=False -> width='content'
- DataFrame.applymap() -> DataFrame.map()
- Remover imports inutilizados
"""

import os
import re
from pathlib import Path

# Directorio de páginas
pages_dir = Path("pages")

# Archivos a procesar
files_to_process = list(pages_dir.glob("*.py"))

print(f"🔍 Analizando {len(files_to_process)} archivos...")
print()

# Patrones de corrección
corrections = {
    # use_container_width -> width
    r'use_container_width\s*=\s*True': "width='stretch'",
    r'use_container_width\s*=\s*False': "width='content'",
    
    # applymap -> map
    r'\.applymap\(': '.map(',
}

# Imports inutilizados a remover
unused_imports = [
    r'^import\s+traceback\s*$',
    r'^from\s+dashboard_config\s+import\s+.*get_current_page_category.*$',
]

stats = {
    'files_processed': 0,
    'use_container_width_replaced': 0,
    'applymap_replaced': 0,
    'imports_removed': 0,
    'files_with_changes': []
}

for file_path in sorted(files_to_process):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        original_content = content
    
    file_changed = False
    
    # Aplicar correcciones de patterns
    for pattern, replacement in corrections.items():
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            if 'use_container_width' in pattern:
                count = len(re.findall(pattern, content))
                stats['use_container_width_replaced'] += count
            elif 'applymap' in pattern:
                count = len(re.findall(pattern, content))
                stats['applymap_replaced'] += count
            content = new_content
            file_changed = True
    
    # Remover imports inutilizados
    lines = content.split('\n')
    new_lines = []
    imports_removed_this_file = 0
    
    for i, line in enumerate(lines):
        # Remover traceback si está importado pero no se usa
        if 'import traceback' in line and 'traceback' not in content.replace(line, ''):
            imports_removed_this_file += 1
            file_changed = True
            continue
        
        # Remover get_current_page_category si está importado pero no se usa
        if 'get_current_page_category' in line and 'get_current_page_category' not in content.replace(line, ''):
            # Limpiar la línea de importación
            if 'from dashboard_config import' in line:
                new_line = line.replace(', get_current_page_category', '')
                new_line = new_line.replace('get_current_page_category, ', '')
                new_line = new_line.replace('get_current_page_category', '')
                if new_line.strip() != 'from dashboard_config import':
                    new_lines.append(new_line)
                    imports_removed_this_file += 1
                    file_changed = True
                    continue
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    stats['imports_removed'] += imports_removed_this_file
    
    # Guardar cambios si hubo modificaciones
    if file_changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        stats['files_with_changes'].append(file_path.name)
        stats['files_processed'] += 1

print("=" * 70)
print("RESUMEN DE CORRECCIONES")
print("=" * 70)
print(f"✅ Archivos procesados: {stats['files_processed']}")
print(f"🔄 use_container_width reemplazados: {stats['use_container_width_replaced']}")
print(f"🔄 applymap reemplazados por map: {stats['applymap_replaced']}")
print(f"🗑️  Imports inutilizados removidos: {stats['imports_removed']}")
print()
print("📝 Archivos modificados:")
for fname in sorted(stats['files_with_changes']):
    print(f"   • {fname}")
print()
print("✅ Correcciones completadas exitosamente")
