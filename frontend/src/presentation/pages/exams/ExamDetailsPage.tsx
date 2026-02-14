import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@presentation/components/ui/Button';
import { CriteriaList } from '@presentation/components/criteria/CriteriaList';
import { AttachmentList } from '@presentation/components/attachments/AttachmentList';
import { useExams } from '@presentation/hooks/useExams';
import { useAttachments } from '@presentation/hooks/useAttachments';
import { useStudents } from '@presentation/hooks/useStudents';
import { useQuestions } from '@presentation/hooks/useQuestions';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';

export const ExamDetailsPage: React.FC = () => {
  const { examUuid } = useParams<{ examUuid: string }>();
  const navigate = useNavigate();
  const {
    currentExam,
    examCriteria,
    loadExamDetails,
    loadExamCriteria,
    isLoading,
  } = useExams();

  const {
    attachments,
    loadAttachments,
    downloadAttachment,
    isLoading: isLoadingAttachments,
  } = useAttachments();

  const { students, loadStudentsByClass } = useStudents();
  const { questions, loadQuestionsByExam, studentAnswers, loadStudentAnswersByQuestion } = useQuestions();

  // Estado para controlar questões expandidas e respostas carregadas
  const [expandedQuestions, setExpandedQuestions] = useState<Set<string>>(new Set());
  const [questionAnswersMap, setQuestionAnswersMap] = useState<Record<string, any[]>>({});
  const [loadingAnswers, setLoadingAnswers] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (examUuid) {
      loadExamDetails(examUuid);
      loadExamCriteria(examUuid);
      loadAttachments(examUuid);
      loadQuestionsByExam(examUuid);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [examUuid]);

  // Carregar alunos quando a turma for identificada
  useEffect(() => {
    if (currentExam?.class_uuid) {
      loadStudentsByClass(currentExam.class_uuid);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentExam?.class_uuid]);

  const isDraft = currentExam?.status === 'DRAFT';

  // Função para expandir/colapsar questão e carregar respostas
  const handleToggleQuestion = async (questionUuid: string) => {
    const newExpanded = new Set(expandedQuestions);
    
    if (newExpanded.has(questionUuid)) {
      newExpanded.delete(questionUuid);
      setExpandedQuestions(newExpanded);
    } else {
      newExpanded.add(questionUuid);
      setExpandedQuestions(newExpanded);
      
      // Carregar respostas se ainda não foram carregadas
      if (!questionAnswersMap[questionUuid]) {
        setLoadingAnswers(prev => new Set(prev).add(questionUuid));
        try {
          await loadStudentAnswersByQuestion(questionUuid);
          // O hook já atualiza studentAnswers, vamos armazenar localmente
        } catch (error) {
          console.error('Erro ao carregar respostas:', error);
        } finally {
          setLoadingAnswers(prev => {
            const newSet = new Set(prev);
            newSet.delete(questionUuid);
            return newSet;
          });
        }
      }
    }
  };

  // Atualizar mapa de respostas quando studentAnswers mudar
  useEffect(() => {
    if (studentAnswers.length > 0 && expandedQuestions.size > 0) {
      const lastExpandedQuestion = Array.from(expandedQuestions).pop();
      if (lastExpandedQuestion) {
        setQuestionAnswersMap(prev => ({
          ...prev,
          [lastExpandedQuestion]: studentAnswers
        }));
      }
    }
  }, [studentAnswers, expandedQuestions]);

  if (isLoading && !currentExam) {
    return (
      <DashboardLayout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-slate-500">Carregando prova...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!currentExam) {
    return (
      <DashboardLayout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <span className="material-symbols-outlined text-slate-300 dark:text-slate-700 text-6xl mb-4">
              error
            </span>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              Prova não encontrada
            </h2>
            <Button onClick={() => navigate('/dashboard/exams')}>
              Voltar para Provas
            </Button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const statusConfig: Record<string, { label: string; className: string }> = {
    DRAFT: { label: 'Rascunho', className: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' },
    PUBLISHED: { label: 'Publicada', className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
    GRADED: { label: 'Corrigida', className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
    WARNING: { label: 'Aviso de Correção', className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
    ARCHIVED: { label: 'Arquivada', className: 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300' },
    FINISHED: { label: 'Finalizada', className: 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300' },
  };

  const status = statusConfig[currentExam.status] || {
    label: currentExam.status || 'Desconhecido',
    className: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  };
  const totalWeight = examCriteria.reduce((sum, c) => sum + c.weight, 0);

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Button */}
        <button
          onClick={() => navigate('/dashboard/exams')}
          className="flex items-center gap-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white mb-6 transition-colors"
        >
          <span className="material-symbols-outlined">arrow_back</span>
          <span className="font-semibold">Voltar para Provas</span>
        </button>

        {/* Header Card */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-8 mb-6 shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
                  {currentExam.title}
                </h1>
                <span className={`px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wider ${status.className}`}>
                  {status.label}
                </span>
              </div>

              {currentExam.description && (
                <p className="text-slate-600 dark:text-slate-400 text-lg mb-4">
                  {currentExam.description}
                </p>
              )}

              <div className="flex flex-wrap items-center gap-6 text-sm">
                {currentExam.class_name && (
                  <div className="flex items-center gap-2 text-slate-500">
                    <span className="material-symbols-outlined text-lg">school</span>
                    <span className="font-semibold">{currentExam.class_name}</span>
                  </div>
                )}

                <div className="flex items-center gap-2 text-slate-500">
                  <span className="material-symbols-outlined text-lg">calendar_today</span>
                  <span>Criada em {new Date(currentExam.created_at).toLocaleDateString('pt-BR')}</span>
                </div>

                <div className="flex items-center gap-2 text-slate-500">
                  <span className="material-symbols-outlined text-lg">update</span>
                  <span>Atualizada em {new Date(currentExam.updated_at).toLocaleDateString('pt-BR')}</span>
                </div>

                <div className="flex items-center gap-2 text-slate-500">
                  <span className="material-symbols-outlined text-lg">checklist</span>
                  <span>{examCriteria.length} critério{examCriteria.length !== 1 ? 's' : ''}</span>
                </div>

                {totalWeight > 0 && (
                  <div className="flex items-center gap-2 text-slate-500">
                    <span className="material-symbols-outlined text-lg">functions</span>
                    <span>{totalWeight.toFixed(1)}% peso total</span>
                  </div>
                )}
              </div>
            </div>

            {isDraft && (
              <div className="flex gap-3">
                <Button
                  onClick={() => navigate(`/dashboard/exams/${examUuid}/edit`)}
                  variant="secondary"
                >
                  <span className="material-symbols-outlined mr-2">edit</span>
                  Editar Prova
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary/10 rounded-lg">
                <span className="material-symbols-outlined text-primary text-2xl">rule</span>
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white">
                  {examCriteria.length}
                </div>
                <div className="text-xs text-slate-500 uppercase tracking-wider">
                  Critérios de Avaliação
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <span className="material-symbols-outlined text-purple-600 dark:text-purple-400 text-2xl">
                  quiz
                </span>
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white">
                  {questions.length}
                </div>
                <div className="text-xs text-slate-500 uppercase tracking-wider">
                  Questões
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
                <span className="material-symbols-outlined text-emerald-600 dark:text-emerald-400 text-2xl">
                  description
                </span>
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white">
                  {attachments.length}
                </div>
                <div className="text-xs text-slate-500 uppercase tracking-wider">
                  Anexos
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <span className="material-symbols-outlined text-blue-600 dark:text-blue-400 text-2xl">
                  groups
                </span>
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white">
                  {students.length}
                </div>
                <div className="text-xs text-slate-500 uppercase tracking-wider">
                  Alunos
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Attachments Section */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-8 shadow-sm mb-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">description</span>
                Materiais e Referências
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Arquivos anexados para esta prova
              </p>
            </div>
          </div>

          {isLoadingAttachments ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <AttachmentList
              attachments={attachments}
              onDownload={downloadAttachment}
            />
          )}
        </div>

        {/* Criteria Section */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-8 shadow-sm mb-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">rule</span>
                Critérios de Avaliação
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                {isDraft ? 'Configure os critérios e pesos para esta prova' : 'Critérios definidos para esta prova'}
              </p>
            </div>
          </div>

          <CriteriaList
            criteria={examCriteria}
            isEditable={false}
          />

          {examCriteria.length === 0 && isDraft && (
            <div className="text-center py-8">
              <p className="text-slate-500 mb-4">Nenhum critério adicionado ainda</p>
              <Button onClick={() => navigate(`/dashboard/exams/${examUuid}/edit`)}>
                Adicionar Critérios
              </Button>
            </div>
          )}
        </div>

        {/* Questions and Answers Section */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-8 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">quiz</span>
                Questões e Respostas
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                {questions.length} {questions.length === 1 ? 'questão' : 'questões'} nesta prova
              </p>
            </div>
          </div>

          {questions.length === 0 ? (
            <div className="text-center py-12">
              <div className="size-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center text-slate-400 mx-auto mb-4">
                <span className="material-symbols-outlined text-3xl">quiz</span>
              </div>
              <p className="text-slate-500 mb-4">Nenhuma questão adicionada ainda</p>
              {isDraft && (
                <Button onClick={() => navigate(`/dashboard/exams/${examUuid}/edit`)}>
                  Adicionar Questões
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {questions
                .sort((a, b) => a.question_order - b.question_order)
                .map((question, index) => {
                  const isExpanded = expandedQuestions.has(question.uuid);
                  const answers = questionAnswersMap[question.uuid] || [];
                  const isLoadingAnswers = loadingAnswers.has(question.uuid);

                  return (
                    <div
                      key={question.uuid}
                      className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden transition-all"
                    >
                      {/* Question Header */}
                      <button
                        onClick={() => handleToggleQuestion(question.uuid)}
                        className="w-full p-6 flex items-start justify-between hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-left"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                              Questão {index + 1}
                            </span>
                            <span className="px-2 py-0.5 bg-primary/10 text-primary text-[10px] font-bold rounded">
                              {question.points} {question.points === 1 ? 'ponto' : 'pontos'}
                            </span>
                            {answers.length > 0 && (
                              <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[10px] font-bold rounded">
                                {answers.length} {answers.length === 1 ? 'resposta' : 'respostas'}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                            {question.statement}
                          </p>
                        </div>
                        <span className={`material-symbols-outlined text-slate-400 transition-transform ml-4 ${
                          isExpanded ? 'rotate-180' : ''
                        }`}>
                          expand_more
                        </span>
                      </button>

                      {/* Question Answers (Expanded) */}
                      {isExpanded && (
                        <div className="border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-6">
                          {isLoadingAnswers ? (
                            <div className="flex items-center justify-center py-8">
                              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                              <span className="ml-3 text-sm text-slate-500">Carregando respostas...</span>
                            </div>
                          ) : answers.length === 0 ? (
                            <div className="text-center py-8">
                              <span className="material-symbols-outlined text-slate-300 dark:text-slate-600 text-4xl mb-2 block">
                                chat_bubble_outline
                              </span>
                              <p className="text-sm text-slate-500">Nenhuma resposta registrada para esta questão</p>
                            </div>
                          ) : (
                            <div className="space-y-4">
                              <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-4">
                                Respostas dos Alunos:
                              </h4>
                              {answers.map((answer) => {
                                const student = students.find(s => s.uuid === answer.student_uuid);
                                const studentName = student?.full_name || student?.name || 'Aluno não identificado';
                                
                                return (
                                  <div
                                    key={answer.uuid}
                                    className="bg-white dark:bg-slate-900 rounded-lg p-4 border border-slate-200 dark:border-slate-700"
                                  >
                                    <div className="flex items-center gap-2 mb-3">
                                      <div className="p-1.5 bg-blue-100 dark:bg-blue-900/30 rounded-full">
                                        <span className="material-symbols-outlined text-blue-600 dark:text-blue-400 text-sm">
                                          person
                                        </span>
                                      </div>
                                      <span className="text-sm font-bold text-slate-900 dark:text-white">
                                        {studentName}
                                      </span>
                                      {student?.registration && (
                                        <span className="text-xs text-slate-500">
                                          ({student.registration})
                                        </span>
                                      )}
                                    </div>
                                    <div className="pl-8">
                                      <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed whitespace-pre-wrap">
                                        {answer.answer_text}
                                      </p>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};
