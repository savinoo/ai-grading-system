/**
 * Tipos para revisão de provas corrigidas.
 */

// ========== Tipos de Critérios e Scores ==========

export interface CriterionScore {
  criterion_uuid: string;
  criterion_name: string;
  criterion_description?: string;
  max_score: number;
  weight: number;
  raw_score: number;
  weighted_score?: number;
  feedback?: string;
}

// ========== Sugestões da IA ==========

export type SuggestionType = 'feedback' | 'score_adjustment';

export interface AISuggestion {
  suggestion_id: string;
  type: SuggestionType;
  content: string;
  confidence: number;
  reasoning?: string;
  accepted: boolean;
}

// ========== Resposta do Aluno ==========

export interface StudentAnswerReview {
  answer_uuid: string;
  student_uuid: string;
  student_name: string;
  student_email?: string;
  answer_text: string;
  score?: number;
  status: 'SUBMITTED' | 'GRADED' | 'INVALID';
  feedback?: string;
  criteria_scores: CriterionScore[];
  ai_suggestions: AISuggestion[];
  graded_at?: string;
}

// ========== Questão com Respostas ==========

export interface QuestionReview {
  question_uuid: string;
  question_number: number;
  statement: string;
  expected_answer?: string;
  max_score: number;
  student_answers: StudentAnswerReview[];
}

// ========== Resposta Completa de Revisão ==========

export interface ExamReview {
  exam_uuid: string;
  exam_title: string;
  exam_description?: string;
  class_name?: string;
  status: 'DRAFT' | 'PUBLISHED' | 'GRADED' | 'WARNING' | 'ARCHIVED' | 'FINISHED';
  total_students: number;
  total_questions: number;
  graded_at?: string;
  questions: QuestionReview[];
  grading_criteria: CriterionScore[];
}

// ========== Request Types ==========

export interface AcceptSuggestionRequest {
  answer_uuid: string;
  suggestion_id: string;
}

export interface RejectSuggestionRequest {
  answer_uuid: string;
  suggestion_id: string;
  reason?: string;
}

export interface AdjustGradeRequest {
  answer_uuid: string;
  new_score: number;
  feedback?: string;
  criteria_adjustments?: Record<string, number>;
}

export interface FinalizeReviewRequest {
  exam_uuid: string;
  send_notifications?: boolean;
  generate_pdf?: boolean;
}

// ========== Response Types para Actions ==========

export interface SuggestionActionResponse {
  message: string;
  suggestion_id: string;
  answer_uuid: string;
}

export interface AdjustGradeResponse {
  message: string;
  answer_uuid: string;
  new_score: number;
}

export interface FinalizeReviewResponse {
  message: string;
  exam_uuid: string;
  pdf_url?: string;
  notifications_sent: boolean;
}

// ========== Response Types API ==========

export interface ExamReviewResponse {
  exam_uuid: string;
  exam_title: string;
  exam_description?: string;
  class_name?: string;
  status: string;
  total_students: number;
  total_questions: number;
  graded_at?: string;
  questions: QuestionReview[];
  grading_criteria: CriterionScore[];
}
