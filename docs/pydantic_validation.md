# Fase 1: Validación Pydantic para Respuestas de IA

## Objetivo
Añadir validación robusta usando Pydantic para asegurar que las respuestas de Gemini cumplen con el schema esperado.

## Implementación

### 1. Instalar Pydantic
```bash
pip install pydantic
```

### 2. Crear Models en ingest.py

```python
from pydantic import BaseModel, Field, validator
from typing import List, Literal

class ViralClip(BaseModel):
    rank: int = Field(ge=1, le=6)
    start: float  # Segundos
    end: float
    score: int = Field(ge=0, le=100)
    title: str = Field(max_length=150)
    category: Literal["Humor", "Educativo", "Polémico", "Inspiracional", "Tutorial", "Historia", "Debate", "Otro"]
    hook_description: str
    payoff_description: str
    reason: str
    
    @validator('end')
    def validate_duration(cls, v, values):
        if 'start' in values:
            duration = v - values['start']
            if duration < 30:
                raise ValueError(f'Clip too short: {duration}s (min 30s)')
            if duration > 180:
                raise ValueError(f'Clip too long: {duration}s (max 180s)')
        return v
    
    @validator('end')
    def end_after_start(cls, v, values):
        if 'start' in values and v <= values['start']:
            raise ValueError('end must be after start')
        return v

class ViralClipsResponse(BaseModel):
    clips: List[ViralClip] = Field(alias='viral_clips', default=[])
    
    @validator('clips')
    def exactly_six_clips(cls, v):
        if len(v) != 6:
            raise ValueError(f'Must return exactly 6 clips, got {len(v)}')
        return v
    
    class Config:
        allow_population_by_field_name = True
```

### 3. Uso en analyze_virality()

```python
def analyze_virality(transcript):
    try:
        # ... código existente de Gemini ...
        
        clips_data = json.loads(text)
        
        # Validar con Pydantic
        try:
            if isinstance(clips_data, dict):
                validated = ViralClipsResponse(**clips_data)
                clips = [clip.dict() for clip in validated.clips]
            else:
                validated = ViralClipsResponse(viral_clips=clips_data)
                clips = [clip.dict() for clip in validated.clips]
                
        except ValidationError as e:
            logging.error(f"Pydantic validation failed: {e}")
            # Intentar reparar datos o usar fallback
            clips = repair_or_fallback(clips_data)
            
        return clips
```

## Beneficios
- ✅ Validación automática de tipos
- ✅ Detección de clips muy cortos/largos
- ✅ Garantiza exactamente 6 clips
- ✅ Categorías válidas enforced
- ✅ Errores claros para debugging
