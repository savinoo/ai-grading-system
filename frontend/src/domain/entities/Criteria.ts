export interface GradingCriteria {
  uuid: string;
  code: string;
  name: string;
  description: string | null;
  active: boolean;
  created_at: string;
}

export interface ExamCriteria {
  uuid: string;
  exam_uuid: string;
  criteria_uuid: string;
  weight: number;
  max_points: number | null;
  active: boolean;
  created_at: string;
  // Campos opcionais que podem vir do backend quando se faz JOIN
  grading_criteria_uuid?: string;
  grading_criteria_name?: string;
  grading_criteria_description?: string;
}

export interface ExamCriteriaWithDetails extends ExamCriteria {
  criteria?: GradingCriteria;
}

export interface CreateExamCriteriaDTO {
  exam_uuid: string;
  criteria_uuid: string;
  weight: number;
  max_points?: number | null;
}

export interface UpdateExamCriteriaDTO {
  weight?: number;
  max_points?: number | null;
}
