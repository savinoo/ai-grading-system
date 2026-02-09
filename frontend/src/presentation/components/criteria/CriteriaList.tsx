import React from 'react';
import { ExamCriteria } from '@domain/entities/Criteria';
import { useExams } from '@presentation/hooks/useExams';

interface CriteriaListProps {
  criteria: ExamCriteria[];
  isEditable: boolean;
  onEdit?: (criteria: ExamCriteria) => void;
}

export const CriteriaList: React.FC<CriteriaListProps> = ({
  criteria,
  isEditable,
  onEdit,
}) => {
  const { deleteCriteria, isLoading } = useExams();

  const handleDelete = async (uuid: string) => {
    if (!confirm('Tem certeza que deseja remover este critério?')) {
      return;
    }

    try {
      await deleteCriteria(uuid);
    } catch (error) {
      console.error('Erro ao remover critério:', error);
    }
  };

  if (criteria.length === 0) {
    return (
      <div className="bg-slate-50 dark:bg-slate-800/50 rounded-lg p-8 text-center border-2 border-dashed border-slate-200 dark:border-slate-700">
        <span className="material-symbols-outlined text-slate-300 dark:text-slate-600 text-5xl mb-3">
          checklist
        </span>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Nenhum critério adicionado ainda
        </p>
        {isEditable && (
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
            Clique em "Adicionar Critério" para começar
          </p>
        )}
      </div>
    );
  }

  const totalWeight = criteria.reduce((sum, c) => sum + c.weight, 0);
  const totalMaxPoints = criteria.reduce((sum, c) => sum + c.max_points, 0);

  return (
    <div className="space-y-4">
      <div className="overflow-hidden bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl">
        <table className="w-full">
          <thead className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-extrabold text-slate-500 uppercase tracking-wider">
                Critério
              </th>
              <th className="px-6 py-4 text-center text-xs font-extrabold text-slate-500 uppercase tracking-wider">
                Peso
              </th>
              <th className="px-6 py-4 text-center text-xs font-extrabold text-slate-500 uppercase tracking-wider">
                Pontuação Máxima
              </th>
              {isEditable && (
                <th className="px-6 py-4 text-right text-xs font-extrabold text-slate-500 uppercase tracking-wider">
                  Ações
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {criteria.map((criterion) => {
              return (
                <tr
                  key={criterion.uuid}
                  className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors"
                >
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-bold text-sm text-slate-900 dark:text-white">
                        {criterion.grading_criteria_name}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        {criterion.grading_criteria_description}
                      </div>
                    </div>
                  </td>

                  <td className="px-6 py-4 text-center">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-primary/10 text-primary">
                      {criterion.weight}
                    </span>
                  </td>

                  <td className="px-6 py-4 text-center">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400">
                      {criterion.max_points.toFixed(1)} pts
                    </span>
                  </td>

                  {isEditable && (
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => onEdit?.(criterion)}
                          className="text-primary hover:text-primary/80 p-1 rounded transition-colors"
                          title="Editar"
                          disabled={isLoading}
                        >
                          <span className="material-symbols-outlined text-lg">edit</span>
                        </button>
                        <button
                          onClick={() => handleDelete(criterion.uuid)}
                          className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 p-1 rounded transition-colors"
                          title="Remover"
                          disabled={isLoading}
                        >
                          <span className="material-symbols-outlined text-lg">delete</span>
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
        <div className="text-sm text-slate-600 dark:text-slate-400">
          Total de critérios: <span className="font-bold text-slate-900 dark:text-white">{criteria.length}</span>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-sm text-slate-600 dark:text-slate-400">
            Peso total: <span className="font-bold text-slate-900 dark:text-white">{totalWeight.toFixed(2)}</span>
          </div>
          <div className="text-sm text-slate-600 dark:text-slate-400">
            Pontuação total: <span className="font-bold text-emerald-600 dark:text-emerald-400">{totalMaxPoints.toFixed(1)} pts</span>
          </div>
        </div>
      </div>
    </div>
  );
};
