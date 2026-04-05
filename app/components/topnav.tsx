'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function TopNav() {
    const pathname = usePathname();

    const navItems = [
        { href: '/', label: '🎬 Nuevo Video', icon: '➕' },
        { href: '/dashboard', label: '📊 Dashboard', icon: '📊' },
        { href: '/clipradar', label: '📡 ClipRadar', icon: '📡' },
        { href: '/schedule', label: '📅 Planificador', icon: '📅' },
        { href: '/connections', label: '🔗 Conexiones', icon: '🔗' },
    ];

    const isActive = (href: string) => {
        if (href === '/') {
            return pathname === '/';
        }
        return pathname?.startsWith(href);
    };

    return (
        <nav className="bg-gradient-to-r from-[#0a0a0a] to-[#1a1a1a] border-b border-[#2a2a2a] sticky top-0 z-50 backdrop-blur-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-3 group">
                        <div className="text-3xl group-hover:scale-110 transition-transform">🔥</div>
                        <div className="flex flex-col">
                            <span className="text-xl font-bold bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">
                                Viral Clips
                            </span>
                            <span className="text-xs text-gray-400">AI-Powered</span>
                        </div>
                    </Link>

                    {/* Navigation Links */}
                    <div className="hidden md:flex items-center gap-2">
                        {navItems.map((item) => (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`
                  px-4 py-2 rounded-lg font-semibold text-sm transition-all
                  ${isActive(item.href)
                                        ? 'bg-orange-600 text-white shadow-lg shadow-orange-600/50'
                                        : 'text-gray-300 hover:bg-[#2a2a2a] hover:text-white'
                                    }
                `}
                            >
                                <span className="inline md:hidden">{item.icon}</span>
                                <span className="hidden md:inline">{item.label}</span>
                            </Link>
                        ))}
                    </div>

                    {/* User Menu */}
                    <div className="flex items-center gap-3">
                        <Link
                            href="/account"
                            className="text-gray-400 hover:text-white transition text-2xl"
                            title="Cuenta"
                        >
                            👤
                        </Link>
                    </div>
                </div>

                {/* Mobile Navigation */}
                <div className="md:hidden pb-3">
                    <div className="flex gap-2 overflow-x-auto">
                        {navItems.map((item) => (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`
                  flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold whitespace-nowrap transition-all
                  ${isActive(item.href)
                                        ? 'bg-orange-600 text-white'
                                        : 'bg-[#1a1a1a] text-gray-300 hover:bg-[#2a2a2a]'
                                    }
                `}
                            >
                                <span>{item.icon}</span>
                                <span>{item.label}</span>
                            </Link>
                        ))}
                    </div>
                </div>
            </div>
        </nav>
    );
}
