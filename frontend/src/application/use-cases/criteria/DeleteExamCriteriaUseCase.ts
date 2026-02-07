import { ICriteriaRepository } from '../../../domain/repositories/ICriteriaRepository';

export class DeleteExamCriteriaUseCase {
  constructor(private criteriaRepository: ICriteriaRepository) {}

  async execute(examCriteriaUuid: string): Promise<void> {
    return await this.criteriaRepository.deleteExamCriteria(examCriteriaUuid);
  }
}
