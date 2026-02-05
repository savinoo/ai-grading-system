import React from 'react';
import { Link } from 'react-router-dom';

export const Header: React.FC = () => {
  return (
    <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-primary/10 px-6 md:px-10 py-4 bg-background-light dark:bg-background-dark sticky top-0 z-50">
      <div className="flex items-center gap-3 text-primary">
        <div className="size-8 flex items-center justify-center bg-primary text-white rounded-lg">
          <span className="material-symbols-outlined text-xl">school</span>
        </div>
        <h2 className="text-slate-900 dark:text-white text-xl font-extrabold leading-tight tracking-[-0.015em]">
          Corretum AI
        </h2>
      </div>
      
      {/* <div className="flex items-center gap-4">
        <button className="hidden sm:flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 text-primary text-sm font-semibold hover:bg-primary/5">
          <span className="truncate">Documentação</span>
        </button>
        <button className="flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em] hover:bg-opacity-90 transition-all shadow-sm shadow-primary/20">
          <span className="truncate">Suporte</span>
        </button>
      </div> */}
    </header>
  );
};


