import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';
import { DashboardHeader } from '@presentation/components/dashboard/DashboardHeader';
import { resultsService } from '@infrastructure/api/resultsService';
import type { GradingDetails, AgentCorrectionDetail, CriterionScoreSimple, CriterionScoreDetail, RAGContextItem } from '@domain/types/results';

type TabType = 'summary' | 'agents' | 'rag';

export const GradingDetailsPage: React.FC = () => {
  const { answerId } = useParams<{ answerId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabType>('summary');
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());

  const { data: details, isLoading, error } = useQuery<GradingDetails>({
    queryKey: ['gradingDetails', answerId],
    queryFn: () => resultsService.getGradingDetails(answerId!),
    enabled: !!answerId,
  });

  const toggleAgentExpansion = (agentId: string) => {
    setExpandedAgents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(agentId)) {
        newSet.delete(agentId);
      } else {
        newSet.add(agentId);
      }
      return newSet;
    });
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <DashboardHeader title="Detalhes da Correção" />
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-slate-600 dark:text-slate-400">Carregando detalhes...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !details) {
    return (
      <DashboardLayout>
        <DashboardHeader title="Detalhes da Correção" />
        <div className="p-8">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
            <span className="material-symbols-outlined text-5xl text-red-600 dark:text-red-400 mb-4">
              error
            </span>
            <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">
              Erro ao carregar detalhes
            </h3>
            <p className="text-red-700 dark:text-red-300">
              {error instanceof Error ? error.message : 'Erro desconhecido'}
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const renderAgentCard = (correction: AgentCorrectionDetail) => {
    const isExpanded = expandedAgents.has(correction.agent_id);
    const isArbiter = correction.agent_id === 'corretor_3_arbiter';

    return (
      <div
        key={correction.agent_id}
        className={`border rounded-lg p-5 ${
          isArbiter
            ? 'border-yellow-400 dark:border-yellow-600 bg-yellow-50 dark:bg-yellow-900/20'
            : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800'
        }`}
      >
        <div className="flex items-center justify-between mb-3">
          <div>
            <h4 className="font-semibold text-slate-900 dark:text-white">
              {correction.agent_name}
              {isArbiter && (
                <span className="ml-2 text-xs bg-yellow-200 dark:bg-yellow-700 text-yellow-800 dark:text-yellow-200 px-2 py-1 rounded">
                  Árbitro
                </span>
              )}
            </h4>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Nota: <span className="font-bold">{correction.total_score.toFixed(1)}</span> / 10.0
            </p>
          </div>
          {correction.confidence_level !== undefined && (
            <div className="text-right">
              <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">Confiança</p>
              <div className="flex items-center gap-1">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-2 h-2 rounded-full ${
                      i < Math.round(correction.confidence_level! * 5)
                        ? 'bg-indigo-600 dark:bg-indigo-400'
                        : 'bg-slate-300 dark:bg-slate-600'
                    }`}
                  />
                ))}
                <span className="ml-1 text-xs font-medium text-slate-700 dark:text-slate-300">
                  {(correction.confidence_level * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Raciocínio (CoT) */}
        <div className="mb-3">
          <div className="flex items-center justify-between mb-2">
            <h5 className="text-sm font-medium text-slate-700 dark:text-slate-300 flex items-center gap-2">
              <span className="material-symbols-outlined text-base">psychology</span>
              Raciocínio (Chain-of-Thought)
            </h5>
            <button
              onClick={() => toggleAgentExpansion(correction.agent_id)}
              className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
            >
              {isExpanded ? 'Recolher' : 'Expandir'}
              <span className="material-symbols-outlined text-sm">
                {isExpanded ? 'expand_less' : 'expand_more'}
              </span>
            </button>
          </div>
          <div
            className={`text-sm text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900/50 rounded p-3 whitespace-pre-wrap ${
              isExpanded ? '' : 'line-clamp-3'
            }`}
          >
            {correction.reasoning_chain}
          </div>
        </div>

        {/* Scores por Critério */}
        {correction.criteria_scores.length > 0 && (
          <div className="space-y-2">
            <h5 className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Scores por Critério
            </h5>
            {correction.criteria_scores.map((criterion: CriterionScoreSimple, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm">
                <span className="text-slate-600 dark:text-slate-400">{criterion.criterion_name}</span>
                <span className="font-medium text-slate-900 dark:text-white">
                  {criterion.score.toFixed(1)} / {criterion.max_score}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <DashboardLayout>
      <DashboardHeader 
        title="Correção Detalhada"
        subtitle={`Aluno: ${details.student.name} | Questão: ${details.question.statement.substring(0, 50)}...`}
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Resposta do Aluno */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
            <span className="material-symbols-outlined">edit_note</span>
            Resposta do Aluno
          </h3>
          <div className="bg-slate-50 dark:bg-slate-900/50 rounded-lg p-4 text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
            {details.answer_text}
          </div>
        </div>

        {/* Resultado Final */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined">grade</span>
            Resultado Final
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg p-4">
              <div className="text-sm text-indigo-700 dark:text-indigo-300 mb-1">Nota Final</div>
              <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                {details.final_score.toFixed(1)}
                <span className="text-lg text-slate-500 dark:text-slate-400 ml-1"> / 10.0</span>
              </div>
            </div>

            <div className={`rounded-lg p-4 ${
              details.divergence_detected
                ? 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
                : 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
            }`}>
              <div className={`text-sm mb-1 ${
                details.divergence_detected
                  ? 'text-yellow-700 dark:text-yellow-300'
                  : 'text-green-700 dark:text-green-300'
              }`}>
                Status
              </div>
              <div className={`text-lg font-semibold flex items-center gap-2 ${
                details.divergence_detected
                  ? 'text-yellow-600 dark:text-yellow-400'
                  : 'text-green-600 dark:text-green-400'
              }`}>
                <span className="material-symbols-outlined">
                  {details.divergence_detected ? 'warning' : 'check_circle'}
                </span>
                {details.divergence_detected ? 'Divergência' : 'Consenso'}
              </div>
              {details.divergence_value && (
                <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                  Diferença: {details.divergence_value.toFixed(1)} pontos
                </div>
              )}
            </div>

            <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
              <div className="text-sm text-slate-600 dark:text-slate-400 mb-1">
                Corrigida em
              </div>
              <div className="text-sm font-medium text-slate-900 dark:text-white">
                {details.graded_at
                  ? new Date(details.graded_at).toLocaleString('pt-BR')
                  : 'Não disponível'}
              </div>
            </div>
          </div>

          {/* Avaliação por Critério */}
          {details.criteria_scores.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                Avaliação por Critério
              </h4>
              <div className="space-y-3">
                {details.criteria_scores.map((criterion: CriterionScoreDetail) => {
                  const percentage = (criterion.raw_score / criterion.max_score) * 100;
                  const hasBreakdown = 
                    criterion.agent_scores.corretor_1 !== undefined ||
                    criterion.agent_scores.corretor_2 !== undefined ||
                    criterion.agent_scores.arbiter !== undefined;

                  return (
                    <div key={criterion.criterion_uuid} className="bg-slate-50 dark:bg-slate-900/50 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="font-medium text-slate-900 dark:text-white mb-1">
                            {criterion.criterion_name}
                            <span className="text-sm text-slate-500 dark:text-slate-400 ml-2">
                              ({criterion.max_score} pts)
                            </span>
                          </div>
                          {hasBreakdown && (
                            <div className="text-xs text-slate-600 dark:text-slate-400 space-x-3">
                              {criterion.agent_scores.corretor_1 !== undefined && (
                                <span>C1: {criterion.agent_scores.corretor_1.toFixed(1)}</span>
                              )}
                              {criterion.agent_scores.corretor_2 !== undefined && (
                                <span>C2: {criterion.agent_scores.corretor_2.toFixed(1)}</span>
                              )}
                              {criterion.agent_scores.arbiter !== undefined && (
                                <span className="text-yellow-600 dark:text-yellow-400">
                                  Árbitro: {criterion.agent_scores.arbiter.toFixed(1)}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-slate-900 dark:text-white">
                            {criterion.raw_score.toFixed(1)}
                          </div>
                        </div>
                      </div>
                      
                      {/* Barra de progresso */}
                      <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            percentage >= 80 ? 'bg-green-600' :
                            percentage >= 60 ? 'bg-yellow-600' :
                            'bg-red-600'
                          }`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>

                      {criterion.feedback && (
                        <div className="mt-2 text-xs text-slate-600 dark:text-slate-400 italic">
                          "{criterion.feedback}"
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Feedback ao Aluno */}
          {details.final_feedback && (
            <div className="mt-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2 flex items-center gap-2">
                <span className="material-symbols-outlined text-base">comment</span>
                Feedback ao Aluno
              </h4>
              <p className="text-sm text-blue-800 dark:text-blue-200 whitespace-pre-wrap">
                {details.final_feedback}
              </p>
            </div>
          )}
        </div>

        {/* Tabs de Navegação */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div className="border-b border-slate-200 dark:border-slate-700">
            <div className="flex">
              <button
                onClick={() => setActiveTab('summary')}
                className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'summary'
                    ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                📊 Resumo
              </button>
              <button
                onClick={() => setActiveTab('agents')}
                className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'agents'
                    ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                🤖 Corretores ({details.corrections.length})
              </button>
              <button
                onClick={() => setActiveTab('rag')}
                className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'rag'
                    ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                📚 Contexto RAG ({details.rag_context.length})
              </button>
            </div>
          </div>

          <div className="p-6">
            {/* Tab: Resumo */}
            {activeTab === 'summary' && (
              <div className="space-y-4">
                <p className="text-slate-600 dark:text-slate-400">
                  Visualização resumida já exibida acima. Use as outras abas para ver detalhes dos agentes e contexto RAG.
                </p>
              </div>
            )}

            {/* Tab: Corretores */}
            {activeTab === 'agents' && (
              <div className="space-y-4">
                {details.corrections.length === 0 ? (
                  <p className="text-slate-600 dark:text-slate-400 text-center py-8">
                    Nenhum detalhe de corretor disponível.
                  </p>
                ) : (
                  details.corrections.map(renderAgentCard)
                )}
              </div>
            )}

            {/* Tab: Contexto RAG */}
            {activeTab === 'rag' && (
              <div className="space-y-4">
                {details.rag_context.length === 0 ? (
                  <p className="text-slate-600 dark:text-slate-400 text-center py-8">
                    Nenhum contexto RAG disponível.
                  </p>
                ) : (
                  details.rag_context.map((item: RAGContextItem, idx) => (
                    <div
                      key={idx}
                      className="border border-slate-300 dark:border-slate-600 rounded-lg p-4 bg-white dark:bg-slate-800"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="material-symbols-outlined text-slate-600 dark:text-slate-400">
                            description
                          </span>
                          <span className="text-sm font-medium text-slate-900 dark:text-white">
                            Trecho {idx + 1}/{details.rag_context.length}
                          </span>
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">
                          Relevância: {(item.relevance_score * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div className="text-xs text-slate-600 dark:text-slate-400 mb-2">
                        Fonte: {item.source}
                        {item.page && ` (p. ${item.page})`}
                      </div>
                      <div className="text-sm text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-900/50 rounded p-3 whitespace-pre-wrap">
                        {item.content}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        {/* Botões de Ação */}
        <div className="flex gap-3">
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-sm">arrow_back</span>
            Voltar
          </button>
          <button
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-sm">download</span>
            Exportar PDF
          </button>
          <button
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-sm">send</span>
            Enviar ao Aluno
          </button>
        </div>
      </div>
    </DashboardLayout>
  );
};
