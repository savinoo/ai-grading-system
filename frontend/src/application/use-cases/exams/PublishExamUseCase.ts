import { IExamRepository } from '../../../domain/repositories/IExamRepository';
import { PublishExamResponse } from '../../../domain/entities/Exam';

export class PublishExamUseCase {
  constructor(private examRepository: IExamRepository) {}

  async execute(examUuid: string): Promise<PublishExamResponse> {
    return await this.examRepository.publishExam(examUuid);
  }
}
