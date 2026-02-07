import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';
import { Button } from '@presentation/components/ui/Button';
import { Input } from '@presentation/components/ui/Input';
import { useExams } from '@presentation/hooks/useExams';
import { useClasses } from '@presentation/hooks/useClasses';
import { GradingCriteria } from '@domain/entities/Criteria';

interface CriteriaFormItem {
  criteria_uuid: string;
  weight: number;
}

export const CreateExamPage: React.FC = () => {
  const navigate = useNavigate();
  const { createExam, createCriteria, loadGradingCriteria, gradingCriteria, isLoading } = useExams();
  const { classes, loadTeacherClasses, isLoading: isLoadingClasses } = useClasses();

  // Estado do formulário
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [classUuid, setClassUuid] = useState<string>('');
  const [selectedCriteria, setSelectedCriteria] = useState<CriteriaFormItem[]>([]);
  const [autoDistribute, setAutoDistribute] = useState(true);

  useEffect(() => {
    loadGradingCriteria();
    loadTeacherClasses();
  }, [loadGradingCriteria, loadTeacherClasses]);

  const totalWeight = selectedCriteria.reduce((sum, c) => sum + c.weight, 0);

  const handleAddCriteria = (criteriaUuid: string) => {
    const newWeight = autoDistribute ? 100 / (selectedCriteria.length + 1) : 10;
    
    const newCriteria = [...selectedCriteria, { criteria_uuid: criteriaUuid, weight: newWeight }];
    
    if (autoDistribute) {
      // Redistribuir pesos igualmente
      const distributedWeight = 100 / newCriteria.length;
      setSelectedCriteria(newCriteria.map(c => ({ ...c, weight: distributedWeight })));
    } else {
      setSelectedCriteria(newCriteria);
    }
  };

  const handleRemoveCriteria = (index: number) => {
    const newCriteria = selectedCriteria.filter((_, i) => i !== index);
    
    if (autoDistribute && newCriteria.length > 0) {
      const distributedWeight = 100 / newCriteria.length;
      setSelectedCriteria(newCriteria.map(c => ({ ...c, weight: distributedWeight })));
    } else {
      setSelectedCriteria(newCriteria);
    }
  };

  const handleWeightChange = (index: number, weight: number) => {
    const newCriteria = [...selectedCriteria];
    newCriteria[index].weight = weight;
    setSelectedCriteria(newCriteria);
  };

  const handleToggleAutoDistribute = () => {
    const newValue = !autoDistribute;
    setAutoDistribute(newValue);
    
    if (newValue && selectedCriteria.length > 0) {
      const distributedWeight = 100 / selectedCriteria.length;
      setSelectedCriteria(selectedCriteria.map(c => ({ ...c, weight: distributedWeight })));
    }
  };

  const handleSaveDraft = async () => {
    if (!title.trim()) {
      alert('Preencha o título da prova');
      return;
    }

    try {
      const exam = await createExam({
        title,
        description: description || undefined,
        status: 'DRAFT',
      });

      alert('Rascunho salvo com sucesso!');
      navigate(`/dashboard/exams/${exam.uuid}`);
    } catch (error) {
      console.error('Erro ao salvar rascunho:', error);
      alert('Erro ao salvar rascunho');
    }
  };

  const handleSubmit = async () => {
    if (!title.trim()) {
      alert('Preencha o título da prova');
      return;
    }

    if (selectedCriteria.length === 0) {
      alert('Adicione pelo menos um critério de avaliação');
      return;
    }

    try {
      // Criar a prova
      const exam = await createExam({
        title,
        description: description || undefined,
        class_uuid: classUuid || null,
        status: 'DRAFT',
      });

      // Criar critérios associados
      for (const criteria of selectedCriteria) {
        await createCriteria({
          exam_uuid: exam.uuid,
          criteria_uuid: criteria.criteria_uuid,
          weight: criteria.weight,
        });
      }

      alert('Prova criada com sucesso!');
      navigate(`/dashboard/exams/${exam.uuid}`);
    } catch (error) {
      console.error('Erro ao criar prova:', error);
      alert('Erro ao criar prova');
    }
  };

  const availableCriteria = gradingCriteria.filter(
    gc => !selectedCriteria.some(sc => sc.criteria_uuid === gc.uuid)
  );

  const getCriteriaById = (uuid: string): GradingCriteria | undefined => {
    return gradingCriteria.find(gc => gc.uuid === uuid);
  };

  return (
    <DashboardLayout>
      <div className="flex-1 max-w-5xl mx-auto w-full px-6 py-8 pb-32">
        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
              Passo 1: Configuração e Rubrica
            </h1>
            <span className="text-sm font-bold text-slate-500">Passo 1 de 2</span>
          </div>
          <div className="flex gap-2">
            <div className="h-2 flex-1 bg-primary rounded-full"></div>
            <div className="h-2 flex-1 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
          </div>
        </div>

        <div className="space-y-10">
          {/* Informações Básicas */}
          <section className="bg-white dark:bg-slate-900 rounded-xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center gap-2 mb-6">
              <span className="material-symbols-outlined text-primary">edit_note</span>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Informações Básicas
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Título da Prova *
                </label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Ex: Análise Histórica: Revolução Industrial"
                  disabled={isLoading}
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Turma
                </label>
                <select
                  value={classUuid}
                  onChange={(e) => setClassUuid(e.target.value)}
                  disabled={isLoading || isLoadingClasses}
                  className="w-full rounded-lg border-slate-200 dark:border-slate-700 dark:bg-slate-800 focus:ring-primary focus:border-primary text-base p-3"
                >
                  <option value="">Selecione uma turma (opcional)</option>
                  {classes.map((cls) => (
                    <option key={cls.uuid} value={cls.uuid}>
                      {cls.name} - {cls.year}/{cls.semester}º Semestre
                    </option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Descrição
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Descrição da prova (opcional)"
                  rows={4}
                  disabled={isLoading}
                  className="w-full rounded-lg border-slate-200 dark:border-slate-700 dark:bg-slate-800 focus:ring-primary focus:border-primary text-base p-3"
                />
              </div>
            </div>
          </section>

          {/* Materiais e Referências */}
          <section className="bg-white dark:bg-slate-900 rounded-xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center gap-2 mb-6">
              <span className="material-symbols-outlined text-primary">description</span>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Materiais e Referências
              </h3>
            </div>

            <div className="space-y-6">
              <div className="border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl p-10 flex flex-col items-center justify-center text-center hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-not-allowed opacity-60">
                <div className="size-12 bg-primary/10 rounded-full flex items-center justify-center text-primary mb-4">
                  <span className="material-symbols-outlined text-3xl">upload_file</span>
                </div>
                <p className="text-sm font-bold text-slate-500">
                  Upload de arquivos em desenvolvimento
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Em breve você poderá enviar PDFs de referência
                </p>
              </div>
            </div>
          </section>

          {/* Rubrica de Avaliação */}
          <section className="bg-white dark:bg-slate-900 rounded-xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">rule</span>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  Rubrica de Avaliação
                </h3>
              </div>

              <div className="flex items-center gap-6">
                <label className="flex items-center gap-3 cursor-pointer group">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Auto-distribuir pesos
                  </span>
                  <div className="relative inline-flex items-center">
                    <input
                      type="checkbox"
                      checked={autoDistribute}
                      onChange={handleToggleAutoDistribute}
                      className="sr-only peer"
                    />
                    <div className="w-10 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
                  </div>
                </label>

                <div className="flex flex-col items-end">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    Peso Total
                  </span>
                  <span className="text-xl font-black text-primary">
                    {totalWeight.toFixed(0)}
                    <span className="text-slate-400 font-normal">%</span>
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              {selectedCriteria.map((item, index) => {
                const criteria = getCriteriaById(item.criteria_uuid);
                if (!criteria) return null;

                return (
                  <div
                    key={index}
                    className="group flex items-start gap-4 p-4 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50 dark:bg-slate-800/50 hover:border-primary/50 transition-colors"
                  >
                    <div className="pt-2">
                      <span className="material-symbols-outlined text-slate-300 cursor-move">
                        drag_indicator
                      </span>
                    </div>

                    <div className="flex-1 grid grid-cols-12 gap-4">
                      <div className="col-span-12 md:col-span-4">
                        <label className="text-[10px] font-bold text-slate-400 uppercase mb-1 block">
                          Critério
                        </label>
                        <div className="text-sm font-bold text-slate-900 dark:text-white">
                          {criteria.name}
                        </div>
                      </div>

                      <div className="col-span-12 md:col-span-5">
                        <label className="text-[10px] font-bold text-slate-400 uppercase mb-1 block">
                          Descrição
                        </label>
                        <div className="text-xs text-slate-500">
                          {criteria.description}
                        </div>
                      </div>

                      <div className="col-span-12 md:col-span-3 flex items-center justify-end gap-3">
                        <div className="flex items-center gap-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded px-2 py-1">
                          <input
                            type="number"
                            value={item.weight.toFixed(1)}
                            onChange={(e) => handleWeightChange(index, parseFloat(e.target.value) || 0)}
                            disabled={autoDistribute || isLoading}
                            className="w-12 border-0 p-0 text-sm font-bold text-center focus:ring-0 bg-transparent text-slate-900 dark:text-white"
                            step="0.1"
                            min="0"
                          />
                          <span className="text-xs font-bold text-slate-400">%</span>
                        </div>

                        <button
                          onClick={() => handleRemoveCriteria(index)}
                          disabled={isLoading}
                          className="text-slate-300 hover:text-red-500 transition-colors"
                        >
                          <span className="material-symbols-outlined text-lg">delete</span>
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}

              {availableCriteria.length > 0 ? (
                <div className="border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl p-4">
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                    Adicionar Critério
                  </label>
                  <div className="flex gap-2">
                    <select
                      onChange={(e) => {
                        if (e.target.value) {
                          handleAddCriteria(e.target.value);
                          e.target.value = '';
                        }
                      }}
                      disabled={isLoading}
                      className="flex-1 rounded-lg border-slate-200 dark:border-slate-700 dark:bg-slate-800 focus:ring-primary focus:border-primary text-sm p-2"
                    >
                      <option value="">-- Selecione um critério --</option>
                      {availableCriteria.map((criteria) => (
                        <option key={criteria.uuid} value={criteria.uuid}>
                          {criteria.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              ) : selectedCriteria.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  Nenhum critério disponível. Carregando...
                </div>
              ) : (
                <div className="text-center py-4 text-sm text-slate-500">
                  Todos os critérios disponíveis foram adicionados
                </div>
              )}
            </div>
          </section>
        </div>
      </div>

      {/* Footer Fixo */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 p-4 z-50">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/dashboard/exams')}
            className="flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-slate-800 dark:hover:text-white transition-colors"
            disabled={isLoading}
          >
            <span className="material-symbols-outlined text-lg">close</span>
            Cancelar e Sair
          </button>

          <div className="flex items-center gap-4">
            <Button
              onClick={handleSaveDraft}
              variant="secondary"
              disabled={isLoading || !title.trim()}
            >
              Salvar Rascunho
            </Button>

            <Button
              onClick={handleSubmit}
              disabled={isLoading || !title.trim() || selectedCriteria.length === 0}
              className="flex items-center gap-2 min-w-[150px] justify-center"
            >
              {isLoading ? 'Criando...' : 'Criar Prova'}
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </Button>
          </div>
        </div>
      </footer>
    </DashboardLayout>
  );
};
