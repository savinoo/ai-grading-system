export interface ExamQuestion {
  uuid: string;
  exam_uuid: string;
  statement: string;
  points: number;
  question_order: number;
  is_graded: boolean;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface QuestionCriteriaOverride {
  uuid: string;
  question_uuid: string;
  criteria_uuid: string;
  max_points_override: number | null;
  weight_override: number | null;
  active: boolean;
  created_at: string;
  criteria_code?: string;
  criteria_name?: string;
  criteria_description?: string;
}

export interface StudentAnswer {
  uuid: string;
  question_uuid: string;
  student_uuid: string;
  answer_text: string;
  score: number | null;
  graded_at: string | null;
  grader_notes: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
  student_name?: string;
  student_registration?: string;
}

export interface CreateExamQuestionDTO {
  exam_uuid: string;
  statement: string;
  points: number;
  question_order: number;
}

export interface UpdateExamQuestionDTO {
  statement?: string;
  points?: number;
  question_order?: number;
  active?: boolean;
}

export interface CreateQuestionCriteriaOverrideDTO {
  question_uuid: string;
  criteria_uuid: string;
  weight_override?: number;
  max_points_override?: number;
  active?: boolean;
}

export interface CreateStudentAnswerDTO {
  exam_uuid: string;
  question_uuid: string;
  student_uuid: string;
  answer_text: string;
}

export interface UpdateStudentAnswerDTO {
  answer_text?: string;
}
