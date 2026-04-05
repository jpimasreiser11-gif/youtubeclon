'use client';

import { useState, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';

interface ScheduledEvent {
    id: string;
    title: string;
    start: string;
    end: string;
    backgroundColor: string;
    extendedProps: {
        clipId: string;
        platform: string;
        status: string;
    };
}

interface AvailableClip {
    id: string;
    title: string;
    virality_score: number;
    category: string;
    duration: number;
}

export default function CalendarPage() {
    const [events, setEvents] = useState<ScheduledEvent[]>([]);
    const [availableClips, setAvailableClips] = useState<AvailableClip[]>([]);
    const [selectedClip, setSelectedClip] = useState<AvailableClip | null>(null);
    const [showScheduleModal, setShowScheduleModal] = useState(false);
    const [scheduleDate, setScheduleDate] = useState('');

    useEffect(() => {
        fetchScheduledEvents();
        fetchAvailableClips();
    }, []);

    const fetchScheduledEvents = async () => {
        try {
            const res = await fetch('/api/scheduled-publications');
            const data = await res.json();

            if (data.events) {
                const formattedEvents = data.events.map((e: any) => ({
                    id: e.id,
                    title: e.title,
                    start: e.scheduled_at,
                    backgroundColor: e.platform === 'youtube' ? '#FF0000' : '#000000',
                    extendedProps: {
                        clipId: e.clip_id,
                        platform: e.platform,
                        status: e.status
                    }
                }));
                setEvents(formattedEvents);
            }
        } catch (error) {
            console.error('Error fetching events:', error);
        }
    };

    const fetchAvailableClips = async () => {
        try {
            // Fetch all completed projects and their clips
            const res = await fetch('/api/clips/available');
            const data = await res.json();

            if (data.clips) {
                setAvailableClips(data.clips);
            }
        } catch (error) {
            console.error('Error fetching clips:', error);
        }
    };

    const handleDateClick = (info: any) => {
        setScheduleDate(info.dateStr);
        setShowScheduleModal(true);
    };

    const handleSchedule = async (platform: 'youtube' | 'tiktok') => {
        if (!selectedClip || !scheduleDate) return;

        try {
            await fetch('/api/schedule-publication', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    clipId: selectedClip.id,
                    platform,
                    scheduledAt: scheduleDate,
                    title: selectedClip.title
                })
            });

            alert('Publicación programada exitosamente!');
            setShowScheduleModal(false);
            fetchScheduledEvents();
        } catch (error) {
            alert('Error al programar publicación');
        }
    };

    return (
        <div className="min-h-screen bg-black text-white p-8">
            <div className="max-w-7xl mx-auto">
                <h1 className="text-4xl font-bold mb-8">Calendario de Publicaciones</h1>

                <div className="grid grid-cols-12 gap-6">
                    {/* Sidebar: Clips disponibles */}
                    <div className="col-span-3">
                        <div className="bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg p-4">
                            <h3 className="font-bold mb-4">📚 Clips Disponibles</h3>

                            <div className="space-y-2 max-h-[600px] overflow-y-auto">
                                {availableClips.length === 0 ? (
                                    <p className="text-sm text-gray-400">No hay clips disponibles</p>
                                ) : (
                                    availableClips.map((clip) => (
                                        <div
                                            key={clip.id}
                                            onClick={() => setSelectedClip(clip)}
                                            className={`p-3 rounded-lg cursor-pointer transition ${selectedClip?.id === clip.id
                                                ? 'bg-orange-600 ring-2 ring-orange-500'
                                                : 'bg-[#111] hover:bg-[#1a1a1a]'
                                                }`}
                                        >
                                            <div className="flex items-center justify-between mb-1">
                                                <span className="text-sm font-semibold">{(clip.title || 'Clip sin título').slice(0, 30)}...</span>
                                                <span className="text-xs text-orange-500">🔥 {clip.virality_score}</span>
                                            </div>
                                            <div className="flex gap-2 text-xs text-gray-400">
                                                <span>{clip.category}</span>
                                                <span>•</span>
                                                <span>{clip.duration}s</span>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>

                            {selectedClip && (
                                <div className="mt-4 p-3 bg-blue-600/20 border border-blue-500/30 rounded-lg">
                                    <div className="text-sm font-semibold mb-2">Clip seleccionado:</div>
                                    <div className="text-xs text-gray-300">{selectedClip.title}</div>
                                    <button
                                        onClick={() => setShowScheduleModal(true)}
                                        className="w-full mt-3 bg-orange-600 hover:bg-orange-700 py-2 rounded text-sm font-semibold"
                                    >
                                        Programar Publicación
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Calendar */}
                    <div className="col-span-9">
                        <div className="bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg p-6">
                            <FullCalendar
                                plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
                                initialView="dayGridMonth"
                                headerToolbar={{
                                    left: 'prev,next today',
                                    center: 'title',
                                    right: 'dayGridMonth,timeGridWeek,timeGridDay'
                                }}
                                events={events}
                                dateClick={handleDateClick}
                                editable={true}
                                droppable={true}
                                height="auto"
                                eventColor="#FF6B00"
                            />
                        </div>
                    </div>
                </div>

                {/* Schedule Modal */}
                {showScheduleModal && selectedClip && (
                    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
                        <div className="bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg p-6 max-w-md w-full">
                            <h2 className="text-2xl font-bold mb-4">Programar Publicación</h2>

                            <div className="mb-4">
                                <div className="text-sm text-gray-400 mb-2">Clip:</div>
                                <div className="font-semibold">{selectedClip.title}</div>
                            </div>

                            <div className="mb-4">
                                <label className="block text-sm font-semibold mb-2">Fecha y Hora:</label>
                                <input
                                    type="datetime-local"
                                    value={scheduleDate}
                                    onChange={(e) => setScheduleDate(e.target.value)}
                                    className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded px-3 py-2"
                                />
                            </div>

                            <div className="mb-6">
                                <div className="text-sm font-semibold mb-2">Plataforma:</div>
                                <div className="grid grid-cols-2 gap-3">
                                    <button
                                        onClick={() => handleSchedule('youtube')}
                                        className="bg-red-600 hover:bg-red-700 py-3 rounded font-semibold"
                                    >
                                        🔴 YouTube
                                    </button>
                                    <button
                                        onClick={() => handleSchedule('tiktok')}
                                        className="bg-gray-900 hover:bg-gray-800 py-3 rounded font-semibold"
                                    >
                                        ⚫ TikTok
                                    </button>
                                </div>
                            </div>

                            <button
                                onClick={() => setShowScheduleModal(false)}
                                className="w-full bg-gray-700 hover:bg-gray-600 py-2 rounded font-semibold"
                            >
                                Cancelar
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
