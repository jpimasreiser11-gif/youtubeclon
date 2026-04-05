'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';

interface Project {
    id: string;
    title: string;
    thumbnail_url: string;
    project_status: string;
    status?: string; // API returns status alias
    created_at: string;
    clips_count?: number;
    progress?: number;
    estimated_time_remaining?: number;
    auto_publish_enabled?: boolean;
}

interface KPIData {
    totalProjects: number;
    totalClips: number;
    scheduledToday: number;
    avgViralityScore: number;
}

export default function DashboardPage() {
    const router = useRouter();
    const [projects, setProjects] = useState<Project[]>([]);
    const [scheduled, setScheduled] = useState<any[]>([]);
    const [kpis, setKPIs] = useState<KPIData>({
        totalProjects: 0,
        totalClips: 0,
        scheduledToday: 0,
        avgViralityScore: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            const [projectsRes, scheduledRes] = await Promise.all([
                fetch('/api/get-jobs'),
                fetch('/api/scheduled-publications')
            ]);

            const projectsData = await projectsRes.json();
            const scheduledData = await scheduledRes.json();

            if (scheduledData.events) {
                setScheduled(scheduledData.events);
            }

            if (projectsData.jobs) {
                const normalizedProjects = projectsData.jobs.map((p: any) => ({
                    ...p,
                    project_status: p.status || p.project_status
                }));
                setProjects(normalizedProjects);

                const totalProjects = normalizedProjects.length;
                const completedProjects = normalizedProjects.filter(
                    (p: Project) => p.project_status === 'COMPLETED'
                );

                const today = new Date().toISOString().split('T')[0];
                const scheduledTodayCount = (scheduledData.events || []).filter((e: any) =>
                    new Date(e.scheduled_at).toISOString().split('T')[0] === today
                ).length;

                setKPIs({
                    totalProjects,
                    totalClips: completedProjects.length * 15,
                    scheduledToday: scheduledTodayCount,
                    avgViralityScore: 85
                });
            }
            setLoading(false);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
            setLoading(false);
        }
    };

    // Poll every 5s when there are PROCESSING projects
    useEffect(() => {
        fetchDashboardData();
        const hasProcessing = projects.some(p => p.project_status === 'PROCESSING');
        if (!hasProcessing) return;
        const interval = setInterval(fetchDashboardData, 5000);
        return () => clearInterval(interval);
    }, [projects.map(p => p.project_status).join(',')]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen bg-black">
                <div className="text-orange-500 text-xl">Cargando dashboard...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-black text-white p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold mb-2">Centro de Comando</h1>
                    <p className="text-gray-400">Vista general de tus proyectos y clips virales</p>
                </div>

                {/* KPI Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <KPICard
                        icon="📊"
                        title="Proyectos Totales"
                        value={kpis.totalProjects}
                        subtitle="Videos procesados"
                        color="blue"
                    />

                    <KPICard
                        icon="🎬"
                        title="Clips Generados"
                        value={kpis.totalClips}
                        subtitle="Momentos virales"
                        color="orange"
                    />

                    <KPICard
                        icon="📅"
                        title="Programados Hoy"
                        value={kpis.scheduledToday}
                        subtitle="Publicaciones pendientes"
                        color="green"
                    />

                    <KPICard
                        icon={kpis.avgViralityScore >= 90 ? "👑" : kpis.avgViralityScore >= 80 ? "🔥" : "🟢"}
                        title="Score Promedio"
                        value={kpis.avgViralityScore}
                        subtitle={kpis.avgViralityScore >= 90 ? "TIER S (God Tier)" : kpis.avgViralityScore >= 80 ? "TIER A (Viral)" : "TIER B (Decente)"}
                        color={kpis.avgViralityScore >= 90 ? "yellow" : kpis.avgViralityScore >= 80 ? "orange" : "green"}
                    />
                </div>

                {/* Scheduled & Recent Publications */}
                <div className="mb-12">
                    <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
                        <span className="bg-orange-500 w-2 h-8 rounded-full"></span>
                        <span>📈 Estado de Publicaciones</span>
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {scheduled.length === 0 ? (
                            <div className="col-span-full bg-[#0a0a0a] border border-[#1f1f1f] rounded-2xl p-12 text-center">
                                <div className="text-4xl mb-4">📭</div>
                                <div className="text-white font-bold mb-1">No hay actividad de publicación</div>
                                <div className="text-[#52525b] text-sm">Activa el AUTO en tus proyectos o programa clips manualmente.</div>
                            </div>
                        ) : (
                            scheduled.slice(0, 8).map((pub) => (
                                <div key={pub.id} className="bg-[#0d0d0d] border border-[#1f1f1f] rounded-xl p-5 hover:border-orange-500/40 transition-all group relative overflow-hidden">
                                    {/* Platform Indicator */}
                                    <div className="flex items-center justify-between mb-4">
                                        <div className={cn(
                                            "px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest",
                                            pub.platform === 'tiktok' ? "bg-white text-black" : "bg-red-600 text-white"
                                        )}>
                                            {pub.platform}
                                        </div>
                                        <div className="text-[10px] text-[#52525b] font-medium uppercase font-mono">
                                            {pub.status === 'success' || pub.status === 'completed'
                                                ? 'Publicado'
                                                : new Date(pub.scheduled_at).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
                                            }
                                        </div>
                                    </div>

                                    {/* Content */}
                                    <h3 className="font-bold text-sm mb-4 line-clamp-2 min-h-[40px] group-hover:text-white transition-colors">
                                        {pub.title || 'Clip Viral'}
                                    </h3>

                                    {/* Metrics / Status Overlay */}
                                    {(pub.status === 'success' || pub.status === 'completed') ? (
                                        <div className="grid grid-cols-3 gap-2 pt-4 border-t border-[#1f1f1f]">
                                            <div className="text-center">
                                                <div className="text-[10px] text-gray-500 uppercase font-black mb-1">Visitas</div>
                                                <div className="text-sm font-bold text-orange-400">{pub.views?.toLocaleString() || '0'}</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-[10px] text-gray-500 uppercase font-black mb-1">Likes</div>
                                                <div className="text-sm font-bold text-white">{pub.likes?.toLocaleString() || '0'}</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-[10px] text-gray-500 uppercase font-black mb-1">Coments</div>
                                                <div className="text-sm font-bold text-white">{pub.comments?.toLocaleString() || '0'}</div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex items-center gap-3 pt-4 border-t border-[#1f1f1f]">
                                            <div className={cn(
                                                "w-2 h-2 rounded-full",
                                                pub.status === 'pending' ? "bg-yellow-500 animate-pulse" : "bg-blue-500"
                                            )} />
                                            <span className="text-[10px] text-gray-500 uppercase font-black tracking-widest">
                                                {pub.status === 'pending' ? 'Programado' : 'Procesando...'}
                                            </span>
                                        </div>
                                    )}

                                    {/* Hover glow effect */}
                                    <div className="absolute -inset-1 bg-gradient-to-r from-orange-500/0 via-orange-500/5 to-orange-500/0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="mb-12">
                    <h2 className="text-2xl font-bold mb-4">Acciones Rápidas</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <button
                            onClick={() => router.push('/')}
                            className="bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 p-6 rounded-lg text-left transition group"
                        >
                            <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">➕</div>
                            <div className="font-bold text-lg">Nuevo Proyecto</div>
                            <div className="text-sm text-gray-200">Analizar video con IA</div>
                        </button>

                        <button
                            onClick={() => router.push('/schedule')}
                            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 p-6 rounded-lg text-left transition group"
                        >
                            <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">📅</div>
                            <div className="font-bold text-lg">Planificador</div>
                            <div className="text-sm text-gray-200">Gestionar programación</div>
                        </button>

                        <button
                            onClick={() => router.push('/connections')}
                            className="bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 p-6 rounded-lg text-left transition group"
                        >
                            <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">🔗</div>
                            <div className="font-bold text-lg">Conectividad</div>
                            <div className="text-sm text-gray-200">YouTube & TikTok</div>
                        </button>
                    </div>
                </div>

                {/* Projects Table */}
                <div className="bg-[#0a0a0a] rounded-lg border border-[#1f1f1f] overflow-hidden">
                    <div className="p-6 border-b border-[#1f1f1f]">
                        <h2 className="text-2xl font-bold">Proyectos Recientes</h2>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-[#111]">
                                <tr>
                                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-400">Video</th>
                                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-400">Estado / Progreso</th>
                                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-400">Clips</th>
                                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-400">Creado</th>
                                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-400">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#1f1f1f]">
                                {projects.length === 0 ? (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-12 text-center text-gray-400">
                                            No hay proyectos. Crea uno nuevo para comenzar.
                                        </td>
                                    </tr>
                                ) : (
                                    projects.map((project) => (
                                        <ProjectRow key={project.id} project={project} />
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}

interface KPICardProps {
    icon: string;
    title: string;
    value: number;
    subtitle: string;
    color: 'blue' | 'orange' | 'green' | 'purple' | 'yellow';
}

function KPICard({ icon, title, value, subtitle, color }: KPICardProps) {
    const colorClasses = {
        blue: 'from-blue-600/20 to-blue-800/20 border-blue-500/30',
        orange: 'from-orange-600/20 to-orange-800/20 border-orange-500/30',
        green: 'from-green-600/20 to-green-800/20 border-green-500/30',
        purple: 'from-purple-600/20 to-purple-800/20 border-purple-500/30',
        yellow: 'from-yellow-500/20 to-yellow-700/20 border-yellow-400/50'
    };

    return (
        <div className={`bg-gradient-to-br ${colorClasses[color]} border rounded-lg p-6`}>
            <div className="flex items-start justify-between mb-4">
                <span className="text-4xl">{icon}</span>
            </div>
            <div className="text-3xl font-bold mb-1">{value}</div>
            <div className="text-sm font-semibold text-gray-300 mb-1">{title}</div>
            <div className="text-xs text-gray-400">{subtitle}</div>
        </div>
    );
}

function ProjectRow({ project }: { project: Project }) {
    const router = useRouter();

    const isProcessing = project.project_status === 'PROCESSING';
    const targetProgress = project.progress || 0;
    const targetEta = project.estimated_time_remaining || 0;

    // Smooth progress animation: +1%/s toward target
    const [displayProgress, setDisplayProgress] = useState(targetProgress);
    const targetRef = useRef(targetProgress);
    useEffect(() => { targetRef.current = targetProgress; }, [targetProgress]);
    useEffect(() => {
        if (!isProcessing) { setDisplayProgress(targetProgress); return; }
        const t = setInterval(() => {
            setDisplayProgress(p => Math.min(p + 1, targetRef.current));
        }, 1000);
        return () => clearInterval(t);
    }, [isProcessing]);

    // Live countdown ETA
    const [displayEta, setDisplayEta] = useState(targetEta);
    useEffect(() => { if (targetEta > 0) setDisplayEta(targetEta); }, [targetEta]);
    useEffect(() => {
        if (!isProcessing) return;
        const t = setInterval(() => setDisplayEta(s => Math.max(s - 1, 0)), 1000);
        return () => clearInterval(t);
    }, [isProcessing]);

    const formatEta = (s: number) => {
        if (s <= 0) return '';
        const h = Math.floor(s / 3600);
        const m = Math.floor((s % 3600) / 60);
        const sec = s % 60;
        if (h > 0) return `~${h}h ${m > 0 ? m + 'm' : ''}`;
        if (m > 0 && sec > 0) return `~${m}m ${sec}s`;
        if (m > 0) return `~${m} min`;
        return `~${sec}s`;
    };

    const statusColors: Record<string, string> = {
        'QUEUED': 'bg-yellow-500/20 text-yellow-500',
        'PROCESSING': 'bg-blue-500/20 text-blue-500',
        'COMPLETED': 'bg-green-500/20 text-green-500',
        'FAILED': 'bg-red-500/20 text-red-500'
    };
    const statusLabels: Record<string, string> = {
        'QUEUED': 'En cola',
        'PROCESSING': 'Procesando',
        'COMPLETED': 'Completado',
        'FAILED': 'Error'
    };

    return (
        <tr className="hover:bg-[#111] transition">
            <td className="px-6 py-4">
                <div className="flex items-center gap-3">
                    {project.thumbnail_url && (
                        <img src={project.thumbnail_url} alt="" className="w-16 h-9 object-cover rounded" />
                    )}
                    <div>
                        <div className="font-semibold max-w-[200px] truncate" title={project.title}>{project.title || 'Sin título'}</div>
                        <div className="text-xs text-gray-400">{project.id.slice(0, 8)}</div>
                    </div>
                </div>
            </td>
            <td className="px-6 py-4">
                <div className="flex flex-col gap-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold w-fit ${statusColors[project.project_status] || statusColors.QUEUED}`}>
                        {statusLabels[project.project_status] || project.project_status}
                    </span>
                    {project.auto_publish_enabled && (
                        <span className="bg-blue-600/20 text-blue-400 text-[9px] font-black px-1.5 py-0.5 rounded border border-blue-500/20 w-fit">AUTO ON</span>
                    )}
                    {isProcessing && (
                        <div className="w-full max-w-[160px]">
                            <div className="w-full bg-gray-800 rounded-full h-1.5 mb-1">
                                <div
                                    className="bg-gradient-to-r from-orange-500 to-red-500 h-1.5 rounded-full transition-all duration-1000"
                                    style={{ width: `${displayProgress}%` }}
                                />
                            </div>
                            <div className="flex justify-between text-[10px] text-gray-400">
                                <span className="font-medium text-white">{displayProgress}%</span>
                                {displayEta > 0 ? (
                                    <span className="text-orange-400 font-medium">{formatEta(displayEta)}</span>
                                ) : (
                                    <span>Calculando...</span>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </td>
            <td className="px-6 py-4">
                <span className="text-gray-300">{project.clips_count || '~'} clips</span>
            </td>
            <td className="px-6 py-4">
                <span className="text-gray-400 text-sm">
                    {new Date(project.created_at).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })}
                </span>
            </td>
            <td className="px-6 py-4">
                {project.project_status === 'COMPLETED' && (
                    <button
                        onClick={() => router.push(`/studio/${project.id}`)}
                        className="bg-orange-600 hover:bg-orange-700 px-4 py-2 rounded text-sm font-semibold transition"
                    >
                        Ver Resultados
                    </button>
                )}
            </td>
        </tr>
    );
}

function cn(...inputs: any[]) {
    return inputs.filter(Boolean).join(' ');
}
