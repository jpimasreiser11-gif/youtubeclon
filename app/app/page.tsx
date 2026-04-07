"use client";
import React, { useState, useEffect, useRef } from 'react';
import { Sidebar } from '@/components/sidebar';
import {
  Link as LinkIcon, Upload, Sparkles, Languages, Scissors, Mic2, Crop,
  Film, MessageCircle, Folder, Loader2, Play, Download, Share2,
  ChevronDown, X, Info, Clock, Trash2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { trackEvent } from '@/lib/analytics';
import { useRouter } from 'next/navigation'; // Added this import

type ViewState = 'HOME' | 'PREVIEW' | 'PROCESSING' | 'RESULTS';
type CreationSystem = 'viral_motor_a' | 'viral_motor_b';

export default function HomePage() {
  const [url, setUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [projectId, setProjectId] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) {
      setError('Please enter a URL.');
      return;
    }

    setIsProcessing(true);
    setError('');

    try {
      const response = await fetch('/api/create-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();

      if (response.ok && data.projectId) {
        setProjectId(data.projectId);
        router.push(`/project/${data.projectId}`);
      } else {
        setError(data.error || 'Failed to create project.');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Original state variables that were not removed by the instruction, but were part of the context
  // Keeping them here as the instruction only specified a replacement for the initial block.
  const [view, setView] = useState<ViewState>('HOME');
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error' | 'processing', message: string } | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [clips, setClips] = useState<any[]>([]);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  // ─── Real values from DB ───────────────────────────
  const [targetProgress, setTargetProgress] = useState(0);  // DB truth
  const [targetEta, setTargetEta] = useState(0);            // DB truth (seconds)
  // ─── Animated display values ───────────────────────
  const [displayProgress, setDisplayProgress] = useState(0); // smooth 1%/s
  const [displayEta, setDisplayEta] = useState(0);           // live countdown

  // Smooth progress: move displayProgress → targetProgress at 1%/s
  const targetProgressRef = useRef(0);
  useEffect(() => {
    targetProgressRef.current = targetProgress;
  }, [targetProgress]);

  useEffect(() => {
    if (view !== 'PROCESSING') return;
    const ticker = setInterval(() => {
      setDisplayProgress(prev => {
        const target = targetProgressRef.current;
        if (prev >= target) return prev;          // never go backwards
        return Math.min(prev + 1, target);        // +1% per tick
      });
    }, 1000); // 1 second per %
    return () => clearInterval(ticker);
  }, [view]);

  // Live ETA countdown: tick down 1s per second, refresh when DB sends new value
  const etaRef = useRef(0);
  useEffect(() => {
    if (targetEta > 0) {
      etaRef.current = targetEta;
      setDisplayEta(targetEta);
    }
  }, [targetEta]);

  useEffect(() => {
    if (view !== 'PROCESSING') return;
    const countdown = setInterval(() => {
      setDisplayEta(prev => {
        if (prev <= 0) return 0;
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(countdown);
  }, [view]);

  // Smart ETA formatter: shows h/min/s correctly
  const formatEta = (seconds: number): string => {
    if (seconds <= 0) return '';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `~${h}h ${m > 0 ? m + ' min' : ''}`;
    if (m > 0 && s > 0) return `~${m} min ${s} s`;
    if (m > 0) return `~${m} min`;
    return `~${s} s`;
  };
  const [jobStep, setJobStep] = useState('Calculando...');
  const [enterpriseOptions, setEnterpriseOptions] = useState({
    audioPro: true,
    smartReframe: true,
    cleanSpeech: true,
    bRoll: true
  });
  const creationSystem: CreationSystem = 'viral_motor_a';
  const [viralNiche, setViralNiche] = useState('finanzas personales');
  const requiresSourceUrl = true;

  // Metadata state
  const [metadata, setMetadata] = useState<{ title: string, thumbnail: string } | null>(null);
  const [allJobs, setAllJobs] = useState<any[]>([]);

  // Fetch all jobs for the dashboard
  const fetchAllJobs = async () => {
    try {
      const res = await fetch('/api/get-jobs');
      const data = await res.json();
      if (data.jobs) setAllJobs(data.jobs);
    } catch (err) {
      console.error("Error fetching all jobs:", err);
    }
  };

  useEffect(() => {
    fetchAllJobs();
    const interval = setInterval(fetchAllJobs, 10000); // Refresh list every 10s
    return () => clearInterval(interval);
  }, []);

  // Phase 1: Fetch Metadata
  const handleUrlSubmit = async () => {
    if (!url) return;
    setIsLoading(true);
    setStatus(null); // Clear previous status
    trackEvent('motor_a_metadata_requested', { has_url: Boolean(url) });

    try {
      const response = await fetch('/api/get-metadata', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const data = await response.json();

      if (response.ok) {
        setMetadata(data);
        setView('PREVIEW');
        trackEvent('motor_a_metadata_loaded', { has_thumbnail: Boolean(data?.thumbnail) });
      } else {
        setStatus({ type: 'error', message: 'No se pudo obtener información del video.' });
        trackEvent('motor_a_metadata_failed');
      }
    } catch (error) {
      setStatus({ type: 'error', message: 'Error de conexión.' });
      trackEvent('motor_a_metadata_failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartJob = async () => {
    if (requiresSourceUrl && !url) return;
    setIsLoading(true);
    setStatus({ type: 'processing', message: 'Obteniendo información del video...' });
    setClips([]); // Clear clips from previous runs
    trackEvent('motor_a_job_create_clicked', { niche: viralNiche, has_url: Boolean(url) });

    try {
      const response = await fetch('/api/create-job', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          enterpriseOptions,
          creationSystem,
          viralNiche,
          viralDryRun: false,
        }),
      });

      const data = await response.json();

      if (response.ok && data.jobId) {
        setJobId(data.jobId);
        setView('PROCESSING');
        setStatus({ type: 'processing', message: 'Generando clips virales...' });
        trackEvent('motor_a_job_created', { job_id: data.jobId, niche: viralNiche });
      } else {
        throw new Error('Error al enviar el video');
      }
    } catch (error) {
      setStatus({ type: 'error', message: 'Hubo un error al conectar con el servidor.' });
      setIsLoading(false);
      trackEvent('motor_a_job_create_failed', { niche: viralNiche });
    }
  };

  // Polling logic — updates targetProgress and targetEta from DB every 3s
  useEffect(() => {
    if (!jobId || jobStatus === 'COMPLETED' || jobStatus === 'FAILED' || view !== 'PROCESSING') return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/get-job?id=${jobId}`);
        const data = await res.json();

        if (data.job) {
          setJobStatus(data.job.status);
          const newProgress = data.job.progress_percent || 0;
          const newEta = data.job.eta_seconds || 0;
          setTargetProgress(newProgress);       // smooth animation target
          if (newEta > 0) setTargetEta(newEta); // refresh countdown
          if (data.job.current_step) setJobStep(data.job.current_step);

          if (data.job.status === 'COMPLETED') {
            setTargetProgress(100);
            setStatus({ type: 'success', message: '¡Video generado con éxito!' });
            setTimeout(() => {
              setView('RESULTS');
              setIsLoading(false);
            }, 1200); // wait for animation to reach 100%
            clearInterval(interval);
          } else if (data.job.status === 'FAILED') {
            setStatus({ type: 'error', message: 'Error en el procesamiento.' });
            setIsLoading(false);
            clearInterval(interval);
          }
        }

        if (data.clips && data.clips.length > 0) {
          setClips(data.clips);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [jobId, jobStatus, view]);

  const handleDeleteJob = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('¿Estás seguro de que quieres eliminar este proyecto?')) return;

    // Actualización Optimista
    const previousJobs = [...allJobs];
    setAllJobs(prev => prev.filter(j => j.id !== id));

    try {
      const res = await fetch(`/api/delete-job?id=${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error("Fallo en api");
    } catch (err) {
      console.error("Error deleting job:", err);
      setAllJobs(previousJobs); // Revertir si falla
      alert("No se pudo eliminar el proyecto.");
    }
  };

  const FeatureIcon = ({ icon: Icon, label, colorClass }: { icon: any, label: string, colorClass: string }) => (
    <div className="flex flex-col items-center gap-3 group cursor-pointer">
      <div className={cn("w-16 h-16 rounded-full flex items-center justify-center bg-[#18181b] border border-[#27272a] transition-all duration-300 group-hover:scale-110 group-hover:bg-[#27272a]", colorClass)}>
        <Icon className="w-7 h-7" />
      </div>
      <span className="text-[11px] font-medium text-[#a1a1aa] text-center max-w-[90px] leading-tight group-hover:text-white transition-colors">
        {label}
      </span>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0a0a0a] font-sans text-white overflow-x-hidden selection:bg-white/20">
      <Sidebar />

      <main className="ml-[60px] min-h-screen flex flex-col items-center relative pt-16 pb-20">

        {/* Background Watermark */}
        {view === 'HOME' && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none select-none z-0">
            <h1 className="text-[28vw] font-black text-[#171717] leading-none tracking-tighter opacity-40">
              OpusClip
            </h1>
          </div>
        )}

        {/* HOME VIEW */}
        {view === 'HOME' && (
          <div className="z-10 w-full max-w-[600px] px-6 mt-[15vh] animate-fade-in">
            <div className="bg-[#000000] border border-[#1f1f1f] rounded-[32px] p-8 shadow-[0_0_50px_rgba(0,0,0,0.5)] space-y-7">
              <div className="space-y-4">
                <div className="relative group">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-[#a1a1aa]">
                    <LinkIcon className="w-5 h-5" />
                  </div>
                  <input
                    className="w-full bg-[#18181b] border border-[#27272a] rounded-2xl h-[64px] pl-12 pr-4 text-white placeholder:text-[#52525b] text-base focus:outline-none focus:ring-1 focus:ring-[#52525b] transition-all"
                    placeholder={requiresSourceUrl ? 'Coloca un enlace de Rumble o YouTube' : 'Modo desde 0: URL no requerida'}
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleUrlSubmit()}
                  />
                </div>
                <div className="flex items-center gap-6 px-1">
                  <button className="flex items-center gap-2 text-[#a1a1aa] hover:text-white transition-colors text-sm font-medium group">
                    <Upload className="w-4 h-4" /> Subir
                  </button>
                  <button className="flex items-center gap-2 text-[#a1a1aa] hover:text-white transition-colors text-sm font-medium group">
                    <Folder className="w-4 h-4" /> Google Drive
                  </button>
                </div>
              </div>

              <button
                onClick={handleUrlSubmit}
                disabled={isLoading || (requiresSourceUrl && !url)}
                className={cn(
                  "w-full h-[64px] rounded-2xl font-bold text-lg transition-all flex items-center justify-center gap-3 active:scale-[0.98]",
                  isLoading ? "bg-[#27272a] text-[#a1a1aa]" : "bg-[#ffffff] text-[#000000] hover:bg-[#f4f4f5] shadow-lg shadow-white/5",
                  (requiresSourceUrl && !url && !isLoading) && "opacity-50 cursor-not-allowed"
                )}
              >
                {isLoading ? <Loader2 className="w-6 h-6 animate-spin" /> : "Obtén clips en 1 clic"}
              </button>
            </div>

            <div className="mt-16 w-full max-w-[1000px] flex flex-wrap justify-center gap-10">
              <FeatureIcon icon={Sparkles} label="Convertir largos en cortos" colorClass="text-yellow-400" />
              <FeatureIcon icon={Languages} label="Subtítulos con IA" colorClass="text-green-400" />
              <FeatureIcon icon={Scissors} label="Editor de vídeo" colorClass="text-blue-500" />
              <FeatureIcon icon={Mic2} label="Mejorar voz" colorClass="text-blue-500" />
              <FeatureIcon icon={Crop} label="Reencuadre con IA" colorClass="text-blue-500" />
              <FeatureIcon icon={Film} label="B-Roll con IA" colorClass="text-blue-500" />
              <FeatureIcon icon={MessageCircle} label="Gancho de IA" colorClass="text-orange-400" />
            </div>
          </div>
        )}

        {/* PREVIEW VIEW */}
        {view === 'PREVIEW' && metadata && (
          <div className="z-10 w-full max-w-[700px] px-6 mt-10 animate-fade-in flex flex-col items-center">

            {/* Input Overlay with Eliminar */}
            <div className="w-full bg-[#000000] border border-[#1f1f1f] rounded-[24px] p-6 shadow-2xl space-y-6">
              <div className="relative">
                <div className="w-full bg-[#080808] border border-[#1f1f1f] rounded-xl h-[56px] pl-10 pr-24 flex items-center text-[#52525b] text-sm truncate">
                  <div className="absolute left-4 text-[#a1a1aa]">
                    <LinkIcon className="w-4 h-4" />
                  </div>
                  {url}
                  <button
                    onClick={() => {
                      setView('HOME');
                      setUrl('');
                      setMetadata(null);
                      setStatus(null);
                    }}
                    className="absolute right-4 text-white font-medium hover:underline text-sm"
                  >
                    Eliminar
                  </button>
                </div>
              </div>

              {/* Main CTA */}
              <button
                onClick={handleStartJob}
                disabled={isLoading}
                className="w-full h-[56px] bg-[#ffffff] text-[#000000] rounded-xl font-bold text-lg hover:bg-[#f4f4f5] transition-all flex items-center justify-center gap-2"
              >
                {isLoading ? <Loader2 className="w-6 h-6 animate-spin" /> : "Obtén clips en 1 clic"}
              </button>

              {/* Options Row */}
              <div className="space-y-4">
                <div className="flex items-center justify-between px-2">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1.5 cursor-pointer group">
                      <span className="text-[#a1a1aa] text-sm">Idioma del habla:</span>
                      <span className="text-white text-sm font-bold flex items-center gap-1">
                        Español <ChevronDown className="w-4 h-4" />
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[#a1a1aa] text-sm">Uso de créditos:</span>
                    <div className="flex items-center gap-1 bg-[#18181b] border border-[#27272a] px-2.5 py-1 rounded-lg">
                      <Sparkles className="w-3.5 h-3.5 text-yellow-500 fill-yellow-500" />
                      <span className="text-white text-sm font-bold">41</span>
                    </div>
                    <Info className="w-4 h-4 text-[#52525b]" />
                  </div>
                </div>

                {/* Enterprise Options Toggles */}
                <div className="bg-[#0a0a0a] border border-[#1f1f1f] rounded-xl p-4 space-y-3">
                  <div className="text-xs font-bold text-gray-500 uppercase tracking-tighter mb-1">Opciones Enterprise</div>

                  <div className="space-y-2">
                    <div className="text-xs font-bold text-gray-500 uppercase tracking-tighter">Motor de clips</div>
                    <div className="w-full bg-[#18181b] border border-[#27272a] rounded-lg px-3 py-2 text-sm text-white">
                      Motor A (único motor para generar clips)
                    </div>
                    <input
                      value={viralNiche}
                      onChange={(e) => setViralNiche(e.target.value)}
                      className="w-full bg-[#18181b] border border-[#27272a] rounded-lg px-3 py-2 text-sm text-white placeholder:text-[#52525b]"
                      placeholder="Nicho (ej: finanzas personales)"
                    />
                    <p className="text-[11px] text-[#71717a]">
                      Para contenido desde cero usa la pestaña dedicada de Motor B.
                    </p>
                  </div>

                  <label className="flex items-center justify-between cursor-pointer group">
                    <div className="flex items-center gap-2">
                      <Mic2 className="w-4 h-4 text-blue-400" />
                      <span className="text-sm font-medium">Neural Audio Pro (-14 LUFS)</span>
                    </div>
                    <input
                      type="checkbox"
                      checked={enterpriseOptions.audioPro}
                      onChange={(e) => setEnterpriseOptions({ ...enterpriseOptions, audioPro: e.target.checked })}
                      className="w-4 h-4 rounded border-[#27272a] bg-[#18181b] checked:bg-orange-600 focus:ring-orange-600"
                    />
                  </label>

                  <label className="flex items-center justify-between cursor-pointer group">
                    <div className="flex items-center gap-2">
                      <Crop className="w-4 h-4 text-purple-400" />
                      <span className="text-sm font-medium">Auto-Reencuadre Inteligente (ASD)</span>
                    </div>
                    <input
                      type="checkbox"
                      checked={enterpriseOptions.smartReframe}
                      onChange={(e) => setEnterpriseOptions({ ...enterpriseOptions, smartReframe: e.target.checked })}
                      className="w-4 h-4 rounded border-[#27272a] bg-[#18181b] checked:bg-orange-600 focus:ring-orange-600"
                    />
                  </label>

                  <label className="flex items-center justify-between cursor-pointer group">
                    <div className="flex items-center gap-2">
                      <Scissors className="w-4 h-4 text-green-400" />
                      <span className="text-sm font-medium">Saneamiento (Quitar Muletillas)</span>
                    </div>
                    <input
                      type="checkbox"
                      checked={enterpriseOptions.cleanSpeech}
                      onChange={(e) => setEnterpriseOptions({ ...enterpriseOptions, cleanSpeech: e.target.checked })}
                      className="w-4 h-4 rounded border-[#27272a] bg-[#18181b] checked:bg-orange-600 focus:ring-orange-600"
                    />
                  </label>

                  <label className="flex items-center justify-between cursor-pointer group">
                    <div className="flex items-center gap-2">
                      <Film className="w-4 h-4 text-blue-400" />
                      <span className="text-sm font-medium">Insertar B-Roll con IA (Viralidad)</span>
                    </div>
                    <input
                      type="checkbox"
                      checked={enterpriseOptions.bRoll}
                      onChange={(e) => setEnterpriseOptions({ ...enterpriseOptions, bRoll: e.target.checked })}
                      className="w-4 h-4 rounded border-[#27272a] bg-[#18181b] checked:bg-orange-600 focus:ring-orange-600"
                    />
                  </label>
                </div>
              </div>

              {/* Big Thumbnail */}
              <div className="relative w-full aspect-video rounded-[24px] overflow-hidden border border-[#1f1f1f] group">
                <img
                  src={metadata.thumbnail}
                  alt={metadata.title}
                  className="w-full h-full object-cover"
                />
                <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-sm px-2 py-0.5 rounded-md text-[10px] font-bold text-white border border-white/10 uppercase tracking-wider">
                  4k
                </div>
                <div className="absolute inset-0 bg-black/20 group-hover:bg-transparent transition-all" />
              </div>

              {/* Legal Disclaimer */}
              <p className="text-center text-[#52525b] text-[11px] leading-relaxed px-10">
                Usar vídeos que no te pertenecen puede violar las leyes de derechos de autor. Al continuar, confirmas que este es tu propio contenido original.
              </p>
            </div>
          </div>
        )}

        {/* PROCESSING VIEW */}
        {view === 'PROCESSING' && (
          <div className="z-10 w-full max-w-[600px] px-6 mt-20 animate-fade-in">
            <div className="bg-[#000000] border border-[#1f1f1f] rounded-[32px] p-12 shadow-2xl flex flex-col items-center justify-center gap-6 text-center">
              <div className="relative">
                <div className="w-24 h-24 rounded-full border-4 border-[#1f1f1f] border-t-orange-500 animate-spin" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Sparkles className="w-10 h-10 text-orange-500 animate-pulse" />
                </div>
              </div>
              <div className="space-y-4 w-full">
                <h2 className="text-2xl font-bold text-white">[{displayProgress}%] {jobStep}</h2>
                <div className="w-full bg-gray-800 rounded-full h-3">
                  <div className="bg-gradient-to-r from-orange-500 to-red-600 h-3 rounded-full transition-all duration-1000 ease-out" style={{ width: `${displayProgress}%` }}></div>
                </div>
                <div className="flex justify-between items-center text-sm font-medium text-gray-400">
                  <span>OpusClip AI Auto-Processing</span>
                  {displayEta > 0 ? (
                    <span>ETA {formatEta(displayEta)}</span>
                  ) : (
                    <span>Calculando ETA...</span>
                  )}
                </div>
              </div>
              {status && jobStatus === 'FAILED' && (
                <div className="mt-4 px-6 py-2 bg-[#18181b] rounded-full text-sm font-medium text-red-500 border border-red-500/20">
                  {status.message}
                </div>
              )}
            </div>
          </div>
        )}

        {/* RESULTS VIEW */}
        {view === 'RESULTS' && clips.length > 0 && (
          <div className="z-10 w-full max-w-[1200px] mt-10 px-6 animate-fade-in">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-bold flex items-center gap-3 italic">
                <Film className="w-6 h-6 text-yellow-400" />
                TUS CLIPS LISTOS
              </h2>
              <div className="flex items-center gap-2 bg-[#18181b] px-4 py-2 rounded-full border border-[#27272a]">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-xs font-medium text-[#a1a1aa]">{clips.length} Clips Generados</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {clips.map((clip, index) => {
                const getTierStyles = (score: number) => {
                  if (score >= 90) return { border: 'border-yellow-400', glow: 'shadow-[0_0_20px_rgba(250,204,21,0.2)]', badge: '👑 GOD TIER' };
                  if (score >= 80) return { border: 'border-orange-500', glow: 'shadow-[0_0_15px_rgba(249,115,22,0.2)]', badge: '🔥 VIRAL' };
                  return { border: 'border-[#1f1f1f] hover:border-[#3f3f46]', glow: 'shadow-2xl', badge: '👍 BUENO' };
                };
                const styles = getTierStyles(clip.virality_score || 0);

                return (
                  <div key={clip.id} className={`relative bg-[#000000] border-2 rounded-[28px] overflow-hidden group transition-all duration-500 ${styles.border} ${styles.glow} hover:-translate-y-1`}>
                    {/* BADGE DE TIER */}
                    <div className="absolute top-4 left-4 z-20 px-3 py-1.5 bg-black/80 backdrop-blur-md border border-white/20 rounded-full text-[10px] font-black shadow-lg tracking-wider">
                      {styles.badge}
                    </div>

                    {/* BADGE DE RITMO (WPM) */}
                    {clip.wpm && (
                      <div className="absolute top-4 right-4 z-20 px-2 py-1 bg-blue-900/80 backdrop-blur-md border border-blue-500/30 text-blue-300 rounded-md text-[10px] font-mono font-bold shadow-lg">
                        ⚡ {Math.round(clip.wpm)} WPM
                      </div>
                    )}

                    {/* Video Preview con 206 Partial Content (Streaming ultrarrápido) */}
                    <div className="relative aspect-[9/16] bg-[#0a0a0a]">
                      <video src={`/api/proxy-video?clipId=${clip.id}`} preload="metadata" className="w-full h-full object-cover" />
                      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center z-10">
                        <button className="w-14 h-14 rounded-full bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center hover:scale-110 transition-transform">
                          <Play className="w-5 h-5 text-white fill-white" />
                        </button>
                      </div>
                      {/* Virality Badge */}
                      <div className="absolute top-4 right-4 bg-green-500 text-white px-3 py-1 rounded-full text-[11px] font-black flex items-center gap-1.5 shadow-lg">
                        <Sparkles className="w-3 h-3" />
                        {clip.virality_score} ESCALA VIRAL
                      </div>
                    </div>

                    {/* Info Section */}
                    <div className="p-6 space-y-5">
                      <h3 className="font-bold text-lg line-clamp-2 leading-snug min-h-[52px] text-[#e4e4e7]">
                        {clip.title || `Clip Viral #${index + 1}`}
                      </h3>
                      <div className="flex items-center gap-2">
                        <button className="flex-1 bg-white text-black h-12 rounded-xl font-bold text-sm flex items-center justify-center gap-2 hover:bg-[#e4e4e7] transition-colors">
                          <Download className="w-4 h-4" /> Descargar
                        </button>
                        <button className="w-12 h-12 bg-[#18181b] border border-[#27272a] rounded-xl flex items-center justify-center hover:bg-[#27272a] transition-colors">
                          <Share2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Support Widget */}
        <div className="fixed bottom-8 right-8 z-50 flex flex-col items-end gap-4">
          <button className="bg-[#18181b] border border-[#27272a] hover:bg-[#27272a] text-white px-6 py-3 rounded-2xl text-[13px] font-black shadow-2xl transition-all tracking-tight">
            ¿Preguntas?
          </button>
        </div>

        {/* PROJECTS SECTION - Matching the reference image */}
        <div className="z-10 w-full max-w-[1200px] mt-32 px-6 pb-20 animate-fade-in border-t border-[#1f1f1f] pt-12">

          {/* Projects Header & Filters */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
            <div className="flex items-center gap-8 border-b border-[#1f1f1f] md:border-none pb-4 md:pb-0">
              <button className="text-white font-bold text-sm relative group cursor-pointer">
                Todos los proyectos ({allJobs.length})
                <div className="absolute -bottom-1 left-0 right-0 h-[2px] bg-white rounded-full mt-4" />
              </button>
              <button className="text-[#a1a1aa] font-medium text-sm hover:text-white transition-colors">
                Proyectos guardados (0)
              </button>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 bg-[#18181b] border border-[#27272a] px-3 py-1.5 rounded-xl cursor-pointer hover:bg-[#27272a] transition-all">
                <div className="w-2 h-2 rounded-full bg-[#52525b]" />
                <span className="text-xs font-bold text-white">Auto-guardar</span>
              </div>
              <div className="flex items-center gap-2 bg-[#18181b] border border-[#27272a] px-3 py-1.5 rounded-xl cursor-pointer hover:bg-[#27272a] transition-all">
                <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]" />
                <span className="text-xs font-bold text-white">Auto-importar <span className="text-[#a1a1aa] font-medium ml-1">Beta</span></span>
              </div>
            </div>
          </div>
        </div>

        {/* Projects Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-6 gap-y-10">
          {allJobs.map((job) => (
            <div key={job.id} className="group cursor-pointer relative">
              {/* Thumbnail Container */}
              <div className="relative aspect-video rounded-2xl overflow-hidden mb-3 border border-[#1f1f1f] transition-all group-hover:border-[#3f3f46]">
                <img
                  src={job.thumbnail_url || `https://img.youtube.com/vi/${job.source_url.split('v=')[1]?.split('&')[0] || 'dQw4w9WgXcQ'}/0.jpg`}
                  alt="Project"
                  className="w-full h-full object-cover grayscale-[0.2] group-hover:grayscale-0 transition-all duration-500"
                />

                {/* Status Overlay - Real Opus Style */}
                {(job.status === 'PROCESSING' || job.status === 'QUEUED') && (
                  <div className="absolute inset-x-0 bottom-4 px-3 z-20">
                    <div className="bg-[#052e16]/90 backdrop-blur-md border border-green-500/30 rounded-lg py-2.5 px-3 flex items-center gap-2.5 shadow-xl">
                      <div className="w-4 h-4 rounded-full flex items-center justify-center bg-green-500/20">
                        <Clock className="w-3 h-3 text-green-400" />
                      </div>
                      <span className="text-[11px] font-bold text-green-400 whitespace-nowrap">
                        {job.progress || 0}% (Tiempo estimado {Math.ceil((job.estimated_time_remaining || 0) / 60)}m)
                      </span>
                    </div>
                    <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-green-500/20 rounded-b-lg overflow-hidden">
                      <div className="h-full bg-green-400 shadow-[0_0_10px_rgba(74,222,128,0.5)] transition-all duration-1000" style={{ width: `${job.progress || 24}%` }} />
                    </div>
                  </div>
                )}

                {/* Status Overlay - Failed */}
                {(job.status === 'FAILED') && (
                  <div className="absolute inset-x-0 bottom-4 px-3 z-20">
                    <div className="bg-red-950/90 backdrop-blur-md border border-red-500/30 rounded-lg py-2 px-3 flex flex-col gap-1 shadow-xl max-h-[80px] overflow-y-auto">
                      <span className="text-[11px] font-bold text-red-500 whitespace-nowrap flex items-center gap-1.5">
                        <X className="w-3 h-3" /> Fallido
                      </span>
                      <span className="text-[10px] font-medium text-red-300 leading-tight">
                        {job.error_log || "Error desconocido en el procesamiento."}
                      </span>
                    </div>
                  </div>
                )}

                {/* High quality overlay for finished ones */}
                <div className="absolute inset-0 bg-black/20 group-hover:bg-transparent transition-all" />

                {/* Plan Badge Removed */}

                {/* Delete Button - Floating on Hover */}
                <button
                  onClick={(e) => handleDeleteJob(job.id, e)}
                  className="absolute top-2 left-2 w-8 h-8 rounded-lg bg-black/60 backdrop-blur-sm border border-white/5 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-500/20 hover:border-red-500/40 text-[#a1a1aa] hover:text-red-400"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Project Info */}
              <div className="space-y-1 px-1">
                <h4 className="font-bold text-sm text-[#e4e4e7] truncate group-hover:text-white transition-colors">
                  {job.title || job.source_url}
                </h4>
                <div className="flex items-center justify-between">
                  <p className="text-[#52525b] text-xs font-medium">Auto</p>
                  <span className="text-[10px] text-[#3f3f46]">{new Date(job.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          ))}

          {/* Empty State / Add New */}
          {allJobs.length === 0 && (
            <div className="col-span-full py-20 flex flex-col items-center border border-dashed border-[#27272a] rounded-[32px] bg-[#09090b]/50">
              <Folder className="w-12 h-12 text-[#27272a] mb-4" />
              <p className="text-sm font-bold text-[#a1a1aa]">No hay proyectos todavía</p>
              <p className="text-xs text-[#52525b] mt-1">Crea tu primer clip pegando un enlace arriba</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
