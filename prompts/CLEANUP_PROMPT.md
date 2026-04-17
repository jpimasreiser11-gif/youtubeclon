# PROMPT DE LIMPIEZA — Eliminar todo lo inútil
# Pega esto en Copilot CLI cuando quieras limpiar el proyecto
# Los agentes analizarán cada archivo y eliminarán lo que no sirve

---

Analiza el proyecto VidFlow AI completo y elimina todo lo que no tiene
utilidad real. Sé agresivo con la limpieza pero muy conservador con lo
que es necesario.

## ELIMINA SIN PREGUNTAR

```bash
# Caché de Python
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

# Archivos del sistema operativo
find . -name ".DS_Store" -delete
find . -name "Thumbs.db" -delete
find . -name "desktop.ini" -delete

# Archivos temporales del pipeline
find outputs/ -name "temp_*" -delete 2>/dev/null
find clips/ -name "temp_*" -delete 2>/dev/null
find audios/ -name "temp_*" -delete 2>/dev/null

# Logs de más de 7 días
find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null

# Archivos vacíos (0 bytes) que no son .gitkeep
find . -type f -empty ! -name ".gitkeep" ! -name "*.env" -delete

# Carpetas vacías (excepto las necesarias)
find . -type d -empty ! -name ".git" ! -name "tests" -delete 2>/dev/null
```

## ANALIZA ANTES DE ELIMINAR

Para cada archivo Python en el proyecto, verifica:

```python
# Criterios para marcar como "candidato a eliminar":
# 1. No es importado por ningún otro archivo
# 2. No aparece en ningún AGENT.md o SKILL.md
# 3. No es un archivo de configuración (.env, requirements.txt, etc.)
# 4. No tiene tests asociados
# 5. Tiene menos de 10 líneas y no tiene función obvia

import os, ast, re

def find_unused_files(project_root="."):
    py_files = []
    imports_found = set()
    
    # Recoger todos los archivos Python
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.copilot']]
        for f in files:
            if f.endswith('.py'):
                py_files.append(os.path.join(root, f))
    
    # Recoger todos los imports
    for fp in py_files:
        try:
            content = open(fp).read()
            # Buscar imports directos y from X import Y
            imports = re.findall(r'(?:import|from)\s+([\w.]+)', content)
            imports_found.update(imports)
        except:
            pass
    
    # Identificar archivos que nadie importa
    candidates = []
    for fp in py_files:
        module_name = os.path.basename(fp).replace('.py', '')
        if module_name not in imports_found and module_name not in [
            'pipeline', 'app', 'main', 'setup', 'init_channels',
            'check_apis', 'run_agents', '__init__'
        ]:
            candidates.append(fp)
    
    return candidates
```

Para cada candidato encontrado, genera una lista en `cleanup_report.md`:

```markdown
# Informe de Limpieza — [FECHA]

## Eliminados automáticamente
- [lista de archivos y carpetas eliminados]

## Candidatos a eliminar (requieren revisión)
| Archivo | Tamaño | Último uso | Razón | Acción recomendada |
|---|---|---|---|---|
| pipeline/old_test.py | 2KB | hace 30 días | No se importa | ELIMINAR |
| utils/deprecated_helper.py | 1KB | hace 60 días | Función movida | ELIMINAR |

## NO eliminar (marcados como esenciales)
| Archivo | Por qué es necesario |
|---|---|
| pipeline/pipeline.py | Módulo principal |
```

## REORGANIZA SI ESTÁ DESORDENADO

Si hay archivos en la raíz que deberían estar en subcarpetas:
- Scripts de utilidad → `utils/`
- Scripts de configuración → `scripts/`
- Archivos de datos → `data/`
- Templates de prompts → `prompts/`

## DESPUÉS DE LIMPIAR

Ejecuta y confirma que todo sigue funcionando:
```bash
python scripts/check_apis.py
python -m pytest tests/ -v 2>/dev/null || echo "No tests yet"
python pipeline/pipeline.py --dry-run 2>/dev/null || echo "No dry-run mode yet"
```

Si algo se rompe después de la limpieza → restaura ese archivo de git:
```bash
git checkout -- [archivo-que-se-rompió]
```

Genera `cleanup_report.md` con el resumen de todo lo que se hizo.
