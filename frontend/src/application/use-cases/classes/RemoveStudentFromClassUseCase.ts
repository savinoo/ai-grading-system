import { IClassRepository } from '../../../domain/repositories/IClassRepository';
import { RemoveStudentResponse } from '../../../domain/entities/Class';

export class RemoveStudentFromClassUseCase {
  constructor(private classRepository: IClassRepository) {}

  async execute(
    classUuid: string,
    studentUuid: string
  ): Promise<RemoveStudentResponse> {
    return await this.classRepository.removeStudentFromClass(
      classUuid,
      studentUuid
    );
  }
}
