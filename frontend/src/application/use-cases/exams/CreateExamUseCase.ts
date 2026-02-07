import { IExamRepository } from '../../../domain/repositories/IExamRepository';
import { CreateExamDTO, Exam } from '../../../domain/entities/Exam';

export class CreateExamUseCase {
  constructor(private examRepository: IExamRepository) {}

  async execute(data: CreateExamDTO): Promise<Exam> {
    return await this.examRepository.createExam(data);
  }
}
