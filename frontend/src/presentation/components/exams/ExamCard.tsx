import React from 'react';
import { Exam, ExamStatus } from '@domain/entities/Exam';
import { useNavigate } from 'react-router-dom';

interface ExamCardProps {
  exam: Exam;
}

const statusConfig: Record<ExamStatus, { label: string; className: string }> = {
  DRAFT: { label: 'Rascunho', className: 'bg-slate-100 text-slate-700' },
  PUBLISHED: { label: 'Publicada', className: 'bg-emerald-100 text-emerald-700' },
  ARCHIVED: { label: 'Arquivada', className: 'bg-amber-100 text-amber-700' },
  FINISHED: { label: 'Finalizada', className: 'bg-blue-100 text-blue-700' },
};

export const ExamCard: React.FC<ExamCardProps> = ({ exam }) => {
  const navigate = useNavigate();

  const handleViewDetails = () => {
    navigate(`/dashboard/exams/${exam.uuid}`);
  };

  const statusInfo = statusConfig[exam.status];

  return (
    <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
      <td className="px-6 py-4">
        <div>
          <div className="font-bold text-slate-900 dark:text-white text-sm">
            {exam.title}
          </div>
          {exam.description && (
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              {exam.description}
            </div>
          )}
        </div>
      </td>

      <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">
        {exam.class_name || (
          <span className="text-slate-400 dark:text-slate-500 italic">Sem turma</span>
        )}
      </td>

      <td className="px-6 py-4">
        <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider ${statusInfo.className}`}>
          {statusInfo.label}
        </span>
      </td>

      <td className="px-6 py-4 text-sm text-slate-500 dark:text-slate-400">
        {new Date(exam.created_at).toLocaleDateString('pt-BR')}
      </td>

      <td className="px-6 py-4 text-right">
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={handleViewDetails}
            className="text-primary hover:text-primary/80 font-semibold text-sm"
          >
            Ver Detalhes
          </button>
          
          {exam.status === 'DRAFT' && (
            <button
              onClick={() => navigate(`/dashboard/exams/${exam.uuid}/edit`)}
              className="text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
              title="Editar"
            >
              <span className="material-symbols-outlined text-lg">edit</span>
            </button>
          )}
        </div>
      </td>
    </tr>
  );
};
