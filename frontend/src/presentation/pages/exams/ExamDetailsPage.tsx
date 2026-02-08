import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@presentation/components/ui/Button';
import { CriteriaList } from '@presentation/components/criteria/CriteriaList';
import { AttachmentList } from '@presentation/components/attachments/AttachmentList';
import { useExams } from '@presentation/hooks/useExams';
import { useAttachments } from '@presentation/hooks/useAttachments';
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

  useEffect(() => {
    if (examUuid) {
      loadExamDetails(examUuid);
      loadExamCriteria(examUuid);
      loadAttachments(examUuid);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [examUuid]);

  const isDraft = currentExam?.status === 'DRAFT';

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

  const statusConfig = {
    DRAFT: { label: 'Rascunho', className: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' },
    PUBLISHED: { label: 'Publicada', className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
    ARCHIVED: { label: 'Arquivada', className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
    FINISHED: { label: 'Finalizada', className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  };

  const status = statusConfig[currentExam.status];
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
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
                  0
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
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-8 shadow-sm">
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
      </div>
    </DashboardLayout>
  );
};
