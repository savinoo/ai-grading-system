import { ICriteriaRepository } from '../../../domain/repositories/ICriteriaRepository';
import { UpdateExamCriteriaDTO, ExamCriteria } from '../../../domain/entities/Criteria';

export class UpdateExamCriteriaUseCase {
  constructor(private criteriaRepository: ICriteriaRepository) {}

  async execute(examCriteriaUuid: string, data: UpdateExamCriteriaDTO): Promise<ExamCriteria> {
    return await this.criteriaRepository.updateExamCriteria(examCriteriaUuid, data);
  }
}
