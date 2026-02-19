import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';
import { DashboardHeader } from '@presentation/components/dashboard/DashboardHeader';
import { analyticsService } from '@infrastructure/api/analyticsService';
import { StudentPerformance, Trend, LearningGap, Strength, SubmissionSummary } from '@domain/types/analytics';

const BackButton: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <button
    onClick={onClick}
    className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors"
  >
    <span className="material-symbols-outlined text-base">arrow_back</span>
    Voltar
  </button>
);

// ---------------------------------------------------------------------------
// Sub-componentes
// ---------------------------------------------------------------------------

const TrendCard: React.FC<{ trend: Trend; confidence: number }> = ({ trend, confidence }) => {
  const config: Record<Trend, { icon: string; label: string; desc: string; cls: string }> = {
    improving: {
      icon: 'trending_up',
      label: 'Melhorando',
      desc: 'O aluno apresenta evolução positiva nas últimas correções.',
      cls: 'border-emerald-300 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400',
    },
    stable: {
      icon: 'trending_flat',
      label: 'Estável',
      desc: 'O desempenho do aluno está consistente ao longo do tempo.',
      cls: 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300',
    },
    declining: {
      icon: 'trending_down',
      label: 'Declinando',
      desc: 'O aluno apresenta piora progressiva nas correções recentes.',
      cls: 'border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400',
    },
    insufficient_data: {
      icon: 'question_mark',
      label: 'Dados insuficientes',
      desc: 'São necessárias pelo menos 3 correções para detectar tendência.',
      cls: 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-500 dark:text-slate-400',
    },
  };
  const c = config[trend] ?? config.insufficient_data;

  return (
    <div className={`rounded-xl border p-4 flex items-start gap-3 ${c.cls}`}>
      <span className="material-symbols-outlined text-2xl mt-0.5">{c.icon}</span>
      <div>
        <p className="font-semibold text-sm">{c.label}</p>
        <p className="text-xs mt-0.5 opacity-80">{c.desc}</p>
        {trend !== 'insufficient_data' && (
          <p className="text-xs mt-1 opacity-60">
            Confiança: {(confidence * 100).toFixed(0)}%
          </p>
        )}
      </div>
    </div>
  );
};

