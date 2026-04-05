"use client";
import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { signOut, useSession } from "next-auth/react";
import { Home, LayoutGrid, Folder, Calendar, BarChart2, Link as LinkIcon, LogOut, ChevronRight, Sparkles, Radio } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Sidebar() {
    const pathname = usePathname();
    const { data: session } = useSession();
    const [mounted, setMounted] = React.useState(false);

    React.useEffect(() => {
        setMounted(true);
    }, []);

    const NavItem = ({ icon: Icon, id, href = '#' }: { icon: any, id: string, href?: string }) => {
        const isActive = pathname === href || (href === '/' && pathname === '');

        return (
            <Link
                href={href}
                className={cn(
                    "w-10 h-10 flex items-center justify-center rounded-lg transition-all duration-200 group relative",
                    isActive
                        ? "text-white"
                        : "text-[#a1a1aa] hover:text-white"
                )}
            >
                <Icon className="w-5 h-5" />
                {isActive && (
                    <div className="absolute left-0 w-1 h-5 bg-white rounded-r-full" />
                )}
            </Link>
        );
    };

    return (
        <div className="fixed left-0 top-0 bottom-0 w-[60px] bg-[#000000] border-r border-[#1f1f1f] flex flex-col items-center py-4 z-[100]">

            {/* Collapse / Arrow icon */}
            <button className="w-10 h-10 flex items-center justify-center text-[#a1a1aa] hover:text-white mb-4">
                <ChevronRight className="w-5 h-5" />
            </button>

            {/* User Avatar - Orange circle with Link to Account */}
            <Link suppressHydrationWarning href="/account" className="w-9 h-9 rounded-full overflow-hidden bg-[#f97316] flex items-center justify-center text-white font-medium text-sm mb-8 cursor-pointer shadow-lg hover:scale-105 transition-transform">
                {mounted ? (
                    session?.user?.image ? (
                        <img src={session.user.image} alt="User" className="w-full h-full object-cover" />
                    ) : (
                        session?.user?.name?.[0]?.toUpperCase() || 'J'
                    )
                ) : (
                    'J'
                )}
            </Link>

            {/* Navigation Group */}
            <div className="flex flex-col items-center gap-3">
                <NavItem icon={Home} id="home" href="/" />
                <NavItem icon={LayoutGrid} id="grid" href="/" />
                <NavItem icon={Folder} id="folder" href="/projects" />
                <NavItem icon={Calendar} id="calendar" href="/calendar" />
                <NavItem icon={BarChart2} id="stats" href="/analytics" />
                <NavItem icon={Sparkles} id="motor-b" href="/motor-b" />
                <NavItem icon={Radio} id="clipradar" href="/clipradar" />
                <NavItem icon={LinkIcon} id="link" href="/links" />
            </div>

            {/* Logout at bottom */}
            <div className="mt-auto pb-4">
                <button
                    onClick={() => signOut({ callbackUrl: "/login" })}
                    className="w-10 h-10 flex items-center justify-center text-[#a1a1aa] hover:text-red-500 transition-colors"
                >
                    <LogOut className="w-5 h-5" />
                </button>
            </div>
        </div>
    );
}
