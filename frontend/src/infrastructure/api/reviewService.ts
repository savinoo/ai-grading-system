/**
 * Service para operações de revisão de provas.
 */

import apiClient from '@infrastructure/http/apiClient';
import type {
  ExamReviewResponse,
  AcceptSuggestionRequest,
  RejectSuggestionRequest,
  AdjustGradeRequest,
  FinalizeReviewRequest,
  SuggestionActionResponse,
  AdjustGradeResponse,
  FinalizeReviewResponse,
} from '@domain/types/review';

/**
 * Service de revisão de provas
 */
export const reviewService = {
  /**
   * Busca dados completos para revisão de uma prova
   * @param examUuid UUID da prova
   * @returns Dados completos para revisão
   */
  getExamReview: async (examUuid: string): Promise<ExamReviewResponse> => {
    return apiClient.get<ExamReviewResponse>(`/reviews/exams/${examUuid}`);
  },

  /**
   * Aceita uma sugestão da IA
   * @param data Dados da sugestão a ser aceita
   * @returns Confirmação da ação
   */
  acceptSuggestion: async (
    data: AcceptSuggestionRequest
  ): Promise<SuggestionActionResponse> => {
    return apiClient.post<SuggestionActionResponse>(
      '/reviews/suggestions/accept',
      data
    );
  },

  /**
   * Rejeita uma sugestão da IA
   * @param data Dados da sugestão a ser rejeitada
   * @returns Confirmação da ação
   */
  rejectSuggestion: async (
    data: RejectSuggestionRequest
  ): Promise<SuggestionActionResponse> => {
    return apiClient.post<SuggestionActionResponse>(
      '/reviews/suggestions/reject',
      data
    );
  },

  /**
   * Ajusta nota manualmente
   * @param data Dados do ajuste de nota
   * @returns Confirmação com nova nota
   */
  adjustGrade: async (
    data: AdjustGradeRequest
  ): Promise<AdjustGradeResponse> => {
    return apiClient.put<AdjustGradeResponse>('/reviews/grades/adjust', data);
  },

  /**
   * Finaliza revisão e gera relatório
   * @param data Dados da finalização
   * @returns Confirmação com informações do relatório
   */
  finalizeReview: async (
    data: FinalizeReviewRequest
  ): Promise<FinalizeReviewResponse> => {
    return apiClient.post<FinalizeReviewResponse>('/reviews/finalize', data);
  },
};
