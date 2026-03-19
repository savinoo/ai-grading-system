import React from 'react';
import { useParams } from 'react-router-dom';

interface KnowledgeGap {
  criteriaName: string;
  gapDescription: string;
  frequency: number;
  severity: 'low' | 'medium' | 'high';
}

export const StudentProfilePage: React.FC = () => {
  const { studentUuid } = useParams<{ studentUuid: string }>();
  const gaps: KnowledgeGap[] = [];

  const severityColor = {
    low: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    medium: 'bg-orange-50 border-orange-200 text-orange-800',
    high: 'bg-red-50 border-red-200 text-red-800',
  };

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => window.history.back()}
          className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          <span className="material-symbols-outlined text-slate-600">arrow_back</span>
        </button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Perfil do Aluno
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Base de conhecimento e lacunas identificadas
          </p>
        </div>
      </div>

      {/* Student UUID badge */}
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 rounded-lg w-fit">
        <span className="material-symbols-outlined text-slate-500 text-base">person</span>
        <code className="text-xs text-slate-600 dark:text-slate-400">{studentUuid}</code>
      </div>

      {/* Knowledge Gaps */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5">
        <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
          <span className="material-symbols-outlined text-amber-500">school</span>
          Lacunas de Conhecimento Identificadas
        </h2>

        {gaps.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="rounded-full bg-green-100 dark:bg-green-900/30 p-3 mb-3">
              <span className="material-symbols-outlined text-green-600 text-3xl">check_circle</span>
            </div>
            <p className="text-sm font-medium text-slate-900 dark:text-white mb-1">
              Nenhuma lacuna registrada
            </p>
            <p className="text-xs text-slate-500">
              Este aluno ainda não possui avaliações com gaps identificados.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {gaps.map((gap, idx) => (
              <div
                key={idx}
                className={`border rounded-lg px-4 py-3 ${severityColor[gap.severity]}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm">{gap.criteriaName}</span>
                  <span className="text-xs opacity-75">
                    {gap.frequency}x detectado
                  </span>
                </div>
                <p className="text-xs opacity-80">{gap.gapDescription}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
