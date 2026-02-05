export interface Student {
  uuid: string;
  full_name: string;
  email: string | null;
  enrolled_at: string;
  active: boolean;
}

export interface CreateStudentDTO {
  email?: string;
  full_name: string;
}
