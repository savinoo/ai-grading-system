import React, { useState } from 'react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { ExamCriteria } from '@domain/entities/Criteria';
import { useExams } from '@presentation/hooks/useExams';

interface EditCriteriaModalProps {
  isOpen: boolean;
  onClose: () => void;
  criteria: ExamCriteria;
  onSuccess?: () => void;
}

export const EditCriteriaModal: React.FC<EditCriteriaModalProps> = ({
  isOpen,
  onClose,
  criteria,
  onSuccess,
}) => {
  const { updateCriteria, isLoading } = useExams();
  const [weight, setWeight] = useState(criteria.weight.toString());
  const [maxPoints, setMaxPoints] = useState(criteria.max_points?.toString() || '');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (Number(weight) <= 0) {
      return;
    }

    try {
      await updateCriteria(criteria.uuid, {
        weight: Number(weight),
        max_points: maxPoints ? Number(maxPoints) : undefined,
      });

      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Erro ao atualizar critério:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl w-full max-w-2xl mx-4">
        <div className="p-6 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
              Editar Critério
            </h2>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              disabled={isLoading}
            >
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <div className="flex items-start gap-3">
              <span className="material-symbols-outlined text-blue-600 dark:text-blue-400">
                info
              </span>
              <div>
                <div className="font-bold text-sm text-blue-900 dark:text-blue-100">
                  {criteria.grading_criteria_name}
                </div>
                <div className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                  {criteria.grading_criteria_description}
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Peso *
              </label>
              <Input
                type="number"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                min="0.1"
                step="0.1"
                required
                disabled={isLoading}
                placeholder="Ex: 1.5"
              />
              <p className="mt-1 text-xs text-slate-500">
                Peso relativo deste critério
              </p>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Pontuação Máxima
              </label>
              <Input
                type="number"
                value={maxPoints}
                onChange={(e) => setMaxPoints(e.target.value)}
                min="0"
                step="0.5"
                disabled={isLoading}
                placeholder="Ex: 10"
              />
              <p className="mt-1 text-xs text-slate-500">
                Pontos máximos (opcional)
              </p>
            </div>
          </div>

          <div className="flex gap-4 justify-end pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              onClick={onClose}
              variant="secondary"
              disabled={isLoading}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={isLoading || Number(weight) <= 0}
            >
              {isLoading ? 'Salvando...' : 'Salvar Alterações'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
