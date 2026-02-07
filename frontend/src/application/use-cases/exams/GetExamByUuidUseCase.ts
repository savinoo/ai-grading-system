import { IExamRepository } from '../../../domain/repositories/IExamRepository';
import { Exam } from '../../../domain/entities/Exam';

export class GetExamByUuidUseCase {
  constructor(private examRepository: IExamRepository) {}

  async execute(examUuid: string): Promise<Exam> {
    return await this.examRepository.getExamByUuid(examUuid);
  }
}
