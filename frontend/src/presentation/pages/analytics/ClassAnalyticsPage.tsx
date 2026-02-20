import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';
import { DashboardHeader } from '@presentation/components/dashboard/DashboardHeader';

const BackButton: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <button
    onClick={onClick}
    className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors"
  >
    <span className="material-symbols-outlined text-base">arrow_back</span>
    Voltar
  </button>
);
import { analyticsService } from '@infrastructure/api/analyticsService';
import {
  ClassAnalytics,
  ClassStudentSummary,
  GradeDistribution,
  Trend,
} from '@domain/types/analytics';

// ---------------------------------------------------------------------------
// Sub-componentes
// ---------------------------------------------------------------------------

const TrendBadge: React.FC<{ trend: Trend }> = ({ trend }) => {
  const map: Record<Trend, { icon: string; label: string; cls: string }> = {
    improving: {
      icon: 'trending_up',
      label: 'Melhorando',
      cls: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400',
    },
    stable: {
      icon: 'trending_flat',
      label: 'Estável',
      cls: 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300',
    },
    declining: {
      icon: 'trending_down',
      label: 'Declinando',
      cls: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
    },
    insufficient_data: {
      icon: 'question_mark',
      label: 'Poucos dados',
      cls: 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400',
    },
  };
  const { icon, label, cls } = map[trend] ?? map.insufficient_data;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      <span className="material-symbols-outlined text-sm">{icon}</span>
      {label}
    </span>
  );
};

