"use client";
import React from 'react';
import { Sidebar } from '@/components/sidebar';
import { TrendingUp, Users, Eye, Heart, BarChart2, Zap, Clock } from 'lucide-react';

export default function AnalyticsPage() {
    return (
        <div className="min-h-screen bg-[#0a0a0a] font-sans text-white overflow-x-hidden selection:bg-white/20">
            <Sidebar />
            <main className="ml-[60px] min-h-screen flex flex-col items-center relative pt-24 pb-20 px-10">
                <div className="w-full max-w-[1200px] space-y-10">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-blue-500/20 flex items-center justify-center border border-blue-500/30">
                            <BarChart2 className="w-6 h-6 text-blue-400" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-black italic tracking-tight"> ANALÍTICAS </h1>
                            <p className="text-[#a1a1aa] text-sm font-medium"> Rendimiento de tus clips virales en tiempo real </p>
                        </div>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        {[
                            { label: 'Clips Totales', value: '142', icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
                            { label: 'Puntuación Viral Media', value: '88%', icon: TrendingUp, color: 'text-green-400', bg: 'bg-green-400/10' },
                            { label: 'Espectadores Únicos', value: '12.4k', icon: Users, color: 'text-purple-400', bg: 'bg-purple-400/10' },
                            { label: 'Tiempo Ahorrado', value: '48h', icon: Clock, color: 'text-blue-400', bg: 'bg-blue-400/10' },
                        ].map((stat, i) => (
                            <div key={i} className="bg-[#111111] border border-[#1f1f1f] p-6 rounded-[24px] space-y-4 hover:border-[#3f3f46] transition-all group">
                                <div className={`w-10 h-10 rounded-xl ${stat.bg} flex items-center justify-center`}>
                                    <stat.icon className={`w-5 h-5 ${stat.color}`} />
                                </div>
                                <div>
                                    <p className="text-[#a1a1aa] text-xs font-bold uppercase tracking-wider">{stat.label}</p>
                                    <p className="text-3xl font-black mt-1 group-hover:scale-105 transition-transform origin-left">{stat.value}</p>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Mock Chart Area */}
                    <div className="bg-[#111111] border border-[#1f1f1f] rounded-[32px] p-8 h-[400px] flex flex-col">
                        <h3 className="text-lg font-bold mb-8">Tendencia de Crecimiento</h3>
                        <div className="flex-1 flex items-end gap-3 px-4">
                            {[40, 70, 45, 90, 65, 80, 55, 95, 75, 85, 60, 100].map((h, i) => (
                                <div key={i} className="flex-1 bg-gradient-to-t from-blue-600/20 to-blue-400/40 rounded-t-lg transition-all hover:to-blue-400 relative group" style={{ height: `${h}%` }}>
                                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-white text-black text-[10px] font-bold px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                                        {h}% viral
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="flex justify-between mt-6 px-4 text-[10px] font-bold text-[#3f3f46] uppercase tracking-widest">
                            <span>Ene</span><span>Feb</span><span>Mar</span><span>Abr</span><span>May</span><span>Jun</span><span>Jul</span><span>Ago</span><span>Sep</span><span>Oct</span><span>Nov</span><span>Dic</span>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
