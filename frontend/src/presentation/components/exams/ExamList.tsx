import React from 'react';
import { Exam } from '@domain/entities/Exam';
import { ExamCard } from './ExamCard';

interface ExamListProps {
  exams: Exam[];
  isLoading?: boolean;
}

export const ExamList: React.FC<ExamListProps> = ({ exams, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-slate-500">Carregando provas...</div>
      </div>
    );
  }

  if (exams.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-12 text-center">
        <span className="material-symbols-outlined text-slate-300 dark:text-slate-700 text-6xl mb-4">
          description
        </span>
        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">
          Nenhuma prova encontrada
        </h3>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Clique em "Nova Prova" para começar
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700">
              <th className="px-6 py-4 text-xs font-extrabold text-slate-500 uppercase tracking-wider">
                Nome da Prova
              </th>
              <th className="px-6 py-4 text-xs font-extrabold text-slate-500 uppercase tracking-wider">
                Turma
              </th>
              <th className="px-6 py-4 text-xs font-extrabold text-slate-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-4 text-xs font-extrabold text-slate-500 uppercase tracking-wider">
                Criação
              </th>
              <th className="px-6 py-4 text-xs font-extrabold text-slate-500 uppercase tracking-wider text-right">
                Ações
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {exams.map((exam) => (
              <ExamCard key={exam.uuid} exam={exam} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
