import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';
import { DashboardHeader } from '@presentation/components/dashboard/DashboardHeader';
import { analyticsService } from '@infrastructure/api/analyticsService';
import { ClassAnalyticsSummary } from '@domain/types/analytics';

const ScoreBar: React.FC<{ score: number }> = ({ score }) => {
  const pct = Math.min(100, (score / 10) * 100);
  const color =
    score >= 7 ? 'bg-emerald-500' : score >= 5 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 w-8 text-right">
        {score.toFixed(1)}
      </span>
    </div>
  );
};

export const AnalyticsPage: React.FC = () => {
  const navigate = useNavigate();

  const { data: classes, isLoading, error } = useQuery<ClassAnalyticsSummary[]>({
    queryKey: ['analytics', 'classes'],
    queryFn: () => analyticsService.listClassesAnalytics(),
  });

  if (isLoading) {
    return (
      <DashboardLayout>
        <DashboardHeader title="Análise Pedagógica" />
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
            <p className="text-slate-600 dark:text-slate-400">Carregando turmas...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <DashboardHeader title="Análise Pedagógica" />
        <div className="p-8">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
            <span className="material-symbols-outlined text-5xl text-red-600 dark:text-red-400 mb-4 block">
              error
            </span>
            <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">
              Erro ao carregar análises
            </h3>
            <p className="text-red-700 dark:text-red-300">
              {error instanceof Error ? error.message : 'Erro desconhecido'}
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!classes || classes.length === 0) {
    return (
      <DashboardLayout>
        <DashboardHeader title="Análise Pedagógica" />
        <div className="p-8 max-w-7xl mx-auto">
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
            <span className="material-symbols-outlined text-6xl text-slate-300 dark:text-slate-600 mb-4 block">
              school
            </span>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              Nenhuma turma com dados
            </h3>
            <p className="text-slate-500 dark:text-slate-400">
              A análise pedagógica estará disponível após as primeiras correções.
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <DashboardHeader title="Análise Pedagógica" />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Header descritivo */}
        <div className="bg-primary/5 dark:bg-primary/10 border border-primary/20 dark:border-primary/30 rounded-xl p-5">
          <div className="flex items-start gap-3">
            <span className="material-symbols-outlined text-primary dark:text-primary-light text-2xl mt-0.5">
              insights
            </span>
            <div>
              <h2 className="text-sm font-semibold text-slate-900 dark:text-white mb-1">
                Visão Geral das Turmas
              </h2>
              <p className="text-xs text-slate-700 dark:text-slate-300">
                Selecione uma turma para ver análise detalhada: tendência de desempenho, alunos em
                dificuldade, pontos fortes e gaps de aprendizado mais comuns.
              </p>
            </div>
          </div>
        </div>

        {/* Lista de turmas */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {classes.map((cls) => (
            <div
              key={cls.class_uuid}
              onClick={() => navigate(`/analytics/classes/${cls.class_uuid}`)}
              className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 cursor-pointer hover:border-primary dark:hover:border-primary-light hover:shadow-md transition-all group"
            >
              {/* Nome da turma */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-base font-semibold text-slate-900 dark:text-white group-hover:text-primary dark:group-hover:text-primary-light transition-colors line-clamp-1">
                    {cls.class_name}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {cls.total_students} aluno{cls.total_students !== 1 ? 's' : ''} ·{' '}
                    {cls.total_submissions} correç{cls.total_submissions !== 1 ? 'ões' : 'ão'}
                  </p>
                </div>
                <span className="material-symbols-outlined text-slate-400 group-hover:text-primary transition-colors">
                  arrow_forward
                </span>
              </div>

              {/* Média geral */}
              <div className="mb-4">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Média da turma</p>
                <ScoreBar score={cls.class_avg_score} />
              </div>

              {/* Badges de outliers */}
              <div className="flex items-center gap-2 flex-wrap">
                {cls.struggling_count > 0 && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400">
                    <span className="material-symbols-outlined text-xs">warning</span>
                    {cls.struggling_count} em dificuldade
                  </span>
                )}
                {cls.top_performers_count > 0 && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400">
                    <span className="material-symbols-outlined text-xs">star</span>
                    {cls.top_performers_count} destaque{cls.top_performers_count !== 1 ? 's' : ''}
                  </span>
                )}
                {cls.struggling_count === 0 && cls.top_performers_count === 0 && (
                  <span className="text-xs text-slate-400 dark:text-slate-500">
                    Sem outliers detectados
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
};
