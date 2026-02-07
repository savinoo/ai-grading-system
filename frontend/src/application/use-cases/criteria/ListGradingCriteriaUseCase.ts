import { ICriteriaRepository } from '../../../domain/repositories/ICriteriaRepository';
import { GradingCriteria } from '../../../domain/entities/Criteria';

export class ListGradingCriteriaUseCase {
  constructor(private criteriaRepository: ICriteriaRepository) {}

  async execute(params?: {
    active_only?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<GradingCriteria[]> {
    return await this.criteriaRepository.listGradingCriteria(params);
  }
}