const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const map: Record<string, string> = {
    high: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
    medium: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400',
    low: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
  };
  const labels: Record<string, string> = { high: 'Alta', medium: 'Média', low: 'Baixa' };
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${map[severity] ?? ''}`}>
      {labels[severity] ?? severity}
    </span>
  );
};

const GradeDistBar: React.FC<{ dist: GradeDistribution[] }> = ({ dist }) => {
  const colors: Record<string, string> = {
    A: 'bg-emerald-500',
    B: 'bg-teal-500',
    C: 'bg-amber-500',
    D: 'bg-orange-500',
    F: 'bg-red-500',
  };
  return (
    <div className="space-y-2">
      {dist.map((d) => (
        <div key={d.label} className="flex items-center gap-3">
          <span className="w-4 text-xs font-bold text-slate-500">{d.label}</span>
          <div className="flex-1 h-3 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
            <div
              className={`h-full rounded-full ${colors[d.label] ?? 'bg-slate-400'}`}
              style={{ width: `${d.percentage}%` }}
            />
          </div>
          <span className="text-xs text-slate-500 w-10 text-right">{d.percentage}%</span>
          <span className="text-xs text-slate-400 w-8 text-right">({d.count})</span>
        </div>
      ))}
    </div>
  );
};

const StudentRow: React.FC<{
  student: ClassStudentSummary;
  onViewProfile: () => void;
}> = ({ student, onViewProfile }) => {
  const score = student.avg_score;
  const scoreColor =
    score >= 7
      ? 'text-emerald-600 dark:text-emerald-400'
      : score >= 5
      ? 'text-amber-600 dark:text-amber-400'
      : 'text-red-600 dark:text-red-400';

  return (
    <tr className="border-t border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
      <td className="py-3 px-4 text-sm text-slate-900 dark:text-white font-medium">
        {student.student_name}
      </td>
      <td className="py-3 px-4">
        <TrendBadge trend={student.trend} />
      </td>
      <td className={`py-3 px-4 text-sm font-bold text-right ${scoreColor}`}>
        {score.toFixed(1)}
      </td>
      <td className="py-3 px-4 text-xs text-slate-500 text-right">{student.submission_count}</td>
      <td className="py-3 px-4 text-right">
        <button
          onClick={onViewProfile}
          className="text-xs text-primary dark:text-primary-light hover:underline font-medium"
        >
          Ver perfil
        </button>
      </td>
    </tr>
  );
};

// ---------------------------------------------------------------------------
// Página principal
// ---------------------------------------------------------------------------

export const ClassAnalyticsPage: React.FC = () => {
  const { classUuid } = useParams<{ classUuid: string }>();
  const navigate = useNavigate();
  const goBack = () => navigate('/analytics');

  const { data: analytics, isLoading, error } = useQuery<ClassAnalytics>({
    queryKey: ['analytics', 'classes', classUuid],
    queryFn: () => analyticsService.getClassAnalytics(classUuid!),
    enabled: !!classUuid,
  });

  if (isLoading) {
    return (
      <DashboardLayout>
        <DashboardHeader title="Análise da Turma" actions={<BackButton onClick={goBack} />} />
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
            <p className="text-slate-600 dark:text-slate-400">Calculando análise pedagógica...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !analytics) {
    return (
      <DashboardLayout>
        <DashboardHeader title="Análise da Turma" actions={<BackButton onClick={goBack} />} />
        <div className="p-8">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
            <span className="material-symbols-outlined text-5xl text-red-600 dark:text-red-400 mb-4 block">
              error
            </span>
            <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">
              Erro ao carregar análise
            </h3>
            <p className="text-red-700 dark:text-red-300">
              {error instanceof Error ? error.message : 'Turma não encontrada ou sem dados.'}
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <DashboardHeader title={analytics.class_name} actions={<BackButton onClick={goBack} />} />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Cards de métricas principais */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              label: 'Alunos',
              value: analytics.total_students,
              icon: 'group',
              color: 'text-primary dark:text-primary-light',
              bg: 'bg-primary/5 dark:bg-primary/10',
            },
            {
              label: 'Média da Turma',
              value: analytics.class_avg_score.toFixed(1),
              icon: 'grade',
              color:
                analytics.class_avg_score >= 7
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : analytics.class_avg_score >= 5
                  ? 'text-amber-600 dark:text-amber-400'
                  : 'text-red-600 dark:text-red-400',
              bg:
                analytics.class_avg_score >= 7
                  ? 'bg-emerald-50 dark:bg-emerald-900/20'
                  : analytics.class_avg_score >= 5
                  ? 'bg-amber-50 dark:bg-amber-900/20'
                  : 'bg-red-50 dark:bg-red-900/20',
            },
            {
              label: 'Em Dificuldade',
              value: analytics.struggling_students.length,
              icon: 'warning',
              color: 'text-red-600 dark:text-red-400',
              bg: 'bg-red-50 dark:bg-red-900/20',
            },
            {
              label: 'Destaques',
              value: analytics.top_performers.length,
              icon: 'star',
              color: 'text-amber-600 dark:text-amber-400',
              bg: 'bg-amber-50 dark:bg-amber-900/20',
            },
          ].map((card) => (
            <div
              key={card.label}
              className={`${card.bg} rounded-xl p-4 flex items-center gap-3 border border-slate-100 dark:border-slate-700`}
            >
              <span className={`material-symbols-outlined text-2xl ${card.color}`}>
                {card.icon}
              </span>
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400">{card.label}</p>
                <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Distribuição de Notas */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-base text-primary">
                bar_chart
              </span>
              Distribuição de Notas
            </h3>
            {analytics.grade_distribution.length > 0 ? (
              <GradeDistBar dist={analytics.grade_distribution} />
            ) : (
              <p className="text-sm text-slate-400">Sem dados suficientes</p>
            )}
            <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700 grid grid-cols-2 gap-2 text-xs text-slate-500 dark:text-slate-400">
              <div>
                <span className="font-medium">Mediana:</span>{' '}
                <span className="text-slate-700 dark:text-slate-300">
                  {analytics.median_score.toFixed(1)}
                </span>
              </div>
              <div>
                <span className="font-medium">Desvio:</span>{' '}
                <span className="text-slate-700 dark:text-slate-300">
                  ±{analytics.std_deviation.toFixed(1)}
                </span>
              </div>
            </div>
          </div>

          {/* Gaps mais comuns */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-base text-red-500">
                report_problem
              </span>
              Gaps Mais Comuns na Turma
            </h3>
            {analytics.most_common_gaps.length > 0 ? (
              <ul className="space-y-3">
                {analytics.most_common_gaps.map((gap) => (
                  <li key={gap.criterion_name} className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                        {gap.criterion_name}
                      </p>
                      <p className="text-xs text-slate-500">
                        Média: {gap.avg_score.toFixed(1)} · {gap.evidence_count} ocorrência
                        {gap.evidence_count !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <SeverityBadge severity={gap.severity} />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-400">Nenhum gap identificado</p>
            )}
          </div>

          {/* Alunos Outliers */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5 space-y-4">
            {/* Em dificuldade */}
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                <span className="material-symbols-outlined text-base text-red-500">warning</span>
                Em Dificuldade
              </h3>
              {analytics.struggling_students.length > 0 ? (
                <ul className="space-y-1">
                  {analytics.struggling_students.map((s) => (
                    <li
                      key={s.student_uuid}
                      className="text-sm text-slate-700 dark:text-slate-300 flex items-center justify-between"
                    >
                      <span className="truncate">{s.student_name}</span>
                      <span className="text-red-600 dark:text-red-400 font-semibold ml-2">
                        {s.avg_score.toFixed(1)}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-400">Nenhum aluno em dificuldade</p>
              )}
            </div>

            <div className="border-t border-slate-100 dark:border-slate-700" />

            {/* Top performers */}
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                <span className="material-symbols-outlined text-base text-amber-500">star</span>
                Destaques
              </h3>
              {analytics.top_performers.length > 0 ? (
                <ul className="space-y-1">
                  {analytics.top_performers.map((s) => (
                    <li
                      key={s.student_uuid}
                      className="text-sm text-slate-700 dark:text-slate-300 flex items-center justify-between"
                    >
                      <span className="truncate">{s.student_name}</span>
                      <span className="text-emerald-600 dark:text-emerald-400 font-semibold ml-2">
                        {s.avg_score.toFixed(1)}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-400">Nenhum destaque identificado</p>
              )}
            </div>
          </div>
        </div>

        {/* Tabela de todos os alunos */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-base text-primary">people</span>
              Todos os Alunos
            </h3>
          </div>

          {analytics.students.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-sm">
              Nenhuma correção registrada ainda.
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-700/50 text-xs text-slate-500 dark:text-slate-400">
                  <th className="py-3 px-4 text-left font-medium">Aluno</th>
                  <th className="py-3 px-4 text-left font-medium">Tendência</th>
                  <th className="py-3 px-4 text-right font-medium">Média</th>
                  <th className="py-3 px-4 text-right font-medium">Correções</th>
                  <th className="py-3 px-4 text-right font-medium" />
                </tr>
              </thead>
              <tbody>
                {analytics.students
                  .sort((a, b) => a.student_name.localeCompare(b.student_name))
                  .map((student) => (
                    <StudentRow
                      key={student.student_uuid}
                      student={student}
                      onViewProfile={() =>
                        navigate(
                          `/analytics/classes/${classUuid}/students/${student.student_uuid}`,
                        )
                      }
                    />
                  ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};
