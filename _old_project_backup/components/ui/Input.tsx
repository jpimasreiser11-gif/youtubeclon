import React, { InputHTMLAttributes, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    icon?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({
    className = '',
    label,
    error,
    icon,
    ...props
}, ref) => {
    return (
        <div className="w-full space-y-1.5">
            {label && (
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider ml-1">
                    {label}
                </label>
            )}
            <div className="relative group">
                {icon && (
                    <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary transition-colors pointer-events-none">
                        <span className="material-symbols-outlined text-[20px]">{icon}</span>
                    </div>
                )}
                <input
                    ref={ref}
                    className={`
            w-full bg-white dark:bg-slate-800/50 
            border-2 border-slate-200 dark:border-slate-700/50 
            rounded-xl py-2.5 ${icon ? 'pl-10' : 'pl-4'} pr-4 
            text-sm font-medium text-slate-900 dark:text-white
            placeholder:text-slate-400
            transition-all duration-200
            focus:border-primary focus:ring-0
            disabled:opacity-50 disabled:bg-slate-100 dark:disabled:bg-slate-800
            ${error ? 'border-red-500 focus:border-red-500' : ''}
            ${className}
          `}
                    {...props}
                />
            </div>
            {error && (
                <p className="text-xs text-red-500 font-medium ml-1 animate-in slide-in-from-left-1">
                    {error}
                </p>
            )}
        </div>
    );
});

Input.displayName = 'Input';
