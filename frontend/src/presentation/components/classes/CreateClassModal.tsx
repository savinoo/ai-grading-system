import React, { useState } from 'react';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { CreateClassDTO } from '@domain/entities/Class';

interface CreateClassModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateClassDTO) => Promise<void>;
}

export const CreateClassModal: React.FC<CreateClassModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState<CreateClassDTO>({
    name: '',
    description: '',
    year: new Date().getFullYear(),
    semester: 1,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      await onSubmit(formData);
      setFormData({
        name: '',
        description: '',
        year: new Date().getFullYear(),
        semester: 1,
      });
      onClose();
    } catch (error) {
      // Error is handled by the parent component
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Nova Turma</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Nome da Turma"
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Ex: Matemática Avançada - Turma A"
            required
          />

          <div className="flex flex-col gap-2">
            <label className="text-slate-900 dark:text-slate-200 text-sm font-bold leading-normal px-1">
              Descrição
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Descreva a turma..."
              rows={3}
              className="form-input flex w-full rounded-lg text-slate-900 dark:text-white border border-slate-200 dark:border-slate-700 focus:border-primary focus:ring-primary/10 bg-white dark:bg-slate-800/50 focus:ring-4 placeholder:text-slate-400 px-4 py-3.5 text-base font-normal leading-normal transition-all focus:outline-none resize-none"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Ano"
              type="number"
              value={formData.year}
              onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
              min="2020"
              max="2030"
              required
            />

            <div className="flex flex-col gap-2">
              <label className="text-slate-900 dark:text-slate-200 text-sm font-bold leading-normal px-1">
                Semestre
              </label>
              <select
                value={formData.semester}
                onChange={(e) => setFormData({ ...formData, semester: parseInt(e.target.value) })}
                className="form-input flex w-full rounded-lg text-slate-900 dark:text-white border border-slate-200 dark:border-slate-700 focus:border-primary focus:ring-primary/10 bg-white dark:bg-slate-800/50 focus:ring-4 h-14 px-4 py-3.5 text-base font-normal leading-normal transition-all focus:outline-none"
                required
              >
                <option value={1}>1º Semestre</option>
                <option value={2}>2º Semestre</option>
              </select>
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              onClick={onClose}
              variant="secondary"
              className="flex-1"
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="primary"
              className="flex-1"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Criando...' : 'Criar Turma'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
