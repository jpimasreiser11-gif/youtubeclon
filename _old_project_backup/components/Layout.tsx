import React from 'react';
import { useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import { NavTab, UserProfile } from '../types';

interface LayoutProps {
    children: React.ReactNode;
    profile: UserProfile | null;
}

const Layout: React.FC<LayoutProps> = ({ children, profile }) => {
    const location = useLocation();

    const getActiveTab = (pathname: string): NavTab => {
        if (pathname === '/') return NavTab.DASHBOARD;
        if (pathname.startsWith('/chat')) return NavTab.TUTOR;
        if (pathname.startsWith('/creator')) return NavTab.CREATOR;
        if (pathname.startsWith('/vision')) return NavTab.VISION;
        return NavTab.DASHBOARD;
    };

    return (
        <div className="flex h-screen bg-slate-50 dark:bg-[#0f172a] overflow-hidden selection:bg-primary/20">
            <div className="relative z-50">
                <Sidebar activeTab={getActiveTab(location.pathname)} profileName={profile?.name || 'Explorer'} />
            </div>
            <div className="flex-1 flex flex-col relative h-full w-full max-w-[100vw] overflow-hidden">
                {/* Background Gradients */}
                <div className="max-md:hidden absolute top-0 left-0 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[100px] -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
                <div className="max-md:hidden absolute bottom-0 right-0 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-[100px] translate-x-1/2 translate-y-1/2 pointer-events-none" />

                {children}
            </div>
        </div>
    );
};

export default Layout;
