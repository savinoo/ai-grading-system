import React, { useEffect } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '@presentation/hooks/useAuth';

export const PrivateRoute: React.FC = () => {
  const { isAuthenticated, isLoading, loadCurrentUser } = useAuth();

  useEffect(() => {
    loadCurrentUser();
  }, [loadCurrentUser]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-light dark:bg-background-dark">
        <div className="flex flex-col items-center gap-4">
          <span className="material-symbols-outlined text-6xl text-primary animate-spin">
            progress_activity
          </span>
          <p className="text-slate-600 dark:text-slate-400 font-medium">Carregando...</p>
        </div>
      </div>
    );
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};
