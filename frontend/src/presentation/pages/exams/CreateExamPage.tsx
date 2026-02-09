import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';
import { Button } from '@presentation/components/ui/Button';
import { QuestionsStep } from '@presentation/components/exams/QuestionsStep';
import { useExams, useClasses, useQuestions, useStudents, useAttachments } from '@presentation/hooks';
import { FileUpload } from '@presentation/components/attachments/FileUpload';
import { AttachmentList } from '@presentation/components/attachments/AttachmentList';

interface CriteriaFormItem {
  criteria_uuid: string;
  weight: number;
  max_points: number;
  uuid?: string;
}

export const CreateExamPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    createExam,
    createCriteria,
    updateCriteria,
    deleteCriteria,
    updateExamData,
    deleteExam,
    loadGradingCriteria,
    gradingCriteria,
    isLoading
  } = useExams();
  const { classes, loadTeacherClasses, isLoading: isLoadingClasses } = useClasses();
  const {
    questions,
    createQuestion,
    updateQuestion,
    loadQuestionsByExam,
    deleteQuestion,
    createQuestionCriteriaOverride,
    updateQuestionCriteriaOverride,
    deleteQuestionCriteriaOverride,
    loadQuestionCriteriaOverrides,
    questionCriteriaOverrides,
    createStudentAnswer,
    updateStudentAnswer,
    deleteStudentAnswer,
    loadStudentAnswersByQuestion,
    studentAnswers,
    isLoading: isLoadingQuestions,
  } = useQuestions();
  const { students, loadStudentsByClass } = useStudents();
  const {
    attachments,
    uploadAttachment,
    loadAttachments,
    deleteAttachment,
    isLoading: isLoadingAttachments,
  } = useAttachments();

  // Estado do formulário - Passo 1
  const [currentStep, setCurrentStep] = useState(1);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [classUuid, setClassUuid] = useState<string>('');
  const [selectedCriteria, setSelectedCriteria] = useState<CriteriaFormItem[]>([]);
  const [autoDistribute, setAutoDistribute] = useState(true);
  const [createdExamUuid, setCreatedExamUuid] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploadingFile, setIsUploadingFile] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    loadGradingCriteria();
    loadTeacherClasses();
  }, [loadGradingCriteria, loadTeacherClasses]);

  useEffect(() => {
    if (classUuid) {
      loadStudentsByClass(classUuid);
    }
  }, [classUuid, loadStudentsByClass]);

  useEffect(() => {
    if (createdExamUuid) {
      loadQuestionsByExam(createdExamUuid);
      loadAttachments(createdExamUuid);
    }
  }, [createdExamUuid, loadQuestionsByExam, loadAttachments]);

  // Criar prova automaticamente quando preencher o mínimo necessário
  useEffect(() => {
    const createDraftAutomatically = async () => {
      if (!createdExamUuid && title.trim() && !isSaving) {
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
  }, [title, description, classUuid, createdExamUuid, createExam, isSaving]);

  const handleAddCriteria = async (criteriaUuid: string) => {
    const newWeight = autoDistribute ? 100 / (selectedCriteria.length + 1) : 10;
    const newMaxPoints = 10;

    if (createdExamUuid) {
      // Se já tem prova criada, cria o critério no backend
      try {
        const newCriteria = await createCriteria({
          exam_uuid: createdExamUuid,
          criteria_uuid: criteriaUuid,
          weight: newWeight,
          max_points: newMaxPoints,
        });

        const newItem = {
          criteria_uuid: criteriaUuid,
          weight: newWeight,
          max_points: newMaxPoints,
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
      const newCriteria = [...selectedCriteria, { criteria_uuid: criteriaUuid, weight: newWeight, max_points: newMaxPoints }];

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

  const handleMaxPointsChange = async (index: number, max_points: number) => {
    const newCriteria = [...selectedCriteria];
    newCriteria[index].max_points = max_points;
    setSelectedCriteria(newCriteria);

    if (newCriteria[index].uuid) {
      // Atualizar no backend
      try {
        await updateCriteria(newCriteria[index].uuid!, { max_points });
        setHasUnsavedChanges(false);
      } catch (error) {
        console.error('Erro ao atualizar pontuação máxima:', error);
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

  const handleNextStep = async () => {
    if (currentStep === 1) {
      // Validar Passo 1
      if (!title.trim()) {
        alert('Preencha o título da prova');
        return;
      }

      if (!classUuid) {
        alert('Selecione uma turma para criar a prova');
        return;
      }

      if (selectedCriteria.length === 0) {
        alert('Adicione pelo menos um critério de avaliação');
        return;
      }

      // Salvar todas as alterações antes de avançar
      await handleSaveDraft();

      // Avançar para o passo 2
      setCurrentStep(2);
    }
  };

  const handlePreviousStep = () => {
    if (currentStep === 2) {
      setCurrentStep(1);
    }
  };

  const handleFinish = async () => {
    if (!createdExamUuid) {
      alert('Erro: Prova não foi criada');
      return;
    }

    navigate(`/dashboard/exams/${createdExamUuid}`);
  };

  const handleCreateQuestion = async (questionData: any) => {
    if (!createdExamUuid) {
      alert('Erro: Prova não foi criada');
      return;
    }

    try {
      // Criar a questão
      const question = await createQuestion({
        exam_uuid: createdExamUuid,
        statement: questionData.statement,
        points: questionData.points,
        question_order: questionData.question_order,
      });

      // Criar critérios customizados se houver
      if (questionData.criteriaOverrides && questionData.criteriaOverrides.length > 0) {
        for (const override of questionData.criteriaOverrides) {
          await createQuestionCriteriaOverride({
            question_uuid: question.uuid,
            criteria_uuid: override.criteria_uuid,
            weight_override: override.weight,
            max_points_override: override.max_points,
            active: override.active,
          });
        }
      }

      // Criar respostas dos alunos se houver
      if (questionData.studentAnswers && questionData.studentAnswers.length > 0) {
        for (const answer of questionData.studentAnswers) {
          if (answer.student_uuid && answer.answer_text.trim()) {
            await createStudentAnswer({
              exam_uuid: createdExamUuid,
              question_uuid: question.uuid,
              student_uuid: answer.student_uuid,
              answer_text: answer.answer_text,
            });
          }
        }
      }
    } catch (error) {
      console.error('Erro ao criar questão:', error);
      throw error;
    }
  };

  const handleUpdateQuestion = async (questionUuid: string, questionData: any) => {
    try {
      // Atualizar a questão
      await updateQuestion(questionUuid, {
        statement: questionData.statement,
        points: questionData.points,
        question_order: questionData.question_order,
      });

      // Nota: Critérios e respostas de alunos não são atualizados aqui
      // Eles são gerenciados separadamente através de seus próprios endpoints
    } catch (error) {
      console.error('Erro ao atualizar questão:', error);
      throw error;
    }
  };

  const handleDeleteQuestion = async (questionUuid: string) => {
    const confirm = window.confirm('Tem certeza que deseja remover esta questão?');
    if (!confirm) return;

    try {
      await deleteQuestion(questionUuid);
    } catch (error) {
      console.error('Erro ao deletar questão:', error);
      alert('Erro ao deletar questão');
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

  const handleSaveDraft = async () => {
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
        alert('Rascunho salvo com sucesso!');
      }
    } catch (error) {
      console.error('Erro ao salvar rascunho:', error);
      alert('Erro ao salvar rascunho');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async () => {
    if (!createdExamUuid) {
      navigate('/dashboard/exams');
      return;
    }

    try {
      await deleteExam(createdExamUuid);
      navigate('/dashboard/exams');
    } catch (error) {
      console.error('Erro ao excluir prova:', error);
      alert('Erro ao excluir prova. Tente novamente.');
    }
  };

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
  };

  const totalWeight = selectedCriteria.reduce((sum, c) => sum + c.weight, 0);

  return (
    <DashboardLayout>
      <div className="flex-1 max-w-5xl mx-auto w-full px-6 py-8 pb-32">
        {/* Header com Progresso */}
        <div className="mb-10">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
              {currentStep === 1 ? 'Passo 1: Configuração e Rubrica' : 'Passo 2: Questões e Respostas'}
            </h1>
            <div className="flex items-center gap-4">
              <span className="text-sm font-bold text-slate-500">Passo {currentStep} de 2</span>
              {createdExamUuid && (
                <span className="px-3 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold rounded-full">
                  Rascunho Salvo
                </span>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            <div className={`h-2 flex-1 rounded-full transition-colors ${currentStep >= 1 ? 'bg-primary' : 'bg-slate-200 dark:bg-slate-700'}`}></div>
            <div className={`h-2 flex-1 rounded-full transition-colors ${currentStep >= 2 ? 'bg-primary' : 'bg-slate-200 dark:bg-slate-700'}`}></div>
          </div>
        </div>

        {/* Conteúdo do Passo 1 */}
        {currentStep === 1 && (
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
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Ex: Análise Histórica: Revolução Industrial"
                    disabled={isLoading}
                    className="w-full rounded-lg border-slate-200 dark:border-slate-700 dark:bg-slate-800 focus:ring-primary focus:border-primary text-base p-3"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                    Turma *
                  </label>
                  <select
                    value={classUuid}
                    onChange={(e) => setClassUuid(e.target.value)}
                    disabled={isLoading || isLoadingClasses}
                    className="w-full rounded-lg border-slate-200 dark:border-slate-700 dark:bg-slate-800 focus:ring-primary focus:border-primary text-base p-3"
                  >
                    <option value="">-- Selecione uma turma --</option>
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
            {createdExamUuid && (
              <section className="bg-white dark:bg-slate-900 rounded-xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm">
                <div className="flex items-center gap-2 mb-6">
                  <span className="material-symbols-outlined text-primary">description</span>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                    Materiais e Referências
                  </h3>
                </div>

                <div className="space-y-6">
                  <FileUpload
                    onFileSelect={handleFileUpload}
                    isUploading={isUploadingFile}
                  />

                  {attachments.length > 0 && (
                    <AttachmentList
                      attachments={attachments}
                      onDelete={handleDeleteAttachment}
                    />
                  )}
                </div>
              </section>
            )}

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
                  const criteria = gradingCriteria.find(gc => gc.uuid === item.criteria_uuid);
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
                        <div className="col-span-12 md:col-span-3">
                          <label className="text-[10px] font-bold text-slate-400 uppercase mb-1 block">
                            Critério
                          </label>
                          <div className="text-sm font-bold text-slate-900 dark:text-white">
                            {criteria.name}
                          </div>
                        </div>

                        <div className="col-span-12 md:col-span-4">
                          <label className="text-[10px] font-bold text-slate-400 uppercase mb-1 block">
                            Descrição
                          </label>
                          <div className="text-xs text-slate-500">
                            {criteria.description}
                          </div>
                        </div>

                        <div className="col-span-12 md:col-span-5 flex items-center justify-end gap-3">
                          <div>
                            <label className="text-[10px] font-bold text-slate-400 uppercase mb-1 block text-center">
                              Pontuação Máx *
                            </label>
                            <div className="flex items-center gap-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded px-2 py-1">
                              <input
                                type="number"
                                value={item.max_points}
                                onChange={(e) => handleMaxPointsChange(index, parseFloat(e.target.value) || 0)}
                                disabled={isLoading}
                                className="w-16 border-0 p-0 text-sm font-bold text-center focus:ring-0 bg-transparent text-slate-900 dark:text-white"
                                step="0.1"
                                min="0"
                              />
                              <span className="text-xs font-bold text-slate-400">pts</span>
                            </div>
                          </div>

                          <div>
                            <label className="text-[10px] font-bold text-slate-400 uppercase mb-1 block text-center">
                              Peso
                            </label>
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
                          </div>

                          <button
                            onClick={() => handleRemoveCriteria(index)}
                            disabled={isLoading}
                            className="text-slate-300 hover:text-red-500 transition-colors mt-4"
                          >
                            <span className="material-symbols-outlined text-lg">delete</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}

                {gradingCriteria.filter(gc => !selectedCriteria.some(sc => sc.criteria_uuid === gc.uuid)).length > 0 ? (
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
                        {gradingCriteria.filter(gc => !selectedCriteria.some(sc => sc.criteria_uuid === gc.uuid)).map((criteria) => (
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
        )}

        {/* Conteúdo do Passo 2 */}
        {currentStep === 2 && createdExamUuid && (
          <>
            {!classUuid ? (
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-8 text-center">
                <div className="text-slate-500 mb-4">
                  <span className="material-symbols-outlined text-5xl block mb-2">warning</span>
                </div>
                <h4 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Turma não selecionada</h4>
                <p className="text-sm text-slate-500 mb-4">Retorne ao passo anterior e selecione uma turma para adicionar questões.</p>
                <button
                  onClick={() => setCurrentStep(1)}
                  className="px-4 py-2 bg-primary text-white rounded-lg font-bold text-sm hover:bg-primary/90 transition-colors"
                >
                  Voltar para Turma
                </button>
              </div>
            ) : (
              <QuestionsStep
                examUuid={createdExamUuid}
                examCriteria={selectedCriteria.map(c => ({
                  uuid: c.uuid || '',
                  exam_uuid: createdExamUuid,
                  criteria_uuid: c.criteria_uuid,
                  weight: c.weight,
                  max_points: c.max_points,
                  active: true,
                  created_at: new Date().toISOString(),
                }))}
                gradingCriteria={gradingCriteria}
                questions={questions}
                students={students}
                isLoading={isLoadingQuestions}
                onCreateQuestion={handleCreateQuestion}
                onUpdateQuestion={handleUpdateQuestion}
                onDeleteQuestion={handleDeleteQuestion}
                questionCriteriaOverrides={questionCriteriaOverrides}
                studentAnswers={studentAnswers}
                onLoadQuestionCriteriaOverrides={loadQuestionCriteriaOverrides}
                onLoadStudentAnswers={loadStudentAnswersByQuestion}
                onCreateQuestionCriteriaOverride={createQuestionCriteriaOverride}
                onUpdateQuestionCriteriaOverride={updateQuestionCriteriaOverride}
                onDeleteQuestionCriteriaOverride={deleteQuestionCriteriaOverride}
                onCreateStudentAnswer={createStudentAnswer}
                onUpdateStudentAnswer={updateStudentAnswer}
                onDeleteStudentAnswer={deleteStudentAnswer}
              />
            )}
          </>
        )}
      </div>

      {/* Footer Fixo */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 p-4 z-50">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <button
            onClick={handleCancel}
            className="flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-slate-800 dark:hover:text-white transition-colors"
            disabled={isLoading}
          >
            <span className="material-symbols-outlined text-lg">close</span>
            Cancelar e Sair
          </button>

          <div className="flex items-center gap-4">
            {hasUnsavedChanges && (
              <span className="text-xs font-bold text-amber-600 dark:text-amber-400">
                Alterações não salvas
              </span>
            )}

            <Button
              onClick={handleSaveDraft}
              variant="secondary"
              disabled={isLoading || !title.trim()}
              className="flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-sm">save</span>
              Salvar Rascunho
            </Button>

            {currentStep === 2 && (
              <Button
                onClick={handlePreviousStep}
                variant="secondary"
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-sm">arrow_back</span>
                Voltar
              </Button>
            )}

            {currentStep === 1 && (
              <Button
                onClick={handleNextStep}
                disabled={isLoading || !title.trim() || selectedCriteria.length === 0}
                className="flex items-center gap-2 min-w-[150px] justify-center"
              >
                {isLoading ? 'Salvando...' : 'Próximo Passo'}
                <span className="material-symbols-outlined text-sm">arrow_forward</span>
              </Button>
            )}

            {currentStep === 2 && (
              <Button
                onClick={handleFinish}
                disabled={isLoading}
                className="flex items-center gap-2 min-w-[150px] justify-center"
              >
                Salvar e Publicar
                <span className="material-symbols-outlined text-sm">check</span>
              </Button>
            )}
          </div>
        </div>
      </footer>

      {/* Modal de Confirmação de Exclusão */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[100]">
          <div className="bg-white dark:bg-slate-900 rounded-xl p-8 max-w-md w-full mx-4 shadow-2xl border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full">
                <span className="material-symbols-outlined text-red-600 dark:text-red-400 text-2xl">warning</span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                Confirmar Exclusão
              </h3>
            </div>
            
            <p className="text-slate-600 dark:text-slate-400 mb-6">
              Tem certeza que deseja cancelar e excluir esta prova rascunho? 
              <strong className="block mt-2 text-slate-900 dark:text-white">
                Todas as informações, anexos, critérios e questões serão removidos permanentemente.
              </strong>
            </p>

            <div className="flex items-center gap-3 justify-end">
              <Button
                onClick={handleCancelDelete}
                variant="secondary"
                className="flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-sm">close</span>
                Não, voltar
              </Button>
              
              <button
                onClick={handleConfirmDelete}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold text-sm transition-colors"
              >
                <span className="material-symbols-outlined text-sm">delete</span>
                Sim, excluir tudo
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
};


