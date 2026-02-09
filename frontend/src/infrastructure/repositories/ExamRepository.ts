import { HttpClient } from '../http/HttpClient';
import { IExamRepository } from '../../domain/repositories/IExamRepository';
import {
  Exam,
  CreateExamDTO,
  UpdateExamDTO,
  ExamListResponse,
} from '../../domain/entities/Exam';

export class ExamRepository implements IExamRepository {
  constructor(private httpClient: HttpClient) {}

  async createExam(data: CreateExamDTO): Promise<Exam> {
    const response = await this.httpClient.post<Exam>('/exams', data);
    return response;
  }

  async getTeacherExams(
    teacherUuid: string,
    params?: {
      active_only?: boolean;
      skip?: number;
      limit?: number;
    }
  ): Promise<ExamListResponse> {
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

    const url = `/exams/teacher/${teacherUuid}${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await this.httpClient.get<ExamListResponse>(url);
    return response;
  }

  async getExamByUuid(examUuid: string): Promise<Exam> {
    const response = await this.httpClient.get<Exam>(`/exams/${examUuid}`);
    return response;
  }

  async updateExam(examUuid: string, data: UpdateExamDTO): Promise<Exam> {
    const response = await this.httpClient.patch<Exam>(`/exams/${examUuid}`, data);
    return response;
  }

  async deleteExam(examUuid: string): Promise<void> {
    await this.httpClient.delete(`/exams/${examUuid}`);
  }
}
