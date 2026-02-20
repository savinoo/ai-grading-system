import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';
import { DashboardHeader } from '@presentation/components/dashboard/DashboardHeader';
import { StatCard } from '@presentation/components/dashboard/StatCard';
import dashboardService from '@infrastructure/api/dashboardService';
import { useAuth } from '@presentation/hooks/useAuth';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Buscar dados reais do dashboard
  const { data: dashboardData, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats', user?.uuid],
    queryFn: () => dashboardService.getDashboardStats(user!.uuid, 10),
    enabled: !!user?.uuid,
    refetchInterval: 60000, // Atualiza a cada 1 minuto
  });

  // Preparar cards de estatísticas
  const stats = dashboardData ? [
    { 
      title: 'Provas em Rascunho', 
      value: String(dashboardData.exam_stats.draft).padStart(2, '0'), 
      icon: 'edit_document', 
      iconColor: 'text-slate-500' 
    },
    { 
      title: 'Provas Ativas', 
      value: String(dashboardData.exam_stats.active).padStart(2, '0'), 
      icon: 'play_circle', 
      iconColor: 'text-primary' 
    },
    { 
      title: 'Respostas Corrigidas', 
      value: String(dashboardData.answer_stats.graded), 
      icon: 'data_check', 
      iconColor: 'text-green-600' 
    },
    { 
      title: 'Pendentes de Revisão', 
      value: String(dashboardData.answer_stats.pending_review), 
      icon: 'rate_review', 
      iconColor: 'text-orange-600',
      borderAccent: dashboardData.answer_stats.pending_review > 0 ? 'border-l-orange-600' : undefined
    },
  ] : [];

  // Configuração de status com cores
  const statusConfig: Record<string, { label: string; className: string }> = {
    'DRAFT': { label: 'Rascunho', className: 'bg-slate-100 text-slate-700 border-slate-200' },
    'PUBLISHED': { label: 'Publicada', className: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
    'GRADING': { label: 'Corrigindo', className: 'bg-amber-100 text-amber-700 border-amber-200' },
    'GRADED': { label: 'Corrigida', className: 'bg-blue-100 text-blue-700 border-blue-200' },
    'FINALIZED': { label: 'Finalizada', className: 'bg-purple-100 text-purple-700 border-purple-200' }
  };

  const getStatusInfo = (status: string) => {
    return statusConfig[status] || { label: status, className: 'bg-slate-100 text-slate-700 border-slate-200' };
  };

  const recentActivities = dashboardData?.recent_exams.map(exam => {
    const statusInfo = getStatusInfo(exam.status);
    return {
      id: exam.uuid,
      name: exam.title,
      code: exam.class_name || 'Sem turma',
      status: statusInfo.label,
      statusClassName: statusInfo.className,
      progress: exam.total_students > 0 
        ? { 
            current: exam.answers_submitted, 
            total: exam.total_students * exam.total_questions, 
            percentage: Math.round((exam.answers_submitted / (exam.total_students * exam.total_questions)) * 100) 
          }
        : null,
      reviewPending: exam.pending_review,
      examUuid: exam.uuid,
    };
  }) || [];

  const actionItems = dashboardData?.pending_actions.map(action => ({
    id: action.exam_uuid,
    title: action.description,
    subtitle: action.created_at ? `Há ${new Date(Date.now() - new Date(action.created_at).getTime()).getMinutes()} min` : 'Recente',
    icon: action.type === 'draft' ? 'pending_actions' : action.type === 'review' ? 'rate_review' : 'upload',
    iconColor: action.priority === 'high' ? 'text-orange-600' : 'text-primary',
    examUuid: action.exam_uuid,
  })) || [];

  const headerActions = (
    <>
      <button 
        onClick={() => navigate('/dashboard/exams/create')}
        className="flex items-center gap-2 bg-primary hover:bg-opacity-90 text-white px-4 py-2 rounded-lg text-sm font-bold transition-all shadow-sm"
      >
        <span className="material-symbols-outlined text-lg">add</span>
        <span>Nova Prova</span>
      </button>
    </>
  );

  return (
    <DashboardLayout>
      <DashboardHeader 
        title="Dashboard do Instrutor" 
        actions={headerActions}
      />
      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-slate-600 dark:text-slate-400">Carregando estatísticas...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <span className="material-symbols-outlined text-6xl text-red-500 mb-4">error</span>
            <p className="text-slate-900 dark:text-white font-semibold mb-2">Erro ao carregar dashboard</p>
            <p className="text-slate-600 dark:text-slate-400">
              {error instanceof Error ? error.message : 'Ocorreu um erro desconhecido'}
            </p>
          </div>
        </div>
      )}

      {/* Main Content */}
      {dashboardData && !isLoading && (
        <div className="p-8 max-w-7xl mx-auto space-y-8">
        {/* Stats Cards */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <StatCard
              key={index}
              title={stat.title}
              value={stat.value}
              icon={stat.icon}
              iconColor={stat.iconColor}
              borderAccent={stat.borderAccent}
            />
          ))}
        </section>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Activities Table */}
          <section className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between px-2">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                Atividades Recentes
              </h3>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-slate-800/30 border-b border-slate-200 dark:border-slate-800">
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">
                        Nome da Prova
                      </th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">
                        Status
                      </th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">
                        Progresso de Inserção
                      </th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">
                        Status de Revisão
                      </th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 text-right">
                        Ações
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                    {recentActivities.map((activity) => (
                      <tr
                        key={activity.id}
                        className="group hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                      >
                        <td className="px-6 py-5">
                          <div className="flex flex-col">
                            <span className="font-bold text-slate-900 dark:text-white text-sm">
                              {activity.name}
                            </span>
                            <span className="text-xs text-slate-500">{activity.code}</span>
                          </div>
                        </td>
                        <td className="px-6 py-5">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${activity.statusClassName}`}
                          >
                            {activity.status}
                          </span>
                        </td>
                        <td className="px-6 py-5">
                          {activity.progress ? (
                            <div className="flex flex-col gap-1">
                              <span className="text-xs font-semibold text-slate-900 dark:text-white">
                                {activity.progress.current} / {activity.progress.total} inseridas
                              </span>
                              <div className="w-24 h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                                <div
                                  className="bg-primary h-full"
                                  style={{ width: `${activity.progress.percentage}%` }}
                                ></div>
                              </div>
                            </div>
                          ) : (
                            <span className="text-xs text-slate-500">Não iniciado</span>
                          )}
                        </td>
                        <td className="px-6 py-5">
                          {activity.reviewPending > 0 ? (
                            <span className="text-xs font-bold text-orange-600">
                              {activity.reviewPending} para revisar
                            </span>
                          ) : (
                            <span className="text-xs text-slate-500">—</span>
                          )}
                        </td>
                        <td className="px-6 py-5 text-right">
                          <button 
                            onClick={() => {
                              const exam = dashboardData.recent_exams.find(e => e.uuid === activity.id);
                              if (!exam) return;
                              
                              if (activity.reviewPending > 0) {
                                navigate(`/dashboard/exams/${activity.id}/review`);
                              } else if (activity.status === 'Rascunho') {
                                navigate(`/dashboard/exams/${activity.id}/edit`);
                              } else {
                                navigate(`/dashboard/exams/${activity.id}`);
                              }
                            }}
                            className="text-primary dark:text-primary-light hover:underline text-xs font-bold"
                          >
                            {activity.reviewPending > 0 
                              ? 'Revisar' 
                              : activity.status === 'Rascunho' 
                                ? 'Retomar' 
                                : 'Gerenciar'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          {/* Action Center Sidebar */}
          <aside className="space-y-4">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white px-2">
              Central de Ações
            </h3>

            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm flex flex-col gap-4">
              {actionItems.length > 0 ? (
                <>
                  {actionItems.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => {
                        const action = dashboardData.pending_actions.find(a => a.exam_uuid === item.id);
                        if (!action) return;
                        
                        if (action.type === 'review') {
                          navigate(`/dashboard/exams/${action.exam_uuid}/review`);
                        } else if (action.type === 'draft') {
                          navigate(`/dashboard/exams/${action.exam_uuid}/edit`);
                        } else {
                          navigate(`/dashboard/exams/${action.exam_uuid}`);
                        }
                      }}
                      className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-primary transition-colors cursor-pointer group"
                    >
                      <span className={`material-symbols-outlined ${item.iconColor}`}>
                        {item.icon}
                      </span>
                      <div className="flex flex-col flex-1">
                        <span className="text-sm font-bold text-slate-900 dark:text-white">
                          {item.title}
                        </span>
                        <span className="text-xs text-slate-500">{item.subtitle}</span>
                      </div>
                      <span className="material-symbols-outlined text-xs self-center opacity-0 group-hover:opacity-100 transition-opacity">
                        chevron_right
                      </span>
                    </div>
                  ))}

                  <button 
                    onClick={() => navigate('/dashboard/exams')}
                    className="mt-2 w-full text-center py-2 text-xs font-bold text-primary dark:text-primary-light bg-slate-100 dark:bg-slate-700 rounded-lg hover:bg-primary hover:text-white transition-all"
                  >
                    Ver Todas as Tarefas
                  </button>
                </>
              ) : (
                <div className="text-center py-6 text-slate-500 text-sm">
                  <span className="material-symbols-outlined text-4xl mb-2 opacity-50">task_alt</span>
                  <p>Nenhuma ação pendente</p>
                </div>
              )}
            </div>
          </aside>
        </div>
      </div>
      )}
    </DashboardLayout>
  );
};

