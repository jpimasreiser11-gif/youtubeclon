"use client";
import React, { useEffect, useState } from 'react';
import { Sidebar } from '@/components/sidebar';
import { useParams } from 'next/navigation';
import { Play, Calendar, Clock, Star, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function ProjectDetails() {
    const params = useParams();
    const [project, setProject] = useState<any>(null);
    const [clips, setClips] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!params.id) return;

        // Redirect to new Studio page
        window.location.href = `/studio/${params.id}`;
    }, [params.id]);

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white font-sans">
            <Sidebar />
            <main className="ml-[60px] pt-24 p-8 max-w-7xl mx-auto">

                {/* Back Link */}
                <div className="mb-8">
                    <Link href="/projects" className="text-[#a1a1aa] hover:text-white transition-colors text-sm font-medium">← All Projects</Link>
                </div>

                {loading ? (
                    <div className="animate-pulse space-y-8">
                        <div className="h-64 bg-[#111111] rounded-[32px] border border-[#1f1f1f]" />
                        <div className="h-96 bg-[#111111] rounded-[32px] border border-[#1f1f1f]" />
                    </div>
                ) : !project ? (
                    <div className="text-center py-20 text-[#52525b]">Project not found</div>
                ) : (
                    <div className="space-y-12">

                        {/* Header Hero */}
                        <div className="bg-[#111111] border border-[#1f1f1f] rounded-[32px] p-8 flex gap-8 items-start">
                            <div className="w-64 aspect-video bg-black rounded-2xl overflow-hidden border border-[#1f1f1f] shadow-lg shrink-0 relative group">
                                {project.thumbnail_url ? (
                                    <img src={project.thumbnail_url} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center">
                                        <Play className="opacity-20" />
                                    </div>
                                )}
                            </div>
                            <div className="space-y-4 flex-1">
                                <div className="space-y-1">
                                    <p className="text-orange-500 font-bold tracking-widest text-[10px] uppercase">PROJECT DETAILS</p>
                                    <h1 className="text-3xl font-black italic">{project.title || project.source_video_url || 'Untitled Project'}</h1>
                                </div>
                                <div className="flex gap-6 text-sm text-[#a1a1aa]">
                                    <div className="flex items-center gap-2">
                                        <Calendar className="w-4 h-4" />
                                        {new Date(project.created_at).toLocaleDateString()}
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Clock className="w-4 h-4" />
                                        {clips.length} Clips Generated
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Clips Grid */}
                        <div className="space-y-6">
                            <h2 className="text-2xl font-bold uppercase tracking-tight">Viral Clips</h2>
                            {clips.length === 0 ? (
                                <p className="text-[#52525b]">No clips found for this project.</p>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {clips.map((clip: any, index: number) => (
                                        <Link key={clip.id} href={`/editor/${clip.id}`} className="group relative bg-[#111111] border border-[#1f1f1f] hover:border-orange-500/50 rounded-[32px] overflow-hidden transition-all hover:-translate-y-1 shadow-2xl">
                                            <div className="aspect-[9/16] bg-black relative">
                                                {/* In a real app we'd fetch clip specific thumbnail from DB. Assuming clip.thumbnail_url exists or using project thumb for now fallback */}
                                                <div className="w-full h-full bg-[#18181b] flex items-center justify-center text-[#27272a] font-black text-6xl opacity-20">
                                                    {index + 1}
                                                </div>
                                                <div className="absolute top-4 right-4 bg-black/80 backdrop-blur-md px-3 py-1 rounded-full border border-white/10 flex items-center gap-1.5 text-xs font-bold text-green-400">
                                                    <Star className="w-3 h-3 fill-green-400" />
                                                    {clip.virality_score}
                                                </div>

                                                <div className="absolute inset-0 bg-black/40 group-hover:bg-transparent transition-all" />
                                                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all scale-90 group-hover:scale-100">
                                                    <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-lg shadow-orange-500/20">
                                                        <Play className="w-6 h-6 text-black ml-1" />
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="p-6">
                                                <h3 className="font-bold text-lg mb-2 line-clamp-2 leading-tight group-hover:text-orange-400 transition-colors">
                                                    Clip #{index + 1}
                                                </h3>
                                                <div className="flex items-center justify-between mt-4">
                                                    <span className="text-xs font-mono text-[#52525b] border border-[#1f1f1f] px-2 py-1 rounded-md">
                                                        {clip.start_time.toFixed(1)}s - {clip.end_time.toFixed(1)}s
                                                    </span>
                                                    <ArrowRight className="w-4 h-4 text-[#52525b] group-hover:translate-x-1 transition-transform" />
                                                </div>
                                            </div>
                                        </Link>
                                    ))}
                                </div>
                            )}
                        </div>

                    </div>
                )}
            </main>
        </div>
    );
}
