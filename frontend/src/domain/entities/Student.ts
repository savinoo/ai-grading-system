export interface Student {
  uuid: string;
  full_name: string;
  name?: string; // Alias para full_name
  registration?: string;
  email: string | null;
  enrolled_at: string;
  active: boolean;
}

export interface CreateStudentDTO {
  email?: string;
  full_name: string;
}
