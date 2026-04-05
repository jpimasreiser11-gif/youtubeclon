'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Edit, Download, Upload, Loader2, Sparkles, X, Scissors, Crop, Mic2 } from 'lucide-react';
import SubtitleEditor from '@/components/SubtitleEditor';

interface ViralClip {
    id: string;
    rank: number;
    start_time: number;
    end_time: number;
    virality_score: number;
    title: string;
    category: string;
    hook_description: string;
    payoff_description: string;
    duration: number;
    transcription_status?: string;
    transcript_json?: any;
    render_status?: 'idle' | 'processing' | 'completed' | 'failed';
    render_progress?: number;
    render_error?: string;
}

export default function StudioPage() {
    const params = useParams();
    const projectId = params.projectId as string;

    const [clips, setClips] = useState<ViralClip[]>([]);
    const [loading, setLoading] = useState(true);
    const [hoveredClip, setHoveredClip] = useState<string | null>(null);
    const [selectedClip, setSelectedClip] = useState<ViralClip | null>(null);
    const [showDownloadModal, setShowDownloadModal] = useState(false);
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [showSubtitleEditor, setShowSubtitleEditor] = useState(false);
    const [actionLoading, setActionLoading] = useState(false);
    const [notification, setNotification] = useState<{ type: 'success' | 'error', message: string } | null>(null);

    useEffect(() => {
        if (notification) {
            const timer = setTimeout(() => setNotification(null), 5000);
            return () => clearTimeout(timer);
        }
    }, [notification]);

    const handleEnterpriseAction = async (clipId: string, action: string) => {
        setActionLoading(true);
        try {
            const res = await fetch('/api/clips/enterprise-action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ clipId, action })
            });
            const data = await res.json();
            if (res.ok) {
                setNotification({ type: 'success', message: '🚀 IA Iniciada: Mejorando audio, reencuadre y quitando muletillas...' });
            } else {
                setNotification({ type: 'error', message: data.error || 'Error al iniciar acción' });
            }
        } catch (err) {
            setNotification({ type: 'error', message: 'Error de red' });
        } finally {
            setActionLoading(false);
        }
    };

    useEffect(() => {
        if (projectId) {
            fetchClips();
        }
    }, [projectId]);

    // Dynamic Polling for background tasks
    useEffect(() => {
        const needsPolling = clips.some(c => c.render_status === 'processing' || c.transcription_status === 'processing');
        if (needsPolling) {
            const interval = setInterval(fetchClips, 3000);
            return () => clearInterval(interval);
        }
    }, [clips]);

    const fetchClips = async () => {
        try {
            const res = await fetch(`/api/get-job?id=${projectId}`);
            const data = await res.json();

            if (data.clips) {
                const clipsWithDuration = data.clips.map((clip: any) => ({
                    ...clip,
                    duration: Math.round(clip.end_time - clip.start_time)
                }));
                setClips(clipsWithDuration);

                // Update selected clip if it's open to refresh its status
                if (selectedClip) {
                    const updated = clipsWithDuration.find((c: any) => c.id === selectedClip.id);
                    if (updated) setSelectedClip(updated);
                }
            }
            setLoading(false);
        } catch (error) {
            console.error('Error fetching clips:', error);
            setLoading(false);
        }
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const handleEdit = (clip: ViralClip) => {
        setSelectedClip(clip);
    };

    const handleDownload = (clip: ViralClip) => {
        setSelectedClip(clip);
        setShowDownloadModal(true);
    };

    const handleUpload = (clip: ViralClip) => {
        console.log('🟢 Upload button clicked!', clip.title);
        setSelectedClip(clip);
        setShowUploadModal(true);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen bg-black">
                <div className="text-orange-500 text-xl">Cargando Clips...</div>
            </div>
        );
    }

    console.log('📊 Studio Page Loaded - Total Clips:', clips.length);

    return (
        <div className="min-h-screen bg-black text-white p-8">
            {/* Header */}
            <div className="mb-8">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">Clips Originales ({clips.length})</h1>
                        <p className="text-gray-400">Selecciona un clip para editar, descargar o publicar</p>
                    </div>
                    <div className="flex gap-3">
                        <button className="px-4 py-2 bg-[#1a1a1a] hover:bg-[#2a2a2a] rounded-lg transition">
                            Filtrar
                        </button>
                        <button className="px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded-lg font-semibold transition">
                            Descargar Todos
                        </button>
                    </div>
                </div>
            </div>

            {/* Clips Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                {clips.map((clip) => (
                    <div
                        key={clip.id}
                        className="group cursor-pointer"
                        onMouseEnter={() => setHoveredClip(clip.id)}
                        onMouseLeave={() => setHoveredClip(null)}
                    >
                        {/* Thumbnail Container */}
                        <div className="relative aspect-[9/16] bg-[#0a0a0a] rounded-lg overflow-hidden border border-[#1f1f1f] hover:border-orange-500 transition-all">
                            {/* Video Thumbnail */}
                            <video
                                src={`/api/proxy-video?clipId=${clip.id}`}
                                className="w-full h-full object-cover"
                                preload="metadata"
                                muted
                                loop
                                playsInline
                                onMouseEnter={(e) => {
                                    const video = e.currentTarget as HTMLVideoElement;
                                    video.play().catch(() => { });
                                }}
                                onMouseLeave={(e) => {
                                    const video = e.currentTarget as HTMLVideoElement;
                                    video.pause();
                                    video.currentTime = 0;
                                }}
                            />

                            {/* Duration Badge */}
                            <div className="absolute top-2 right-2 bg-black/90 px-2 py-1 rounded text-xs font-semibold">
                                {formatTime(clip.duration)}
                            </div>

                            {/* Virality Score Badge */}
                            {(() => {
                                const score = clip.virality_score || 0;
                                let bgClass = "bg-green-600/90 text-white";
                                let icon = "🟢";
                                let shadow = "";
                                if (score >= 90) {
                                    bgClass = "bg-gradient-to-r from-yellow-400 to-yellow-600 text-black border border-yellow-300";
                                    icon = "👑";
                                    shadow = "shadow-[0_0_15px_rgba(250,204,21,0.5)]";
                                } else if (score >= 80) {
                                    bgClass = "bg-orange-600/90 text-white";
                                    icon = "🔥";
                                }
                                return (
                                    <div className={`absolute top-2 left-2 ${bgClass} px-2 py-1 rounded text-xs font-bold flex items-center gap-1 ${shadow}`}>
                                        {icon} {score}
                                    </div>
                                );
                            })()}

                            {/* Tier Badge */}
                            {clip.virality_score >= 90 && (
                                <div className="absolute top-12 left-2 bg-gradient-to-r from-yellow-600 to-yellow-400 text-black px-2 py-0.5 rounded text-xs font-black border border-yellow-300 shadow-md">
                                    TIER S
                                </div>
                            )}
                            {clip.virality_score >= 80 && clip.virality_score < 90 && (
                                <div className="absolute top-12 left-2 bg-white text-black px-2 py-0.5 rounded text-xs font-bold shadow-sm">
                                    TIER A
                                </div>
                            )}

                            {/* Rendering Progress Overlay */}
                            {clip.render_status === 'processing' && (
                                <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center p-4 z-10">
                                    <Loader2 className="w-8 h-8 text-orange-500 animate-spin mb-3" />
                                    <div className="text-xs font-bold text-center mb-2">Renderizando Subtítulos...</div>
                                    <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
                                        <div
                                            className="bg-orange-500 h-full transition-all duration-500"
                                            style={{ width: `${clip.render_progress || 0}%` }}
                                        ></div>
                                    </div>
                                    <div className="text-[10px] text-gray-400 mt-1">{clip.render_progress || 0}%</div>
                                </div>
                            )}

                            {/* Hover Overlay */}
                            {hoveredClip === clip.id && (
                                <div className="absolute inset-0 bg-black/70 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                    <div className="flex gap-2">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleEdit(clip);
                                            }}
                                            className="p-3 bg-blue-600 hover:bg-blue-700 rounded-full transition"
                                            title="Editar clip"
                                        >
                                            <Edit className="w-5 h-5" />
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDownload(clip);
                                            }}
                                            className="p-3 bg-orange-600 hover:bg-orange-700 rounded-full transition"
                                            title="Descargar"
                                        >
                                            <Download className="w-5 h-5" />
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleUpload(clip);
                                            }}
                                            className="p-3 bg-green-600 hover:bg-green-700 rounded-full transition"
                                            title="Subir a redes"
                                        >
                                            <Upload className="w-5 h-5" />
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Clip Info */}
                        <div className="mt-3 px-1">
                            <h3 className="font-semibold text-sm mb-1 line-clamp-2 leading-tight">
                                {clip.title}
                            </h3>
                            <p className="text-xs text-gray-400 mb-2 line-clamp-2">
                                {clip.hook_description}
                            </p>
                            <div className="flex items-center justify-between text-xs text-gray-500">
                                <span className="line-clamp-1">{clip.category}</span>
                                <span>Clip #{clip.rank}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Empty State */}
            {clips.length === 0 && (
                <div className="flex flex-col items-center justify-center h-64 text-gray-400">
                    <div className="text-6xl mb-4">🎬</div>
                    <p className="text-xl font-semibold mb-2">No hay clips disponibles</p>
                    <p className="text-sm">Los clips aparecerán aquí una vez que el proyecto sea procesado</p>
                </div>
            )}

            {/* Modals */}
            {selectedClip && showDownloadModal && (
                <DownloadModal
                    clipId={selectedClip.id}
                    clipTitle={selectedClip.title}
                    onClose={() => {
                        setShowDownloadModal(false);
                        setSelectedClip(null);
                    }}
                />
            )}

            {selectedClip && showUploadModal && (
                <UploadModal
                    clip={selectedClip}
                    onClose={() => {
                        setShowUploadModal(false);
                        setSelectedClip(null);
                    }}
                />
            )}

            {selectedClip && !showDownloadModal && !showUploadModal && (
                <ClipViewerModal
                    clip={selectedClip}
                    onClose={() => setSelectedClip(null)}
                    actionLoading={actionLoading}
                    handleEnterpriseAction={handleEnterpriseAction}
                    onRefresh={fetchClips}
                />
            )}

            {/* Notification Toast */}
            {notification && (
                <div className={`fixed bottom-8 right-8 z-[100] p-4 rounded-xl shadow-2xl border flex items-center gap-3 animate-slide-up ${notification.type === 'success' ? 'bg-green-600/20 border-green-500 text-green-400' : 'bg-red-600/20 border-red-500 text-red-400'
                    }`}>
                    <Sparkles className="w-5 h-5" />
                    <span className="font-bold">{notification.message}</span>
                </div>
            )}
        </div>
    );
}

