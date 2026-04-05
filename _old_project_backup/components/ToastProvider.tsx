import React, { createContext, useContext, useState, useCallback } from 'react';

type ToastType = 'success' | 'error' | 'info';

interface Toast {
    id: string;
    message: string;
    type: ToastType;
}

interface ToastContextType {
    showToast: (message: string, type: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const showToast = useCallback((message: string, type: ToastType) => {
        const id = Date.now().toString();
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, 3000);
    }, []);

    return (
        <ToastContext.Provider value={{ showToast }}>
            {children}
            <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2 pointer-events-none">
                {toasts.map(toast => (
                    <div
                        key={toast.id}
                        className={`
              pointer-events-auto
              flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl border
              animate-in slide-in-from-bottom-2 fade-in duration-300
              ${toast.type === 'success' ? 'bg-white dark:bg-slate-800 border-green-500/20 text-green-600 dark:text-green-400' : ''}
              ${toast.type === 'error' ? 'bg-white dark:bg-slate-800 border-red-500/20 text-red-600 dark:text-red-400' : ''}
              ${toast.type === 'info' ? 'bg-white dark:bg-slate-800 border-blue-500/20 text-blue-600 dark:text-blue-400' : ''}
            `}
                    >
                        <span className="material-symbols-outlined text-xl">
                            {toast.type === 'success' && 'check_circle'}
                            {toast.type === 'error' && 'error'}
                            {toast.type === 'info' && 'info'}
                        </span>
                        <span className="font-semibold text-sm pr-2 text-slate-900 dark:text-white">{toast.message}</span>
                    </div>
                ))}
            </div>
        </ToastContext.Provider>
    );
};

export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) throw new Error('useToast must be used within a ToastProvider');
    return context;
};
