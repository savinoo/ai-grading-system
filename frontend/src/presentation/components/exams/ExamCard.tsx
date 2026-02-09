import React, { useState } from 'react';
import { Exam, ExamStatus } from '@domain/entities/Exam';
import { useNavigate } from 'react-router-dom';
import { useExams } from '@presentation/hooks/useExams';

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
  const { deleteExam, updateExamData, isLoading } = useExams();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleViewDetails = () => {
    navigate(`/dashboard/exams/${exam.uuid}`);
  };

  const handlePublish = async () => {
    try {
      await updateExamData(exam.uuid, { status: 'PUBLISHED' });
      // O estado será atualizado automaticamente através do store
    } catch (error) {
      console.error('Erro ao publicar prova:', error);
      alert('Erro ao publicar prova. Tente novamente.');
    }
  };

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async () => {
    try {
      await deleteExam(exam.uuid);
      setShowDeleteConfirm(false);
    } catch (error) {
      console.error('Erro ao deletar prova:', error);
      alert('Erro ao deletar prova. Tente novamente.');
    }
  };

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
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
            <>
              <button
                onClick={() => navigate(`/dashboard/exams/${exam.uuid}/edit`)}
                className="text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                title="Editar"
                disabled={isLoading}
              >
                <span className="material-symbols-outlined text-lg">edit</span>
              </button>

              <button
                onClick={handlePublish}
                className="text-emerald-600 hover:text-emerald-700 dark:hover:text-emerald-500 transition-colors"
                title="Publicar prova"
                disabled={isLoading}
              >
                <span className="material-symbols-outlined text-lg">publish</span>
              </button>

              <button
                onClick={handleDeleteClick}
                className="text-red-500 hover:text-red-700 dark:hover:text-red-400 transition-colors"
                title="Excluir prova"
                disabled={isLoading}
              >
                <span className="material-symbols-outlined text-lg">delete</span>
              </button>
            </>
          )}
        </div>

        {/* Modal de Confirmação de Exclusão */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[100]">
            <div className="bg-white dark:bg-slate-900 rounded-xl p-8 max-w-md w-full mx-4 shadow-2xl border border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full">
                  <span className="material-symbols-outlined text-red-600 dark:text-red-400 text-2xl">warning</span>
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                  Confirmar Exclusão
                </h3>
              </div>
              
              <p className="text-slate-600 dark:text-slate-400 mb-6">
                Tem certeza que deseja excluir a prova <strong>"{exam.title}"</strong>?
                <span className="block mt-2 text-slate-500 dark:text-slate-400 text-sm">
                  Esta ação é irreversível e removerá todos os dados associados à prova.
                </span>
              </p>

              <div className="flex items-center gap-3 justify-end">
                <button
                  onClick={handleCancelDelete}
                  disabled={isLoading}
                  className="px-4 py-2 text-sm font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-50"
                >
                  Cancelar
                </button>
                
                <button
                  onClick={handleConfirmDelete}
                  disabled={isLoading}
                  className="px-4 py-2 text-sm font-bold text-white bg-red-600 hover:bg-red-700 dark:hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  <span className="material-symbols-outlined text-sm">delete</span>
                  Sim, excluir
                </button>
              </div>
            </div>
          </div>
        )}
      </td>
    </tr>
  );
};
