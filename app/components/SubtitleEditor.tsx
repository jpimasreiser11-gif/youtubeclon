'use client';
import { useState, useEffect, useRef } from 'react';
import { Play, Pause, Save, Download, Plus, Trash2 } from 'lucide-react';
import { motion } from 'framer-motion';

export default function SubtitleEditor({ clipId, videoSrc, onClose }: { clipId: string, videoSrc: string, onClose: () => void }) {
    const [words, setWords] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [currentTime, setCurrentTime] = useState(0);
    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
        fetch(`/api/clips/${clipId}/subtitles`)
            .then(res => res.json())
            .then(data => { setWords(data.words || []); setLoading(false); });
    }, [clipId]);

    const handleSave = async () => {
        await fetch(`/api/clips/${clipId}/subtitles`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ words })
        });
        alert('Guardado correctamente');
    };

    // Encuentra la palabra activa en base al tiempo actual del video
    const activeWord = words.find(w => currentTime >= w.start && currentTime <= w.end);

    if (loading) return <div className="fixed inset-0 bg-black flex items-center justify-center font-bold text-xl text-white">Cargando transcripción...</div>;

    return (
        <div className="fixed inset-0 bg-[#0a0a0a] z-50 flex flex-col text-white">
            <div className="p-4 border-b border-[#1f1f1f] flex justify-between items-center bg-[#111]">
                <h1 className="font-bold text-xl flex items-center gap-2">⚡ Editor Dinámico</h1>
                <div className="flex gap-4">
                    <button onClick={handleSave} className="bg-orange-600 hover:bg-orange-500 transition px-6 py-2 rounded-lg font-bold flex items-center gap-2">
                        <Save size={18} /> Guardar Cambios
                    </button>
                    <button onClick={onClose} className="bg-[#18181b] border border-[#27272a] hover:bg-[#27272a] transition px-6 py-2 rounded-lg">Cerrar</button>
                </div>
            </div>

            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 p-6 gap-6 overflow-hidden">
                {/* REPRODUCTOR CON OVERLAY DE REACT */}
                <div className="relative bg-black rounded-2xl overflow-hidden border border-[#1f1f1f] flex flex-col items-center justify-center">
                    <video
                        ref={videoRef}
                        src={videoSrc}
                        className="w-full h-full object-contain absolute inset-0"
                        onTimeUpdate={(e: any) => setCurrentTime(e.target.currentTime)}
                        controls
                    />

                    {/* LA MAGIA: Capa de Subtítulos con Framer Motion */}
                    {activeWord && (
                        <div className="absolute bottom-[15%] w-full text-center pointer-events-none z-10 flex justify-center items-center gap-2 flex-wrap px-8">
                            <motion.span
                                key={activeWord.word + activeWord.start} // Obliga a Framer a animar cada palabra nueva
                                initial={{ scale: 0.5, opacity: 0, y: 20 }}
                                animate={{ scale: 1.1, opacity: 1, y: 0 }}
                                transition={{ type: "spring", stiffness: 500, damping: 20 }}
                                className="inline-block text-4xl md:text-5xl font-black uppercase text-yellow-400"
                                style={{
                                    textShadow: '3px 3px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000',
                                    filter: 'drop-shadow(0px 8px 6px rgba(0,0,0,0.9))'
                                }}
                            >
                                {activeWord.word}
                            </motion.span>
                        </div>
                    )}
                </div>

                {/* LISTA DE PALABRAS (Inputs) */}
                <div className="bg-[#111] rounded-2xl border border-[#1f1f1f] p-4 overflow-y-auto space-y-2">
                    {words.map((w, i) => (
                        <div key={i} className={`p-3 rounded-lg border flex gap-3 items-center transition-colors ${currentTime >= w.start && currentTime <= w.end ? 'border-orange-500 bg-orange-500/10' : 'border-[#27272a] hover:border-[#3f3f46]'}`}>
                            <input
                                value={w.word}
                                onChange={(e) => {
                                    const n = [...words]; n[i].word = e.target.value; setWords(n);
                                }}
                                className="flex-1 bg-transparent outline-none font-medium text-lg"
                            />
                            <span className="text-xs font-mono text-gray-500 bg-black px-2 py-1 rounded">{w.start.toFixed(2)}s</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
