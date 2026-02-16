/**
 * Tipos para resultados de correção de provas.
 */

// ========== Lista de Provas com Resultados ==========

export interface ExamResultsSummary {
  exam_uuid: string;
  exam_title: string;
  status: 'GRADED' | 'PARTIAL' | 'PENDING';
  graded_at: string | null;
  total_students: number;
  average_score: number;
  arbiter_rate: number;
}

// ========== Estatísticas de Prova ==========

export interface ScoreDistribution {
  range: string;
  count: number;
}

export interface QuestionStatistics {
  question_uuid: string;
  question_number: number;
  question_title: string;
  average_score: number;
  std_deviation: number;
  max_score: number;
  min_score: number;
  arbiter_count: number;
}

export interface ExamStatistics {
  total_students: number;
  total_questions: number;
  arbiter_rate: number;
  average_score: number;
  std_deviation: number;
  max_score: number;
  min_score: number;
  median: number;
  distribution: ScoreDistribution[];
}

export interface ExamResults {
  exam_uuid: string;
  exam_title: string;
  status: 'GRADED' | 'PARTIAL' | 'PENDING';
  graded_at: string | null;
  statistics: ExamStatistics;
  questions_stats: QuestionStatistics[];
}

// ========== Detalhes de Correção ==========

export interface StudentInfo {
  uuid: string;
  name: string;
  email?: string;
}

export interface QuestionInfo {
  uuid: string;
  statement: string;
  max_score: number;
}

export interface AgentScoreBreakdown {
  corretor_1?: number;
  corretor_2?: number;
  arbiter?: number;
}

export interface CriterionScoreDetail {
  criterion_uuid: string;
  criterion_name: string;
  max_score: number;
  raw_score: number;
  weighted_score?: number;
  feedback?: string;
  agent_scores: AgentScoreBreakdown;
}

export interface CriterionScoreSimple {
  criterion_name: string;
  score: number;
  max_score: number;
  feedback?: string;
}

export interface AgentCorrectionDetail {
  agent_id: 'corretor_1' | 'corretor_2' | 'corretor_3_arbiter';
  agent_name: string;
  total_score: number;
  reasoning_chain: string;
  feedback_text: string;
  confidence_level?: number;
  criteria_scores: CriterionScoreSimple[];
}

export interface RAGContextItem {
  content: string;
  source: string;
  page?: number;
  relevance_score: number;
}

export interface GradingDetails {
  answer_uuid: string;
  student: StudentInfo;
  question: QuestionInfo;
  answer_text: string;
  
  // Resultado final
  final_score: number;
  status: string;
  graded_at: string | null;
  
  // Feedback consolidado
  final_feedback: string;
  
  // Divergência
  divergence_detected: boolean;
  divergence_value?: number;
  
  // Scores por critério
  criteria_scores: CriterionScoreDetail[];
  
  // Detalhes dos agentes
  corrections: AgentCorrectionDetail[];
  
  // Contexto RAG
  rag_context: RAGContextItem[];
}
