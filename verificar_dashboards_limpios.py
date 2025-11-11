#!/usr/bin/env python3
"""
Script de verificación para confirmar que los dashboards de nivel están limpios
y listos para producción sin referencias a filtros removidos.
"""

import os
import re

def check_file_for_undefined_vars(filepath, undefined_vars):
    """
    Verifica si un archivo contiene referencias a variables indefinidas.
    """
    if not os.path.exists(filepath):
        print(f"❌ Archivo no encontrado: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    for var in undefined_vars:
        # Buscar referencias a la variable (excluyendo comentarios)
        pattern = rf'\b{var}\b'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            # Calcular número de línea
            line_num = content[:match.start()].count('\n') + 1
            line_content = content.split('\n')[line_num - 1]
            
            # Verificar que no sea un comentario
            if not line_content.strip().startswith('#'):
                issues.append({
                    'variable': var,
                    'line': line_num,
                    'content': line_content.strip()
                })
    
    return len(issues) == 0, issues

def main():
    dashboards_dir = r"d:\Proyectos Jc Code\Archivos para BD rionegro\Observatorio\Dashboards"
    
    print("=" * 80)
    print("🔍 VERIFICACIÓN DE DASHBOARDS - Búsqueda de referencias indefinidas")
    print("=" * 80)
    print()
    
    # Verificaciones específicas
    checks = {
        os.path.join(dashboards_dir, "estudiantes_niveles_sabados.py"): [],  # Debe estar limpio
        os.path.join(dashboards_dir, "estudiantes_niveles_intensificacion.py"): ['selected_tipo', 'selected_institucion'],
    }
    
    all_passed = True
    
    for filepath, undefined_vars in checks.items():
        filename = os.path.basename(filepath)
        print(f"\n📄 Verificando: {filename}")
        print("-" * 80)
        
        is_clean, issues = check_file_for_undefined_vars(filepath, undefined_vars)
        
        if not os.path.exists(filepath):
            print(f"  ❌ Archivo no encontrado")
            all_passed = False
            continue
        
        if is_clean:
            print(f"  ✅ Sin referencias a variables indefinidas")
        else:
            print(f"  ❌ Se encontraron {len(issues)} referencias problemáticas:")
            for issue in issues:
                print(f"     - Línea {issue['line']}: {issue['variable']}")
                print(f"       Contenido: {issue['content'][:70]}...")
            all_passed = False
    
    print()
    print("=" * 80)
    
    # Verificación adicional: Verificar que los selectboxes de año existen
    print("\n✅ VERIFICACIÓN DE SELECTORES DE AÑO")
    print("-" * 80)
    
    for filepath in checks.keys():
        filename = os.path.basename(filepath)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "selected_year = st.sidebar.selectbox" in content and "selected_year" in content:
                print(f"  ✅ {filename}: Selector de año presente")
            else:
                print(f"  ❌ {filename}: Selector de año FALTANTE")
                all_passed = False
    
    print()
    print("=" * 80)
    if all_passed:
        print("✅ TODAS LAS VERIFICACIONES PASARON - Dashboards listos")
    else:
        print("❌ ALGUNAS VERIFICACIONES FALLARON - Revisar dashboards")
    print("=" * 80)

if __name__ == "__main__":
    main()
