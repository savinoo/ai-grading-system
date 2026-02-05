import React from 'react';
import { Link } from 'react-router-dom';

export const Footer: React.FC = () => {
  return (
    <footer className="px-6 py-8 flex flex-col sm:flex-row justify-center items-center gap-6 border-t border-primary/10 text-slate-400 text-xs font-medium">
      <div className="flex items-center gap-6">
        <Link className="hover:text-primary transition-colors" to="/privacy">
          Política de Privacidade
        </Link>
        <Link className="hover:text-primary transition-colors" to="/terms">
          Termos de Serviço
        </Link>
      </div>
    </footer>
  );
};
