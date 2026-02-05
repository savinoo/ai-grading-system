import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: string;
  iconColor?: string;
  borderAccent?: string;
}

export const StatCard: React.FC<StatCardProps> = ({ 
  title, 
  value, 
  icon, 
  iconColor = 'text-slate-500',
  borderAccent 
}) => {
  return (
    <div className={`bg-white dark:bg-slate-800/50 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col gap-1 ${borderAccent ? `border-l-4 ${borderAccent}` : ''}`}>
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
        {title}
      </p>
      <div className="flex items-center justify-between mt-1">
        <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
          {value}
        </h3>
        <span className={`material-symbols-outlined ${iconColor} opacity-40`}>
          {icon}
        </span>
      </div>
    </div>
  );
};
