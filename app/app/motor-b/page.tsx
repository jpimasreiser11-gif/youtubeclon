"use client";

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar } from '@/components/sidebar';
import { Sparkles, TrendingUp, Loader2, Wand2 } from 'lucide-react';

type ScriptParts = {
  parte_1: string;
  parte_2: string;
  parte_3: string;
};

type PrebuiltScript = ScriptParts | { es: ScriptParts; en: ScriptParts };

type MotorBPayload = {
  tema: string;
  hook: string;
  angulo: string;
  nicho: string;
  palabras_clave: string[];
  prebuilt_script?: PrebuiltScript;
};

type SuggestionItem = {
  id: string;
  title: string;
  subgenre: string;
  niche: string;
  theme: string;
  hook: string;
  angle: string;
  keywords: string[];
  language: 'es' | 'en' | 'bilingual';
  prebuilt_script: PrebuiltScript;
};

const PROMPT_TEMPLATE = `Instrucciones: Motor B - Generacion de Video Corto 100% con IA\n\nProceso en 5 fases: input JSON, guion 3 partes, TTS, imagenes 9:16, ensamblado con subtitulos y musica.\nInput base:\n{\n  "tema": "",
  "hook": "",
  "angulo": "",
  "nicho": "",
  "palabras_clave": []
}`;

