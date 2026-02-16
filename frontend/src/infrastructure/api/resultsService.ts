/**
 * Serviço de API para resultados de correção.
 */

import apiClient from '@infrastructure/http/apiClient';
import { ExamResults, GradingDetails, ExamResultsSummary } from '@domain/types/results';

export const resultsService = {
  /**
   * Busca lista de todas as provas com resultados disponíveis.
   */
  async getExamsList(): Promise<ExamResultsSummary[]> {
    return apiClient.get<ExamResultsSummary[]>('/results/exams');
  },
  /**
   * Busca estatísticas e resultados de uma prova corrigida.
   */
  async getExamResults(examUuid: string): Promise<ExamResults> {
    return apiClient.get<ExamResults>(`/results/exams/${examUuid}`);
  },

  /**
   * Busca detalhes completos da correção de uma resposta.
   */
  async getGradingDetails(answerUuid: string): Promise<GradingDetails> {
    return apiClient.get<GradingDetails>(
      `/results/answers/${answerUuid}/details`
    );
  },
};
