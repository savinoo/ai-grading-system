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

export interface IQuestionRepository {
  // Exam Questions
  createQuestion(data: CreateExamQuestionDTO): Promise<ExamQuestion>;
  updateQuestion(questionUuid: string, data: UpdateExamQuestionDTO): Promise<ExamQuestion>;
  listQuestionsByExam(examUuid: string): Promise<ExamQuestion[]>;
  deleteQuestion(questionUuid: string): Promise<void>;
  deleteAllQuestionAnswers(questionUuid: string): Promise<void>;

  // Question Criteria Override
  createQuestionCriteriaOverride(data: CreateQuestionCriteriaOverrideDTO): Promise<QuestionCriteriaOverride>;
  updateQuestionCriteriaOverride(overrideUuid: string, data: Partial<CreateQuestionCriteriaOverrideDTO>): Promise<QuestionCriteriaOverride>;
  deleteQuestionCriteriaOverride(overrideUuid: string): Promise<void>;
  listQuestionCriteriaOverrides(questionUuid: string): Promise<QuestionCriteriaOverride[]>;
  resetQuestionCriteria(questionUuid: string): Promise<void>;

  // Student Answers
  createStudentAnswer(data: CreateStudentAnswerDTO): Promise<StudentAnswer>;
  updateStudentAnswer(answerUuid: string, data: UpdateStudentAnswerDTO): Promise<StudentAnswer>;
  deleteStudentAnswer(answerUuid: string): Promise<void>;
  listStudentAnswersByQuestion(questionUuid: string): Promise<StudentAnswer[]>;
}
