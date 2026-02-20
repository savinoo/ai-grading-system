import React, { useState, useEffect } from 'react';
import { ExamQuestion, QuestionCriteriaOverride, StudentAnswer } from '@domain/entities/Question';
import { GradingCriteria, ExamCriteria } from '@domain/entities/Criteria';
import { Student } from '@domain/entities/Student';

interface QuestionFormData {
  statement: string;
  points: number;
  question_order: number;
  criteriaOverrides: {
    criteria_uuid: string;
    weight?: number;
    max_points?: number;
    active?: boolean;
    uuid?: string; // Para rastrear critérios existentes ao editar
  }[];
  studentAnswers: {
    student_uuid: string;
    answer_text: string;
    tempId?: string; // Para identificar antes de salvar (UUID quando já existe)
  }[];
}

interface QuestionsStepProps {
  examUuid: string;
  examCriteria: ExamCriteria[];
  gradingCriteria: GradingCriteria[];
  questions: ExamQuestion[];
  students: Student[];
  isLoading: boolean;
  onCreateQuestion: (data: QuestionFormData) => Promise<void>;
  onUpdateQuestion: (questionUuid: string, data: QuestionFormData) => Promise<void>;
  onDeleteQuestion: (questionUuid: string) => Promise<void>;
  questionCriteriaOverrides: QuestionCriteriaOverride[];
  studentAnswers: StudentAnswer[];
  onLoadQuestionCriteriaOverrides: (questionUuid: string) => Promise<void>;
  onLoadStudentAnswers: (questionUuid: string) => Promise<void>;
  onCreateQuestionCriteriaOverride: (data: any) => Promise<QuestionCriteriaOverride>;
  onUpdateQuestionCriteriaOverride: (overrideUuid: string, data: any) => Promise<QuestionCriteriaOverride>;
  onDeleteQuestionCriteriaOverride: (overrideUuid: string) => Promise<void>;
  onCreateStudentAnswer: (data: any) => Promise<StudentAnswer>;
  onUpdateStudentAnswer: (answerUuid: string, data: any) => Promise<StudentAnswer>;
  onDeleteStudentAnswer: (answerUuid: string) => Promise<void>;
}

