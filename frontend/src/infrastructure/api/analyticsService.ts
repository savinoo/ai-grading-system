/**
 * Serviço de API para análise pedagógica.
 */

import apiClient from '@infrastructure/http/apiClient';
import {
  ClassAnalyticsSummary,
  ClassAnalytics,
  StudentPerformance,
} from '@domain/types/analytics';

export const analyticsService = {
  /**
   * Retorna sumário analítico de todas as turmas do professor.
   */
  async listClassesAnalytics(): Promise<ClassAnalyticsSummary[]> {
    return apiClient.get<ClassAnalyticsSummary[]>('/analytics/classes');
  },

  /**
   * Retorna análise pedagógica completa de uma turma.
   */
  async getClassAnalytics(classUuid: string): Promise<ClassAnalytics> {
    return apiClient.get<ClassAnalytics>(`/analytics/classes/${classUuid}`);
  },

  /**
   * Retorna o perfil de desempenho individual de um aluno em uma turma.
   */
  async getStudentPerformance(
    classUuid: string,
    studentUuid: string,
  ): Promise<StudentPerformance> {
    return apiClient.get<StudentPerformance>(
      `/analytics/classes/${classUuid}/students/${studentUuid}`,
    );
  },
};
