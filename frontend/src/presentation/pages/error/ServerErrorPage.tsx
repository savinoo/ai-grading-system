import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@presentation/components/ui/Button';

export const ServerErrorPage: React.FC = () => {
  const navigate = useNavigate();

  const handleReload = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-red-100 dark:bg-red-900/20 mb-6">
          <span className="material-symbols-outlined text-6xl text-red-600 dark:text-red-400">
            error
          </span>
        </div>
        
        <h1 className="text-6xl font-extrabold text-slate-900 dark:text-white mb-2">
          500
        </h1>
        
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
          Erro no servidor
        </h2>
        
        <p className="text-slate-500 dark:text-slate-400 mb-8">
          Ocorreu um erro inesperado. Nossa equipe foi notificada e estamos trabalhando para resolver o problema.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button
            variant="primary"
            onClick={handleReload}
          >
            Tentar novamente
          </Button>
          
          <button
            onClick={() => navigate('/dashboard')}
            className="px-6 py-3 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg font-bold hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            Ir para o Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};
