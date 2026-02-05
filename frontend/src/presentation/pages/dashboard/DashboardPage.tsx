import React from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';
import { DashboardHeader } from '@presentation/components/dashboard/DashboardHeader';
import { StatCard } from '@presentation/components/dashboard/StatCard';
import { Button } from '@presentation/components/ui/Button';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();

  // Mock data - será substituído por dados reais da API
  const stats = [
    { title: 'Provas em Rascunho', value: '04', icon: 'edit_document', iconColor: 'text-slate-500' },
    { title: 'Provas Ativas', value: '08', icon: 'play_circle', iconColor: 'text-primary' },
    { title: 'Respostas Inseridas', value: '412', icon: 'data_check', iconColor: 'text-slate-500' },
    { 
      title: 'Pendentes de Revisão', 
      value: '26', 
      icon: 'rate_review', 
      iconColor: 'text-orange-600',
      borderAccent: 'border-l-orange-600'
    },
  ];

  const recentActivities = [
    {
      id: 1,
      name: 'Redação Intermediária Ética',
      code: 'FIL-201 • Semestre Atual',
      status: 'Ativa',
      progress: { current: 105, total: 120, percentage: 87 },
      reviewPending: 15,
    },
    {
      id: 2,
      name: 'Quiz de História 101',
      code: 'HIS-101 • Graduação',
      status: 'Rascunho',
      progress: null,
      reviewPending: 0,
    },
    {
      id: 3,
      name: 'Final de Biologia 202',
      code: 'BIO-202 • Primavera 2024',
      status: 'Ativa',
      progress: { current: 45, total: 50, percentage: 90 },
      reviewPending: 5,
    },
  ];

  const actionItems = [
    {
      id: 1,
      title: 'Finalizar Rascunho: História 101',
      subtitle: 'Editado há 2 horas',
      icon: 'pending_actions',
      iconColor: 'text-orange-600',
    },
    {
      id: 2,
      title: 'Revisar 5 respostas de Bio 202',
      subtitle: 'Requer aprovação final da nota',
      icon: 'rate_review',
      iconColor: 'text-primary',
    },
    {
      id: 3,
      title: 'Importar Digitalizações (OMR)',
      subtitle: '12 arquivos aguardando na fila',
      icon: 'upload',
      iconColor: 'text-slate-500',
    },
  ];

  const headerActions = (
    <>
      <button className="flex items-center gap-2 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-900 dark:text-white px-4 py-2 rounded-lg text-sm font-bold transition-all">
        <span className="material-symbols-outlined text-lg">upload_file</span>
        <span>Importar CSV</span>
      </button>
      <button className="flex items-center gap-2 border border-primary text-primary hover:bg-primary/5 px-4 py-2 rounded-lg text-sm font-bold transition-all">
        <span className="material-symbols-outlined text-lg">edit_note</span>
        <span>Inserir Respostas</span>
      </button>
      <button className="flex items-center gap-2 bg-primary hover:bg-opacity-90 text-white px-4 py-2 rounded-lg text-sm font-bold transition-all shadow-sm">
        <span className="material-symbols-outlined text-lg">add</span>
        <span>+ Criar Nova Prova</span>
      </button>
    </>
  );

  return (
    <DashboardLayout>
      <DashboardHeader 
        title="Dashboard do Instrutor" 
        actions={headerActions}
      />

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
                <span className="bg-slate-100 dark:bg-slate-800 text-slate-500 text-[10px] px-2 py-0.5 rounded-full">
                  Progresso de Inserção Manual
                </span>
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
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              activity.status === 'Ativa'
                                ? 'bg-primary/10 text-primary border border-primary/20'
                                : 'bg-yellow-100 text-orange-600 border border-yellow-200'
                            }`}
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
                          <button className="text-primary hover:underline text-xs font-bold">
                            {activity.status === 'Rascunho' ? 'Retomar' : 'Gerenciar'}
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
              {actionItems.map((item) => (
                <div
                  key={item.id}
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

              <button className="mt-2 w-full text-center py-2 text-xs font-bold text-primary bg-slate-100 dark:bg-slate-700 rounded-lg hover:bg-primary hover:text-white transition-all">
                Ver Todas as Tarefas
              </button>
            </div>

            {/* Tip Card */}
            <div className="bg-gradient-to-br from-primary to-[#2a8b9e] p-5 rounded-xl text-white shadow-md">
              <div className="flex items-center gap-2 mb-2">
                <span className="material-symbols-outlined text-sm">info</span>
                <span className="text-xs font-bold uppercase tracking-wider">Dica Corretum</span>
              </div>
              <p className="text-xs leading-relaxed opacity-90">
                Use a ferramenta 'Inserir Respostas' para transcrição manual de redações
                manuscritas. Nossa IA sugerirá notas automaticamente conforme você digita.
              </p>
            </div>
          </aside>
        </div>
      </div>
    </DashboardLayout>
  );
};

