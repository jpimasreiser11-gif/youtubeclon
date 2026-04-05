'use client';

import { useState, useRef } from 'react';
import toast from 'react-hot-toast';
import ClipEditor from '@/components/ClipEditor';
import DownloadModal from '@/components/DownloadModal';

interface ClipViewerProps {
    clip: {
        id: string;
        project_id: string;
        rank: number;
        start_time: number;
        end_time: number;
        virality_score: number;
        title: string;
        category: string;
        hook_description: string;
        payoff_description: string;
        reason: string;
        transcript?: string;
    };
}

export default function ClipViewer({ clip }: ClipViewerProps) {
    const [expanded, setExpanded] = useState(false);
    const [showEditor, setShowEditor] = useState(false);
    const [showDownloadModal, setShowDownloadModal] = useState(false);
    const [isVerticalFullScreen, setIsVerticalFullScreen] = useState(false);
    const [tab, setTab] = useState<'analysis' | 'transcript'>('analysis');
    const videoRef = useRef<HTMLVideoElement>(null);

    const duration = clip.end_time - clip.start_time;
    const timeRange = `[${formatTimeRange(clip.start_time)} - ${formatTimeRange(clip.end_time)}]`;

    const handleDownloadHD = () => {
        setShowDownloadModal(true);
    };

    const handlePublish = () => {
        // Abrir modal de publicación
        alert('Funcionalidad de publicación - conectar con YouTube/TikTok');
    };

    const handleExportXML = () => {
        alert('Exportar metadatos XML');
    };

    if (showEditor) {
        return (
            <div className="fixed inset-0 z-50 bg-black">
                <button
                    onClick={() => setShowEditor(false)}
                    className="absolute top-4 right-4 z-10 bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-lg"
                >
                    ✕ Cerrar Editor
                </button>
                <ClipEditor clip={clip} videoDuration={300} />
            </div>
        );
    }

    return (
        <div className={`${expanded ? 'fixed inset-0 z-50 p-8' : ''} bg-[#0a0a0a] text-white rounded-lg`}>
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-[#1f1f1f]">
                <h2 className="text-xl font-bold">{clip.title}</h2>
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="text-gray-400 hover:text-white text-2xl"
                >
                    {expanded ? '✕' : '⛶'}
                </button>
            </div>

            <div className="grid grid-cols-12 gap-6 p-6">
                {/* Left: Video Preview */}
                <div className="col-span-4">
                    <div className="bg-black rounded-lg overflow-hidden border border-[#1f1f1f]">
                        {/* Low res preview label */}
                        <div className="bg-[#1a1a1a] px-3 py-2 text-xs text-gray-400 flex items-center justify-between">
                            <span>VISTA PREVIA DE BAJA RESOLUCIÓN</span>
                            <span className="bg-orange-500/20 text-orange-500 px-2 py-0.5 rounded">
                                {formatTime(duration)}
                            </span>
                        </div>

                        {/* Video */}
                        <div className="relative aspect-[9/16] bg-gray-900">
                            <video
                                ref={videoRef}
                                src={`/api/proxy-video?clipId=${clip.id}`}
                                className="w-full h-full object-contain"
                                controls
                                loop
                            />

                            {/* Opus Clip watermark style */}
                            <div className="absolute top-4 left-4 flex items-center gap-2 bg-black/60 px-3 py-1.5 rounded-full">
                                <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse" />
                                <span className="text-xs font-medium">OpusClip</span>
                            </div>

                            {/* Virality score overlay */}
                            <div className="absolute top-4 right-4 bg-orange-500 text-white px-3 py-1 rounded-full font-bold text-sm">
                                🔥 {clip.virality_score}
                            </div>

                            {/* Fullscreen Toggle Button */}
                            <button
                                onClick={() => setIsVerticalFullScreen(true)}
                                className="absolute bottom-20 right-4 bg-black/60 hover:bg-black/90 p-2 rounded-full text-white transition-all transform hover:scale-110"
                                title="Pantalla Completa Vertical"
                            >
                                <span className="text-xl">📱</span>
                            </button>
                        </div>
                    </div>
                </div>

                {/* Center: Analysis & Transcript */}
                <div className="col-span-5">
                    {/* Tabs */}
                    <div className="flex gap-4 mb-4 border-b border-[#1f1f1f]">
                        <button
                            onClick={() => setTab('analysis')}
                            className={`pb-2 px-1 ${tab === 'analysis'
                                ? 'border-b-2 border-orange-500 text-white'
                                : 'text-gray-400'
                                }`}
                        >
                            Análisis de escena
                        </button>
                        <button
                            onClick={() => setTab('transcript')}
                            className={`pb-2 px-1 flex items-center gap-2 ${tab === 'transcript'
                                ? 'border-b-2 border-orange-500 text-white'
                                : 'text-gray-400'
                                }`}
                        >
                            <span>Solo transcripción</span>
                            <input type="checkbox" className="ml-2" />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="bg-[#111] rounded-lg p-4 h-[400px] overflow-y-auto">
                        {tab === 'analysis' ? (
                            <div className="space-y-4">
                                {/* Time range */}
                                <div className="text-sm text-gray-400 font-mono">
                                    {timeRange}
                                </div>

                                {/* Transcript/Analysis */}
                                <div className="text-sm leading-relaxed">
                                    <p className="mb-4">
                                        {clip.transcript || generateMockTranscript(clip)}
                                    </p>
                                </div>

                                {/* AI Insights */}
                                <div className="mt-6 space-y-3">
                                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
                                        <div className="text-xs text-blue-400 font-semibold mb-1">🎣 GANCHO</div>
                                        <div className="text-sm">{clip.hook_description}</div>
                                    </div>

                                    <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                                        <div className="text-xs text-green-400 font-semibold mb-1">✨ RESOLUCIÓN</div>
                                        <div className="text-sm">{clip.payoff_description}</div>
                                    </div>

                                    <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3">
                                        <div className="text-xs text-purple-400 font-semibold mb-1">📊 POR QUÉ ES VIRAL</div>
                                        <div className="text-sm">{clip.reason}</div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="text-sm leading-relaxed">
                                <p>{clip.transcript || 'Transcripción no disponible'}</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right: Actions */}
                <div className="col-span-3 space-y-3">
                    {/* Publish */}
                    <button
                        onClick={handlePublish}
                        className="w-full bg-blue-600 hover:bg-blue-700 px-4 py-3 rounded-lg font-semibold flex items-center gap-2 transition"
                    >
                        <span className="text-xl">📤</span>
                        <span>Publicar en redes sociales</span>
                    </button>

                    {/* Export XML */}
                    <button
                        onClick={handleExportXML}
                        className="w-full bg-purple-600 hover:bg-purple-700 px-4 py-3 rounded-lg font-semibold flex items-center gap-2 transition"
                    >
                        <span className="text-xl">📄</span>
                        <span>Exportar XML</span>
                    </button>

                    {/* Download HD */}
                    <button
                        onClick={handleDownloadHD}
                        className="w-full bg-orange-600 hover:bg-orange-700 px-4 py-3 rounded-lg font-semibold flex items-center gap-2 transition"
                    >
                        <span className="text-xl">📥</span>
                        <span>Descargar en HD</span>
                    </button>

                    {/* Edit Clip */}
                    <button
                        onClick={() => setShowEditor(true)}
                        className="w-full bg-gray-700 hover:bg-gray-600 px-4 py-3 rounded-lg font-semibold flex items-center justify-between transition"
                    >
                        <div className="flex items-center gap-2">
                            <span className="text-xl">✂️</span>
                            <span>Editar clip</span>
                        </div>
                    </button>

                    {/* Enterprise Features Divider */}
                    <div className="pt-2 pb-1">
                        <div className="text-xs text-gray-500 font-bold uppercase tracking-wider">Funciones Enterprise</div>
                    </div>

                    {/* Add Subtitles */}
                    <button
                        onClick={async () => {
                            await toast.promise(
                                fetch('/api/clips/add-subtitles', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ clipId: clip.id, style: 'tiktok' })
                                }).then(async (res) => {
                                    const data = await res.json();
                                    if (!data.success) throw new Error(data.error || 'Error desconocido');
                                    return data;
                                }),
                                {
                                    loading: 'Generando subtítulos...',
                                    success: (data) => `✅ Subtítulos agregados! (${data.subtitleCount || 0} palabras)`,
                                    error: (err) => `❌ ${err.message}`
                                }
                            );
                        }}
                        className="w-full bg-yellow-600 hover:bg-yellow-700 px-4 py-3 rounded-lg font-semibold flex items-center justify-between transition"
                    >
                        <div className="flex items-center gap-2">
                            <span className="text-xl">📝</span>
                            <span>Añadir Subtítulos</span>
                        </div>
                    </button>

                    {/* Audio Pro */}
                    <button
                        onClick={async () => {
                            await toast.promise(
                                fetch('/api/clips/enhance-audio', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ clipId: clip.id })
                                }).then(async (res) => {
                                    const data = await res.json();
                                    if (!data.success) throw new Error(data.error || 'Error desconocido');
                                    return data;
                                }),
                                {
                                    loading: 'Normalizando audio a -14 LUFS...',
                                    success: '✅ Audio mejorado profesionalmente!',
                                    error: (err) => `❌ ${err.message}`
                                }
                            );
                        }}
                        className="w-full bg-blue-600 hover:bg-blue-700 px-4 py-3 rounded-lg font-semibold flex items-center justify-between transition"
                    >
                        <div className="flex items-center gap-2">
                            <span className="text-xl">🎵</span>
                            <span>Audio Pro (-14 LUFS)</span>
                        </div>
                    </button>

                    {/* Smart Reframe */}
                    <button
                        onClick={async () => {
                            await toast.promise(
                                fetch('/api/clips/apply-smart-crop', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ clipId: clip.id })
                                }).then(async (res) => {
                                    const data = await res.json();
                                    if (!data.success) throw new Error(data.error || 'Error desconocido');
                                    return data;
                                }),
                                {
                                    loading: 'Aplicando recorte inteligente con IA...',
                                    success: '✅ Reencuadre aplicado exitosamente!',
                                    error: (err) => `❌ ${err.message}`
                                }
                            );
                        }}
                        className="w-full bg-purple-600 hover:bg-purple-700 px-4 py-3 rounded-lg font-semibold flex items-center justify-between transition"
                    >
                        <div className="flex items-center gap-2">
                            <span className="text-xl">🎥</span>
                            <span>Auto-Reencuadre AI</span>
                        </div>
                    </button>

                    {/* Clean Speech */}
                    <button
                        onClick={async () => {
                            await toast.promise(
                                fetch('/api/clips/enterprise-action', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ clipId: clip.id, action: 'clean_speech' })
                                }).then(async (res) => {
                                    const data = await res.json();
                                    if (!data.success) throw new Error(data.error || 'Error desconocido');
                                    return data;
                                }),
                                {
                                    loading: 'Eliminando muletillas...',
                                    success: '✅ Muletillas eliminadas!',
                                    error: (err) => `❌ ${err.message}`
                                }
                            );
                        }}
                        className="w-full bg-green-600 hover:bg-green-700 px-4 py-3 rounded-lg font-semibold flex items-center justify-between transition"
                    >
                        <div className="flex items-center gap-2">
                            <span className="text-xl">✂️</span>
                            <span>Limpiar Muletillas</span>
                        </div>
                    </button>

                    {/* Add B-roll */}
                    <button
                        onClick={() => toast('Función B-Roll con IA - En desarrollo 🚧', { icon: '🎬' })}
                        className="w-full bg-gray-700 hover:bg-gray-600 px-4 py-3 rounded-lg font-semibold flex items-center justify-between transition"
                    >
                        <div className="flex items-center gap-2">
                            <span className="text-xl">🎬</span>
                            <span>Añadir B-roll AI</span>
                        </div>
                    </button>

                    {/* Clip Info */}
                    <div className="mt-6 p-4 bg-[#111] rounded-lg space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-gray-400">Duración:</span>
                            <span className="font-semibold">{formatTime(duration)}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-400">Categoría:</span>
                            <span className="font-semibold">{clip.category}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-400">Ranking:</span>
                            <span className="font-semibold">#{clip.rank}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Vertical Full Screen Overlay */}
            {isVerticalFullScreen && (
                <div className="fixed inset-0 z-[100] bg-black/95 backdrop-blur-xl flex items-center justify-center p-4 md:p-8 animate-in fade-in zoom-in duration-300">
                    {/* Close Button */}
                    <button
                        onClick={() => setIsVerticalFullScreen(false)}
                        className="absolute top-6 right-6 z-10 bg-white/10 hover:bg-white/20 p-3 rounded-full text-white transition-all"
                    >
                        <span className="text-2xl">✕</span>
                    </button>

                    {/* Pro Tip Overlay */}
                    <div className="absolute bottom-10 left-10 hidden md:block text-white/40 max-w-xs">
                        <p className="text-sm font-medium">✨ Modo de Visualización Real</p>
                        <p className="text-xs">Así se verá tu clip exactamente en dispositivos móviles.</p>
                    </div>

                    {/* Video Container (9:16 Restricted) */}
                    <div className="relative h-full aspect-[9/16] bg-black shadow-2xl shadow-orange-500/10 rounded-2xl overflow-hidden border border-white/10">
                        <video
                            autoPlay
                            controls
                            loop
                            src={`/api/proxy-video?clipId=${clip.id}`}
                            className="w-full h-full object-cover"
                        />

                        {/* Floating Metadata in Fullscreen */}
                        <div className="absolute top-6 left-6 flex items-center gap-3 bg-black/40 backdrop-blur-md px-4 py-2 rounded-full border border-white/10">
                            <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-pulse" />
                            <span className="text-sm font-bold tracking-tight">{clip.title}</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Download Modal */}
            {showDownloadModal && (
                <DownloadModal
                    clipId={clip.id}
                    clipTitle={clip.title}
                    onClose={() => setShowDownloadModal(false)}
                />
            )}
        </div>
    );
}

function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatTimeRange(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function generateMockTranscript(clip: any): string {
    return `${clip.hook_description} ${clip.payoff_description} Esta es una transcripción de ejemplo generada automáticamente del contenido del clip.`;
}
