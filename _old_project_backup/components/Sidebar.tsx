import React, { useState } from 'react';
import { NavTab } from '../types';
import { Link } from 'react-router-dom';

interface SidebarProps {
    activeTab: NavTab;
    profileName: string;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, profileName }) => {
    const [collapsed, setCollapsed] = useState(false);

    const menuItems = [
        { id: NavTab.DASHBOARD, icon: 'space_dashboard', label: 'Dashboard', path: '/' },
        { id: NavTab.TUTOR, icon: 'chat_bubble', label: 'AI Tutor', path: '/chat' },
        { id: NavTab.CREATOR, icon: 'school', label: 'Course Creator', path: '/creator' },
        { id: NavTab.VISION, icon: 'visibility', label: 'Vision Tools', path: '/vision' },
    ];

    return (
        <aside
            className={`${collapsed ? 'w-20' : 'w-64'} h-full bg-white dark:bg-[#0f172a] border-r border-slate-200 dark:border-slate-800 transition-all duration-300 ease-in-out flex flex-col relative z-20 shadow-xl shadow-slate-200/50 dark:shadow-none`}
        >
            <button
                onClick={() => setCollapsed(!collapsed)}
                className="absolute -right-3 top-8 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-full p-1 text-slate-400 hover:text-primary transition-colors hover:scale-110 shadow-sm"
            >
                <span className="material-symbols-outlined text-sm">{collapsed ? 'chevron_right' : 'chevron_left'}</span>
            </button>

            <div className={`p-6 flex items-center gap-3 ${collapsed ? 'justify-center' : ''} mb-6`}>
                <div className="size-10 bg-gradient-to-tr from-primary to-blue-400 rounded-xl flex items-center justify-center shadow-lg shadow-primary/30 shrink-0">
                    <span className="material-symbols-outlined text-white text-xl">auto_stories</span>
                </div>
                {!collapsed && (
                    <div className="animate-in fade-in slide-in-from-left-4 duration-500">
                        <h1 className="font-extrabold text-xl tracking-tight text-slate-900 dark:text-white">EduMind</h1>
                    </div>
                )}
            </div>

            <nav className="flex-1 px-3 space-y-2">
                {menuItems.map((item) => {
                    const isActive = activeTab === item.id;
                    return (
                        <Link
                            key={item.id}
                            to={item.path}
                            className={`
                group flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200
                ${isActive
                                    ? 'bg-primary text-white shadow-lg shadow-primary/25 translate-x-1'
                                    : 'text-slate-500 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800/50 dark:hover:text-slate-200'
                                }
                ${collapsed ? 'justify-center' : ''}
              `}
                        >
                            <span className={`material-symbols-outlined transition-transform duration-300 ${isActive ? '' : 'group-hover:scale-110'}`}>
                                {item.icon}
                            </span>
                            {!collapsed && (
                                <span className={`font-semibold text-sm whitespace-nowrap ${isActive ? '' : ''}`}>
                                    {item.label}
                                </span>
                            )}

                            {/* Tooltip for collapsed state */}
                            {collapsed && (
                                <div className="absolute left-full ml-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity">
                                    {item.label}
                                </div>
                            )}
                        </Link>
                    );
                })}
            </nav>

            <div className={`p-4 mt-auto border-t border-slate-100 dark:border-slate-800/50 ${collapsed ? 'items-center' : ''}`}>
                <div className={`flex items-center gap-3 p-2 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 ${collapsed ? 'justify-center p-0 size-10 rounded-full bg-transparent border-none' : ''}`}>
                    {!collapsed ? (
                        <>
                            <div className="size-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs shrink-0">
                                {profileName.charAt(0)}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-bold text-slate-900 dark:text-white truncate">{profileName}</p>
                                <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Student</p>
                            </div>
                            <Link to="/settings" className="p-1.5 hover:bg-white dark:hover:bg-slate-700 rounded-lg text-slate-400 hover:text-primary transition-colors">
                                <span className="material-symbols-outlined text-lg">settings</span>
                            </Link>
                        </>
                    ) : (
                        <Link to="/settings" className="flex items-center justify-center size-10 rounded-xl text-slate-400 hover:text-primary hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                            <span className="material-symbols-outlined">settings</span>
                        </Link>
                    )}
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
