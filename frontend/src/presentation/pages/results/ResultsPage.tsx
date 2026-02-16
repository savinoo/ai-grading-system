import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';
import { DashboardHeader } from '@presentation/components/dashboard/DashboardHeader';
import { resultsService } from '@infrastructure/api/resultsService';
import { ExamResultsSummary } from '@domain/types/results';

export const ResultsPage: React.FC = () => {
  const navigate = useNavigate();

  const { data: exams, isLoading, error } = useQuery<ExamResultsSummary[]>({
    queryKey: ['examsList'],
    queryFn: () => resultsService.getExamsList(),
  });

  if (isLoading) {
    return (
      <DashboardLayout>
        <DashboardHeader title="Resultados e Análises" />
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-slate-600 dark:text-slate-400">Carregando provas...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <DashboardHeader title="Resultados e Análises" />
        <div className="p-8">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
            <span className="material-symbols-outlined text-5xl text-red-600 dark:text-red-400 mb-4">
              error
            </span>
            <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">
              Erro ao carregar provas
            </h3>
            <p className="text-red-700 dark:text-red-300">
              {error instanceof Error ? error.message : 'Erro desconhecido'}
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!exams || exams.length === 0) {
    return (
      <DashboardLayout>
        <DashboardHeader title="Resultados e Análises" />
        <div className="p-8 max-w-7xl mx-auto">
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
            <span className="material-symbols-outlined text-6xl text-slate-300 dark:text-slate-600 mb-4">
              analytics
            </span>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              Nenhuma prova corrigida
            </h3>
            <p className="text-slate-500 dark:text-slate-400">
              Aguardando correção de provas
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'GRADED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
            <span className="material-symbols-outlined text-sm">check_circle</span>
            Corrigida
          </span>
        );
      case 'PARTIAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400">
            <span className="material-symbols-outlined text-sm">pending</span>
            Parcial
          </span>
        );
      case 'PENDING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
            <span className="material-symbols-outlined text-sm">schedule</span>
            Pendente
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <DashboardLayout>
      <DashboardHeader 
        title="Resultados e Análises" 
        subtitle={`${exams.length} prova(s) com resultados`}
      />

      <div className="p-8 max-w-7xl mx-auto">
        <div className="grid gap-4">
          {exams.map((exam) => (
            <div
              key={exam.exam_uuid}
              onClick={() => navigate(`/results/exams/${exam.exam_uuid}`)}
              className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 hover:border-indigo-300 dark:hover:border-indigo-600 transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                      {exam.exam_title}
                    </h3>
                    {getStatusBadge(exam.status)}
                  </div>
                  {exam.graded_at && (
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      Corrigida em {new Date(exam.graded_at).toLocaleString('pt-BR')}
                    </p>
                  )}
                </div>
                <span className="material-symbols-outlined text-slate-400 dark:text-slate-500 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                  arrow_forward
                </span>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="material-symbols-outlined text-sm text-slate-600 dark:text-slate-400">group</span>
                    <div className="text-xs text-slate-600 dark:text-slate-400">Total de Alunos</div>
                  </div>
                  <div className="text-xl font-bold text-slate-900 dark:text-white">
                    {exam.total_students}
                  </div>
                </div>

                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="material-symbols-outlined text-sm text-slate-600 dark:text-slate-400">analytics</span>
                    <div className="text-xs text-slate-600 dark:text-slate-400">Média Geral</div>
                  </div>
                  <div className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
                    {exam.average_score.toFixed(1)}
                  </div>
                </div>

                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="material-symbols-outlined text-sm text-slate-600 dark:text-slate-400">gavel</span>
                    <div className="text-xs text-slate-600 dark:text-slate-400">Taxa Árbitro</div>
                  </div>
                  <div className="text-xl font-bold text-slate-900 dark:text-white">
                    {exam.arbiter_rate.toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
};
