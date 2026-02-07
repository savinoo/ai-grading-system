import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';
import { Button } from '@presentation/components/ui/Button';
import { Input } from '@presentation/components/ui/Input';
import { useExams } from '@presentation/hooks/useExams';
import { useClasses } from '@presentation/hooks/useClasses';
import { useAttachments } from '@presentation/hooks/useAttachments';
import { FileUpload } from '@presentation/components/attachments/FileUpload';
import { AttachmentList } from '@presentation/components/attachments/AttachmentList';
import { GradingCriteria } from '@domain/entities/Criteria';

interface CriteriaFormItem {
  criteria_uuid: string;
  weight: number;
  uuid?: string; // UUID do ExamCriteria se já foi criado
}

export const ExamFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { examUuid } = useParams<{ examUuid?: string }>();
  const isEditMode = !!examUuid;

  const {
    createExam,
    updateExamData,
    loadExamDetails,
    loadExamCriteria,
    createCriteria,
    updateCriteria,
    deleteCriteria,
    loadGradingCriteria,
    currentExam,
    examCriteria,
    gradingCriteria,
    isLoading
  } = useExams();

  const { classes, loadTeacherClasses, isLoading: isLoadingClasses } = useClasses();

  const {
    attachments,
    uploadAttachment,
    loadAttachments,
    deleteAttachment,
    isLoading: isLoadingAttachments,
  } = useAttachments();

  // Estado do formulário
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [classUuid, setClassUuid] = useState<string>('');
  const [selectedCriteria, setSelectedCriteria] = useState<CriteriaFormItem[]>([]);
  const [autoDistribute, setAutoDistribute] = useState(true);
  const [createdExamUuid, setCreatedExamUuid] = useState<string | null>(examUuid || null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploadingFile, setIsUploadingFile] = useState(false);

  // Carregar dados iniciais
  useEffect(() => {
    loadGradingCriteria();
    loadTeacherClasses();

    if (isEditMode && examUuid) {
      loadExamDetails(examUuid);
      loadExamCriteria(examUuid);
      loadAttachments(examUuid);
    }
  }, [examUuid, isEditMode, loadGradingCriteria, loadTeacherClasses, loadExamDetails, loadExamCriteria, loadAttachments]);

  // Carregar anexos quando a prova for criada automaticamente
  useEffect(() => {
    if (createdExamUuid && !isEditMode) {
      loadAttachments(createdExamUuid);
    }
  }, [createdExamUuid, isEditMode, loadAttachments]);

  // Preencher form quando carregar prova existente
  useEffect(() => {
    if (currentExam && isEditMode) {
      setTitle(currentExam.title);
      setDescription(currentExam.description || '');
      setClassUuid(currentExam.class_uuid || '');
      setCreatedExamUuid(currentExam.uuid);
    }
  }, [currentExam, isEditMode]);

  // Preencher critérios quando carregar
  useEffect(() => {
    if (examCriteria.length > 0 && isEditMode) {
      setSelectedCriteria(
        examCriteria.map(ec => ({
          criteria_uuid: ec.criteria_uuid,
          weight: ec.weight,
          uuid: ec.uuid
        }))
      );
    }
  }, [examCriteria, isEditMode]);

  const totalWeight = selectedCriteria.reduce((sum, c) => sum + c.weight, 0);

  // Criar prova automaticamente quando preencher o mínimo necessário
  useEffect(() => {
    const createDraftAutomatically = async () => {
      if (!isEditMode && !createdExamUuid && title.trim() && !isSaving) {
        setIsSaving(true);
        try {
          const exam = await createExam({
            title,
            description: description || undefined,
            class_uuid: classUuid || null,
            status: 'DRAFT',
          });
          setCreatedExamUuid(exam.uuid);
          setHasUnsavedChanges(false);
        } catch (error) {
          console.error('Erro ao criar prova automaticamente:', error);
        } finally {
          setIsSaving(false);
        }
      }
    };

    // Debounce para não criar múltiplas vezes
    const timer = setTimeout(createDraftAutomatically, 1000);
    return () => clearTimeout(timer);
  }, [title, description, classUuid, createdExamUuid, isEditMode, createExam, isSaving]);

  const handleAddCriteria = async (criteriaUuid: string) => {
    const newWeight = autoDistribute ? 100 / (selectedCriteria.length + 1) : 10;

    if (createdExamUuid) {
      // Se já tem prova criada, cria o critério no backend
      try {
        const newCriteria = await createCriteria({
          exam_uuid: createdExamUuid,
          criteria_uuid: criteriaUuid,
          weight: newWeight,
        });

        const newItem = {
          criteria_uuid: criteriaUuid,
          weight: newWeight,
          uuid: newCriteria.uuid
        };

        let newList = [...selectedCriteria, newItem];

        if (autoDistribute) {
          const distributedWeight = 100 / newList.length;
          newList = newList.map(c => ({ ...c, weight: distributedWeight }));

          // Atualizar pesos no backend
          for (const item of newList) {
            if (item.uuid && item.uuid !== newCriteria.uuid) {
              await updateCriteria(item.uuid, { weight: distributedWeight });
            }
          }
        }

        setSelectedCriteria(newList);
        setHasUnsavedChanges(false);
      } catch (error) {
        console.error('Erro ao adicionar critério:', error);
      }
    } else {
      // Modo local (antes de criar prova)
      const newCriteria = [...selectedCriteria, { criteria_uuid: criteriaUuid, weight: newWeight }];

      if (autoDistribute) {
        const distributedWeight = 100 / newCriteria.length;
        setSelectedCriteria(newCriteria.map(c => ({ ...c, weight: distributedWeight })));
      } else {
        setSelectedCriteria(newCriteria);
      }
      setHasUnsavedChanges(true);
    }
  };

  const handleRemoveCriteria = async (index: number) => {
    const item = selectedCriteria[index];

    if (item.uuid) {
      // Remover do backend
      try {
        await deleteCriteria(item.uuid);
        const newCriteria = selectedCriteria.filter((_, i) => i !== index);

        if (autoDistribute && newCriteria.length > 0) {
          const distributedWeight = 100 / newCriteria.length;
          for (const c of newCriteria) {
            if (c.uuid) {
              await updateCriteria(c.uuid, { weight: distributedWeight });
            }
          }
          setSelectedCriteria(newCriteria.map(c => ({ ...c, weight: distributedWeight })));
        } else {
          setSelectedCriteria(newCriteria);
        }
      } catch (error) {
        console.error('Erro ao remover critério:', error);
      }
    } else {
      // Remover local
      const newCriteria = selectedCriteria.filter((_, i) => i !== index);
      setSelectedCriteria(newCriteria);
      setHasUnsavedChanges(true);
    }
  };

  const handleWeightChange = async (index: number, weight: number) => {
    const newCriteria = [...selectedCriteria];
    newCriteria[index].weight = weight;
    setSelectedCriteria(newCriteria);

    if (newCriteria[index].uuid) {
      // Atualizar no backend
      try {
        await updateCriteria(newCriteria[index].uuid!, { weight });
        setHasUnsavedChanges(false);
      } catch (error) {
        console.error('Erro ao atualizar peso:', error);
      }
    } else {
      setHasUnsavedChanges(true);
    }
  };

  const handleToggleAutoDistribute = async () => {
    const newValue = !autoDistribute;
    setAutoDistribute(newValue);

    if (newValue && selectedCriteria.length > 0) {
      const distributedWeight = 100 / selectedCriteria.length;
      const newCriteria = selectedCriteria.map(c => ({ ...c, weight: distributedWeight }));
      setSelectedCriteria(newCriteria);

      // Atualizar no backend se já existe
      if (createdExamUuid) {
        for (const item of newCriteria) {
          if (item.uuid) {
            await updateCriteria(item.uuid, { weight: distributedWeight });
          }
        }
      }
    }
  };

  const handleSave = async () => {
    if (!title.trim()) {
      alert('Preencha o título da prova');
      return;
    }

    try {
      setIsSaving(true);

      if (createdExamUuid) {
        // Atualizar prova existente
        await updateExamData(createdExamUuid, {
          title,
          description: description || undefined,
          class_uuid: classUuid || null,
        });
        setHasUnsavedChanges(false);
        alert('Alterações salvas com sucesso!');
      }
    } catch (error) {
      console.error('Erro ao salvar:', error);
      alert('Erro ao salvar alterações');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = async () => {
    if (createdExamUuid && !isEditMode) {
      // Se criou uma prova nova, perguntar se quer deletar
      const shouldDelete = confirm(
        'Você criou um rascunho. Deseja remover esta prova?'
      );

      if (shouldDelete) {
        // TODO: Implementar delete exam
        // await deleteExam(createdExamUuid);
      }
    } else if (hasUnsavedChanges) {
      const shouldDiscard = confirm(
        'Você tem alterações não salvas. Deseja descartar e sair?'
      );
      if (!shouldDiscard) return;
    }

    navigate('/dashboard/exams');
  };

  const handleBack = () => {
    if (hasUnsavedChanges) {
      const shouldSave = confirm(
        'Você tem alterações não salvas. Deseja salvar antes de sair?'
      );
      if (shouldSave) {
        handleSave().then(() => navigate('/dashboard/exams'));
      } else {
        navigate('/dashboard/exams');
      }
    } else {
      navigate('/dashboard/exams');
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!createdExamUuid) {
      alert('A prova precisa ser criada antes de anexar arquivos');
      return;
    }

    try {
      setIsUploadingFile(true);
      await uploadAttachment(createdExamUuid, file);
      alert('Arquivo anexado com sucesso!');
    } catch (error) {
      console.error('Erro ao fazer upload:', error);
      alert('Erro ao fazer upload do arquivo. Tente novamente.');
    } finally {
      setIsUploadingFile(false);
    }
  };

  const handleDeleteAttachment = async (attachmentUuid: string) => {
    const shouldDelete = confirm('Deseja remover este arquivo?');
    if (!shouldDelete) return;

    try {
      await deleteAttachment(attachmentUuid);
      alert('Arquivo removido com sucesso!');
    } catch (error) {
      console.error('Erro ao deletar anexo:', error);
      alert('Erro ao remover arquivo. Tente novamente.');
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
              {isEditMode ? 'Editar Prova' : 'Nova Prova'}
            </h1>
            {createdExamUuid && (
              <span className="px-3 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold rounded-full">
                Rascunho Salvo
              </span>
            )}
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
                  onChange={(e) => {
                    setTitle(e.target.value);
                    setHasUnsavedChanges(true);
                  }}
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
                  onChange={(e) => {
                    setClassUuid(e.target.value);
                    setHasUnsavedChanges(true);
                  }}
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
                  onChange={(e) => {
                    setDescription(e.target.value);
                    setHasUnsavedChanges(true);
                  }}
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
              {createdExamUuid ? (
                <>
                  <FileUpload
                    onFileSelect={handleFileUpload}
                    isUploading={isUploadingFile}
                    acceptedTypes=".pdf"
                    maxSizeMB={200}
                  />

                  {attachments.length > 0 && (
                    <div className="mt-6">
                      <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
                        Arquivos Anexados ({attachments.length})
                      </h4>
                      <AttachmentList
                        attachments={attachments}
                        onDelete={handleDeleteAttachment}
                        isDeleting={isLoadingAttachments}
                      />
                    </div>
                  )}
                </>
              ) : (
                <div className="border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl p-10 flex flex-col items-center justify-center text-center bg-slate-50/50 dark:bg-slate-800/30">
                  <div className="size-12 bg-amber-100 dark:bg-amber-900/30 rounded-full flex items-center justify-center text-amber-600 dark:text-amber-400 mb-4">
                    <span className="material-symbols-outlined text-3xl">info</span>
                  </div>
                  <p className="text-sm font-bold text-slate-700 dark:text-slate-300">
                    Preencha o título para começar a anexar arquivos
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    A prova será salva automaticamente como rascunho
                  </p>
                </div>
              )}
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
            onClick={handleBack}
            className="flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-slate-800 dark:hover:text-white transition-colors"
            disabled={isLoading}
          >
            <span className="material-symbols-outlined text-lg">arrow_back</span>
            Voltar para Provas
          </button>

          <div className="flex items-center gap-4">
            {hasUnsavedChanges && (
              <span className="text-xs text-amber-600 dark:text-amber-400">
                Alterações não salvas
              </span>
            )}

            <Button
              onClick={handleCancel}
              variant="secondary"
              disabled={isLoading}
            >
              Cancelar
            </Button>

            <Button
              onClick={handleSave}
              disabled={isLoading || !title.trim() || isSaving}
            >
              {isSaving ? 'Salvando...' : 'Salvar Alterações'}
            </Button>
          </div>
        </div>
      </footer>
    </DashboardLayout>
  );
};
