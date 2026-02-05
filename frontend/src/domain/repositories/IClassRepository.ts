import {
  Class,
  ClassWithStudents,
  CreateClassDTO,
  ClassListResponse,
  AddStudentsDTO,
  RemoveStudentResponse,
} from '../entities/Class';

export interface IClassRepository {
  createClass(data: CreateClassDTO): Promise<Class>;
  getTeacherClasses(teacherUuid: string): Promise<ClassListResponse>;
  getClassDetails(classUuid: string): Promise<ClassWithStudents>;
  addStudentsToClass(classUuid: string, data: AddStudentsDTO): Promise<void>;
  removeStudentFromClass(classUuid: string, studentUuid: string): Promise<RemoveStudentResponse>;
  deactivateClass(classUuid: string): Promise<Class>;
}
