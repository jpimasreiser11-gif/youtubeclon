"use client";

import { useState, useEffect, type ReactNode } from 'react';
import { useSearchParams } from 'next/navigation';
import { CheckCircle2, AlertCircle, Link2, PlugZap, ShieldCheck, Youtube, Smartphone } from 'lucide-react';

interface Connection {
    platform: 'youtube' | 'tiktok';
    connected: boolean;
    accountName?: string;
    lastSync?: string;
    credentialsType?: string | null;
    expiresAt?: string | null;
    tokenObtainedAt?: string | null;
    lastValidatedAt?: string | null;
}

type Banner = {
    type: 'success' | 'error' | 'info';
    text: string;
};

export default function ConnectionsClient() {
    const [connections, setConnections] = useState<Connection[]>([
        { platform: 'youtube', connected: false },
        { platform: 'tiktok', connected: false }
    ]);
    const [loading, setLoading] = useState(false);
    const [busyPlatform, setBusyPlatform] = useState<'youtube' | 'tiktok' | null>(null);
    const [banner, setBanner] = useState<Banner | null>(null);
    const searchParams = useSearchParams();

    useEffect(() => {
        checkConnections();
        const ytStatus = searchParams.get('youtube');
        if (ytStatus === 'pending') {
            setBanner({ type: 'info', text: 'Se abrió la autorización de YouTube. Aprueba permisos y vuelve a esta pestaña.' });
            const interval = setInterval(async () => {
                await checkConnections();
            }, 5000);
            setTimeout(() => clearInterval(interval), 120000);
        } else if (ytStatus === 'connected') {
            setBanner({ type: 'success', text: 'YouTube conectado correctamente. Ya puedes publicar desde el sistema viral.' });
            checkConnections();
        } else if (ytStatus === 'error') {
            setBanner({ type: 'error', text: 'No se completó OAuth de YouTube. Revisa client id/secret y redirect URI.' });
        }
    }, []);

    const checkConnections = async () => {
        try {
            const res = await fetch('/api/connections/status');
            const data = await res.json();
            if (data.connections) {
                setConnections(data.connections);
            }
        } catch (error) {
            console.error('Error checking connections:', error);
        }
    };

    const handleYouTubeConnect = async () => {
        setLoading(true);
        setBusyPlatform('youtube');
        try {
            window.location.href = '/api/auth/youtube';
        } catch (error) {
            console.error('Error connecting YouTube:', error);
            setLoading(false);
            setBusyPlatform(null);
        }
    };

    const handleYouTubeTest = async () => {
        setLoading(true);
        setBusyPlatform('youtube');
        try {
            const res = await fetch('/api/auth/youtube/test');
            const data = await res.json();
            if (res.ok && data.ok) {
                setBanner({ type: 'success', text: `YouTube OK: ${data.accountName || 'Canal conectado'}` });
                await checkConnections();
            } else {
                setBanner({ type: 'error', text: `Error YouTube: ${data.error || 'No se pudo validar la conexión'}` });
            }
        } catch (error) {
            setBanner({ type: 'error', text: 'Error de red al validar YouTube OAuth.' });
        } finally {
            setLoading(false);
            setBusyPlatform(null);
        }
    };

    const handleTikTokConnect = async () => {
        const sessionCookie = prompt(
            'Como obtener tu cookie de TikTok:\n\n' +
            '1. Abre TikTok.com en tu navegador y haz login\n' +
            '2. Presiona F12 para abrir DevTools\n' +
            '3. Ve a Application > Cookies > tiktok.com\n' +
            '4. Busca "sessionid" y copia su valor\n' +
            '5. Pégalo aquí abajo:'
        );
        if (!sessionCookie) return;

        setLoading(true);
        setBusyPlatform('tiktok');
        try {
            const res = await fetch('/api/tiktok/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sessionCookie })
            });

            const data = await res.json();
            if (data.success) {
                setBanner({ type: 'success', text: 'TikTok conectado correctamente. Ya puedes programar publicaciones.' });
                await checkConnections();
            } else {
                setBanner({ type: 'error', text: 'Error: ' + (data.error || 'Cookie inválida') });
            }
        } catch (error) {
            setBanner({ type: 'error', text: 'Error al conectar TikTok. Inténtalo de nuevo.' });
        } finally {
            setLoading(false);
            setBusyPlatform(null);
        }
    };

    const handleDisconnect = async (platform: 'youtube' | 'tiktok') => {
        if (!confirm(`¿Desconectar ${platform}?`)) return;

        setBusyPlatform(platform);
        setLoading(true);
        try {
            await fetch('/api/connections/disconnect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ platform })
            });
            await checkConnections();
            setBanner({ type: 'info', text: `${platform} desconectado.` });
        } catch (error) {
            console.error('Error disconnecting:', error);
            setBanner({ type: 'error', text: `No se pudo desconectar ${platform}.` });
        } finally {
            setLoading(false);
            setBusyPlatform(null);
        }
    };

    const connectedCount = connections.filter(c => c.connected).length;
    const yt = connections.find(c => c.platform === 'youtube');
    const tk = connections.find(c => c.platform === 'tiktok');

    return (
        <div className="min-h-screen bg-[#0b0b0d] text-white p-6 md:p-10 relative overflow-hidden">
            <div className="pointer-events-none absolute -top-24 -right-24 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl" />
            <div className="pointer-events-none absolute -bottom-24 -left-24 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl" />

            <div className="max-w-5xl mx-auto relative">
                <div className="mb-8">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-white/5 text-xs text-gray-300 mb-4">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                        Seguridad OAuth + Conexiones activas
                    </div>

                    <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-3">
                        Centro de Conexiones
                    </h1>
                    <p className="text-gray-300 max-w-2xl">
                        Conecta YouTube y TikTok para publicar automáticamente desde el sistema viral con control de estado en tiempo real.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <MetricCard label="Conexiones activas" value={`${connectedCount}/2`} accent="text-white" />
                    <MetricCard label="YouTube" value={yt?.connected ? 'Conectado' : 'Pendiente'} accent="text-red-400" />
                    <MetricCard label="TikTok" value={tk?.connected ? 'Conectado' : 'Pendiente'} accent="text-cyan-300" />
                </div>

                {banner && (
                    <div
                        className={`mb-6 p-4 rounded-xl border text-sm flex items-center gap-2 ${banner.type === 'success'
                            ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-200'
                            : banner.type === 'error'
                                ? 'bg-red-500/10 border-red-500/40 text-red-200'
                                : 'bg-amber-500/10 border-amber-500/40 text-amber-200'
                            }`}
                    >
                        {banner.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : banner.type === 'error' ? <AlertCircle className="w-4 h-4" /> : <Link2 className="w-4 h-4" />}
                        {banner.text}
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <ConnectionCard
                        platform="YouTube"
                        icon={<Youtube className="w-7 h-7 text-red-400" />}
                        connected={yt?.connected || false}
                        accountName={yt?.accountName}
                        lastValidatedAt={yt?.lastValidatedAt}
                        expiresAt={yt?.expiresAt}
                        onConnect={handleYouTubeConnect}
                        onDisconnect={() => handleDisconnect('youtube')}
                        onTest={handleYouTubeTest}
                        scopes={["Subir videos", "Ver canal", "Programar publicaciones"]}
                        loading={loading}
                        busy={busyPlatform === 'youtube'}
                        accent="youtube"
                    />

                    <ConnectionCard
                        platform="TikTok"
                        icon={<Smartphone className="w-7 h-7 text-cyan-300" />}
                        connected={tk?.connected || false}
                        accountName={tk?.accountName}
                        lastValidatedAt={tk?.lastValidatedAt}
                        expiresAt={tk?.expiresAt}
                        onConnect={handleTikTokConnect}
                        onDisconnect={() => handleDisconnect('tiktok')}
                        method="cookie"
                        scopes={["Subir videos"]}
                        loading={loading}
                        busy={busyPlatform === 'tiktok'}
                        accent="tiktok"
                    />
                </div>

                <div className="mt-8 p-5 bg-[#101114] border border-white/10 rounded-2xl">
                    <h3 className="text-amber-300 font-semibold mb-3 flex items-center gap-2">
                        <PlugZap className="w-4 h-4" />
                        Guía rápida
                    </h3>
                    <ul className="text-sm text-gray-300 space-y-2">
                        <li>• YouTube usa OAuth oficial y permite validar token desde el botón de prueba.</li>
                        <li>• TikTok usa cookie de sesión temporal y puedes renovarla cuando quieras.</li>
                        <li>• Si una conexión falla, el sistema hace fallback al flujo clásico automáticamente.</li>
                        <li>• Puedes desconectar en cualquier momento sin perder tus clips generados.</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}

function MetricCard({ label, value, accent }: { label: string; value: string; accent: string }) {
    return (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs text-gray-400 mb-1">{label}</p>
            <p className={`text-2xl font-bold ${accent}`}>{value}</p>
        </div>
    );
}

function formatDate(value?: string | null) {
    if (!value) return 'N/D';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return 'N/D';
    return d.toLocaleString();
}

interface ConnectionCardProps {
    platform: string;
    icon: ReactNode;
    connected: boolean;
    accountName?: string;
    lastValidatedAt?: string | null;
    expiresAt?: string | null;
    onConnect: () => void;
    onDisconnect: () => void;
    onTest?: () => void;
    scopes: string[];
    method?: 'oauth' | 'cookie';
    loading?: boolean;
    busy?: boolean;
    accent?: 'youtube' | 'tiktok';
}

function ConnectionCard({
    platform,
    icon,
    connected,
    accountName,
    lastValidatedAt,
    expiresAt,
    onConnect,
    onDisconnect,
    onTest,
    scopes,
    method = 'oauth',
    loading,
    busy,
    accent = 'youtube'
}: ConnectionCardProps) {
    const accentClass = accent === 'youtube'
        ? 'from-red-500/20 to-amber-500/10 border-red-500/30'
        : 'from-cyan-500/20 to-slate-500/10 border-cyan-500/30';

    return (
        <div className={`bg-gradient-to-br ${accentClass} border rounded-2xl p-6 backdrop-blur-sm`}>
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-black/30 border border-white/10 flex items-center justify-center">{icon}</div>
                    <div>
                        <h2 className="text-xl font-bold">{platform}</h2>
                        {connected && accountName && (
                            <p className="text-sm text-gray-300">{accountName}</p>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {connected ? (
                        <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                    ) : (
                        <span className="w-3 h-3 bg-gray-500 rounded-full"></span>
                    )}
                    <span className="text-sm text-gray-300">
                        {connected ? 'Conectado' : 'Desconectado'}
                    </span>
                </div>
            </div>

            <div className="mb-4">
                <p className="text-sm text-gray-300 mb-2">Permisos:</p>
                <div className="flex flex-wrap gap-2">
                    {scopes.map((scope) => (
                        <span key={scope} className="text-xs bg-black/30 px-3 py-1 rounded-full text-gray-200 border border-white/10">
                            {scope}
                        </span>
                    ))}
                </div>
            </div>

            {connected && (
                <div className="mb-4 text-xs text-gray-300 space-y-1 border border-white/10 rounded-lg p-3 bg-black/20">
                    <div>Última validación OAuth: <span className="text-white">{formatDate(lastValidatedAt)}</span></div>
                    <div>Expiración token: <span className="text-white">{formatDate(expiresAt)}</span></div>
                </div>
            )}

            {method === 'cookie' && !connected && (
                <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-xs text-yellow-200">
                    <strong>Método Cookie:</strong> Necesitarás copiar tu cookie de sesión desde las DevTools del navegador
                </div>
            )}

            <button
                onClick={connected ? onDisconnect : onConnect}
                disabled={loading}
                className={`w-full py-3 rounded-xl font-semibold transition ${connected
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-amber-500 text-black hover:bg-amber-400'
                    } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
                {busy ? 'Procesando...' : connected ? 'Desconectar' : `Conectar ${platform}`}
            </button>

            {connected && platform === 'YouTube' && onTest && (
                <button
                    onClick={onTest}
                    disabled={loading}
                    className={`mt-2 w-full py-2 rounded-xl font-semibold transition bg-[#1b2635] hover:bg-[#26354a] ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                    Probar YouTube OAuth
                </button>
            )}
        </div>
    );
}
