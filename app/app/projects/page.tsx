"use client";
import React, { useEffect, useState } from 'react';
import { Sidebar } from '@/components/sidebar';
import { Folder, Play, Trash2, Clock } from 'lucide-react';
import Link from 'next/link';

interface Project {
    id: string;
    title: string;
    source_url: string;
    status: string;
    progress: number;
    created_at: string;
    thumbnail_url: string;
    auto_publish_enabled: boolean;
    publish_slots_per_day: number;
    publish_platforms: string[];
}

export default function ProjectsPage() {
    const [projects, setProjects] = useState<Project[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetch('/api/get-jobs')
            .then(res => res.json())
            .then(data => {
                if (data.jobs) setProjects(data.jobs);
                setIsLoading(false);
            })
            .catch(err => {
                console.error(err);
                setIsLoading(false);
            });
    }, []);

    const handleDelete = async (id: string) => {
        if (!confirm('¿Eliminar proyecto?')) return;
        const res = await fetch(`/api/delete-job?id=${id}`, { method: 'DELETE' });
        if (res.ok) {
            setProjects(prev => prev.filter((p: any) => p.id !== id));
        }
    };

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white font-sans">
            <Sidebar />            <main className="ml-[60px] pt-24 p-8 max-w-7xl mx-auto">
                <header className="flex items-center justify-between mb-12">
                    <div className="space-y-1">
                        <h1 className="text-4xl font-black italic tracking-tighter uppercase italic">Mis Proyectos</h1>
                        <p className="text-[#a1a1aa] font-medium text-sm">Gestiona tus vídeos y clips generados</p>
                    </div>
                </header>

                {isLoading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-[300px] bg-[#111111] border border-[#1f1f1f] rounded-[32px] animate-pulse" />
                        ))}
                    </div>
                ) : projects.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-32 border border-dashed border-[#1f1f1f] rounded-[40px] bg-[#09090b]">
                        <div className="w-16 h-16 bg-[#111111] rounded-2xl flex items-center justify-center mb-6 border border-[#1f1f1f]">
                            <Folder className="w-8 h-8 text-[#3f3f46]" />
                        </div>
                        <h3 className="text-xl font-bold mb-2">No hay proyectos</h3>
                        <p className="text-[#52525b] mb-8">Empieza pegando un enlace en el dashboard principal.</p>
                        <Link href="/" className="px-8 py-3 bg-white text-black rounded-2xl font-black uppercase text-sm hover:bg-[#e4e4e7] transition-all">
                            Ir al Dashboard
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {projects.map((job: any) => (
                            <Link href={`/projects/${job.id}`} key={job.id} className="block">
                                <div className="group bg-[#111111] border border-[#1f1f1f] rounded-[32px] overflow-hidden hover:border-orange-500/50 transition-all shadow-2xl">
                                    <div className="aspect-video relative bg-black">
                                        {job.thumbnail_url ? (
                                            <img src={job.thumbnail_url} className="w-full h-full object-cover opacity-60" />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center bg-[#18181b]">
                                                <Play className="w-12 h-12 text-[#27272a]" />
                                            </div>
                                        )}
                                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
                                        <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <div className={cn(
                                                    "px-2 py-1 rounded-md text-[10px] font-black uppercase tracking-widest",
                                                    job.status === 'COMPLETED' ? "bg-green-500/20 text-green-400 border border-green-500/30" : "bg-orange-500/20 text-orange-400 border border-orange-500/30"
                                                )}>
                                                    {job.status}
                                                </div>
                                            </div>
                                            <button
                                                onClick={(e) => {
                                                    e.preventDefault(); // Prevent navigation when clicking delete
                                                    handleDelete(job.id);
                                                }}
                                                className="p-2 bg-black/60 rounded-xl text-[#52525b] hover:text-red-500 transition-colors"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                    <div className="p-6">
                                        <div className="flex items-start justify-between mb-1">
                                            <h4 className="font-bold text-[#e4e4e7] truncate flex-1">{job.title || job.source_url}</h4>
                                            {job.status === 'COMPLETED' && (
                                                <button
                                                    onClick={async (e) => {
                                                        e.preventDefault();
                                                        const newState = !job.auto_publish_enabled;
                                                        const res = await fetch('/api/update-project-automation', {
                                                            method: 'POST',
                                                            headers: { 'Content-Type': 'application/json' },
                                                            body: JSON.stringify({ projectId: job.id, enabled: newState })
                                                        });
                                                        if (res.ok) {
                                                            setProjects(prev => prev.map((p) =>
                                                                p.id === job.id ? { ...p, auto_publish_enabled: newState } : p
                                                            ));
                                                        }
                                                    }}
                                                    className={cn(
                                                        "ml-2 px-2 py-0.5 rounded-full text-[9px] font-black uppercase transition-all",
                                                        job.auto_publish_enabled
                                                            ? "bg-blue-500 text-white shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                                                            : "bg-[#1f1f1f] text-[#52525b] hover:bg-[#27272a]"
                                                    )}
                                                >
                                                    {job.auto_publish_enabled ? "AUTO: ON" : "AUTO: OFF"}
                                                </button>
                                            )}
                                        </div>
                                        <div className="flex items-center justify-between text-[11px] text-[#52525b] font-medium">
                                            <span>{new Date(job.created_at).toLocaleDateString()}</span>
                                            {job.status === 'PROCESSING' ? (
                                                <span className="flex items-center gap-1.5 text-orange-400">
                                                    <Clock className="w-3 h-3" /> {job.progress}%
                                                </span>
                                            ) : job.auto_publish_enabled ? (
                                                <span className="text-blue-400 font-bold">DAILY QUEUE ACTIVE</span>
                                            ) : null}
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}

function cn(...inputs: any) {
    return inputs.filter(Boolean).join(' ');
}