// Download Modal Component
function DownloadModal({ clipId, clipTitle, onClose }: { clipId: string; clipTitle: string; onClose: () => void }) {
    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-[#0a0a0a] border border-[#2a2a2a] rounded-lg p-6 max-w-md w-full">
                <h3 className="text-xl font-bold mb-4">Descargar Clip</h3>
                <p className="text-gray-400 mb-4">{clipTitle}</p>
                <div className="flex gap-3">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-2 bg-[#1a1a1a] hover:bg-[#2a2a2a] rounded-lg transition"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={() => {
                            // Use download API
                            window.open(`/api/clips/download?clipId=${clipId}&format=original`, '_blank');
                            onClose();
                        }}
                        className="flex-1 px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded-lg transition"
                    >
                        Descargar
                    </button>
                </div>
            </div>
        </div>
    );
}

// Upload Modal Component
function UploadModal({ clip, onClose }: { clip: ViralClip; onClose: () => void }) {
    const [uploading, setUploading] = useState(false);
    const [platform, setPlatform] = useState<string | null>(null);
    const [scheduleAt, setScheduleAt] = useState('');
    const [connections, setConnections] = useState<any[]>([]);

    useEffect(() => {
        const checkStatus = async () => {
            const res = await fetch('/api/connections/status');
            const data = await res.json();
            if (data.connections) setConnections(data.connections);
        };
        checkStatus();
    }, []);

    const isConnected = (p: string) => connections.find(c => c.platform === p)?.connected;

    const handleUpload = async (selectedPlatform: string) => {
        if (!isConnected(selectedPlatform)) {
            alert(`⚠️ ${selectedPlatform.toUpperCase()} no está conectado. Ve a la página de Conexiones.`);
            return;
        }

        setPlatform(selectedPlatform);
        setUploading(true);

        try {
            const response = await fetch('/api/clips/publish', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    clipId: clip.id,
                    platform: selectedPlatform,
                    scheduleAt: scheduleAt || null
                })
            });

            const data = await response.json();
            if (response.ok) {
                alert(data.message || `✅ Publicación programada en ${selectedPlatform}`);
                onClose();
            } else {
                alert(data.error || 'Error al programar publicación');
            }
        } catch (error) {
            console.error('Upload error:', error);
            alert('Error de conexión');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-[#0a0a0a] border border-[#2a2a2a] rounded-lg p-6 max-w-md w-full shadow-2xl">
                <h3 className="text-xl font-bold mb-4">Publicar Clip</h3>
                <p className="text-gray-400 mb-6 text-sm">Selecciona una plataforma y (opcionalmente) una fecha para programar.</p>

                <div className="mb-6 space-y-2">
                    <label className="text-xs text-gray-500 uppercase font-bold">Programar para (Opcional)</label>
                    <input
                        type="datetime-local"
                        value={scheduleAt}
                        onChange={(e) => setScheduleAt(e.target.value)}
                        className="w-full bg-[#111] border border-[#222] rounded-lg px-4 py-2 text-white text-sm outline-none focus:border-orange-500 transition-colors"
                    />
                </div>

                <div className="space-y-3 mb-6">
                    <button
                        onClick={() => handleUpload('youtube')}
                        disabled={uploading}
                        className={`w-full px-4 py-3 rounded-lg flex items-center gap-3 transition ${isConnected('youtube') ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-800 opacity-50 cursor-not-allowed'
                            }`}
                    >
                        <span className="text-2xl">📺</span>
                        <div className="text-left">
                            <div className="font-bold">YouTube Shorts</div>
                            <div className="text-[10px] opacity-70">{isConnected('youtube') ? 'CONECTADO' : 'NO CONECTADO'}</div>
                        </div>
                        {uploading && platform === 'youtube' && <Loader2 className="w-4 h-4 animate-spin ml-auto" />}
                    </button>
                    <button
                        onClick={() => handleUpload('tiktok')}
                        disabled={uploading}
                        className={`w-full px-4 py-3 rounded-lg flex items-center gap-3 transition ${isConnected('tiktok') ? 'bg-black border border-white/20 hover:bg-gray-900' : 'bg-gray-800 opacity-50 cursor-not-allowed'
                            }`}
                    >
                        <span className="text-2xl">🎵</span>
                        <div className="text-left">
                            <div className="font-bold">TikTok</div>
                            <div className="text-[10px] opacity-70">{isConnected('tiktok') ? 'CONECTADO' : 'NO CONECTADO'}</div>
                        </div>
                        {uploading && platform === 'tiktok' && <Loader2 className="w-4 h-4 animate-spin ml-auto" />}
                    </button>
                    {/* Instagram Placeholder */}
                    <button
                        disabled={true}
                        className="w-full px-4 py-3 bg-gray-800 opacity-30 rounded-lg flex items-center gap-3 cursor-not-allowed"
                    >
                        <span className="text-2xl">📱</span>
                        <div className="text-left">
                            <div className="font-bold">Instagram Reels</div>
                            <div className="text-[10px] opacity-70">PRÓXIMAMENTE</div>
                        </div>
                    </button>
                </div>
                <button
                    onClick={onClose}
                    disabled={uploading}
                    className="w-full px-4 py-2 bg-[#1a1a1a] hover:bg-[#2a2a2a] disabled:bg-gray-600 rounded-lg transition text-sm font-medium"
                >
                    Cancelar
                </button>
            </div>
        </div>
    );
}