export default function MotorBPage() {
  const router = useRouter();
  const [tema, setTema] = useState('El experimento que el gobierno oculto durante 40 anos');
  const [hook, setHook] = useState('Te cuento un secreto que casi nadie conoce');
  const [angulo, setAngulo] = useState('Narrativa intima de misterio con revelacion final');
  const [nicho, setNicho] = useState('misterios y enigmas');
  const [keywords, setKeywords] = useState('dark forest fog, abandoned building night, secret laboratory, conspiracy, hidden truth');
  const [trendMode, setTrendMode] = useState<'internet' | 'manual-only'>('internet');
  const [suggestionLang, setSuggestionLang] = useState<'es' | 'en' | 'mixed'>('mixed');
  const [suggestionSearch, setSuggestionSearch] = useState('');
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [selectedSuggestionId, setSelectedSuggestionId] = useState<string | null>(null);
  const [prebuiltScript, setPrebuiltScript] = useState<PrebuiltScript | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastJobId, setLastJobId] = useState<string | null>(null);

  const parsedKeywords = keywords
    .split(',')
    .map((x) => x.trim())
    .filter(Boolean)
    .slice(0, 5);

  const payload: MotorBPayload = {
    tema: tema.trim(),
    hook: hook.trim(),
    angulo: angulo.trim(),
    nicho: nicho.trim(),
    palabras_clave: parsedKeywords,
    ...(prebuiltScript ? { prebuilt_script: prebuiltScript } : {}),
  };

  const promptWithData = JSON.stringify(payload, null, 2);

  useEffect(() => {
    let ignore = false;

    const fetchSuggestions = async () => {
      setLoadingSuggestions(true);
      try {
        const qs = new URLSearchParams();
        qs.set('lang', suggestionLang);
        if (suggestionSearch.trim()) qs.set('q', suggestionSearch.trim());

        const res = await fetch(`/api/motor-b-suggestions?${qs.toString()}`, { cache: 'no-store' });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data?.error || 'No se pudieron cargar sugerencias');
        }
        if (!ignore) {
          setSuggestions(Array.isArray(data?.suggestions) ? data.suggestions : []);
        }
      } catch (e: any) {
        if (!ignore) {
          setSuggestions([]);
          setError(e?.message || 'Error cargando sugerencias');
        }
      } finally {
        if (!ignore) setLoadingSuggestions(false);
      }
    };

    fetchSuggestions();
    return () => {
      ignore = true;
    };
  }, [suggestionLang, suggestionSearch]);

  const selectedSuggestion = useMemo(
    () => suggestions.find((s) => s.id === selectedSuggestionId) || null,
    [suggestions, selectedSuggestionId]
  );

  const applySuggestion = (item: SuggestionItem) => {
    setTema(item.theme);
    setHook(item.hook);
    setAngulo(item.angle);
    setNicho(item.niche);
    setKeywords(item.keywords.join(', '));
    setPrebuiltScript(item.prebuilt_script);
    setSelectedSuggestionId(item.id);
    setError('');
  };

  const submit = async () => {
    if (!payload.tema || !payload.hook || !payload.angulo || !payload.nicho || payload.palabras_clave.length === 0) {
      setError('Completa tema, hook, angulo, nicho y al menos 1 palabra clave.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/create-job', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          creationSystem: 'viral_motor_b',
          viralNiche: payload.nicho,
          viralDryRun: false,
          motorBInput: payload,
          motorBTrendMode: trendMode,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error || 'No se pudo crear el job de Motor B');
      }

      setLastJobId(data.jobId || null);
      if (data.jobId) {
        router.push(`/projects/${data.jobId}`);
      }
    } catch (e: any) {
      setError(e?.message || 'Error creando job de Motor B');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f16] text-white">
      <Sidebar />
      <main className="ml-[60px] p-6 md:p-10">
        <div className="max-w-5xl mx-auto space-y-6">
          <section className="rounded-3xl border border-[#1f2937] bg-gradient-to-br from-[#0f172a] via-[#111827] to-[#0b1220] p-6 md:p-8 shadow-2xl">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-11 h-11 rounded-2xl bg-[#1d4ed8]/20 border border-[#3b82f6]/30 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-[#93c5fd]" />
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-black tracking-tight">Motor B Tendencias</h1>
                <p className="text-sm text-[#9ca3af]">Sistema separado: analiza tendencias en internet y genera video vertical desde cero con IA.</p>
                <p className="text-xs text-[#fca5a5] mt-1">Modo Mystery activo automaticamente cuando el nicho incluye misterio/enigma/conspiracion. Genera canal ES + EN.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-[#9ca3af] uppercase tracking-wide">Tema</label>
                <input value={tema} onChange={(e) => setTema(e.target.value)} className="mt-1 w-full rounded-xl bg-[#0b1220] border border-[#243147] px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs text-[#9ca3af] uppercase tracking-wide">Nicho</label>
                <input value={nicho} onChange={(e) => setNicho(e.target.value)} className="mt-1 w-full rounded-xl bg-[#0b1220] border border-[#243147] px-3 py-2 text-sm" />
              </div>
              <div className="md:col-span-2">
                <label className="text-xs text-[#9ca3af] uppercase tracking-wide">Hook</label>
                <input value={hook} onChange={(e) => setHook(e.target.value)} className="mt-1 w-full rounded-xl bg-[#0b1220] border border-[#243147] px-3 py-2 text-sm" />
              </div>
              <div className="md:col-span-2">
                <label className="text-xs text-[#9ca3af] uppercase tracking-wide">Angulo</label>
                <input value={angulo} onChange={(e) => setAngulo(e.target.value)} className="mt-1 w-full rounded-xl bg-[#0b1220] border border-[#243147] px-3 py-2 text-sm" />
              </div>
              <div className="md:col-span-2">
                <label className="text-xs text-[#9ca3af] uppercase tracking-wide">Palabras clave (coma separadas, max 5)</label>
                <input value={keywords} onChange={(e) => setKeywords(e.target.value)} className="mt-1 w-full rounded-xl bg-[#0b1220] border border-[#243147] px-3 py-2 text-sm" />
              </div>
            </div>

            <div className="mt-5 rounded-2xl border border-[#243147] bg-[#0a1120] p-4">
              <div className="flex flex-wrap items-center gap-3 mb-3">
                <p className="text-sm font-semibold text-[#dbeafe]">Sugerencias predeterminadas (historias y enigmas)</p>
                <span className="text-[11px] text-[#93c5fd]">Guion precreado con IA gratuita</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                <div>
                  <label className="text-xs text-[#9ca3af] uppercase tracking-wide">Idioma sugerencias</label>
                  <select
                    value={suggestionLang}
                    onChange={(e) => setSuggestionLang(e.target.value as 'es' | 'en' | 'mixed')}
                    className="mt-1 w-full rounded-xl bg-[#0b1220] border border-[#243147] px-3 py-2 text-sm"
                  >
                    <option value="mixed">Bilingue (ES + EN)</option>
                    <option value="es">Solo Espanol</option>
                    <option value="en">Solo English</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="text-xs text-[#9ca3af] uppercase tracking-wide">Buscar subgenero o tema</label>
                  <input
                    value={suggestionSearch}
                    onChange={(e) => setSuggestionSearch(e.target.value)}
                    placeholder="conspiracion, radio, expediente..."
                    className="mt-1 w-full rounded-xl bg-[#0b1220] border border-[#243147] px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {loadingSuggestions ? (
                  <p className="text-sm text-[#93c5fd]">Cargando sugerencias...</p>
                ) : (
                  suggestions.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => applySuggestion(item)}
                      className={`text-left rounded-xl border px-4 py-3 transition ${selectedSuggestionId === item.id ? 'border-[#22c55e] bg-[#052e1b]' : 'border-[#243147] bg-[#0b1220] hover:border-[#3b82f6]'}`}
                    >
                      <p className="text-sm font-semibold text-white">{item.title}</p>
                      <p className="text-xs text-[#9ca3af] mt-1">{item.subgenre}</p>
                      <p className="text-xs text-[#cbd5e1] mt-2 line-clamp-2">{item.hook}</p>
                    </button>
                  ))
                )}
              </div>

              {selectedSuggestion && (
                <p className="mt-3 text-xs text-[#86efac]">
                  Sugerencia aplicada: {selectedSuggestion.title}. El pipeline usara su guion precreado.
                </p>
              )}
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2 text-sm">
                <TrendingUp className="w-4 h-4 text-[#60a5fa]" />
                <span className="text-[#cbd5e1]">Modo de tendencias:</span>
              </div>
              <select
                value={trendMode}
                onChange={(e) => setTrendMode(e.target.value as 'internet' | 'manual-only')}
                className="rounded-xl bg-[#0b1220] border border-[#243147] px-3 py-2 text-sm"
              >
                <option value="internet">Internet (YouTube + Twitter + Google Trends)</option>
                <option value="manual-only">Solo tu input (sin scraping externo)</option>
              </select>

              <button
                onClick={submit}
                disabled={loading}
                className="ml-auto inline-flex items-center gap-2 rounded-xl bg-[#22c55e] hover:bg-[#16a34a] disabled:opacity-60 text-black font-bold px-4 py-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
                Crear con Motor B
              </button>
            </div>

            {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
            {lastJobId && <p className="mt-3 text-xs text-[#93c5fd]">Job creado: {lastJobId}</p>}
          </section>

          <section className="rounded-2xl border border-[#1f2937] bg-[#0b1220] p-5">
            <h2 className="font-bold mb-2">Prompt tecnico base para IA (editable)</h2>
            <pre className="text-xs leading-relaxed text-[#cbd5e1] whitespace-pre-wrap">{PROMPT_TEMPLATE}\n\nInput actual:\n{promptWithData}</pre>
          </section>
        </div>
      </main>
    </div>
  );
}
