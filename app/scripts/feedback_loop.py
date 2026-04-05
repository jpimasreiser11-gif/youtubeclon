"""
Feedback Loop: Aprende de Métricas Reales para Mejorar Scoring Futuro
Analiza qué características tienen los clips con mejor performance
y ajusta el prompt de Gemini para generar mejores clips
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
import json
from collections import Counter
import statistics

DB_CONFIG = {
    "user": "n8n",
    "password": "n8n",
    "host": "localhost",
    "port": 5432,
    "database": "antigravity"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def get_top_performers(min_views: int = 10000, limit: int = 50) -> List[Dict]:
    """
    Obtiene clips con mejor performance real
    
    Args:
        min_views: Mínimo de views para considerar
        limit: Cantidad máxima de clips
    
    Returns:
        Lista de clips con sus métricas
    """
    print(f"🔍 Analizando top performers (min {min_views} views)...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            """SELECT c.*, pm.views, pm.likes, pm.retention_rate, pm.platform
               FROM clips c
               JOIN performance_metrics pm ON c.id = pm.clip_id
               WHERE pm.views >= %s
               ORDER BY pm.views DESC
               LIMIT %s""",
            (min_views, limit)
        )
        
        clips = cur.fetchall()
        print(f"✓ {len(clips)} top performers encontrados")
        return clips
        
    finally:
        cur.close()
        conn.close()

def analyze_patterns(clips: List[Dict]) -> Dict[str, Any]:
    """
    Analiza patrones en clips exitosos
    
    Returns:
        Dict con insights:
        - Categorías más exitosas
        - Rango de duración óptimo
        - Keywords comunes en hooks
        - Score promedio vs views
    """
    print("🧠 Analizando patrones de éxito...")
    
    if not clips:
        return {}
    
    # 1. Categorías más exitosas
    categories = [c['category'] for c in clips]
    category_counts = Counter(categories)
    top_categories = category_counts.most_common(3)
    
    # 2. Duración óptima
    durations = [c['end_time'] - c['start_time'] for c in clips]
    avg_duration = statistics.mean(durations)
    optimal_range = (min(durations), max(durations))
    
    # 3. Keywords comunes en hooks
    all_hooks = ' '.join([c.get('hook_description', '') for c in clips]).lower()
    # Simplificado: palabras más comunes
    words = all_hooks.split()
    stopwords = {'el', 'la', 'de', 'que', 'en', 'y', 'a', 'los', 'las', 'un', 'una', 'por', 'para', 'con'}
    keywords = [w for w in words if len(w) > 4 and w not in stopwords]
    top_keywords = Counter(keywords).most_common(10)
    
    # 4. Correlación score vs views
    scores = [c.get('virality_score', 0) for c in clips]
    views = [c.get('views', 0) for c in clips]
    avg_score = statistics.mean(scores)
    avg_views = statistics.mean(views)
    
    patterns = {
        'top_categories': [cat for cat, count in top_categories],
        'optimal_duration_avg': round(avg_duration, 1),
        'optimal_duration_range': optimal_range,
        'common_hook_keywords': [kw for kw, count in top_keywords],
        'avg_virality_score': round(avg_score, 1),
        'avg_views': int(avg_views),
        'total_clips_analyzed': len(clips)
    }
    
    print(f"\n📊 INSIGHTS:")
    print(f"  Categorías top: {patterns['top_categories']}")
    print(f"  Duración óptima: {patterns['optimal_duration_avg']}s")
    print(f"  Keywords comunes: {patterns['common_hook_keywords'][:5]}")
    print(f"  Score promedio: {patterns['avg_virality_score']}")
    print(f"  Views promedio: {patterns['avg_views']:,}\n")
    
    return patterns

def generate_improved_prompt(patterns: Dict[str, Any]) -> str:
    """
    Genera prompt mejorado para Gemini basado en learnings
    """
    print("📝 Generando prompt optimizado...")
    
    base_prompt = """Analiza este video y genera clips virales.

LEARNINGS DE CLIPS EXITOSOS:
"""
    
    if patterns.get('top_categories'):
        base_prompt += f"\n- Categorías con mejor performance: {', '.join(patterns['top_categories'])}"
    
    if patterns.get('optimal_duration_avg'):
        base_prompt += f"\n- Duración óptima: ~{patterns['optimal_duration_avg']}s"
    
    if patterns.get('common_hook_keywords'):
        base_prompt += f"\n- Keywords efectivos en hooks: {', '.join(patterns['common_hook_keywords'][:5])}"
    
    base_prompt += """

Prioriza:
1. Clips en las categorías de alto rendimiento
2. Duración cercana al promedio óptimo
3. Hooks que incluyan keywords probados
4. Score predicho >= 85

Devuelve 20-30 clips ordenados por potencial viral.
"""
    
    print("✓ Prompt optimizado generado")
    return base_prompt

def save_learnings(patterns: Dict[str, Any], output_file: str = "learnings.json"):
    """
    Guarda learnings en archivo JSON para referencia futura
    """
    with open(output_file, 'w') as f:
        json.dump(patterns, f, indent=2)
    
    print(f"✓ Learnings guardados en {output_file}")

def run_feedback_loop():
    """
    Ejecuta el ciclo completo de feedback
    """
    print("\n" + "="*60)
    print("🔄 FEEDBACK LOOP: Aprendiendo de clips exitosos")
    print("="*60 + "\n")
    
    # 1. Obtener top performers
    clips = get_top_performers(min_views=5000, limit=100)
    
    if not clips:
        print("⚠️ No hay suficientes clips con métricas")
        return None
    
    # 2. Analizar patrones
    patterns = analyze_patterns(clips)
    
    # 3. Generar prompt mejorado
    improved_prompt = generate_improved_prompt(patterns)
    
    # 4. Guardar learnings
    save_learnings(patterns)
    
    print("\n✅ FEEDBACK LOOP COMPLETADO")
    print("   Usa learnings.json para mejorar futuros clips\n")
    
    return patterns

# CLI
if __name__ == "__main__":
    run_feedback_loop()
