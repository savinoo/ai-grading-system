import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';
import { DashboardHeader } from '@presentation/components/dashboard/DashboardHeader';
import { resultsService } from '@infrastructure/api/resultsService';
import type { ExamResults, QuestionStatistics, ScoreDistribution } from '@domain/types/results';

export const ExamResultsPage: React.FC = () => {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();

  const { data: results, isLoading, error } = useQuery<ExamResults>({
    queryKey: ['examResults', examId],
    queryFn: () => resultsService.getExamResults(examId!),
    enabled: !!examId,
  });

  if (isLoading) {
    return (
      <DashboardLayout>
        <DashboardHeader title="Resultados da Prova" />
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-slate-600 dark:text-slate-400">Carregando resultados...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !results) {
    return (
      <DashboardLayout>
        <DashboardHeader title="Resultados da Prova" />
        <div className="p-8">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
            <span className="material-symbols-outlined text-5xl text-red-600 dark:text-red-400 mb-4">
              error
            </span>
            <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">
              Erro ao carregar resultados
            </h3>
            <p className="text-red-700 dark:text-red-300">
              {error instanceof Error ? error.message : 'Erro desconhecido'}
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const { statistics, questions_stats } = results;

  return (
    <DashboardLayout>
      <DashboardHeader 
        title={`Resultados: ${results.exam_title}`}
        subtitle={results.graded_at ? `Corrigida em ${new Date(results.graded_at).toLocaleString('pt-BR')}` : undefined}
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Status Header */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            {results.status === 'GRADED' && (
              <>
                <span className="material-symbols-outlined text-green-600">check_circle</span>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Correção Concluída
                </h3>
              </>
            )}
            {results.status === 'PARTIAL' && (
              <>
                <span className="material-symbols-outlined text-yellow-600">pending</span>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Correção Parcial
                </h3>
              </>
            )}
            {results.status === 'PENDING' && (
              <>
                <span className="material-symbols-outlined text-slate-600">schedule</span>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Aguardando Correção
                </h3>
              </>
            )}
          </div>

          {/* Cards de Métricas */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
              <div className="text-sm text-slate-600 dark:text-slate-400 mb-1">Total de Alunos</div>
              <div className="text-3xl font-bold text-slate-900 dark:text-white">
                {statistics.total_students}
              </div>
            </div>
            <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
              <div className="text-sm text-slate-600 dark:text-slate-400 mb-1">Total Questões</div>
              <div className="text-3xl font-bold text-slate-900 dark:text-white">
                {statistics.total_questions}
              </div>
            </div>
            <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
              <div className="text-sm text-slate-600 dark:text-slate-400 mb-1">Taxa Árbitro</div>
              <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                {statistics.arbiter_rate.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>

        {/* Estatísticas Gerais */}        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined">analytics</span>
            Estatísticas Gerais
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div>
              <div className="text-sm text-slate-600 dark:text-slate-400 mb-1">Média Geral</div>
              <div className="text-2xl font-bold text-slate-900 dark:text-white">
                {statistics.average_score.toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-600 dark:text-slate-400 mb-1">Desvio Padrão</div>
              <div className="text-2xl font-bold text-slate-900 dark:text-white">
                {statistics.std_deviation.toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-600 dark:text-slate-400 mb-1">Nota Máxima</div>
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {statistics.max_score.toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-600 dark:text-slate-400 mb-1">Nota Mínima</div>
              <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                {statistics.min_score.toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-600 dark:text-slate-400 mb-1">Mediana</div>
              <div className="text-2xl font-bold text-slate-900 dark:text-white">
                {statistics.median.toFixed(1)}
              </div>
            </div>
          </div>

          {/* Gráfico de Distribuição */}
          {statistics.distribution.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                Distribuição de Notas
              </h4>
              <div className="space-y-2">
                {statistics.distribution.map((dist: ScoreDistribution) => {
                  const maxCount = Math.max(...statistics.distribution.map((d: ScoreDistribution) => d.count));
                  const percentage = maxCount > 0 ? (dist.count / maxCount) * 100 : 0;
                  
                  return (
                    <div key={dist.range} className="flex items-center gap-3">
                      <div className="w-16 text-sm text-slate-600 dark:text-slate-400 font-medium">
                        {dist.range}
                      </div>
                      <div className="flex-1 bg-slate-200 dark:bg-slate-700 rounded-full h-6 overflow-hidden">
                        <div
                          className="bg-indigo-600 dark:bg-indigo-500 h-full rounded-full flex items-center justify-end pr-2 transition-all"
                          style={{ width: `${percentage}%` }}
                        >
                          {dist.count > 0 && (
                            <span className="text-xs text-white font-medium">{dist.count}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Estatísticas por Questão */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined">quiz</span>
            Desempenho por Questão
          </h3>

          <div className="space-y-3">
            {questions_stats.map((question: QuestionStatistics) => {
              const performanceColor = 
                question.average_score >= 8 ? 'text-green-600 dark:text-green-400' :
                question.average_score >= 6 ? 'text-yellow-600 dark:text-yellow-400' :
                'text-red-600 dark:text-red-400';
              
              return (
                <div
                  key={question.question_uuid}
                  className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                        Q{question.question_number}:
                      </span>
                      <span className="text-sm text-slate-600 dark:text-slate-400">
                        {question.question_title}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-500">
                      Desvio padrão: {question.std_deviation.toFixed(2)} | 
                      Árbitros: {question.arbiter_count}
                    </div>
                  </div>
                  <div className={`text-2xl font-bold ${performanceColor}`}>
                    {question.average_score.toFixed(1)}
                    <span className="text-sm text-slate-500 dark:text-slate-400 ml-1">
                      / {question.max_score}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Botões de Ação */}
        <div className="flex gap-3">
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-sm">arrow_back</span>
            Voltar
          </button>
          <button
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-sm">download</span>
            Exportar Relatório
          </button>
        </div>
      </div>
    </DashboardLayout>
  );
};
