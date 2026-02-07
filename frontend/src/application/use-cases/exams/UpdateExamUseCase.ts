import { IExamRepository } from '../../../domain/repositories/IExamRepository';
import { UpdateExamDTO, Exam } from '../../../domain/entities/Exam';

export class UpdateExamUseCase {
  constructor(private examRepository: IExamRepository) {}

  async execute(examUuid: string, data: UpdateExamDTO): Promise<Exam> {
    return await this.examRepository.updateExam(examUuid, data);
  }
}
