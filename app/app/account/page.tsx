"use client";
import React from 'react';
import { Sidebar } from '@/components/sidebar';
import { User, Mail, Shield, CreditCard, ChevronRight, LogOut, Sparkles } from 'lucide-react';

export default function AccountPage() {
    return (
        <div className="min-h-screen bg-[#0a0a0a] font-sans text-white overflow-x-hidden selection:bg-white/20">
            <Sidebar />
            <main className="ml-[60px] min-h-screen flex flex-col items-center relative pt-24 pb-20 px-10">
                <div className="w-full max-w-[800px] space-y-10">

                    {/* Header */}
                    <div className="flex items-center gap-6">
                        <div className="w-24 h-24 rounded-[32px] bg-gradient-to-br from-[#f97316] to-[#ea580c] flex items-center justify-center text-4xl font-black shadow-2xl">
                            J
                        </div>
                        <div>
                            <h1 className="text-4xl font-black italic tracking-tighter uppercase leading-none"> Mi Cuenta </h1>
                            <p className="text-[#a1a1aa] text-base mt-2 font-medium"> j.pima@example.com </p>
                            <div className="mt-4 flex items-center gap-2">
                                <span className="bg-[#1a1a1a] border border-[#2d2d2d] px-3 py-1 rounded-full text-[10px] font-black text-orange-500 uppercase tracking-widest flex items-center gap-1.5">
                                    <Sparkles className="w-3 h-3" /> Plan Sovereign
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Settings Sections */}
                    <div className="space-y-4">
                        {[
                            { label: 'Perfil y Datos', icon: User, desc: 'Gestiona tu información personal' },
                            { label: 'Seguridad', icon: Shield, desc: 'Contraseña y verificación en dos pasos' },
                            { label: 'Suscripción', icon: CreditCard, desc: 'Detalles de facturación y límites' },
                            { label: 'Notificaciones', icon: Mail, desc: 'Alertas de renderizado y correos' },
                        ].map((item, i) => (
                            <button key={i} className="w-full bg-[#111111] border border-[#1f1f1f] p-6 rounded-[24px] flex items-center justify-between group hover:border-[#3f3f46] transition-all">
                                <div className="flex items-center gap-6 text-left">
                                    <div className="w-12 h-12 rounded-2xl bg-[#0a0a0a] border border-[#1f1f1f] flex items-center justify-center group-hover:bg-white group-hover:text-black transition-all">
                                        <item.icon className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <p className="text-lg font-bold">{item.label}</p>
                                        <p className="text-[#a1a1aa] text-sm font-medium">{item.desc}</p>
                                    </div>
                                </div>
                                <ChevronRight className="w-5 h-5 text-[#3f3f46] group-hover:text-white transition-colors" />
                            </button>
                        ))}
                    </div>

                    {/* Danger Zone */}
                    <div className="pt-10 border-t border-[#1f1f1f] flex items-center justify-between">
                        <button className="flex items-center gap-2 text-red-500 font-bold hover:underline">
                            <LogOut className="w-5 h-5" /> Cerrar sesión
                        </button>
                        <p className="text-[10px] font-black text-[#1f1f1f] uppercase tracking-[0.3em]">
                            Edumind AI Sovereign Engine 1.0
                        </p>
                    </div>

                </div>
            </main>
        </div>
    );
}
