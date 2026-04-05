import React from 'react';

interface CardProps {
    children: React.ReactNode;
    className?: string;
    hover?: boolean;
}

export const Card: React.FC<CardProps> = ({ children, className = '', hover = false }) => {
    return (
        <div className={`
      bg-white dark:bg-slate-800/80 backdrop-blur-sm
      border border-slate-200 dark:border-slate-700/50
      rounded-2xl p-6 shadow-sm
      ${hover ? 'transition-all duration-300 hover:shadow-lg hover:shadow-primary/5 hover:border-primary/20 hover:-translate-y-0.5' : ''}
      ${className}
    `}>
            {children}
        </div>
    );
};
