import { ICriteriaRepository } from '../../../domain/repositories/ICriteriaRepository';
import { ExamCriteria } from '../../../domain/entities/Criteria';

export class ListExamCriteriaUseCase {
  constructor(private criteriaRepository: ICriteriaRepository) {}

  async execute(
    examUuid: string,
    params?: {
      active_only?: boolean;
      skip?: number;
      limit?: number;
    }
  ): Promise<ExamCriteria[]> {
    return await this.criteriaRepository.listExamCriteria(examUuid, params);
  }
}
