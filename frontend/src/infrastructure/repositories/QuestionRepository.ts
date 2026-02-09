import { HttpClient } from '../http/HttpClient';
import { IQuestionRepository } from '@domain/repositories/IQuestionRepository';
import {
  ExamQuestion,
  QuestionCriteriaOverride,
  StudentAnswer,
  CreateExamQuestionDTO,
  UpdateExamQuestionDTO,
  CreateQuestionCriteriaOverrideDTO,
  CreateStudentAnswerDTO,
  UpdateStudentAnswerDTO
} from '@domain/entities/Question';

export class QuestionRepository implements IQuestionRepository {
  constructor(private httpClient: HttpClient) {}

  async createQuestion(data: CreateExamQuestionDTO): Promise<ExamQuestion> {
    return this.httpClient.post<ExamQuestion>('/exam-questions', data);
  }

  async updateQuestion(questionUuid: string, data: UpdateExamQuestionDTO): Promise<ExamQuestion> {
    return this.httpClient.put<ExamQuestion>(`/exam-questions/${questionUuid}`, data);
  }

  async listQuestionsByExam(examUuid: string): Promise<ExamQuestion[]> {
    return this.httpClient.get<ExamQuestion[]>(`/exam-questions/exam/${examUuid}`);
  }

  async deleteQuestion(questionUuid: string): Promise<void> {
    return this.httpClient.delete(`/exam-questions/${questionUuid}`);
  }

  async deleteAllQuestionAnswers(questionUuid: string): Promise<void> {
    return this.httpClient.delete(`/exam-questions/${questionUuid}/answers`);
  }

  async createQuestionCriteriaOverride(data: CreateQuestionCriteriaOverrideDTO): Promise<QuestionCriteriaOverride> {
    return this.httpClient.post<QuestionCriteriaOverride>('/question-criteria-override', data);
  }

  async updateQuestionCriteriaOverride(
    overrideUuid: string,
    data: Partial<CreateQuestionCriteriaOverrideDTO>
  ): Promise<QuestionCriteriaOverride> {
    return this.httpClient.put<QuestionCriteriaOverride>(`/question-criteria-override/${overrideUuid}`, data);
  }

  async deleteQuestionCriteriaOverride(overrideUuid: string): Promise<void> {
    return this.httpClient.delete(`/question-criteria-override/${overrideUuid}`);
  }

  async listQuestionCriteriaOverrides(questionUuid: string): Promise<QuestionCriteriaOverride[]> {
    return this.httpClient.get<QuestionCriteriaOverride[]>(`/question-criteria-override/question/${questionUuid}`);
  }

  async resetQuestionCriteria(questionUuid: string): Promise<void> {
    return this.httpClient.delete(`/question-criteria-override/question/${questionUuid}/reset`);
  }

  async createStudentAnswer(data: CreateStudentAnswerDTO): Promise<StudentAnswer> {
    return this.httpClient.post<StudentAnswer>('/student-answers', data);
  }

  async updateStudentAnswer(answerUuid: string, data: UpdateStudentAnswerDTO): Promise<StudentAnswer> {
    return this.httpClient.put<StudentAnswer>(`/student-answers/${answerUuid}`, data);
  }

  async deleteStudentAnswer(answerUuid: string): Promise<void> {
    return this.httpClient.delete(`/student-answers/${answerUuid}`);
  }

  async listStudentAnswersByQuestion(questionUuid: string): Promise<StudentAnswer[]> {
    return this.httpClient.get<StudentAnswer[]>(`/student-answers/question/${questionUuid}`);
  }
}
