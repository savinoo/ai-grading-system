import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@presentation/hooks/useAuth';

interface SidebarProps {
  className?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ className = '' }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const menuItems = [
    { path: '/dashboard', icon: 'dashboard', label: 'Dashboard' },
    { path: '/exams', icon: 'description', label: 'Provas' },
    { path: '/classes', icon: 'groups', label: 'Turmas' },
    { path: '/results', icon: 'analytics', label: 'Resultados' },
  ];

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <aside className={`w-64 flex-shrink-0 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between p-4 ${className}`}>
      {/* Logo e Header */}
      <div className="flex flex-col gap-8">
        <div className="flex items-center gap-3 px-2">
          <div className="bg-primary rounded-lg size-10 flex items-center justify-center text-white">
            <span className="material-symbols-outlined">auto_awesome</span>
          </div>
          <div className="flex flex-col">
            <h1 className="text-slate-900 dark:text-white text-base font-bold leading-tight">
              Corretum AI
            </h1>
            <p className="text-primary text-xs font-semibold uppercase tracking-wider">
              Portal do Professor
            </p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-1">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium transition-colors
                  ${
                    isActive
                      ? 'bg-primary text-white'
                      : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }
                `}
              >
                <span className="material-symbols-outlined">{item.icon}</span>
                <span className={`text-sm ${!isActive && 'text-slate-900 dark:text-slate-300'}`}>
                  {item.label}
                </span>
              </Link>
            );
          })}

          <div className="my-4 border-t border-slate-200 dark:border-slate-800"></div>

          <Link
            to="/settings"
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors font-medium"
          >
            <span className="material-symbols-outlined">settings</span>
            <span className="text-sm text-slate-900 dark:text-slate-300">Configurações</span>
          </Link>

          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors font-medium"
          >
            <span className="material-symbols-outlined">logout</span>
            <span className="text-sm text-slate-900 dark:text-slate-300">Sair</span>
          </button>
        </nav>
      </div>

      {/* User Profile */}
      <div className="flex items-center gap-3 p-2 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
        <div className="size-9 rounded-full bg-primary flex items-center justify-center text-white font-bold">
          {user?.email?.charAt(0).toUpperCase() || 'U'}
        </div>
        <div className="flex flex-col overflow-hidden">
          <p className="text-xs font-bold text-slate-900 dark:text-white truncate">
            {user?.email || 'Usuário'}
          </p>
          <p className="text-[10px] text-slate-500 truncate font-medium">
            {user?.user_type === 'teacher' ? 'Professor' : 'Usuário'}
          </p>
        </div>
      </div>
    </aside>
  );
};
