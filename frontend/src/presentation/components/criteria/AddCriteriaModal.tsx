import React, { useState } from 'react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { GradingCriteria } from '@domain/entities/Criteria';
import { useExams } from '@presentation/hooks/useExams';

interface AddCriteriaModalProps {
  isOpen: boolean;
  onClose: () => void;
  examUuid: string;
  availableCriteria: GradingCriteria[];
  onSuccess?: () => void;
}

export const AddCriteriaModal: React.FC<AddCriteriaModalProps> = ({
  isOpen,
  onClose,
  examUuid,
  availableCriteria,
  onSuccess,
}) => {
  const { createCriteria, isLoading } = useExams();
  const [selectedCriteriaUuid, setSelectedCriteriaUuid] = useState('');
  const [weight, setWeight] = useState('1');
  const [maxPoints, setMaxPoints] = useState('10');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedCriteriaUuid || Number(weight) <= 0) {
      return;
    }

    try {
      await createCriteria({
        exam_uuid: examUuid,
        criteria_uuid: selectedCriteriaUuid,
        weight: Number(weight),
        max_points: Number(maxPoints) || undefined,
      });

      setSelectedCriteriaUuid('');
      setWeight('1');
      setMaxPoints('10');
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Erro ao adicionar critério:', error);
    }
  };

  if (!isOpen) return null;

  const selectedCriteria = availableCriteria.find(c => c.uuid === selectedCriteriaUuid);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl w-full max-w-2xl mx-4">
        <div className="p-6 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
              Adicionar Critério
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
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Selecione o Critério *
            </label>
            <select
              value={selectedCriteriaUuid}
              onChange={(e) => setSelectedCriteriaUuid(e.target.value)}
              required
              disabled={isLoading}
              className="w-full rounded-lg border-slate-200 dark:border-slate-700 dark:bg-slate-800 focus:ring-primary focus:border-primary text-base p-3"
            >
              <option value="">-- Selecione --</option>
              {availableCriteria.map((criteria) => (
                <option key={criteria.uuid} value={criteria.uuid}>
                  {criteria.name}
                </option>
              ))}
            </select>

            {selectedCriteria && (
              <div className="mt-3 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {selectedCriteria.description}
                </p>
              </div>
            )}
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
              disabled={isLoading || !selectedCriteriaUuid || Number(weight) <= 0}
            >
              {isLoading ? 'Adicionando...' : 'Adicionar'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