const GapCard: React.FC<{ gap: LearningGap }> = ({ gap }) => {
  const severityConfig: Record<string, { cls: string; label: string }> = {
    high: { cls: 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10', label: 'Alta' },
    medium: { cls: 'border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/10', label: 'Média' },
    low: { cls: 'border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/10', label: 'Baixa' },
  };
  const { cls, label } = severityConfig[gap.severity] ?? severityConfig.low;

  return (
    <div className={`rounded-lg border p-3 ${cls}`}>
      <div className="flex items-start justify-between gap-2 mb-1">
        <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
          {gap.criterion_name}
        </p>
        <span className="text-xs text-slate-500">Severidade: {label}</span>
      </div>
      <p className="text-xs text-slate-500 mb-1">
        Média: <span className="font-medium text-red-600 dark:text-red-400">{gap.avg_score.toFixed(1)}</span>
        {' · '}{gap.evidence_count} amostras
      </p>
      {gap.suggestion && (
        <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 italic">
          💡 {gap.suggestion}
        </p>
      )}
    </div>
  );
};

const StrengthCard: React.FC<{ strength: Strength }> = ({ strength }) => (
  <div className="rounded-lg border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/10 p-3">
    <div className="flex items-start justify-between gap-2 mb-1">
      <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
        {strength.criterion_name}
      </p>
      <span className="material-symbols-outlined text-sm text-emerald-500">star</span>
    </div>
    <p className="text-xs text-slate-500">
      Média: <span className="font-medium text-emerald-600 dark:text-emerald-400">{strength.avg_score.toFixed(1)}</span>
      {' · '}Consistência: {(strength.consistency * 100).toFixed(0)}%
    </p>
  </div>
);

const HistoryRow: React.FC<{ sub: SubmissionSummary }> = ({ sub }) => {
  const score = sub.score;
  const max = sub.max_score;
  const pct = max > 0 ? (score / max) * 100 : 0;
  const color = score >= 7 ? 'bg-emerald-500' : score >= 5 ? 'bg-amber-500' : 'bg-red-500';
  const textColor =
    score >= 7
      ? 'text-emerald-600 dark:text-emerald-400'
      : score >= 5
      ? 'text-amber-600 dark:text-amber-400'
      : 'text-red-600 dark:text-red-400';

  return (
    <tr className="border-t border-slate-100 dark:border-slate-700">
      <td className="py-3 px-4 text-sm text-slate-700 dark:text-slate-300 max-w-xs">
        <p className="truncate font-medium">{sub.exam_title || '—'}</p>
        <p className="text-xs text-slate-400">
          {sub.graded_at
            ? new Date(sub.graded_at).toLocaleDateString('pt-BR')
            : 'Data desconhecida'}
        </p>
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <div className="flex-1 h-2 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden max-w-[100px]">
            <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
          </div>
          <span className={`text-sm font-bold ${textColor}`}>{score.toFixed(1)}</span>
          <span className="text-xs text-slate-400">/ {max.toFixed(0)}</span>
        </div>
      </td>
    </tr>
  );
};

// ---------------------------------------------------------------------------
// Página principal
// ---------------------------------------------------------------------------

export const StudentPerformancePage: React.FC = () => {
  const { classUuid, studentUuid } = useParams<{ classUuid: string; studentUuid: string }>();
  const navigate = useNavigate();
  const goBack = () => navigate(`/analytics/classes/${classUuid}`);

  const { data: performance, isLoading, error } = useQuery<StudentPerformance>({
    queryKey: ['analytics', 'students', classUuid, studentUuid],
    queryFn: () => analyticsService.getStudentPerformance(classUuid!, studentUuid!),
    enabled: !!classUuid && !!studentUuid,
  });

  if (isLoading) {
    return (
      <DashboardLayout>
        <DashboardHeader title="Desempenho do Aluno" actions={<BackButton onClick={goBack} />} />
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4" />
            <p className="text-slate-600 dark:text-slate-400">Calculando perfil do aluno...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !performance) {
    return (
      <DashboardLayout>
        <DashboardHeader title="Desempenho do Aluno" actions={<BackButton onClick={goBack} />} />
        <div className="p-8">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
            <span className="material-symbols-outlined text-5xl text-red-600 dark:text-red-400 mb-4 block">
              error
            </span>
            <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">
              Erro ao carregar desempenho
            </h3>
            <p className="text-red-700 dark:text-red-300">
              {error instanceof Error ? error.message : 'Aluno não encontrado ou sem dados.'}
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const scoreColor =
    performance.avg_score >= 7
      ? 'text-emerald-600 dark:text-emerald-400'
      : performance.avg_score >= 5
      ? 'text-amber-600 dark:text-amber-400'
      : 'text-red-600 dark:text-red-400';

  return (
    <DashboardLayout>
      <DashboardHeader title={performance.student_name} actions={<BackButton onClick={goBack} />} />

      <div className="p-8 max-w-5xl mx-auto space-y-6">
        {/* Cards de métricas */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 text-center">
            <p className={`text-3xl font-bold ${scoreColor}`}>
              {performance.avg_score.toFixed(1)}
            </p>
            <p className="text-xs text-slate-500 mt-1">Média geral</p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 text-center">
            <p className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
              {performance.submission_count}
            </p>
            <p className="text-xs text-slate-500 mt-1">Respostas corrigidas</p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 text-center">
            <p className="text-3xl font-bold text-red-600 dark:text-red-400">
              {performance.learning_gaps.length}
            </p>
            <p className="text-xs text-slate-500 mt-1">Gaps identificados</p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 text-center">
            <p className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">
              {performance.strengths.length}
            </p>
            <p className="text-xs text-slate-500 mt-1">Pontos fortes</p>
          </div>
        </div>

        {/* Tendência */}
        <div>
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
            <span className="material-symbols-outlined text-base text-indigo-500">show_chart</span>
            Tendência de Evolução
          </h2>
          <TrendCard trend={performance.trend} confidence={performance.trend_confidence} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Gaps de aprendizado */}
          <div>
            <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-base text-red-500">report_problem</span>
              Gaps de Aprendizado
            </h2>
            {performance.learning_gaps.length > 0 ? (
              <div className="space-y-2">
                {performance.learning_gaps.map((gap) => (
                  <GapCard key={gap.criterion_name} gap={gap} />
                ))}
              </div>
            ) : (
              <div className="bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 text-center">
                <span className="material-symbols-outlined text-3xl text-emerald-300 dark:text-emerald-700 block mb-2">
                  check_circle
                </span>
                <p className="text-sm text-slate-500">Nenhum gap identificado</p>
              </div>
            )}
          </div>

          {/* Pontos fortes */}
          <div>
            <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-base text-amber-500">star</span>
              Pontos Fortes
            </h2>
            {performance.strengths.length > 0 ? (
              <div className="space-y-2">
                {performance.strengths.map((s) => (
                  <StrengthCard key={s.criterion_name} strength={s} />
                ))}
              </div>
            ) : (
              <div className="bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 text-center">
                <p className="text-sm text-slate-500">
                  Ainda sem pontos fortes consolidados.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Histórico de submissões */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-base text-indigo-500">history</span>
              Histórico de Correções
            </h3>
          </div>
          {performance.submissions_history.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-sm">
              Nenhuma correção registrada ainda.
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-700/50 text-xs text-slate-500 dark:text-slate-400">
                  <th className="py-3 px-4 text-left font-medium">Prova / Data</th>
                  <th className="py-3 px-4 text-left font-medium">Nota</th>
                </tr>
              </thead>
              <tbody>
                {[...performance.submissions_history]
                  .sort((a, b) => {
                    if (!a.graded_at) return 1;
                    if (!b.graded_at) return -1;
                    return new Date(b.graded_at).getTime() - new Date(a.graded_at).getTime();
                  })
                  .map((sub) => (
                    <HistoryRow key={sub.answer_uuid} sub={sub} />
                  ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};