// Clip Viewer Modal Component - Full Editor
function ClipViewerModal({ clip, onClose, actionLoading, handleEnterpriseAction, onRefresh }: {
    clip: ViralClip;
    onClose: () => void;
    actionLoading: boolean;
    handleEnterpriseAction: (clipId: string, action: string) => Promise<void>;
    onRefresh: () => void;
}) {
    const [showSubtitles, setShowSubtitles] = useState(false);
    const [aspectRatio, setAspectRatio] = useState('9:16');
    const [transcription, setTranscription] = useState<any[]>([]);
    const [tStatus, setTStatus] = useState<string>(clip.transcription_status || 'idle');
    const [selectedStyle, setSelectedStyle] = useState('hormozi');

    const formatTimestamp = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    // Fetch transcription on mount
    useEffect(() => {
        if (clip.transcript_json) {
            try {
                const words = typeof clip.transcript_json === 'string'
                    ? JSON.parse(clip.transcript_json)
                    : clip.transcript_json;

                if (Array.isArray(words)) setTranscription(words);
            } catch (e) {
                console.error("Error parsing transcript:", e);
                setTranscription([]);
            }
        } else {
            setTranscription([]);
        }
    }, [clip]);


    const handlePublish = () => {
        // Close editor and let parent handle upload modal
        alert('Para publicar, usa el botón verde "Subir" en la galería de clips');
        onClose();
    };

    const handleExportXML = async () => {
        try {
            const response = await fetch(`/api/clips/export-xml?clipId=${clip.id}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${clip.title || 'clip'}.xml`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }
        } catch (error) {
            console.error('Error exporting XML:', error);
            alert('Error al exportar XML. Verifica la consola.');
        }
    };

    const handleDownloadHD = () => {
        window.open(`/api/clips/download?clipId=${clip.id}&format=original`, '_blank');
    };

    const handleTranscribe = async () => {
        console.log('[DEBUG] Starting transcription for clip:', clip.id);
        console.log('[DEBUG] Full clip object:', clip);

        setTStatus('processing');
        try {
            const response = await fetch(`/api/clips/${clip.id}/transcribe`, {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok) {
                alert('⏳ Transcripción iniciada. Los subtítulos estarán listos en unos momentos.');
                if (onRefresh) onRefresh();
            } else {
                setTStatus('error');
                const errorMsg = data.error || data.message || 'Error desconocido';
                alert(`❌ Error al iniciar transcripción: ${errorMsg}`);
                console.error('Transcription API error:', data);
            }
        } catch (error) {
            setTStatus('error');
            console.error('Error starting transcription:', error);
            alert(`❌ Error de red: ${error instanceof Error ? error.message : 'Error desconocido'}`);
        }
    };

    const [sLoading, setSLoading] = useState(false);

    const handleAddSubtitles = async () => {
        setSLoading(true);
        try {
            const response = await fetch('/api/clips/add-subtitles', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ clipId: clip.id, style: selectedStyle })
            });
            const data = await response.json();

            if (response.ok) {
                if (data.isBackground) {
                    alert('⏳ El renderizado ha comenzado en segundo plano.\n\nRecibirás una notificación o podrás ver el clip actualizado en unos minutos.');
                    if (onRefresh) onRefresh();
                } else {
                    alert('✅ Subtítulos añadidos correctamente con estilo ' + selectedStyle.toUpperCase());
                }
            } else {
                alert(`❌ Error: ${data.error || 'No se pudieron añadir subtítulos'}`);
            }
        } catch (error) {
            console.error('Error adding subtitles:', error);
            alert('Error al añadir subtítulos');
        } finally {
            setSLoading(false);
        }
    };

    const handleAddBRoll = () => {
        alert('Función B-roll disponible próximamente');
    };

    const handleChangeAspectRatio = (ratio: string) => {
        setAspectRatio(ratio);
        // Esta función requeriría re-procesamiento del video
        alert(`Formato ${ratio} seleccionado. Re-procesamiento disponible próximamente.`);
    };

    return (
        <div className="fixed inset-0 bg-black/95 z-50 overflow-hidden">
            <div className="h-full flex flex-col">
                {/* Header */}
                <div className="bg-[#0a0a0a] border-b border-[#1f1f1f] px-6 py-4 flex items-center justify-between">
                    <h1 className="text-xl font-bold">{clip.title}</h1>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white text-2xl px-4 py-2 hover:bg-[#1a1a1a] rounded-lg transition"
                    >
                        ✕
                    </button>
                </div>

                {/* Main Content */}
                <div className="flex-1 grid grid-cols-12 gap-6 p-6 min-h-0 overflow-hidden" style={{ gridTemplateRows: 'minmax(0, 1fr)' }}>
                    {/* Left: Video Preview */}
                    <div className="col-span-3 flex flex-col gap-4 overflow-y-auto h-full pr-2">
                        <div className="bg-[#111] rounded-lg p-4 border border-[#1f1f1f]">
                            <div className="text-xs text-gray-400 mb-2 uppercase">Vista previa de baja resolución</div>
                            <div className="aspect-[9/16] bg-black rounded-lg overflow-hidden">
                                <video
                                    src={`/api/proxy-video?clipId=${clip.id}`}
                                    controls
                                    className="w-full h-full object-contain"
                                />
                            </div>
                            <div className="mt-3 flex items-center justify-between text-sm">
                                <span className="text-gray-400">{formatTimestamp(clip.start_time)} - {formatTimestamp(clip.end_time)}</span>
                                <span className="text-orange-500 font-bold">🔥 {clip.virality_score}</span>
                            </div>
                        </div>
                    </div>

                    {/* Center: Scene Analysis & Transcription */}
                    <div className="col-span-6 flex flex-col gap-4 overflow-y-auto h-full pr-2">
                        <div className="bg-[#111] rounded-lg p-6 border border-[#1f1f1f] flex-1 overflow-y-auto">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold">Análisis de escena</h2>
                                <label className="flex items-center gap-2 text-sm text-gray-400">
                                    <input type="checkbox" className="rounded" />
                                    Solo transcripción
                                </label>
                            </div>

                            {/* Scene Description */}
                            <div className="mb-6">
                                <p className="text-gray-300 leading-relaxed">
                                    {clip.hook_description} {clip.payoff_description}
                                </p>
                            </div>

                            {/* Transcription with Timestamps */}
                            <div className="space-y-3">
                                <h3 className="text-sm font-semibold text-gray-400 uppercase mb-3 text-orange-400">Transcripción Completa ({transcription.length} palabras)</h3>

                                <div className="space-y-4">
                                    {transcription.length > 0 ? (
                                        // Group words into chunks for better readability
                                        Array.from({ length: Math.ceil(transcription.length / 15) }).map((_, i) => {
                                            const chunk = transcription.slice(i * 15, (i + 1) * 15);
                                            const startTime = chunk[0].start;
                                            return (
                                                <div key={i} className="flex gap-4 p-2 hover:bg-[#1a1a1a] rounded transition">
                                                    <span className="text-gray-500 text-xs font-mono pt-1 select-none">
                                                        {formatTimestamp(startTime + clip.start_time)}
                                                    </span>
                                                    <p className="text-gray-200 text-sm flex-1 leading-relaxed">
                                                        {chunk.map((w: any, idx: number) => (
                                                            <span key={idx} title={`Conf: ${Math.round(w.confidence * 100)}%`} className="hover:text-white cursor-pointer">
                                                                {w.word}{' '}
                                                            </span>
                                                        ))}
                                                    </p>
                                                </div>
                                            );
                                        })
                                    ) : (
                                        <div className="text-center py-10 text-gray-500">
                                            <p>No hay transcripción detallada disponible.</p>
                                            <p className="text-xs mt-2">Prueba a regenerar el clip para obtener datos de palabras.</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right: Actions */}
                    <div className="col-span-3 flex flex-col gap-3 overflow-y-auto h-full pr-2">
                        <button
                            onClick={handlePublish}
                            className="w-full px-4 py-3 bg-red-600 hover:bg-red-700 rounded-lg font-semibold flex items-center gap-3 transition"
                        >
                            <span className="text-xl">📱</span>
                            Publicar en redes sociales
                        </button>

                        <button
                            onClick={handleExportXML}
                            className="w-full px-4 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold flex items-center gap-3 transition"
                        >
                            <span className="text-xl">📋</span>
                            Exportar XML
                        </button>

                        <div className="bg-[#111] rounded-lg p-4 border border-[#1f1f1f] space-y-4">
                            <h3 className="text-sm font-semibold text-gray-400 uppercase">Subtitles & IA</h3>

                            <div className="space-y-2">
                                <label className="text-xs text-gray-500 block">Estilo de Subtítulos</label>
                                <select
                                    value={selectedStyle}
                                    onChange={(e) => setSelectedStyle(e.target.value)}
                                    className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded px-3 py-2 text-sm text-white"
                                >
                                    <option value="hormozi">Hormozi (Viral Highlighting)</option>
                                    <option value="tiktok">TikTok (Yellow Caps)</option>
                                    <option value="minimal">Minimalist (White)</option>
                                    <option value="clean">🚫 Sin Subtítulos (Clean)</option>
                                    <option value="default">Classic</option>
                                </select>
                            </div>

                            <button
                                onClick={handleAddSubtitles}
                                disabled={sLoading || clip.render_status === 'processing'}
                                className={`w-full px-4 py-3 ${sLoading || clip.render_status === 'processing' ? 'bg-indigo-900' : 'bg-indigo-600 hover:bg-indigo-700'} rounded-lg font-semibold flex items-center gap-3 transition`}
                            >
                                <span className="text-xl">
                                    {sLoading || clip.render_status === 'processing' ? <Loader2 className="w-5 h-5 animate-spin" /> : '💬'}
                                </span>
                                {clip.render_status === 'processing' ? `Renderizando... ${clip.render_progress}%` : sLoading ? 'Iniciando...' : 'Aplicar Subtítulos'}
                            </button>

                            <button
                                onClick={handleTranscribe}
                                disabled={tStatus === 'processing'}
                                className={`w-full px-4 py-3 ${tStatus === 'processing' ? 'bg-gray-700' : 'bg-emerald-600 hover:bg-emerald-700'} rounded-lg font-semibold flex items-center gap-3 transition`}
                            >
                                <span className="text-xl">{tStatus === 'processing' ? '⏳' : '🎙️'}</span>
                                {tStatus === 'processing' ? 'Transcribiendo...' : 'Generar Transcripción de IA'}
                            </button>
                        </div>

                        <div className="border-t border-[#2a2a2a] my-2"></div>

                        <button
                            onClick={() => handleEnterpriseAction(clip.id, 'pro-edit')}
                            disabled={actionLoading}
                            className={`w-full px-4 py-3 ${actionLoading ? 'bg-blue-900' : 'bg-blue-600 hover:bg-blue-700'} rounded-lg font-semibold flex items-center justify-between transition`}
                        >
                            <div className="flex items-center gap-3">
                                {actionLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <span className="text-xl">✂️</span>}
                                <span>{actionLoading ? 'Procesando...' : 'Editar clip (IA Pro)'}</span>
                            </div>
                            <span className="text-xs bg-white text-black px-2 py-1 rounded">Pro</span>
                        </button>

                        <button
                            onClick={() => alert('Gancho de IA - Próximamente')}
                            className="w-full px-4 py-3 bg-[#1a1a1a] hover:bg-[#2a2a2a] rounded-lg font-semibold flex items-center justify-between transition"
                        >
                            <div className="flex items-center gap-3">
                                <span className="text-xl">🔥</span>
                                <span>Gancho de IA</span>
                            </div>
                            <span className="text-xs bg-white text-black px-2 py-1 rounded">Pro</span>
                        </button>

                        <button
                            onClick={handleAddBRoll}
                            className="w-full px-4 py-3 bg-[#1a1a1a] hover:bg-[#2a2a2a] rounded-lg font-semibold flex items-center justify-between transition"
                        >
                            <div className="flex items-center gap-3">
                                <span className="text-xl">🎬</span>
                                <span>Añadir B-roll</span>
                            </div>
                            <span className="text-xs bg-white text-black px-2 py-1 rounded">Pro</span>
                        </button>

                        <button
                            onClick={() => handleChangeAspectRatio(aspectRatio === '9:16' ? '16:9' : '9:16')}
                            className="w-full px-4 py-3 bg-[#1a1a1a] hover:bg-[#2a2a2a] rounded-lg font-semibold flex items-center justify-between transition"
                        >
                            <div className="flex items-center gap-3">
                                <span className="text-xl">📐</span>
                                <span>{aspectRatio}</span>
                            </div>
                            <span className="text-xs bg-white text-black px-2 py-1 rounded">Pro</span>
                        </button>

                        <div className="mt-auto pt-4">
                            <div className="bg-[#111] rounded-lg p-4 border border-[#1f1f1f]">
                                <div className="text-xs text-gray-500 mb-2">Categoría</div>
                                <div className="text-sm font-semibold">{clip.category}</div>
                                <div className="text-xs text-gray-500 mt-3 mb-1">Rango viral</div>
                                <div className="flex items-center gap-2">
                                    <div className="flex-1 bg-[#0a0a0a] rounded-full h-2">
                                        <div
                                            className="bg-orange-500 h-2 rounded-full"
                                            style={{ width: `${clip.virality_score}%` }}
                                        ></div>
                                    </div>
                                    <span className="text-sm font-bold text-orange-500">{clip.virality_score}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
