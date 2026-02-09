import { IQuestionRepository } from '@domain/repositories/IQuestionRepository';
import { ExamQuestion, UpdateExamQuestionDTO } from '@domain/entities/Question';

export class UpdateQuestionUseCase {
  constructor(private questionRepository: IQuestionRepository) {}

  async execute(questionUuid: string, data: UpdateExamQuestionDTO): Promise<ExamQuestion> {
    return await this.questionRepository.updateQuestion(questionUuid, data);
  }
}
