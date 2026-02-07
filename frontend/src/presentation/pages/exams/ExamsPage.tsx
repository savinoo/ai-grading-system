import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';
import { Button } from '@presentation/components/ui/Button';
import { ExamList } from '@presentation/components/exams/ExamList';
import { useExams } from '@presentation/hooks/useExams';

export const ExamsPage: React.FC = () => {
  const navigate = useNavigate();
  const { exams, loadTeacherExams, isLoading } = useExams();

  useEffect(() => {
    loadTeacherExams();
  }, [loadTeacherExams]);

  return (
    <DashboardLayout>
      <div className="p-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                Minhas Provas
              </h1>
              <p className="text-slate-500 dark:text-slate-400">
                Gerencie suas provas e critérios de avaliação
              </p>
            </div>

            <Button onClick={() => navigate('/dashboard/exams/create')}>
              <span className="material-symbols-outlined mr-2">add</span>
              Nova Prova
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary/10 rounded-lg">
                <span className="material-symbols-outlined text-primary text-2xl">
                  description
                </span>
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white">
                  {exams.length}
                </div>
                <div className="text-xs text-slate-500 uppercase tracking-wider">
                  Total de Provas
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
                <span className="material-symbols-outlined text-emerald-600 dark:text-emerald-400 text-2xl">
                  check_circle
                </span>
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white">
                  {exams.filter((e) => e.status === 'PUBLISHED').length}
                </div>
                <div className="text-xs text-slate-500 uppercase tracking-wider">
                  Publicadas
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                <span className="material-symbols-outlined text-slate-600 dark:text-slate-400 text-2xl">
                  edit_note
                </span>
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white">
                  {exams.filter((e) => e.status === 'DRAFT').length}
                </div>
                <div className="text-xs text-slate-500 uppercase tracking-wider">
                  Rascunhos
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <span className="material-symbols-outlined text-blue-600 dark:text-blue-400 text-2xl">
                  done_all
                </span>
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white">
                  {exams.filter((e) => e.status === 'FINISHED').length}
                </div>
                <div className="text-xs text-slate-500 uppercase tracking-wider">
                  Finalizadas
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Exam List */}
        <ExamList exams={exams} isLoading={isLoading} />
      </div>
    </DashboardLayout>
  );
};
