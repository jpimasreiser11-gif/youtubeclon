import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/auth'

type ScriptParts = {
  parte_1: string
  parte_2: string
  parte_3: string
}

type SuggestionItem = {
  id: string
  title: string
  subgenre: string
  niche: string
  theme: string
  hook: string
  angle: string
  keywords: string[]
  language: 'es' | 'en' | 'bilingual'
  prebuilt_script: ScriptParts | { es: ScriptParts; en: ScriptParts }
}

type Seed = {
  id: string
  subgenre: string
  title_es: string
  title_en: string
  theme_es: string
  theme_en: string
  hook_es: string
  hook_en: string
  angle_es: string
  angle_en: string
  keywords_es: string[]
  keywords_en: string[]
  twist_es: string
  twist_en: string
}

const DEFAULT_SEEDS: Seed[] = [
  {
    id: 'black-file-001',
    subgenre: 'expedientes ocultos',
    title_es: 'El expediente que desaparecio dos veces',
    title_en: 'The file that vanished twice',
    theme_es: 'Un informe clasificado reaparece con paginas reescritas',
    theme_en: 'A classified report resurfaces with rewritten pages',
    hook_es: 'Te cuento un secreto que no estaba en los archivos oficiales',
    hook_en: 'Let me tell you a secret that was never in the official files',
    angle_es: 'Narracion documental con giro final y pregunta abierta',
    angle_en: 'Documentary narration with a final twist and open question',
    keywords_es: ['archivo secreto', 'documento filtrado', 'pista borrada', 'testigo anonimo', 'verdad oculta'],
    keywords_en: ['secret file', 'leaked document', 'erased clue', 'anonymous witness', 'hidden truth'],
    twist_es: 'la firma del cierre pertenece a alguien que habia muerto antes',
    twist_en: 'the closing signature belongs to someone declared dead years earlier',
  },
  {
    id: 'signal-forest-002',
    subgenre: 'senales imposibles',
    title_es: 'La senal de radio que no deberia existir',
    title_en: 'The radio signal that should not exist',
    theme_es: 'Una frecuencia perdida vuelve cada noche a la misma hora',
    theme_en: 'A lost frequency returns every night at the same time',
    hook_es: 'Si escuchas esto completo, no vuelves a oir el silencio igual',
    hook_en: 'If you hear this to the end, silence will never feel the same again',
    angle_es: 'Suspenso sonoro con cronologia de pruebas y contradicciones',
    angle_en: 'Audio suspense with a timeline of evidence and contradictions',
    keywords_es: ['radio fantasma', 'frecuencia perdida', 'onda corta', 'cabana aislada', 'ruido blanco'],
    keywords_en: ['ghost radio', 'lost frequency', 'shortwave', 'isolated cabin', 'white noise'],
    twist_es: 'la grabacion coincide con un mensaje emitido meses antes del evento',
    twist_en: 'the recording matches a message aired months before the event',
  },
  {
    id: 'metro-door-003',
    subgenre: 'lugares prohibidos',
    title_es: 'La puerta sellada bajo la estacion central',
    title_en: 'The sealed door beneath central station',
    theme_es: 'Trabajadores encuentran un tunel sin planos oficiales',
    theme_en: 'Workers find a tunnel absent from all official blueprints',
    hook_es: 'Nadie sabe por que esa puerta sigue cerrada desde 1984',
    hook_en: 'Nobody knows why that door has stayed shut since 1984',
    angle_es: 'Relato en primera persona con evidencia visual y final ambiguo',
    angle_en: 'First-person storytelling with visual evidence and an ambiguous ending',
    keywords_es: ['tunel secreto', 'estacion abandonada', 'puerta sellada', 'plano borrado', 'obra nocturna'],
    keywords_en: ['secret tunnel', 'abandoned station', 'sealed door', 'erased blueprint', 'night construction'],
    twist_es: 'el candado es nuevo, pero los restos dentro tienen decadas',
    twist_en: 'the lock is new, but the debris inside is decades old',
  },
  {
    id: 'hotel-room-004',
    subgenre: 'enigmas historicos',
    title_es: 'La habitacion del hotel donde nadie duro una noche',
    title_en: 'The hotel room no one survived a full night in',
    theme_es: 'Un registro de huespedes muestra nombres tachados y fechas repetidas',
    theme_en: 'A guest log shows crossed-out names and repeating dates',
    hook_es: 'Este cuarto parecia normal... hasta que revisaron el libro antiguo',
    hook_en: 'That room looked normal... until they opened the old ledger',
    angle_es: 'Narrativa de caso con tres hipotesis y cierre con decision del publico',
    angle_en: 'Case narrative with three hypotheses and a viewer-driven ending',
    keywords_es: ['hotel antiguo', 'registro oculto', 'piso clausurado', 'llave oxidada', 'historia prohibida'],
    keywords_en: ['old hotel', 'hidden registry', 'sealed floor', 'rusted key', 'forbidden history'],
    twist_es: 'la misma firma aparece en anos distintos con la misma letra intacta',
    twist_en: 'the same signature appears decades apart in identical handwriting',
  },
]

