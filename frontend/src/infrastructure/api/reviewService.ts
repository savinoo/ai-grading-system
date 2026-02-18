/**
 * Service para operações de revisão de provas.
 */

import apiClient from '@infrastructure/http/apiClient';
import type {
  ExamReviewResponse,
  AdjustGradeRequest,
  FinalizeReviewRequest,
  ApproveAnswerResponse,
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

  // acceptSuggestion e rejectSuggestion removidos - funcionalidade descontinuada
  // As sugestões da IA agora são tratadas apenas como referência visual,
  // sem persistência ou aceitação/rejeição formal no backend

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
   * Aprova uma resposta individual, marcando como finalizada
   * @param answerUuid UUID da resposta a ser aprovada
   * @returns Confirmação com dados da resposta aprovada
   */
  approveAnswer: async (
    answerUuid: string
  ): Promise<ApproveAnswerResponse> => {
    return apiClient.post<ApproveAnswerResponse>(
      `/reviews/approve-answer/${answerUuid}`,
      {}
    );
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

  /**
   * Aprova uma resposta individual
   * @param answerUuid UUID da resposta a ser aprovada
   * @returns Confirmação da aprovação
   */
  approveAnswer: async (answerUuid: string): Promise<{ message: string }> => {
    return apiClient.post<{ message: string }>(`/reviews/approve-answer/${answerUuid}`, {});
  },
};
