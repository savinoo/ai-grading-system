import { HttpClient } from '../http/HttpClient';
import { ICriteriaRepository } from '../../domain/repositories/ICriteriaRepository';
import {
  GradingCriteria,
  ExamCriteria,
  CreateExamCriteriaDTO,
  UpdateExamCriteriaDTO,
} from '../../domain/entities/Criteria';

export class CriteriaRepository implements ICriteriaRepository {
  constructor(private httpClient: HttpClient) {}

  async listGradingCriteria(params?: {
    active_only?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<GradingCriteria[]> {
    const queryParams = new URLSearchParams();
    
    if (params?.active_only !== undefined) {
      queryParams.append('active_only', String(params.active_only));
    }
    if (params?.skip !== undefined) {
      queryParams.append('skip', String(params.skip));
    }
    if (params?.limit !== undefined) {
      queryParams.append('limit', String(params.limit));
    }

    const url = `/grading-criteria${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await this.httpClient.get<GradingCriteria[]>(url);
    return response;
  }

  async createExamCriteria(data: CreateExamCriteriaDTO): Promise<ExamCriteria> {
    const response = await this.httpClient.post<ExamCriteria>('/exam-criteria', data);
    return response;
  }

  async listExamCriteria(
    examUuid: string,
    params?: {
      active_only?: boolean;
      skip?: number;
      limit?: number;
    }
  ): Promise<ExamCriteria[]> {
    const queryParams = new URLSearchParams();
    
    if (params?.active_only !== undefined) {
      queryParams.append('active_only', String(params.active_only));
    }
    if (params?.skip !== undefined) {
      queryParams.append('skip', String(params.skip));
    }
    if (params?.limit !== undefined) {
      queryParams.append('limit', String(params.limit));
    }

    const url = `/exam-criteria/exam/${examUuid}${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await this.httpClient.get<ExamCriteria[]>(url);
    return response;
  }

  async updateExamCriteria(
    examCriteriaUuid: string,
    data: UpdateExamCriteriaDTO
  ): Promise<ExamCriteria> {
    const response = await this.httpClient.patch<ExamCriteria>(
      `/exam-criteria/${examCriteriaUuid}`,
      data
    );
    return response;
  }

  async deleteExamCriteria(examCriteriaUuid: string): Promise<void> {
    await this.httpClient.delete(`/exam-criteria/${examCriteriaUuid}`);
  }
}