function buildScriptEs(seed: Seed): ScriptParts {
  return {
    parte_1: `${seed.hook_es}. Todo empieza con ${seed.theme_es}. Lo raro no fue encontrar la evidencia, sino ver que faltaba justo la pagina clave. En esta historia hay tres detalles que no encajan: una fecha que cambia sola, un testigo que niega su propia voz y una foto que aparece en dos lugares distintos. Si esto fuera montaje, alguien habria cometido un error facil de detectar... pero no lo hizo.`,
    parte_2: `Primero revisaron los registros y encontraron patrones imposibles. Segundo, compararon versiones del mismo documento y descubrieron ediciones con diferencias milimetricas. Tercero, un audio antiguo revelo una frase que coincide con reportes actuales. El problema es que ninguna fuente acepta ser la original. Y cuando intentaron cerrar el caso, alguien movio una pieza clave: ${seed.twist_es}.`,
    parte_3: `La conclusion oficial dice que fue una confusion administrativa. Pero la evidencia apunta a un guion repetido: ocultar, reescribir y volver a ocultar. Si conectas los tres indicios, aparece una explicacion inquietante: alguien protegia la historia real desde dentro. Ahora dime tu version: accidente, encubrimiento o experimento? Te leo en comentarios si quieres la parte dos con documentos y mapa completo.`,
  }
}

function buildScriptEn(seed: Seed): ScriptParts {
  return {
    parte_1: `${seed.hook_en}. It starts with ${seed.theme_en}. The strange part was not finding evidence, but noticing the one page that should explain everything was missing. Three details do not match: a date that shifts across copies, a witness denying their own recorded statement, and one photo showing up in two unrelated archives. If this was staged, someone should have slipped... but nobody did.`,
    parte_2: `First, investigators compared records and found impossible repetition patterns. Second, they overlaid two versions of the same file and detected precision edits where no revision log exists. Third, an old audio tape repeated a line that appears in a modern incident report. No source claims to be the original. Then, right before closure, one final change appeared: ${seed.twist_en}.`,
    parte_3: `The official answer calls it clerical noise. The evidence suggests a loop: hide, rewrite, hide again. When you connect all three clues, one unsettling possibility appears: someone inside was preserving a controlled version of the truth. What is your verdict: coincidence, cover-up, or a failed experiment? Comment your theory and I will post part two with timeline and source map.`,
  }
}

function mapSeed(seed: Seed, lang: 'es' | 'en' | 'mixed'): SuggestionItem {
  if (lang === 'en') {
    return {
      id: seed.id,
      title: seed.title_en,
      subgenre: seed.subgenre,
      niche: 'mysteries and enigmas',
      theme: seed.theme_en,
      hook: seed.hook_en,
      angle: seed.angle_en,
      keywords: seed.keywords_en,
      language: 'en',
      prebuilt_script: buildScriptEn(seed),
    }
  }

  if (lang === 'mixed') {
    return {
      id: seed.id,
      title: `${seed.title_es} / ${seed.title_en}`,
      subgenre: seed.subgenre,
      niche: 'misterios y enigmas',
      theme: seed.theme_es,
      hook: seed.hook_es,
      angle: seed.angle_es,
      keywords: seed.keywords_es,
      language: 'bilingual',
      prebuilt_script: {
        es: buildScriptEs(seed),
        en: buildScriptEn(seed),
      },
    }
  }

  return {
    id: seed.id,
    title: seed.title_es,
    subgenre: seed.subgenre,
    niche: 'misterios y enigmas',
    theme: seed.theme_es,
    hook: seed.hook_es,
    angle: seed.angle_es,
    keywords: seed.keywords_es,
    language: 'es',
    prebuilt_script: buildScriptEs(seed),
  }
}

export async function GET(request: NextRequest) {
  const session = await auth()
  if (!session || !session.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { searchParams } = new URL(request.url)
  const q = (searchParams.get('q') || '').toLowerCase().trim()
  const langParam = (searchParams.get('lang') || 'es').toLowerCase()
  const lang: 'es' | 'en' | 'mixed' = langParam === 'en' ? 'en' : (langParam === 'mixed' ? 'mixed' : 'es')

  let seeds = DEFAULT_SEEDS
  if (q) {
    seeds = seeds.filter((seed) => {
      const haystack = [
        seed.subgenre,
        seed.title_es,
        seed.title_en,
        seed.theme_es,
        seed.theme_en,
        ...seed.keywords_es,
        ...seed.keywords_en,
      ].join(' ').toLowerCase()
      return haystack.includes(q)
    })
  }

  const suggestions = seeds.slice(0, 8).map((seed) => mapSeed(seed, lang))

  return NextResponse.json({
    source: 'free-template-ai',
    count: suggestions.length,
    lang,
    suggestions,
  })
}
