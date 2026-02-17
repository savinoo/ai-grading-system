export interface ExamStatsCount {
  draft: number;
  active: number;
  grading: number;
  graded: number;
  finalized: number;
  total: number;
}

export interface AnswerStatsCount {
  total: number;
  pending: number;
  graded: number;
  pending_review: number;
}

export interface RecentExam {
  uuid: string;
  title: string;
  class_name: string | null;
  status: string;
  starts_at: string | null;
  ends_at: string | null;
  total_questions: number;
  total_students: number;
  answers_submitted: number;
  answers_graded: number;
  pending_review: number;
  created_at: string;
}

export interface PendingAction {
  type: 'draft' | 'review' | 'grading';
  exam_uuid: string;
  exam_title: string;
  description: string;
  count: number;
  priority: 'high' | 'normal' | 'low';
  created_at: string | null;
}

export interface DashboardStats {
  exam_stats: ExamStatsCount;
  answer_stats: AnswerStatsCount;
  recent_exams: RecentExam[];
  pending_actions: PendingAction[];
}
