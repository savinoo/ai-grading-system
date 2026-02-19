/**
 * Tipos para o módulo de análise pedagógica.
 */

// ========== Primitivos ==========

export type Trend = 'improving' | 'stable' | 'declining' | 'insufficient_data';
export type GapSeverity = 'low' | 'medium' | 'high';
export type GradeLabel = 'A' | 'B' | 'C' | 'D' | 'F';

// ========== Gaps e Pontos Fortes ==========

export interface LearningGap {
  criterion_name: string;
  severity: GapSeverity;
  evidence_count: number;
  avg_score: number;
  suggestion?: string;
}

export interface Strength {
  criterion_name: string;
  avg_score: number;
  /** 0–1: quão consistente o aluno é neste critério */
  consistency: number;
}

// ========== Submissão individual ==========

export interface SubmissionSummary {
  answer_uuid: string;
  question_uuid: string;
  exam_uuid: string;
  exam_title: string;
  score: number;
  max_score: number;
  graded_at: string | null;
}

// ========== Perfil de aluno ==========

export interface StudentPerformance {
  student_uuid: string;
  student_name: string;
  student_email?: string;

  avg_score: number;
  submission_count: number;
  trend: Trend;
  trend_confidence: number;

  learning_gaps: LearningGap[];
  strengths: Strength[];
  submissions_history: SubmissionSummary[];

  first_submission: string | null;
  last_submission: string | null;
  last_updated: string;
}

// ========== Distribuição de notas ==========

export interface GradeDistribution {
  label: GradeLabel;
  range: string;
  count: number;
  percentage: number;
}

// ========== Aluno no contexto da turma ==========

export interface ClassStudentSummary {
  student_uuid: string;
  student_name: string;
  avg_score: number;
  submission_count: number;
  trend: Trend;
}

// ========== Análise da turma ==========

export interface ClassAnalytics {
  class_uuid: string;
  class_name: string;

  total_students: number;
  total_submissions: number;

  class_avg_score: number;
  median_score: number;
  std_deviation: number;

  grade_distribution: GradeDistribution[];
  struggling_students: ClassStudentSummary[];
  top_performers: ClassStudentSummary[];
  most_common_gaps: LearningGap[];
  students: ClassStudentSummary[];

  analysis_timestamp: string;
}

// ========== Sumário de turma (listagem) ==========

export interface ClassAnalyticsSummary {
  class_uuid: string;
  class_name: string;
  total_students: number;
  total_submissions: number;
  class_avg_score: number;
  struggling_count: number;
  top_performers_count: number;
  analysis_timestamp: string;
}
