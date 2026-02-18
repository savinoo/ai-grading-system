import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';
import { reviewService } from '@infrastructure/api/reviewService';
import type { StudentAnswerReview } from '@domain/types/review';
// 🔥 TESTE: Verificar se imports estão funcionando
console.log('📦 reviewService importado:', reviewService);
console.log('📦 reviewService.getExamReview existe?', typeof reviewService.getExamReview === 'function');

// Configuração de status das respostas
const answerStatusConfig: Record<string, { label: string; className: string }> = {
  SUBMITTED: { label: 'Enviada', className: 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400' },
  GRADED: { label: 'Corrigida', className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
  FINALIZED: { label: 'Aprovada', className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
  INVALID: { label: 'Inválida', className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
};

export const ExamReviewPage: React.FC = () => {
  const { examUuid } = useParams<{ examUuid: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  // 🔥 DEBUG: Log inicial
  console.log('🚀 ExamReviewPage MONTADO - examUuid:', examUuid);
  console.log('🚀 ExamReviewPage MONTADO - timestamp:', new Date().toISOString());
  
  const [activeQuestionIndex, setActiveQuestionIndex] = useState(0);
  const [activeStudentIndex, setActiveStudentIndex] = useState(0);
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [newScore, setNewScore] = useState<number>(0);
  const [newFeedback, setNewFeedback] = useState<string>('');
  
  console.log('📍 Estado atual:', { activeQuestionIndex, activeStudentIndex, showAdjustModal });

  // Buscar dados da revisão
  const { data: reviewData, isLoading, error } = useQuery({
    queryKey: ['exam-review', examUuid],
    queryFn: async () => {
      console.log('🔍 Buscando review para exam:', examUuid);
      const data = await reviewService.getExamReview(examUuid!);
      console.log('✅ Review data recebida:', data);
      console.log('📊 Total de questões:', data.questions.length);
      data.questions.forEach((q, idx) => {
        console.log(`   Questão ${idx + 1}:`, q.student_answers.length, 'respostas');
      });
      return data;
    },
    enabled: !!examUuid,
  });

  // Mutation para ajustar nota
  const adjustGradeMutation = useMutation({
    mutationFn: reviewService.adjustGrade,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exam-review', examUuid] });
      setShowAdjustModal(false);
    },
  });

  // Mutation para aprovar resposta individual
  const approveAnswerMutation = useMutation({
    mutationFn: reviewService.approveAnswer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exam-review', examUuid] });
    },
  });

  // Mutation para finalizar revisão
  const finalizeReviewMutation = useMutation({
    mutationFn: reviewService.finalizeReview,
    onSuccess: () => {
      console.log('✅ Revisão finalizada com sucesso');
      // Navegar para a página de detalhes da prova
      // O relatório pode ser baixado de lá através do botão "Baixar Relatório"
      navigate(`/dashboard/exams/${examUuid}`);
    },
  });


  const handleOpenAdjustModal = (answer: StudentAnswerReview) => {
    setNewScore(answer.score || 0);
    setNewFeedback(answer.feedback || '');
    setShowAdjustModal(true);
  };

  const handleAdjustGrade = () => {
    if (!currentAnswer) return;
    console.log('📝 Ajustar nota clicado:', { answer_uuid: currentAnswer.answer_uuid, newScore, newFeedback });
    adjustGradeMutation.mutate({
      answer_uuid: currentAnswer.answer_uuid,
      new_score: newScore,
      feedback: newFeedback,
    });
  };

  const handleApproveAnswer = () => {
    if (!currentAnswer) return;
    console.log('✅ Aprovar resposta clicado:', currentAnswer.answer_uuid);
    const confirmed = window.confirm(
      `Tem certeza que deseja aprovar a resposta de ${currentAnswer.student_name}? A nota será marcada como finalizada.`
    );
    if (confirmed) {
      console.log('✅ Confirmado - aprovando resposta');
      approveAnswerMutation.mutate(currentAnswer.answer_uuid);
    } else {
      console.log('❌ Cancelado pelo usuário');
    }
  };

  const handleFinalizeReview = () => {
    if (!examUuid) return;
    console.log('🏁 Finalizar revisão clicado:', examUuid);
    const confirmed = window.confirm(
      'Deseja finalizar a revisão? Isso gerará o relatório e notificará os alunos.'
    );
    if (confirmed) {
      console.log('✅ Confirmado - finalizando revisão');
      finalizeReviewMutation.mutate({
        exam_uuid: examUuid,
        send_notifications: true,
        generate_pdf: true,
      });
    } else {
      console.log('❌ Cancelado pelo usuário');
    }
  };

  // Loading e error states
  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-slate-600 dark:text-slate-400">Carregando dados de revisão...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !reviewData) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <span className="material-symbols-outlined text-6xl text-red-500 mb-4">error</span>
            <p className="text-slate-900 dark:text-white font-semibold mb-2">Erro ao carregar dados</p>
            <p className="text-slate-600 dark:text-slate-400">
              {error instanceof Error ? error.message : 'Ocorreu um erro desconhecido'}
            </p>
            <button
              onClick={() => navigate(`/dashboard/exams/${examUuid}`)}
              className="mt-4 px-4 py-2 bg-primary text-white rounded-lg"
            >
              Voltar para detalhes da prova
            </button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const currentQuestion = reviewData.questions[activeQuestionIndex];
  const currentAnswer = currentQuestion?.student_answers[activeStudentIndex];
  
  console.log('🎯 Dados atuais:', {
    totalQuestions: reviewData.questions.length,
    activeQuestionIndex,
    currentQuestion: currentQuestion ? {
      uuid: currentQuestion.question_uuid,
      number: currentQuestion.question_number,
      totalAnswers: currentQuestion.student_answers.length
    } : null,
    activeStudentIndex,
    currentAnswer: currentAnswer ? {
      uuid: currentAnswer.answer_uuid,
      studentName: currentAnswer.student_name,
      totalSuggestions: currentAnswer.ai_suggestions?.length || 0,
      totalCriteria: currentAnswer.criteria_scores.length
    } : null
  });

  if (!currentQuestion || !currentAnswer) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <p className="text-slate-600 dark:text-slate-400">Nenhuma resposta disponível para revisão.</p>
        </div>
      </DashboardLayout>
    );
  }

  const calculateTotalScore = () => {
    return currentAnswer.criteria_scores.reduce((sum, c) => sum + c.raw_score, 0);
  };

  const getAnswerStatusInfo = (status: string) => {
    return answerStatusConfig[status] || {
      label: status,
      className: 'bg-slate-100 text-slate-700 dark:bg-slate-900/30 dark:text-slate-400',
    };
  };

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="px-8 pt-4 pb-2 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
        <div className="flex items-center gap-2 mb-2 text-xs">
          <button onClick={() => navigate('/dashboard/exams')} className="text-slate-500 hover:text-primary transition-colors">
            Exames
          </button>
          <span className="material-symbols-outlined text-xs text-slate-400">chevron_right</span>
          <button onClick={() => navigate(`/dashboard/exams/${examUuid}`)} className="text-slate-500 hover:text-primary transition-colors">
            {reviewData.exam_title}
          </button>
          <span className="material-symbols-outlined text-xs text-slate-400">chevron_right</span>
          <span className="text-primary font-semibold">Revisão de Correção AI</span>
        </div>

        <div className="flex flex-wrap justify-between items-start gap-4 pb-3">
          <div className="flex flex-col">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{currentAnswer.student_name}</h1>
              <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${getAnswerStatusInfo(currentAnswer.status).className}`}>
                {getAnswerStatusInfo(currentAnswer.status).label}
              </span>
            </div>
            <div className="flex flex-wrap gap-4 text-slate-600 dark:text-slate-400 text-xs">
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-sm">email</span>
                {currentAnswer.student_email || 'Sem email'}
              </span>
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-sm">groups</span>
                Turma: {reviewData.class_name || 'Sem turma'}
              </span>
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-sm">event</span>
                {currentAnswer.graded_at
                  ? new Date(currentAnswer.graded_at).toLocaleString('pt-BR')
                  : 'Não corrigida'}
              </span>
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => handleOpenAdjustModal(currentAnswer)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 text-sm font-medium transition-colors"
            >
              <span className="material-symbols-outlined text-sm">edit</span>
              Ajustar nota
            </button>
            <button
              onClick={handleApproveAnswer}
              disabled={approveAnswerMutation.isPending || currentAnswer.status === 'FINALIZED'}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="material-symbols-outlined text-sm">
                {currentAnswer.status === 'FINALIZED' ? 'check_circle' : 'task_alt'}
              </span>
              {approveAnswerMutation.isPending
                ? 'Aprovando...'
                : currentAnswer.status === 'FINALIZED'
                ? 'Aprovada'
                : 'Aprovar Resposta'}
            </button>
          </div>
        </div>
      </div>

      {/* Tabs de Questões */}
      <div className="px-8 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
        <div className="flex gap-6 overflow-x-auto">
          {reviewData.questions.map((q, idx) => (
            <button
              key={q.question_uuid}
              onClick={() => setActiveQuestionIndex(idx)}
              className={`py-3 px-2 border-b-2 text-sm font-medium whitespace-nowrap transition-colors ${
                activeQuestionIndex === idx
                  ? 'border-primary text-primary'
                  : 'border-transparent text-slate-500 hover:text-primary'
              }`}
            >
              Questão {q.question_number}
            </button>
          ))}
        </div>
      </div>

      {/* Navegação entre alunos */}
      {currentQuestion.student_answers.length > 1 && (
        <div className="px-8 py-2 bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <button
            onClick={() => setActiveStudentIndex(Math.max(0, activeStudentIndex - 1))}
            disabled={activeStudentIndex === 0}
            className="flex items-center gap-1 px-3 py-1 text-sm font-medium text-slate-600 hover:text-slate-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="material-symbols-outlined text-sm">chevron_left</span>
            Anterior
          </button>
          <span className="text-sm text-slate-600">
            Aluno {activeStudentIndex + 1} de {currentQuestion.student_answers.length}
          </span>
          <button
            onClick={() =>
              setActiveStudentIndex(Math.min(currentQuestion.student_answers.length - 1, activeStudentIndex + 1))
            }
            disabled={activeStudentIndex === currentQuestion.student_answers.length - 1}
            className="flex items-center gap-1 px-3 py-1 text-sm font-medium text-slate-600 hover:text-slate-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Próximo
            <span className="material-symbols-outlined text-sm">chevron_right</span>
          </button>
        </div>
      )}

      {/* Conteúdo Principal */}
      <div className="flex-1 flex overflow-hidden">
        {/* Coluna Esquerda - Resposta */}
        <section className="flex-1 bg-white dark:bg-slate-800 overflow-y-auto p-8">
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Enunciado */}
            <details className="bg-slate-50 dark:bg-slate-700/50 rounded-xl border border-slate-200 dark:border-slate-600 p-4" open>
              <summary className="flex items-center justify-between cursor-pointer list-none">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary">quiz</span>
                  <span className="font-semibold text-sm uppercase text-slate-600 dark:text-slate-400">Enunciado</span>
                </div>
                <span className="material-symbols-outlined">expand_more</span>
              </summary>
              <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-600 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                {currentQuestion.statement}
              </div>
              {currentQuestion.expected_answer && (
                <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-600">
                  <p className="text-xs font-semibold text-slate-500 uppercase mb-2">Resposta Esperada</p>
                  <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                    {currentQuestion.expected_answer}
                  </p>
                </div>
              )}
            </details>

            {/* Resposta do Aluno */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-primary">description</span>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white uppercase tracking-wide">Resposta do Aluno</h3>
              </div>
              <div className="prose dark:prose-invert max-w-none">
                <div className="text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
                  {currentAnswer.answer_text || 'Resposta não fornecida'}
                </div>
              </div>
            </div>

            {/* Feedback Consolidado */}
            {currentAnswer.feedback && (
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <span className="material-symbols-outlined text-blue-600">feedback</span>
                  <h3 className="font-semibold text-sm uppercase text-blue-600">Feedback Consolidado</h3>
                </div>
                <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{currentAnswer.feedback}</p>
              </div>
            )}
          </div>
        </section>

        {/* Coluna Direita - Análise */}
        <aside className="w-[480px] bg-slate-50 dark:bg-slate-900 flex flex-col border-l border-slate-200 dark:border-slate-700 overflow-y-auto">
          <div className="p-6 space-y-6">
            
            {/* Rubrica Dinâmica */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Rubrica Dinâmica</h4>
                <span className="text-xs font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded">
                  CORREÇÃO AUTOMÁTICA
                </span>
              </div>

              {currentAnswer.criteria_scores.map((criterion) => {
                const percentage = (criterion.raw_score / criterion.max_score) * 100;
                return (
                  <div key={criterion.criterion_uuid} className="bg-white dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-semibold text-sm text-slate-900 dark:text-white">{criterion.criterion_name}</span>
                      <span className="text-sm font-bold text-primary">
                        {criterion.raw_score.toFixed(1)}
                        <span className="text-slate-400 font-normal">/{criterion.max_score.toFixed(1)}</span>
                      </span>
                    </div>
                    <div className="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full mb-2">
                      <div className="bg-primary h-full rounded-full transition-all" style={{ width: `${percentage}%` }}></div>
                    </div>
                    <div className="flex justify-between text-xs text-slate-500">
                      <span>Peso: {criterion.weight.toFixed(1)}%</span>
                      <span>{percentage.toFixed(0)}%</span>
                    </div>
                    {criterion.feedback && (
                      <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-600">
                        <p className="text-xs text-slate-600 dark:text-slate-400">{criterion.feedback}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Nota Total */}
          <div className="p-6 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 mt-auto">
            <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4 border border-slate-200 dark:border-slate-600 flex items-center justify-between">
              <div>
                <h5 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Nota Total</h5>
                <p className="text-xs text-slate-400">Questão {currentQuestion.question_number}</p>
              </div>
              <div className="text-right">
                <span className="text-3xl font-bold text-primary">
                  {currentAnswer.score?.toFixed(1) || calculateTotalScore().toFixed(1)}
                </span>
                <span className="text-lg text-slate-400 font-semibold">/{currentQuestion.max_score.toFixed(1)}</span>
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* Footer */}
      <div className="h-14 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-8 flex items-center justify-end gap-3">
        <button
          onClick={() => navigate(`/dashboard/exams/${examUuid}`)}
          className="text-sm font-semibold text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
        >
          Voltar
        </button>
        <button
          onClick={handleFinalizeReview}
          disabled={finalizeReviewMutation.isPending}
          className="px-6 py-1.5 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary/90 transition-all shadow-lg shadow-primary/20 disabled:opacity-50"
        >
          {finalizeReviewMutation.isPending ? 'Finalizando...' : 'Finalizar Revisão'}
        </button>
      </div>

      {/* Modal de Ajuste de Nota */}
      {showAdjustModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-900 rounded-xl p-8 max-w-md w-full mx-4 shadow-2xl border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-primary/10 rounded-full">
                <span className="material-symbols-outlined text-primary text-2xl">edit</span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">Ajustar Nota</h3>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  Nova Nota
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max={currentQuestion.max_score}
                  value={newScore}
                  onChange={(e) => setNewScore(parseFloat(e.target.value))}
                  className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary"
                />
                <p className="text-xs text-slate-500 mt-1">Nota máxima: {currentQuestion.max_score.toFixed(1)}</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  Feedback (opcional)
                </label>
                <textarea
                  rows={4}
                  value={newFeedback}
                  onChange={(e) => setNewFeedback(e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary"
                  placeholder="Adicione um comentário sobre o ajuste..."
                />
              </div>
            </div>

            <div className="flex items-center gap-3 justify-end mt-6">
              <button
                onClick={() => setShowAdjustModal(false)}
                disabled={adjustGradeMutation.isPending}
                className="px-4 py-2 text-sm font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleAdjustGrade}
                disabled={adjustGradeMutation.isPending}
                className="px-6 py-2 text-sm font-bold text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors shadow-lg shadow-primary/20 disabled:opacity-50 flex items-center gap-2"
              >
                {adjustGradeMutation.isPending ? (
                  <>
                    <span className="animate-spin material-symbols-outlined text-sm">refresh</span>
                    Salvando...
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-sm">check</span>
                    Salvar Ajuste
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
};
