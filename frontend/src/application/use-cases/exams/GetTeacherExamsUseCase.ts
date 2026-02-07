import { IExamRepository } from '../../../domain/repositories/IExamRepository';
import { ExamListResponse } from '../../../domain/entities/Exam';

export class GetTeacherExamsUseCase {
  constructor(private examRepository: IExamRepository) {}

  async execute(
    teacherUuid: string,
    params?: {
      active_only?: boolean;
      skip?: number;
      limit?: number;
    }
  ): Promise<ExamListResponse> {
    return await this.examRepository.getTeacherExams(teacherUuid, params);
  }
}
