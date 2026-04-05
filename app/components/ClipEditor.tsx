'use client';

import { useState, useRef, useEffect } from 'react';

import { Play, Pause, Save, Scissors, Sparkles, Languages, Maximize2 } from 'lucide-react';
import SubtitleEditor from './SubtitleEditor';

interface ClipEditorProps {
    clip: {
        id: string;
        project_id: string;
        start_time: number;
        end_time: number;
        title: string;
        virality_score: number;
        category: string;
    };
    videoDuration: number;
    words?: Array<{ word: string, start: number, end: number }>;
}

export default function ClipEditor({ clip, videoDuration, words }: ClipEditorProps) {
    const [startTime, setStartTime] = useState(clip.start_time);
    const [endTime, setEndTime] = useState(clip.end_time);
    const [currentTime, setCurrentTime] = useState(clip.start_time);
    const [playing, setPlaying] = useState(false);
    const [showSubtitleModal, setShowSubtitleModal] = useState(false);
    const [saving, setSaving] = useState(false);

    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
        if (videoRef.current) {
            videoRef.current.currentTime = startTime;
        }
    }, [startTime]);

    const handleTimeUpdate = () => {
        const video = videoRef.current;
        if (!video) return;

        const current = video.currentTime;
        setCurrentTime(current);

        // Loop dentro del rango del clip
        if (current >= endTime) {
            video.currentTime = startTime;
            if (!playing) {
                video.pause();
            }
        }
    };

    const handlePlayPause = () => {
        const video = videoRef.current;
        if (!video) return;

        if (playing) {
            video.pause();
        } else {
            video.currentTime = Math.max(startTime, video.currentTime);
            video.play();
        }
        setPlaying(!playing);
    };

    const handleSetStartHere = () => {
        const video = videoRef.current;
        if (!video) return;

        const newStart = video.currentTime;
        if (newStart < endTime - 30) {  // Mínimo 30 segundos
            setStartTime(newStart);
        } else {
            alert('El clip debe tener al menos 30 segundos de duración');
        }
    };

    const handleSetEndHere = () => {
        const video = videoRef.current;
        if (!video) return;

        const newEnd = video.currentTime;
        if (newEnd > startTime + 30 && newEnd <= videoDuration) {
            setEndTime(newEnd);
        } else {
            alert('El clip debe tener al menos 30 segundos de duración');
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const response = await fetch('/api/clips/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    clipId: clip.id,
                    newStart: startTime,
                    newEnd: endTime
                })
            });

            if (response.ok) {
                alert('Clip actualizado. Regenerando video...');
                // Trigger regeneration
                await fetch('/api/clips/regenerate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ clipId: clip.id })
                });

                window.location.reload(); // Recargar para ver el nuevo clip
            }
        } catch (error) {
            console.error('Error saving clip:', error);
            alert('Error al guardar los cambios');
        } finally {
            setSaving(false);
        }
    };

    const handleSmartCrop = async () => {
        setSaving(true);
        try {
            const response = await fetch('/api/clips/apply-smart-crop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ clipId: clip.id })
            });

            if (response.ok) {
                alert('Auto-Reencuadre completado con éxito.');
                window.location.reload();
            } else {
                const err = await response.json();
                alert('Error al aplicar el reencuadre AI: ' + (err.error || 'N/A'));
            }
        } catch (error) {
            console.error('Error in Smart Crop:', error);
            alert('Error de conexión');
        } finally {
            setSaving(false);
        }
    };

    const duration = endTime - startTime;
    const timelineProgress = ((currentTime - startTime) / duration) * 100;

    return (
        <div className="h-full flex flex-col bg-black text-white">
            {/* Header */}
            <div className="p-6 border-b border-[#1f1f1f]">
                <div className="flex items-center justify-between mb-2">
                    <h1 className="text-2xl font-bold">{clip.title}</h1>
                    <div className="flex items-center gap-2">
                        <span className="text-3xl">🔥</span>
                        <span className="text-3xl font-bold text-orange-500">{clip.virality_score}</span>
                    </div>
                </div>
                <div className="flex gap-4 text-sm text-gray-400">
                    <span>{clip.category}</span>
                    <span>•</span>
                    <span>{formatTime(duration)}</span>
                </div>
            </div>

            {/* Video Player */}
            <div className="flex-1 bg-gray-900 flex items-center justify-center p-4 relative group">
                <video
                    ref={videoRef}
                    src={`/storage/source/${clip.project_id}.mp4`}
                    className="max-h-full max-w-full object-contain"
                    onTimeUpdate={handleTimeUpdate}
                    onPlay={() => setPlaying(true)}
                    onPause={() => setPlaying(false)}
                />

                {/* [NEW] Pillar 3: High-Fidelity Subtitle Layer */}
                <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                    <div className="w-full max-w-md text-center px-4">
                        {words?.map((w, idx) => {
                            const isVisible = currentTime >= w.start && currentTime <= w.end;
                            if (!isVisible) return null;
                            return (
                                <span
                                    key={idx}
                                    className="text-4xl font-black uppercase italic text-yellow-400 drop-shadow-[0_4px_4px_rgba(0,0,0,0.8)]"
                                    style={{
                                        WebkitTextStroke: '2px black',
                                        fontFamily: 'Impact, sans-serif'
                                    }}
                                >
                                    {w.word}
                                </span>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Timeline */}
            <div className="p-6 bg-[#0a0a0a] border-t border-[#1f1f1f]">
                <div className="mb-4">
                    <div className="flex justify-between text-sm text-gray-400 mb-2">
                        <span>Inicio: {formatTime(startTime)}</span>
                        <span>Actual: {formatTime(currentTime)}</span>
                        <span>Fin: {formatTime(endTime)}</span>
                    </div>

                    {/* Timeline Track */}
                    <div className="relative h-16 bg-[#1a1a1a] rounded-lg overflow-hidden">
                        {/* Full video representation */}
                        <div className="absolute inset-0">
                            {/* Clip region */}
                            <div
                                className="absolute top-0 bottom-0 bg-orange-500/30"
                                style={{
                                    left: `${(startTime / videoDuration) * 100}%`,
                                    right: `${100 - (endTime / videoDuration) * 100}%`
                                }}
                            >
                                {/* Progress indicator */}
                                <div
                                    className="absolute top-0 bottom-0 w-1 bg-orange-500"
                                    style={{ left: `${timelineProgress}%` }}
                                />

                                {/* Start handle */}
                                <div
                                    className="absolute top-0 bottom-0 w-2 bg-blue-500 cursor-ew-resize hover:bg-blue-400 left-0"
                                    onMouseDown={(e) => handleDragStart(e, 'start')}
                                />

                                {/* End handle */}
                                <div
                                    className="absolute top-0 bottom-0 w-2 bg-blue-500 cursor-ew-resize hover:bg-blue-400 right-0"
                                    onMouseDown={(e) => handleDragStart(e, 'end')}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Controls */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                    <button
                        onClick={handlePlayPause}
                        className="bg-orange-600 hover:bg-orange-700 px-4 py-3 rounded-lg font-semibold transition"
                    >
                        {playing ? '⏸ Pausar' : '▶ Reproducir'}
                    </button>

                    <button
                        onClick={() => videoRef.current && (videoRef.current.currentTime = startTime)}
                        className="bg-gray-700 hover:bg-gray-600 px-4 py-3 rounded-lg font-semibold transition"
                    >
                        ⏮ Ir al Inicio
                    </button>
                </div>

                {/* Editing Controls */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                    <button
                        onClick={handleSetStartHere}
                        className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-sm font-semibold transition"
                    >
                        📍 Marcar Inicio Aquí
                    </button>

                    <button
                        onClick={handleSetEndHere}
                        className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-sm font-semibold transition"
                    >
                        📍 Marcar Fin Aquí
                    </button>

                    <button
                        onClick={() => setShowSubtitleModal(true)}
                        className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded text-sm font-semibold transition flex items-center justify-center gap-2"
                    >
                        <Languages size={16} /> Subtítulos
                    </button>

                    <button
                        onClick={handleSmartCrop}
                        disabled={saving}
                        className="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded text-sm font-semibold transition flex items-center justify-center gap-2"
                    >
                        <Sparkles size={16} /> Reencuadre AI
                    </button>
                </div>

                {/* Save Button */}
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className={`w-full py-3 rounded-lg font-bold text-lg transition ${saving
                        ? 'bg-gray-600 cursor-not-allowed'
                        : 'bg-green-600 hover:bg-green-700'
                        }`}
                >
                    {saving ? 'Guardando...' : '💾 Guardar Cambios y Regenerar Clip'}
                </button>
            </div>

            {/* Subtitle Modal (Enterprise Precision Update) */}
            {showSubtitleModal && (
                <SubtitleEditor
                    clipId={clip.id}
                    videoSrc={`/storage/source/${clip.project_id}.mp4`}
                    onClose={() => setShowSubtitleModal(false)}
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

// Placeholder for drag handlers (can be implemented with mouse events)
function handleDragStart(e: React.MouseEvent, handle: 'start' | 'end') {
    // Implement drag logic here
    console.log(`Dragging ${handle} handle`);
}