export const QuestionsStep: React.FC<QuestionsStepProps> = ({
  examUuid: _examUuid,
  examCriteria,
  gradingCriteria,
  questions,
  students,
  isLoading,
  onCreateQuestion,
  onUpdateQuestion,
  onDeleteQuestion,
  questionCriteriaOverrides,
  studentAnswers,
  onLoadQuestionCriteriaOverrides,
  onLoadStudentAnswers,
  onCreateQuestionCriteriaOverride,
  onUpdateQuestionCriteriaOverride,
  onDeleteQuestionCriteriaOverride,
  onCreateStudentAnswer,
  onUpdateStudentAnswer,
  onDeleteStudentAnswer,
}) => {
  const [isAddingQuestion, setIsAddingQuestion] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<ExamQuestion | null>(null);
  const [autoDistributeWeights, setAutoDistributeWeights] = useState(true);
  const [originalCriteriaOverrides, setOriginalCriteriaOverrides] = useState<QuestionCriteriaOverride[]>([]);
  const [originalStudentAnswers, setOriginalStudentAnswers] = useState<StudentAnswer[]>([]);
  const [newQuestion, setNewQuestion] = useState<QuestionFormData>({
    statement: '',
    points: 10,
    question_order: questions.length + 1,
    criteriaOverrides: [],
    studentAnswers: [],
  });

  const handleAddQuestion = () => {
    setIsAddingQuestion(true);
    setAutoDistributeWeights(true);
    setNewQuestion({
      statement: '',
      points: 10,
      question_order: questions.length + 1,
      criteriaOverrides: [],
      studentAnswers: [],
    });
  };

  const handleCancelNewQuestion = () => {
    setIsAddingQuestion(false);
    setEditingQuestion(null);
    setOriginalCriteriaOverrides([]);
    setOriginalStudentAnswers([]);
    setAutoDistributeWeights(true);
    setNewQuestion({
      statement: '',
      points: 10,
      question_order: questions.length + 1,
      criteriaOverrides: [],
      studentAnswers: [],
    });
  };

  const handleEditQuestion = async (question: ExamQuestion) => {
    try {
      setEditingQuestion(question);
      setIsAddingQuestion(true);
      
      // Carregar critérios customizados da questão
      await onLoadQuestionCriteriaOverrides(question.uuid);
      
      // Carregar respostas dos alunos da questão
      await onLoadStudentAnswers(question.uuid);
    } catch (error) {
      console.error('Erro ao carregar dados da questão:', error);
      alert('Erro ao carregar dados da questão');
    }
  };

  // Quando os dados são carregados, atualizar o formulário
  useEffect(() => {
    if (editingQuestion && isAddingQuestion) {
      // Mapear critérios
      const criteriaOverrides = questionCriteriaOverrides
        .filter(override => override.question_uuid === editingQuestion.uuid)
        .map(override => ({
          criteria_uuid: override.criteria_uuid,
          weight: override.weight_override || undefined,
          max_points: override.max_points_override || undefined,
          active: override.active,
          uuid: override.uuid,
        }));

      // Mapear respostas
      const answers = studentAnswers
        .filter(answer => answer.question_uuid === editingQuestion.uuid)
        .map(answer => ({
          student_uuid: answer.student_uuid,
          answer_text: answer.answer_text,
          tempId: answer.uuid, // Usar uuid como tempId para identificar
        }));

      setOriginalCriteriaOverrides(questionCriteriaOverrides.filter(o => o.question_uuid === editingQuestion.uuid));
      setOriginalStudentAnswers(studentAnswers.filter(a => a.question_uuid === editingQuestion.uuid));

      setNewQuestion({
        statement: editingQuestion.statement,
        points: editingQuestion.points,
        question_order: editingQuestion.question_order,
        criteriaOverrides,
        studentAnswers: answers,
      });
    }
  }, [questionCriteriaOverrides, studentAnswers, editingQuestion, isAddingQuestion]);

  const handleSaveNewQuestion = async () => {
    if (!newQuestion.statement.trim()) {
      alert('Preencha o enunciado da questão');
      return;
    }

    if (!newQuestion.points || newQuestion.points <= 0) {
      alert('A pontuação deve ser maior que 0');
      return;
    }

    try {
      if (editingQuestion) {
        // Modo de edição
        await onUpdateQuestion(editingQuestion.uuid, {
          ...newQuestion,
          question_order: editingQuestion.question_order, // Mantém a ordem original
        });

        // ========== SINCRONIZAR CRITÉRIOS CUSTOMIZADOS ==========
        
        // 1. Identificar critérios a DELETAR (estavam no original mas não estão mais)
        for (const originalOverride of originalCriteriaOverrides) {
          const stillExists = newQuestion.criteriaOverrides.find(
            co => co.uuid === originalOverride.uuid
          );
          if (!stillExists) {
            await onDeleteQuestionCriteriaOverride(originalOverride.uuid);
          }
        }

        // 2. Criar NOVOS critérios ou ATUALIZAR existentes
        for (const override of newQuestion.criteriaOverrides) {
          if (override.uuid) {
            // Critério existe, verificar se foi modificado
            const original = originalCriteriaOverrides.find(o => o.uuid === override.uuid);
            if (original) {
              const hasChanged = 
                original.weight_override !== override.weight ||
                original.max_points_override !== override.max_points ||
                original.active !== override.active;
              
              if (hasChanged) {
                await onUpdateQuestionCriteriaOverride(override.uuid, {
                  weight_override: override.weight,
                  max_points_override: override.max_points,
                  active: override.active,
                });
              }
            }
          } else {
            // Critério novo, criar
            await onCreateQuestionCriteriaOverride({
              question_uuid: editingQuestion.uuid,
              criteria_uuid: override.criteria_uuid,
              weight_override: override.weight,
              max_points_override: override.max_points,
              active: override.active,
            });
          }
        }

        // ========== SINCRONIZAR RESPOSTAS DOS ALUNOS ==========
        
        // 1. Identificar respostas a DELETAR (estavam no original mas não estão mais)
        for (const originalAnswer of originalStudentAnswers) {
          const stillExists = newQuestion.studentAnswers.find(
            sa => sa.tempId === originalAnswer.uuid
          );
          if (!stillExists) {
            await onDeleteStudentAnswer(originalAnswer.uuid);
          }
        }

        // 2. Criar NOVAS respostas ou ATUALIZAR existentes
        for (const answer of newQuestion.studentAnswers) {
          // Verifica se é uma resposta existente (UUID real, não temp-*)
          const isExistingAnswer = answer.tempId && !answer.tempId.startsWith('temp-');
          
          if (isExistingAnswer) {
            // Resposta existe, verificar se foi modificada
            const original = originalStudentAnswers.find(o => o.uuid === answer.tempId!);
            if (original) {
              const hasChanged = original.answer_text !== answer.answer_text;
              
              if (hasChanged) {
                await onUpdateStudentAnswer(answer.tempId!, {
                  answer_text: answer.answer_text,
                });
              }
            }
          } else {
            // Resposta nova, criar
            if (answer.student_uuid && answer.answer_text.trim()) {
              await onCreateStudentAnswer({
                exam_uuid: editingQuestion.exam_uuid,
                question_uuid: editingQuestion.uuid,
                student_uuid: answer.student_uuid,
                answer_text: answer.answer_text,
              });
            }
          }
        }

      } else {
        // Modo de criação
        const questionOrder = questions.length + 1;
        await onCreateQuestion({
          ...newQuestion,
          question_order: questionOrder,
        });
      }

      setIsAddingQuestion(false);
      setEditingQuestion(null);
      setOriginalCriteriaOverrides([]);
      setOriginalStudentAnswers([]);
      setAutoDistributeWeights(true);
      setNewQuestion({
        statement: '',
        points: 10,
        question_order: (questions.length + 1) + 1,
        criteriaOverrides: [],
        studentAnswers: [],
      });
    } catch (error) {
      console.error('Erro ao salvar questão:', error);
      alert('Erro ao salvar questão');
    }
  };

  const recalculateWeightsIfAuto = (overridesToRecalculate: typeof newQuestion.criteriaOverrides) => {
    if (!autoDistributeWeights) return overridesToRecalculate;

    // Ensure all exam criteria have entries in overrides
    let allOverrides = [...overridesToRecalculate];
    examCriteria.forEach(ec => {
      if (!allOverrides.some(co => co.criteria_uuid === ec.criteria_uuid)) {
        allOverrides.push({
          criteria_uuid: ec.criteria_uuid,
          weight: ec.weight,
          max_points: ec.max_points,
          active: true,
        });
      }
    });

    const activeExamCriteria = examCriteria.filter(
      ec => !allOverrides.some(co => co.criteria_uuid === ec.criteria_uuid && co.active === false)
    );
    const activeAddedCriteria = allOverrides.filter(
      co => !examCriteria.some(ec => ec.criteria_uuid === co.criteria_uuid) && co.active !== false
    );
    const totalActive = activeExamCriteria.length + activeAddedCriteria.length;

    if (totalActive > 0) {
      const evenWeight = 100 / totalActive;
      return allOverrides.map(co =>
        co.active === false ? co : { ...co, weight: evenWeight }
      );
    }

    return allOverrides;
  };

  const handleAddCriteriaOverride = (criteriaUuid: string) => {
    const examCrit = examCriteria.find(ec => ec.criteria_uuid === criteriaUuid);
    const defaultWeight = examCrit?.weight ?? 0;
    const defaultMaxPoints = examCrit?.max_points ?? 10;

    setNewQuestion(prev => {
      const existingIndex = prev.criteriaOverrides.findIndex(co => co.criteria_uuid === criteriaUuid);
      let updatedOverrides;

      if (existingIndex >= 0) {
        updatedOverrides = prev.criteriaOverrides.map((co, i) =>
          i === existingIndex
            ? {
                ...co,
                active: true,
                weight: co.weight ?? defaultWeight,
                max_points: co.max_points ?? defaultMaxPoints,
              }
            : co
        );
      } else {
        updatedOverrides = [
          ...prev.criteriaOverrides,
          {
            criteria_uuid: criteriaUuid,
            weight: defaultWeight,
            max_points: defaultMaxPoints,
            active: true,
          },
        ];
      }

      const finalOverrides = recalculateWeightsIfAuto(updatedOverrides);
      return { ...prev, criteriaOverrides: finalOverrides };
    });
  };

  const renderCriteriaCard = (
    criteriaUuid: string,
    examCriteria_value?: typeof examCriteria[0]
  ) => {
    const criteria = gradingCriteria.find(gc => gc.uuid === criteriaUuid);
    const overrideIndex = newQuestion.criteriaOverrides.findIndex(
      co => co.criteria_uuid === criteriaUuid
    );
    const override = overrideIndex >= 0 ? newQuestion.criteriaOverrides[overrideIndex] : undefined;
    
    if (!criteria) return null;

    const isRemoved = override?.active === false;
    const isCustomized = override !== undefined && !isRemoved;
    const isAdded = !examCriteria_value; // True if this is an added (unmapped) criteria
    const displayWeight = override?.weight ?? examCriteria_value?.weight ?? 0;
    const displayPoints = override?.max_points ?? examCriteria_value?.max_points ?? 10;

    return (
      <div
        key={criteriaUuid}
        className={`p-4 rounded-lg border transition-all ${
          isRemoved
            ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
            : isCustomized
              ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'
              : isAdded
                ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                : 'bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700'
        }`}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h6 className="text-sm font-bold text-slate-900 dark:text-white">{criteria.name}</h6>
              {isAdded && (
                <span className="px-2 py-0.5 bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 text-[10px] font-bold rounded">
                  Adicional
                </span>
              )}
              {isCustomized && !isAdded && (
                <span className="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 text-[10px] font-bold rounded">
                  Customizado
                </span>
              )}
              {isRemoved && (
                <span className="px-2 py-0.5 bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 text-[10px] font-bold rounded">
                  Removido
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-1">{criteria.description}</p>
          </div>
          <div className="flex items-center gap-2">
            {isAdded ? (
              // Para critérios adicionais: apenas delete
              <button
                onClick={() => {
                  if (overrideIndex >= 0) {
                    handleRemoveCriteriaOverride(overrideIndex);
                  }
                }}
                disabled={isLoading}
                className="text-slate-300 hover:text-red-500 transition-colors disabled:opacity-50"
                title="Remover critério adicionado"
              >
                <span className="material-symbols-outlined text-lg">delete</span>
              </button>
            ) : (
              // Para critérios da prova: block e edit
              <>
                <button
                  onClick={() => {
                    if (isRemoved) {
                      if (overrideIndex >= 0) {
                        handleRemoveCriteriaOverride(overrideIndex);
                      }
                    } else {
                      handleDeactivateCriteriaOverride(criteriaUuid);
                    }
                  }}
                  disabled={isLoading}
                  className="text-slate-300 hover:text-red-500 transition-colors disabled:opacity-50"
                  title={isRemoved ? 'Restaurar critério' : 'Remover critério'}
                >
                  <span className="material-symbols-outlined text-lg">
                    {isRemoved ? 'undo' : 'block'}
                  </span>
                </button>
                <button
                  onClick={() => {
                    if (isCustomized) {
                      if (overrideIndex >= 0) {
                        handleRemoveCriteriaOverride(overrideIndex);
                      }
                    } else {
                      handleAddCriteriaOverride(criteriaUuid);
                    }
                  }}
                  disabled={isLoading || isRemoved}
                  className="text-slate-300 hover:text-amber-600 transition-colors disabled:opacity-50"
                  title={isCustomized ? 'Remover customização' : 'Customizar'}
                >
                  <span className="material-symbols-outlined text-lg">
                    {isCustomized ? 'close' : 'edit'}
                  </span>
                </button>
              </>
            )}
          </div>
        </div>

        {/* Inputs customizáveis */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
              Peso (%)
            </label>
            <input
              type="number"
              value={displayWeight.toFixed(1)}
              onChange={(e) => {
                const value = parseFloat(e.target.value) || 0;
                if (!isCustomized) {
                  handleAddCriteriaOverride(criteriaUuid);
                }
                if (overrideIndex >= 0) {
                  handleUpdateCriteriaOverride(overrideIndex, 'weight', value);
                }
              }}
              disabled={isLoading || isRemoved || autoDistributeWeights}
              step="0.1"
              min="0"
              className="w-full rounded px-2 py-1.5 text-sm font-bold text-center border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:ring-primary focus:border-primary disabled:opacity-50"
            />
          </div>

          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
              Pontos Máx
            </label>
            <input
              type="number"
              value={displayPoints.toFixed(1)}
              onChange={(e) => {
                const value = parseFloat(e.target.value) || 0;
                if (!isCustomized) {
                  handleAddCriteriaOverride(criteriaUuid);
                }
                if (overrideIndex >= 0) {
                  handleUpdateCriteriaOverride(overrideIndex, 'max_points', value);
                }
              }}
              disabled={isLoading || isRemoved}
              step="0.1"
              min="0"
              className="w-full rounded px-2 py-1.5 text-sm font-bold text-center border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:ring-primary focus:border-primary"
            />
          </div>
        </div>
      </div>
    );
  };

  const handleDeactivateCriteriaOverride = (criteriaUuid: string) => {
    setNewQuestion(prev => {
      const existingIndex = prev.criteriaOverrides.findIndex(co => co.criteria_uuid === criteriaUuid);
      let updatedOverrides;

      if (existingIndex >= 0) {
        updatedOverrides = prev.criteriaOverrides.map((co, i) =>
          i === existingIndex
            ? { ...co, active: false, weight: undefined, max_points: undefined }
            : co
        );
      } else {
        updatedOverrides = [
          ...prev.criteriaOverrides,
          { criteria_uuid: criteriaUuid, active: false },
        ];
      }

      const finalOverrides = recalculateWeightsIfAuto(updatedOverrides);
      return { ...prev, criteriaOverrides: finalOverrides };
    });
  };

  const handleRemoveCriteriaOverride = (index: number) => {
    setNewQuestion(prev => {
      let updatedOverrides = prev.criteriaOverrides.filter((_, i) => i !== index);
      const finalOverrides = recalculateWeightsIfAuto(updatedOverrides);
      return { ...prev, criteriaOverrides: finalOverrides };
    });
  };

  const handleUpdateCriteriaOverride = (index: number, field: 'weight' | 'max_points', value: number) => {
    setNewQuestion(prev => ({
      ...prev,
      criteriaOverrides: prev.criteriaOverrides.map((co, i) =>
        i === index ? { ...co, [field]: value, active: true } : co
      ),
    }));
  };

  const handleAddStudentAnswer = () => {
    setNewQuestion(prev => ({
      ...prev,
      studentAnswers: [
        ...prev.studentAnswers,
        {
          student_uuid: '',
          answer_text: '',
          tempId: `temp-${Date.now()}`,
        },
      ],
    }));
  };

  const handleRemoveStudentAnswer = (tempId: string) => {
    setNewQuestion(prev => ({
      ...prev,
      studentAnswers: prev.studentAnswers.filter(sa => sa.tempId !== tempId),
    }));
  };

  const handleUpdateStudentAnswer = (tempId: string, field: 'student_uuid' | 'answer_text', value: string) => {
    setNewQuestion(prev => ({
      ...prev,
      studentAnswers: prev.studentAnswers.map(sa =>
        sa.tempId === tempId ? { ...sa, [field]: value } : sa
      ),
    }));
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-slate-900 dark:text-white">Questões da Prova</h3>
          <p className="text-sm text-slate-500">Defina as questões dissertativas e insira as respostas dos alunos.</p>
        </div>
        <button
          onClick={handleAddQuestion}
          disabled={isAddingQuestion || isLoading}
          className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-bold text-primary dark:text-primary-light hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors disabled:opacity-50 dark:disabled:opacity-70 disabled:cursor-not-allowed"
        >
          <span className="material-symbols-outlined text-lg">add</span>
          Adicionar Questão
        </button>
      </div>

      {/* Lista de Questões Existentes */}
      <div className="space-y-4">
        {questions.length === 0 && !isAddingQuestion && (
          <div className="text-center py-8 text-slate-500">
            <p>Nenhuma questão adicionada ainda</p>
            <p className="text-sm">Clique em "Adicionar Questão" para começar</p>
          </div>
        )}
        {questions.map((question) => (
          <div
            key={question.uuid}
            onClick={() => handleEditQuestion(question)}
            className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden cursor-pointer hover:border-primary hover:shadow-md transition-all"
          >
            <div className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-bold text-slate-400 uppercase">Questão {question.question_order}</span>
                    <span className="px-2 py-0.5 bg-primary/10 dark:bg-primary-light/20 text-primary dark:text-primary-light text-[10px] font-bold rounded">
                      {question.points} ponto{question.points !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{question.statement}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteQuestion(question.uuid);
                  }}
                  disabled={isLoading}
                  className="text-slate-300 hover:text-red-500 transition-colors disabled:opacity-50 ml-4"
                >
                  <span className="material-symbols-outlined">delete</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Formulário de Nova Questão */}
      {isAddingQuestion && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border-2 border-primary dark:border-primary shadow-lg p-8 space-y-6">
          <div className="flex items-center justify-between">
            <h4 className="text-lg font-bold text-slate-900 dark:text-white">
              {editingQuestion ? 'Editar Questão' : 'Nova Questão'}
            </h4>
            <button
              onClick={handleCancelNewQuestion}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>

          {/* Dados Básicos */}
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Enunciado da Questão *
              </label>
              <textarea
                value={newQuestion.statement}
                onChange={(e) => setNewQuestion(prev => ({ ...prev, statement: e.target.value }))}
                placeholder="Ex: Explique o conceito de polimorfismo em programação orientada a objetos..."
                rows={4}
                disabled={isLoading}
                className="w-full rounded-lg border-slate-200 dark:border-slate-700 dark:bg-slate-900 dark:text-white text-sm focus:ring-primary focus:border-primary p-3"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Pontuação *
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={newQuestion.points}
                  onChange={(e) => setNewQuestion(prev => ({ ...prev, points: parseFloat(e.target.value) || 0 }))}
                  placeholder="Ex: 10"
                  disabled={isLoading}
                  step="0.5"
                  min="0"
                  className="w-32 rounded-lg border-slate-200 dark:border-slate-700 dark:bg-slate-900 dark:text-primary-light text-center font-bold text-primary focus:ring-primary focus:border-primary p-2"
                />
                <span className="text-sm font-medium text-slate-400">ponto{newQuestion.points !== 1 ? 's' : ''}</span>
              </div>
            </div>
          </div>

          {/* Critérios de Avaliação */}
          {examCriteria.length > 0 && (
            <div className="border-t border-slate-200 dark:border-slate-700 pt-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h5 className="text-sm font-bold text-slate-900 dark:text-white mb-1">
                    Critérios de Avaliação
                  </h5>
                  <p className="text-xs text-slate-500">
                    Edite os pesos e pontuações conforme necessário, ou remova critérios que não se aplicam a esta questão.
                  </p>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <span className="text-xs font-bold text-slate-500 uppercase">AUTO-DISTRIBUIR PESOS</span>
                  <button
                    onClick={() => {
                      const newAutoState = !autoDistributeWeights;
                      setAutoDistributeWeights(newAutoState);
                      
                      if (newAutoState) {
                        // Quando ligar auto, garantir que todos os critérios tenham overrides e recalcular
                        setNewQuestion(prev => {
                          let allOverrides = [...prev.criteriaOverrides];
                          
                          // Adicionar overrides para critérios da prova que não têm
                          examCriteria.forEach(ec => {
                            if (!allOverrides.some(co => co.criteria_uuid === ec.criteria_uuid)) {
                              allOverrides.push({
                                criteria_uuid: ec.criteria_uuid,
                                weight: ec.weight,
                                max_points: ec.max_points,
                                active: true,
                              });
                            }
                          });

                          // Calcular pesos
                          const activeCount = allOverrides.filter(co => co.active !== false).length;
                          if (activeCount > 0) {
                            const evenWeight = 100 / activeCount;
                            allOverrides = allOverrides.map(co =>
                              co.active === false ? co : { ...co, weight: evenWeight }
                            );
                          }

                          return { ...prev, criteriaOverrides: allOverrides };
                        });
                      }
                    }}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      autoDistributeWeights
                        ? 'bg-primary'
                        : 'bg-slate-300 dark:bg-slate-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        autoDistributeWeights ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                {/* Renderizar critérios da prova */}
                {examCriteria.map((ec) => renderCriteriaCard(ec.criteria_uuid, ec))}

                {/* Renderizar critérios adicionados (não estão em examCriteria) */}
                {newQuestion.criteriaOverrides
                  .filter(co => !examCriteria.some(ec => ec.criteria_uuid === co.criteria_uuid))
                  .map((override) => renderCriteriaCard(override.criteria_uuid))}
              </div>

              {/* Adicionar critério extra (não está na prova) */}
              {gradingCriteria.length > examCriteria.length && (
                <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                  <p className="text-xs text-slate-500 mb-2">Adicionar outro critério:</p>
                  <select
                    onChange={(e) => {
                      if (e.target.value) {
                        handleAddCriteriaOverride(e.target.value);
                        e.target.value = '';
                      }
                    }}
                    disabled={isLoading}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white text-sm p-2"
                  >
                    <option value="">+ Adicionar critério</option>
                    {gradingCriteria
                      .filter(gc => 
                        !examCriteria.some(ec => ec.criteria_uuid === gc.uuid) &&
                        !newQuestion.criteriaOverrides.some(co => co.criteria_uuid === gc.uuid)
                      )
                      .map((criteria) => (
                        <option key={criteria.uuid} value={criteria.uuid}>
                          {criteria.name}
                        </option>
                      ))}
                  </select>
                </div>
              )}
            </div>
          )}

          {/* Respostas dos Alunos */}
          <div className="border-t border-slate-200 dark:border-slate-700 pt-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <h5 className="text-sm font-bold text-slate-900 dark:text-white">
                  Respostas dos Alunos
                </h5>
                <span className="text-xs font-semibold px-2 py-1 rounded-full bg-primary/10 dark:bg-primary-light/20 text-primary dark:text-primary-light">
                  {newQuestion.studentAnswers.length}/{students.length}
                </span>
              </div>
              <button
                onClick={handleAddStudentAnswer}
                disabled={newQuestion.studentAnswers.length === students.length && students.length > 0}
                className={`text-xs font-bold flex items-center gap-1 ${
                  newQuestion.studentAnswers.length === students.length && students.length > 0
                    ? 'text-slate-300 dark:text-slate-600 cursor-not-allowed'
                    : 'text-primary dark:text-primary-light hover:text-primary/80 dark:hover:text-primary-light/80'
                }`}
              >
                <span className="material-symbols-outlined text-sm">add</span>
                Adicionar Resposta
              </button>
            </div>

            <div className="space-y-4">
              {newQuestion.studentAnswers.map((answer) => {
                // Filtrar alunos que não têm resposta adicionada (ou que é o aluno atual)
                const availableStudents = students.filter(student =>
                  !newQuestion.studentAnswers.some(
                    sa => sa.student_uuid === student.uuid && sa.tempId !== answer.tempId
                  )
                );

                return (
                <div
                  key={answer.tempId}
                  className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg p-4"
                >
                  <div className="flex items-center justify-between mb-3">
                    {students.length > 0 ? (
                      <select
                        value={answer.student_uuid}
                        onChange={(e) => handleUpdateStudentAnswer(answer.tempId!, 'student_uuid', e.target.value)}
                        className="flex-1 rounded-lg border-slate-200 dark:border-slate-700 dark:bg-slate-900 dark:text-white text-sm focus:ring-primary focus:border-primary p-2 mr-2"
                      >
                        <option value="">-- Selecione o aluno --</option>
                        {availableStudents.map((student) => (
                          <option key={student.uuid} value={student.uuid}>
                            {student.full_name || student.name} {student.registration ? `(${student.registration})` : ''}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <div className="flex-1 rounded border border-yellow-200 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20 p-2 mr-2 text-sm text-yellow-700 dark:text-yellow-300">
                        ⚠️ Nenhum aluno encontrado na turma. Verifique se a turma foi selecionada corretamente.
                      </div>
                    )}

                    <button
                      onClick={() => handleRemoveStudentAnswer(answer.tempId!)}
                      className="text-slate-400 hover:text-red-500 transition-colors"
                      title="Remover resposta"
                    >
                      <span className="material-symbols-outlined text-xl">delete</span>
                    </button>
                  </div>

                  <textarea
                    value={answer.answer_text}
                    onChange={(e) => handleUpdateStudentAnswer(answer.tempId!, 'answer_text', e.target.value)}
                    placeholder="Cole a resposta do aluno aqui..."
                    rows={5}
                    className="w-full rounded-lg border-slate-200 dark:border-slate-700 dark:bg-slate-900 dark:text-white text-sm focus:ring-primary focus:border-primary p-3"
                  />
                </div>
                );
              })}

              {newQuestion.studentAnswers.length === 0 && (
                <div className="text-center py-6 text-sm text-slate-400 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-lg">
                  Nenhuma resposta de aluno adicionada
                </div>
              )}
            </div>
          </div>

          {/* Ações */}
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-700">
            <button
              onClick={handleCancelNewQuestion}
              className="px-4 py-2 text-sm font-bold text-slate-600 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
            >
              Cancelar
            </button>
            <button
              onClick={handleSaveNewQuestion}
              disabled={isLoading || !newQuestion.statement.trim() || newQuestion.points <= 0}
              className="px-6 py-2 bg-primary text-white text-sm font-bold rounded-lg hover:opacity-90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Salvando...' : editingQuestion ? 'Atualizar Questão' : 'Salvar Questão'}
            </button>
          </div>
        </div>
      )}

      {/* Estado vazio */}
      {!isAddingQuestion && questions.length === 0 && (
        <div className="bg-slate-50 dark:bg-slate-900 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl py-16 text-center">
          <div className="size-16 bg-primary/10 rounded-full flex items-center justify-center text-primary mx-auto mb-4">
            <span className="material-symbols-outlined text-3xl">quiz</span>
          </div>
          <h4 className="text-lg font-bold text-slate-900 dark:text-white mb-2">
            Nenhuma questão adicionada
          </h4>
          <p className="text-sm text-slate-500 mb-6">
            Comece adicionando a primeira questão da prova
          </p>
          <button
            onClick={handleAddQuestion}
            className="px-6 py-2 bg-primary text-white text-sm font-bold rounded-lg hover:opacity-90"
          >
            Adicionar Primeira Questão
          </button>
        </div>
      )}
    </div>
  );
};
