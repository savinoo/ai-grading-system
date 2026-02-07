import {
  Exam,
  CreateExamDTO,
  UpdateExamDTO,
  ExamListResponse,
} from '../entities/Exam';

export interface IExamRepository {
  createExam(data: CreateExamDTO): Promise<Exam>;

  getTeacherExams(
    teacherUuid: string,
    params?: {
      active_only?: boolean;
      skip?: number;
      limit?: number;
    }
  ): Promise<ExamListResponse>;

  getExamByUuid(examUuid: string): Promise<Exam>;

  updateExam(examUuid: string, data: UpdateExamDTO): Promise<Exam>;
}
