import React, { ReactNode } from 'react';

interface DashboardHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({ title, subtitle, actions }) => {
  return (
    <header className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md px-8 py-4">
      <div className="flex flex-col gap-1">
        <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
          {title}
        </h2>
        {subtitle && (
          <p className="text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>
        )}
      </div>
      
      {actions && (
        <div className="flex items-center gap-3">
          {actions}
        </div>
      )}
    </header>
  );
};
