'use client';

import { useState, useEffect } from 'react';
import {
    Calendar as CalendarIcon,
    Clock,
    CheckCircle,
    AlertCircle,
    Plus,
    Trash2,
    Youtube,
    Smartphone,
    ChevronLeft,
    ChevronRight,
    Filter,
    MoreVertical,
    X,
    PlusCircle,
    Hash,
    Type,
    FileText
} from 'lucide-react';
import { format, addDays, startOfDay, isSameDay, parseISO, isAfter } from 'date-fns';
import { es } from 'date-fns/locale';
import toast from 'react-hot-toast';

interface ScheduledPost {
    id: string;
    clip_id: string;
    platform: 'youtube' | 'tiktok';
    scheduled_at: string;
    status: 'pending' | 'uploading' | 'completed' | 'failed' | 'cancelled';
    title: string;
    description: string;
    hashtags: string;
    virality_score: number;
    project_title: string;
    thumbnail_url: string;
}

interface AvailableClip {
    id: string;
    title: string;
    virality_score: number;
    duration: number;
    thumbnail_url?: string;
    project_title: string;
}

export default function SchedulePage() {
    const [scheduledPosts, setScheduledPosts] = useState<ScheduledPost[]>([]);
    const [availableClips, setAvailableClips] = useState<AvailableClip[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);

    // Create state for the new post
    const [newPost, setNewPost] = useState({
        clipId: '',
        platform: 'tiktok' as 'tiktok' | 'youtube',
        scheduledAt: format(addDays(new Date(), 1), "yyyy-MM-dd'T'HH:mm"),
        title: '',
        description: '',
        hashtags: '#viral #fyp #short'
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [scheduleRes, availableRes] = await Promise.all([
                fetch('/api/schedule'),
                fetch('/api/clips/available')
            ]);

            const scheduleData = await scheduleRes.json();
            const availableData = await availableRes.json();

            if (scheduleData.success) setScheduledPosts(scheduleData.scheduled);
            if (availableData.clips) setAvailableClips(availableData.clips);
        } catch (error) {
            toast.error('Error al cargar datos');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('¿Seguro que quieres cancelar esta publicación?')) return;

        try {
            const res = await fetch(`/api/schedule/${id}`, { method: 'DELETE' });
            if (res.ok) {
                toast.success('Publicación cancelada');
                fetchData();
            }
        } catch (error) {
            toast.error('Error al cancelar');
        }
    };

    const handleSchedule = async () => {
        if (!newPost.clipId || !newPost.scheduledAt) {
            toast.error('Completa los campos obligatorios');
            return;
        }

        try {
            const res = await fetch('/api/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newPost)
            });

            if (res.ok) {
                toast.success('¡Programado con éxito!');
                setShowModal(false);
                fetchData();
                // Reset form
                setNewPost({
                    clipId: '',
                    platform: 'tiktok',
                    scheduledAt: format(addDays(new Date(), 1), "yyyy-MM-dd'T'HH:mm"),
                    title: '',
                    description: '',
                    hashtags: '#viral #fyp #short'
                });
            }
        } catch (error) {
            toast.error('Error al programar');
        }
    };

    // Group posts by day
    const days = Array.from({ length: 7 }, (_, i) => addDays(startOfDay(new Date()), i));

    const getPostsForDay = (day: Date) => {
        return scheduledPosts.filter(post => isSameDay(parseISO(post.scheduled_at), day));
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'text-green-400 bg-green-400/10 border-green-400/20';
            case 'failed': return 'text-red-400 bg-red-400/10 border-red-400/20';
            case 'uploading': return 'text-blue-400 bg-blue-400/10 border-blue-400/20 animate-pulse';
            default: return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
        }
    };

    return (
        <div className="min-h-screen bg-[#050505] text-white p-4 md:p-8">
            <div className="max-w-7xl mx-auto">

                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-10">
                    <div>
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-white to-gray-500 bg-clip-text text-transparent">
                            Planificador Viral
                        </h1>
                        <p className="text-gray-400 mt-2">Gestiona tus próximas publicaciones en TikTok y YouTube Shorts</p>
                    </div>

                    <button
                        onClick={() => setShowModal(true)}
                        className="flex items-center gap-2 bg-orange-600 hover:bg-orange-500 text-white px-6 py-3 rounded-xl font-bold transition-all shadow-lg shadow-orange-600/20 hover:scale-105 active:scale-95"
                    >
                        <PlusCircle className="w-5 h-5" />
                        Programar Contenido
                    </button>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin"></div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-7 gap-6">
                        {days.map((day, idx) => {
                            const posts = getPostsForDay(day);
                            const isToday = isSameDay(day, new Date());

                            return (
                                <div key={idx} className="flex flex-col gap-4">
                                    <div className={`text-center p-3 rounded-xl border ${isToday ? 'bg-orange-600/10 border-orange-600/50' : 'bg-[#0a0a0a] border-[#1a1a1a]'}`}>
                                        <span className="block text-xs uppercase font-bold text-gray-500">{format(day, 'EEE', { locale: es })}</span>
                                        <span className={`text-xl font-black ${isToday ? 'text-orange-500' : ''}`}>{format(day, 'd')}</span>
                                    </div>

                                    <div className="flex flex-col gap-3">
                                        {posts.length === 0 ? (
                                            <div className="h-20 border-2 border-dashed border-[#1a1a1a] rounded-xl flex items-center justify-center opacity-30">
                                                <Plus className="w-5 h-5" />
                                            </div>
                                        ) : (
                                            posts.map(post => (
                                                <div key={post.id} className="group relative bg-[#0f0f0f] border border-[#1f1f1f] rounded-xl overflow-hidden hover:border-orange-600/50 transition-all shadow-xl hover:-translate-y-1">
                                                    {/* Platform Icon Overlay */}
                                                    <div className="absolute top-2 left-2 z-10">
                                                        {post.platform === 'youtube' ? (
                                                            <div className="bg-red-600 p-1.5 rounded-lg shadow-lg">
                                                                <Youtube className="w-3 h-3 text-white" />
                                                            </div>
                                                        ) : (
                                                            <div className="bg-white p-1.5 rounded-lg shadow-lg">
                                                                <Smartphone className="w-3 h-3 text-black" />
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* Delete Button Overlay */}
                                                    <button
                                                        onClick={() => handleDelete(post.id)}
                                                        className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 p-1.5 bg-red-600/80 hover:bg-red-600 rounded-lg transition-all"
                                                    >
                                                        <Trash2 className="w-3 h-3 text-white" />
                                                    </button>

                                                    {/* Thumbnail / Image */}
                                                    <div className="h-24 bg-[#1a1a1a] relative">
                                                        {post.thumbnail_url ? (
                                                            <img src={post.thumbnail_url} className="w-full h-full object-cover opacity-60" alt="" />
                                                        ) : (
                                                            <div className="w-full h-full flex items-center justify-center text-[#2a2a2a]">
                                                                <FileText className="w-8 h-8" />
                                                            </div>
                                                        )}
                                                        <div className="absolute bottom-1 right-1 bg-black/80 px-1.5 py-0.5 rounded text-[10px] font-bold">
                                                            {format(parseISO(post.scheduled_at), 'HH:mm')}
                                                        </div>
                                                    </div>

                                                    {/* Info */}
                                                    <div className="p-3">
                                                        <h3 className="text-xs font-bold line-clamp-1 mb-1">{post.title || 'Sin título'}</h3>
                                                        <div className="flex items-center justify-between mt-2">
                                                            <span className={`text-[10px] px-2 py-0.5 rounded-full border ${getStatusColor(post.status)}`}>
                                                                {post.status.toUpperCase()}
                                                            </span>
                                                            <span className="text-[10px] text-orange-500 font-bold">🔥 {post.virality_score}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Modal Selection */}
                {showModal && (
                    <div className="fixed inset-0 bg-black/90 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
                        <div className="bg-[#0a0a0a] border border-[#1f1f1f] w-full max-w-4xl rounded-3xl overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-300">
                            <div className="flex items-center justify-between p-6 border-b border-[#1a1a1a]">
                                <h2 className="text-2xl font-bold flex items-center gap-2">
                                    <CalendarIcon className="w-6 h-6 text-orange-600" />
                                    Programar Nuevo Clip
                                </h2>
                                <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white transition-colors">
                                    <X className="w-6 h-6" />
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2">
                                {/* Left: Settings */}
                                <div className="p-8 border-r border-[#1a1a1a] flex flex-col gap-6">
                                    <div className="space-y-4">
                                        <label className="block">
                                            <span className="text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
                                                <Type className="w-4 h-4" /> Título (Clickbait)
                                            </span>
                                            <input
                                                type="text"
                                                value={newPost.title}
                                                onChange={e => setNewPost({ ...newPost, title: e.target.value })}
                                                placeholder="El secreto de..."
                                                className="w-full bg-[#111] border border-[#222] rounded-xl px-4 py-3 focus:outline-none focus:border-orange-600 transition"
                                            />
                                        </label>

                                        <label className="block">
                                            <span className="text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
                                                <FileText className="w-4 h-4" /> Descripción / Hook
                                            </span>
                                            <textarea
                                                value={newPost.description}
                                                onChange={e => setNewPost({ ...newPost, description: e.target.value })}
                                                rows={3}
                                                placeholder="En este video te enseño..."
                                                className="w-full bg-[#111] border border-[#222] rounded-xl px-4 py-3 focus:outline-none focus:border-orange-600 transition resize-none"
                                            />
                                        </label>

                                        <label className="block">
                                            <span className="text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
                                                <Hash className="w-4 h-4" /> Hashtags
                                            </span>
                                            <input
                                                type="text"
                                                value={newPost.hashtags}
                                                onChange={e => setNewPost({ ...newPost, hashtags: e.target.value })}
                                                className="w-full bg-[#111] border border-[#222] rounded-xl px-4 py-3 focus:outline-none focus:border-orange-600 transition"
                                            />
                                        </label>

                                        <div className="grid grid-cols-2 gap-4">
                                            <label className="block">
                                                <span className="text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
                                                    <Clock className="w-4 h-4" /> Fecha y Hora
                                                </span>
                                                <input
                                                    type="datetime-local"
                                                    value={newPost.scheduledAt}
                                                    onChange={e => setNewPost({ ...newPost, scheduledAt: e.target.value })}
                                                    className="w-full bg-[#111] border border-[#222] rounded-xl px-4 py-3 focus:outline-none focus:border-orange-600 transition [color-scheme:dark]"
                                                />
                                            </label>

                                            <label className="block">
                                                <span className="text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
                                                    Plataforma
                                                </span>
                                                <div className="flex bg-[#111] border border-[#222] rounded-xl overflow-hidden p-1">
                                                    <button
                                                        onClick={() => setNewPost({ ...newPost, platform: 'tiktok' })}
                                                        className={`flex-1 py-2 flex items-center justify-center gap-2 rounded-lg transition ${newPost.platform === 'tiktok' ? 'bg-white text-black font-bold' : 'text-gray-500 hover:text-white'}`}
                                                    >
                                                        <Smartphone className="w-4 h-4" /> TikTok
                                                    </button>
                                                    <button
                                                        onClick={() => setNewPost({ ...newPost, platform: 'youtube' })}
                                                        className={`flex-1 py-2 flex items-center justify-center gap-2 rounded-lg transition ${newPost.platform === 'youtube' ? 'bg-red-600 text-white font-bold' : 'text-gray-500 hover:text-white'}`}
                                                    >
                                                        <Youtube className="w-4 h-4" /> YouTube
                                                    </button>
                                                </div>
                                            </label>
                                        </div>
                                    </div>

                                    <button
                                        onClick={handleSchedule}
                                        className="w-full bg-orange-600 hover:bg-orange-500 text-white py-4 rounded-2xl font-black text-lg transition-all shadow-xl shadow-orange-600/30 active:scale-[0.98] mt-4"
                                    >
                                        Confirmar Programación
                                    </button>
                                </div>

                                {/* Right: Clip Selection */}
                                <div className="bg-[#080808] p-8 flex flex-col gap-4">
                                    <span className="text-sm font-bold text-gray-500 uppercase tracking-widest">Elige un Clip Disponible</span>
                                    <div className="overflow-y-auto max-h-[400px] pr-2 flex flex-col gap-3 custom-scrollbar">
                                        {availableClips.length === 0 ? (
                                            <div className="text-center py-20 text-gray-600 italic">No hay clips procesados aún</div>
                                        ) : (
                                            availableClips.map(clip => (
                                                <div
                                                    key={clip.id}
                                                    onClick={() => {
                                                        setNewPost({ ...newPost, clipId: clip.id, title: clip.title });
                                                        toast.success(`Clip fijado: ${clip.title.substring(0, 20)}...`);
                                                    }}
                                                    className={`p-4 rounded-2xl border-2 transition-all cursor-pointer flex gap-4 items-center ${newPost.clipId === clip.id ? 'bg-orange-600/10 border-orange-600 shadow-lg shadow-orange-600/10' : 'bg-[#0f0f0f] border-[#1a1a1a] hover:border-[#333]'}`}
                                                >
                                                    <div className="w-16 h-16 bg-[#1a1a1a] rounded-lg overflow-hidden flex-shrink-0 relative">
                                                        {clip.thumbnail_url && <img src={clip.thumbnail_url} className="w-full h-full object-cover" />}
                                                        <div className="absolute inset-0 flex items-center justify-center text-[10px] font-bold bg-black/40">
                                                            {clip.duration}s
                                                        </div>
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <h4 className="text-sm font-bold truncate">{clip.title || 'Clip sin título'}</h4>
                                                        <p className="text-[10px] text-gray-500 truncate mt-0.5">{clip.project_title}</p>
                                                        <div className="flex items-center gap-2 mt-2">
                                                            <span className="text-[10px] font-black text-orange-500">🔥 SCORE: {clip.virality_score}</span>
                                                        </div>
                                                    </div>
                                                    {newPost.clipId === clip.id && <CheckCircle className="w-5 h-5 text-orange-500 flex-shrink-0" />}
                                                </div>
                                            ))
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

            </div>
            <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #222;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #333;
        }
      `}</style>
        </div>
    );
}
