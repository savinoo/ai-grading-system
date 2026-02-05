import { Student } from './Student';

export interface Class {
  uuid: string;
  name: string;
  description: string;
  year: number;
  semester: number;
  created_at?: string;
}

export interface ClassWithStudents extends Class {
  total_students: number;
  students: Student[];
}

export interface CreateClassDTO {
  name: string;
  description: string;
  year: number;
  semester: number;
}

export interface ClassListResponse {
  classes: Class[];
  total_classes: number;
}

export interface AddStudentsDTO {
  students: {
    email?: string;
    full_name: string;
  }[];
}

export interface RemoveStudentResponse {
  message: string;
  class_uuid: string;
  class_name: string;
  student_uuid: string;
  student_name: string;
}
