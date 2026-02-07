export type ExamStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED' | 'FINISHED';

export interface Exam {
  uuid: string;
  title: string;
  description: string | null;
  created_by: string | null;
  class_uuid: string | null;
  class_name: string | null;
  status: ExamStatus;
  starts_at: string | null;
  ends_at: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateExamDTO {
  title: string;
  description?: string | null;
  class_uuid?: string | null;
  status?: ExamStatus;
  starts_at?: string | null;
  ends_at?: string | null;
}

export interface UpdateExamDTO {
  title?: string;
  description?: string | null;
  class_uuid?: string | null;
  status?: ExamStatus;
  starts_at?: string | null;
  ends_at?: string | null;
}

export interface ExamListResponse {
  exams: Exam[];
  total: number;
}
