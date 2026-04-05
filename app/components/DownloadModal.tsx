'use client';

import { useState } from 'react';
import { Download, X } from 'lucide-react';

interface DownloadModalProps {
    clipId: string;
    clipTitle: string;
    onClose: () => void;
}

export default function DownloadModal({ clipId, clipTitle, onClose }: DownloadModalProps) {
    const [downloading, setDownloading] = useState(false);
    const [format, setFormat] = useState<'original' | 'subtitled' | 'vertical'>('original');

    const handleDownload = async () => {
        setDownloading(true);

        try {
            const response = await fetch(`/api/clips/download?clipId=${clipId}&format=${format}`);

            if (!response.ok) {
                throw new Error('Download failed');
            }

            // Crear blob y descargar
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${clipTitle}_${format}.mp4`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            onClose();
        } catch (error) {
            alert('Error al descargar clip');
            console.error(error);
        } finally {
            setDownloading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-[#0a0a0a] border border-[#2a2a2a] rounded-lg p-6 max-w-md w-full">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold">Descargar Clip</h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Título del clip */}
                <div className="mb-6">
                    <p className="text-sm text-gray-400 mb-1">Clip:</p>
                    <p className="font-semibold text-white">{clipTitle}</p>
                </div>

                {/* Opciones de formato */}
                <div className="mb-6">
                    <p className="text-sm font-semibold mb-3">Formato:</p>

                    <div className="space-y-3">
                        <label className={`flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition ${format === 'original'
                                ? 'border-orange-500 bg-orange-500/10'
                                : 'border-[#2a2a2a] hover:border-[#3a3a3a]'
                            }`}>
                            <input
                                type="radio"
                                name="format"
                                value="original"
                                checked={format === 'original'}
                                onChange={(e) => setFormat(e.target.value as any)}
                                className="mt-1"
                            />
                            <div>
                                <div className="font-semibold">Original</div>
                                <div className="text-xs text-gray-400">Video sin modificaciones</div>
                            </div>
                        </label>

                        <label className={`flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition ${format === 'subtitled'
                                ? 'border-orange-500 bg-orange-500/10'
                                : 'border-[#2a2a2a] hover:border-[#3a3a3a]'
                            }`}>
                            <input
                                type="radio"
                                name="format"
                                value="subtitled"
                                checked={format === 'subtitled'}
                                onChange={(e) => setFormat(e.target.value as any)}
                                className="mt-1"
                            />
                            <div>
                                <div className="font-semibold">Con Subtítulos</div>
                                <div className="text-xs text-gray-400">Si has añadido subtítulos</div>
                            </div>
                        </label>

                        <label className={`flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition ${format === 'vertical'
                                ? 'border-orange-500 bg-orange-500/10'
                                : 'border-[#2a2a2a] hover:border-[#3a3a3a]'
                            }`}>
                            <input
                                type="radio"
                                name="format"
                                value="vertical"
                                checked={format === 'vertical'}
                                onChange={(e) => setFormat(e.target.value as any)}
                                className="mt-1"
                            />
                            <div>
                                <div className="font-semibold">Vertical (9:16)</div>
                                <div className="text-xs text-gray-400">Optimizado para TikTok/Shorts</div>
                            </div>
                        </label>
                    </div>
                </div>

                {/* Botones */}
                <div className="flex gap-3">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-3 bg-[#1a1a1a] hover:bg-[#2a2a2a] rounded-lg font-semibold transition"
                    >
                        Cancelar
                    </button>

                    <button
                        onClick={handleDownload}
                        disabled={downloading}
                        className="flex-1 px-4 py-3 bg-orange-600 hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-semibold transition flex items-center justify-center gap-2"
                    >
                        {downloading ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                Descargando...
                            </>
                        ) : (
                            <>
                                <Download className="w-4 h-4" />
                                Descargar
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
