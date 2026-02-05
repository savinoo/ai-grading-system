import React from 'react';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';
import { DashboardHeader } from '@presentation/components/dashboard/DashboardHeader';

export const SettingsPage: React.FC = () => {
  return (
    <DashboardLayout>
      <DashboardHeader title="Configurações" />
      <div className="p-8 max-w-7xl mx-auto">
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
          <span className="material-symbols-outlined text-6xl text-slate-300 dark:text-slate-600 mb-4">
            settings
          </span>
          <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
            Configurações
          </h3>
          <p className="text-slate-500 dark:text-slate-400">
            Em desenvolvimento
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
};
