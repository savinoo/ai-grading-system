import { IClassRepository } from '../../../domain/repositories/IClassRepository';
import { ClassListResponse } from '../../../domain/entities/Class';

export class GetTeacherClassesUseCase {
  constructor(private classRepository: IClassRepository) {}

  async execute(teacherUuid: string): Promise<ClassListResponse> {
    return await this.classRepository.getTeacherClasses(teacherUuid);
  }
}
