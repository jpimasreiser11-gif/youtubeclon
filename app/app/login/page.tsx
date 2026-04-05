"use client";
import React from 'react';
import { signIn } from "next-auth/react";
import { Sparkles, ArrowRight } from 'lucide-react';

export default function LoginPage() {
    return (
        <div className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center p-6 text-white font-sans selection:bg-white/10">

            {/* Background Glow */}
            <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-orange-500/10 blur-[120px] rounded-full -z-10" />

            <div className="w-full max-w-[440px] space-y-10 animate-fade-in text-center">

                {/* Logo Section */}
                <div className="space-y-4">
                    <div className="w-20 h-20 bg-gradient-to-br from-[#f97316] to-[#ea580c] rounded-[32px] mx-auto flex items-center justify-center shadow-2xl shadow-orange-500/20">
                        <Sparkles className="w-10 h-10 text-white" />
                    </div>
                    <h1 className="text-4xl font-black italic tracking-tighter uppercase leading-none">
                        Project Sovereign
                    </h1>
                    <p className="text-[#a1a1aa] font-medium text-lg italic">
                        Tu fábrica personal de clips virales
                    </p>
                </div>

                {/* Login Card */}
                <div className="bg-[#111111] border border-[#1f1f1f] rounded-[40px] p-10 space-y-8 shadow-2xl">
                    <div className="space-y-2">
                        <h2 className="text-2xl font-bold">Bienvenido</h2>
                        <p className="text-[#52525b] text-sm font-medium leading-relaxed">
                            Inicia sesión con tu cuenta de Google para acceder a tus proyectos y procesamiento real de IA.
                        </p>
                    </div>

                    <button
                        onClick={() => signIn("google", { redirectTo: "/" })}
                        className="w-full bg-white text-black h-14 rounded-2xl flex items-center justify-center gap-3 font-black text-base hover:bg-[#e4e4e7] transition-all group active:scale-95"
                    >
                        <img src="https://www.google.com/favicon.ico" className="w-5 h-5" alt="Google" />
                        Continuar con Google
                        <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </button>

                    <div className="pt-4">
                        <p className="text-[10px] font-black text-[#27272a] uppercase tracking-[0.4em]">
                            Sovereign Engine v2.0
                        </p>
                    </div>
                </div>

                {/* Footer Disclaimer */}
                <p className="text-[11px] text-[#3f3f46] font-medium leading-relaxed px-10">
                    Al continuar, aceptas que Project Sovereign procesará tus vídeos y datos de forma local y soberana.
                </p>
            </div>
        </div>
    );
}
