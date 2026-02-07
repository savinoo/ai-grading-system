import {
  GradingCriteria,
  ExamCriteria,
  CreateExamCriteriaDTO,
  UpdateExamCriteriaDTO,
} from '../entities/Criteria';

export interface ICriteriaRepository {
  // Critérios de Avaliação (GradingCriteria)
  listGradingCriteria(params?: {
    active_only?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<GradingCriteria[]>;

  // Critérios de Prova (ExamCriteria)
  createExamCriteria(data: CreateExamCriteriaDTO): Promise<ExamCriteria>;

  listExamCriteria(
    examUuid: string,
    params?: {
      active_only?: boolean;
      skip?: number;
      limit?: number;
    }
  ): Promise<ExamCriteria[]>;

  updateExamCriteria(
    examCriteriaUuid: string,
    data: UpdateExamCriteriaDTO
  ): Promise<ExamCriteria>;

  deleteExamCriteria(examCriteriaUuid: string): Promise<void>;
}
