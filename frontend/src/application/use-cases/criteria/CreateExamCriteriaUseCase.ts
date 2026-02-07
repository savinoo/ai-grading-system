import { ICriteriaRepository } from '../../../domain/repositories/ICriteriaRepository';
import { CreateExamCriteriaDTO, ExamCriteria } from '../../../domain/entities/Criteria';

export class CreateExamCriteriaUseCase {
  constructor(private criteriaRepository: ICriteriaRepository) {}

  async execute(data: CreateExamCriteriaDTO): Promise<ExamCriteria> {
    return await this.criteriaRepository.createExamCriteria(data);
  }
}
