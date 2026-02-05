import { HttpClient } from '../http/HttpClient';
import { IClassRepository } from '../../domain/repositories/IClassRepository';
import {
  Class,
  ClassWithStudents,
  CreateClassDTO,
  ClassListResponse,
  AddStudentsDTO,
  RemoveStudentResponse,
} from '../../domain/entities/Class';

export class ClassRepository implements IClassRepository {
  constructor(private httpClient: HttpClient) {}

  async createClass(data: CreateClassDTO): Promise<Class> {
    const response = await this.httpClient.post<Class>('/classes', data);
    return response;
  }

  async getTeacherClasses(teacherUuid: string): Promise<ClassListResponse> {
    const response = await this.httpClient.get<ClassListResponse>(
      `/classes/${teacherUuid}`
    );
    return response;
  }

  async getClassDetails(classUuid: string): Promise<ClassWithStudents> {
    const response = await this.httpClient.get<ClassWithStudents>(
      `/classes/class/${classUuid}`
    );
    return response;
  }

  async addStudentsToClass(
    classUuid: string,
    data: AddStudentsDTO
  ): Promise<void> {
    await this.httpClient.post(`/classes/${classUuid}/students`, data);
  }

  async removeStudentFromClass(
    classUuid: string,
    studentUuid: string
  ): Promise<RemoveStudentResponse> {
    const response = await this.httpClient.delete<RemoveStudentResponse>(
      `/classes/${classUuid}/students/${studentUuid}`
    );
    return response;
  }

  async deactivateClass(classUuid: string): Promise<Class> {
    const response = await this.httpClient.patch<Class>(
      `/classes/${classUuid}/deactivate`
    );
    return response;
  }
}
