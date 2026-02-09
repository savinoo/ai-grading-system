import { IExamRepository } from '@domain/repositories/IExamRepository';

export class DeleteExamUseCase {
  constructor(private examRepository: IExamRepository) {}

  async execute(examUuid: string): Promise<void> {
    await this.examRepository.deleteExam(examUuid);
  }
}
