'use client';

import { useState, useEffect } from 'react';
import { Calendar, Clock, CheckCircle, XCircle, Loader, RefreshCw, Trash2 } from 'lucide-react';

interface ScheduledUpload {
    id: string;
    clipId: string;
    clipTitle: string;
    platform: string;
    scheduledAt: string;
    status: string;
    attempts: number;
    lastError?: string;
    videoUrl?: string;
}

interface UploadStats {
    pending: number;
    success: number;
    failed: number;
    totalToday: number;
}

export default function UploadsPage() {
    const [uploads, setUploads] = useState<ScheduledUpload[]>([]);
    const [stats, setStats] = useState<UploadStats>({ pending: 0, success: 0, failed: 0, totalToday: 0 });
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');

    useEffect(() => {
        loadUploads();
        // Refresh every 30 seconds
        const interval = setInterval(loadUploads, 30000);
        return () => clearInterval(interval);
    }, [filter]);

    const loadUploads = async () => {
        try {
            const res = await fetch(`/api/uploads?status=${filter}`);
            const data = await res.json();
            setUploads(data.uploads || []);
            setStats(data.stats || {});
        } catch (error) {
            console.error('Error loading uploads:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleRetry = async (uploadId: string) => {
        try {
            await fetch(`/api/uploads/${uploadId}/retry`, { method: 'POST' });
            loadUploads();
        } catch (error) {
            console.error('Error retrying upload:', error);
        }
    };

    const handleCancel = async (uploadId: string) => {
        if (!confirm('¿Cancelar esta subida programada?')) return;

        try {
            await fetch(`/api/uploads/${uploadId}`, { method: 'DELETE' });
            loadUploads();
        } catch (error) {
            console.error('Error cancelling upload:', error);
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'success':
                return <CheckCircle className="text-green-500" size={20} />;
            case 'failed':
                return <XCircle className="text-red-500" size={20} />;
            case 'uploading':
                return <Loader className="text-blue-500 animate-spin" size={20} />;
            default:
                return <Clock className="text-gray-400" size={20} />;
        }
    };

    const getPlatformColor = (platform: string) => {
        switch (platform) {
            case 'tiktok':
                return 'bg-pink-600';
            case 'youtube':
                return 'bg-red-600';
            case 'instagram':
                return 'bg-purple-600';
            default:
                return 'bg-gray-600';
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-black text-white flex items-center justify-center">
                <Loader className="animate-spin" size={40} />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-black text-white p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">📅 Upload Scheduler</h1>
                    <p className="text-gray-400">Gestiona las subidas programadas a TikTok y YouTube</p>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-4 gap-4 mb-8">
                    <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg p-6">
                        <div className="text-sm text-gray-400 mb-2">Pendientes</div>
                        <div className="text-3xl font-bold text-orange-500">{stats.pending}</div>
                    </div>
                    <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg p-6">
                        <div className="text-sm text-gray-400 mb-2">Exitosas</div>
                        <div className="text-3xl font-bold text-green-500">{stats.success}</div>
                    </div>
                    <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg p-6">
                        <div className="text-sm text-gray-400 mb-2">Fallidas</div>
                        <div className="text-3xl font-bold text-red-500">{stats.failed}</div>
                    </div>
                    <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg p-6">
                        <div className="text-sm text-gray-400 mb-2">Hoy</div>
                        <div className="text-3xl font-bold">{stats.totalToday}</div>
                    </div>
                </div>

                {/* Filters */}
                <div className="flex gap-3 mb-6">
                    {['all', 'pending', 'uploading', 'success', 'failed'].map(status => (
                        <button
                            key={status}
                            onClick={() => setFilter(status)}
                            className={`px-4 py-2 rounded-lg transition ${filter === status
                                    ? 'bg-orange-600 text-white'
                                    : 'bg-[#1a1a1a] text-gray-400 hover:bg-[#2a2a2a]'
                                }`}
                        >
                            {status.charAt(0).toUpperCase() + status.slice(1)}
                        </button>
                    ))}
                    <button
                        onClick={loadUploads}
                        className="ml-auto px-4 py-2 bg-[#1a1a1a] hover:bg-[#2a2a2a] rounded-lg flex items-center gap-2 transition"
                    >
                        <RefreshCw size={18} />
                        Refresh
                    </button>
                </div>

                {/* Upload List */}
                <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-[#0a0a0a] border-b border-[#2a2a2a]">
                                <tr>
                                    <th className="px-6 py-4 text-left text-sm font-semibold">Status</th>
                                    <th className="px-6 py-4 text-left text-sm font-semibold">Clip</th>
                                    <th className="px-6 py-4 text-left text-sm font-semibold">Plataforma</th>
                                    <th className="px-6 py-4 text-left text-sm font-semibold">Fecha Programada</th>
                                    <th className="px-6 py-4 text-left text-sm font-semibold">Intentos</th>
                                    <th className="px-6 py-4 text-left text-sm font-semibold">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#2a2a2a]">
                                {uploads.map(upload => (
                                    <tr key={upload.id} className="hover:bg-[#151515] transition">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                {getStatusIcon(upload.status)}
                                                <span className="text-sm capitalize">{upload.status}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="font-medium">{upload.clipTitle}</div>
                                            {upload.lastError && (
                                                <div className="text-xs text-red-400 mt-1">{upload.lastError}</div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-3 py-1 rounded-full text-xs font-semibold text-white ${getPlatformColor(upload.platform)}`}>
                                                {upload.platform}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-400">
                                            {new Date(upload.scheduledAt).toLocaleString('es-ES', {
                                                dateStyle: 'short',
                                                timeStyle: 'short'
                                            })}
                                        </td>
                                        <td className="px-6 py-4 text-sm">
                                            <span className={upload.attempts > 0 ? 'text-orange-400' : ''}>
                                                {upload.attempts} / 3
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex gap-2">
                                                {upload.status === 'failed' && (
                                                    <button
                                                        onClick={() => handleRetry(upload.id)}
                                                        className="p-2 bg-orange-600 hover:bg-orange-700 rounded transition"
                                                        title="Reintentar"
                                                    >
                                                        <RefreshCw size={16} />
                                                    </button>
                                                )}
                                                {upload.status === 'pending' && (
                                                    <button
                                                        onClick={() => handleCancel(upload.id)}
                                                        className="p-2 bg-red-600 hover:bg-red-700 rounded transition"
                                                        title="Cancelar"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                )}
                                                {upload.videoUrl && (
                                                    <a
                                                        href={upload.videoUrl}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="p-2 bg-blue-600 hover:bg-blue-700 rounded transition"
                                                        title="Ver video"
                                                    >
                                                        🔗
                                                    </a>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>

                        {uploads.length === 0 && (
                            <div className="text-center py-12 text-gray-400">
                                No hay subidas {filter !== 'all' && filter}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
