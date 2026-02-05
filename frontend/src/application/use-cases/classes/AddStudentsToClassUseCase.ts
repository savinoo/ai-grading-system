import { IClassRepository } from '../../../domain/repositories/IClassRepository';
import { AddStudentsDTO } from '../../../domain/entities/Class';

export class AddStudentsToClassUseCase {
  constructor(private classRepository: IClassRepository) {}

  async execute(classUuid: string, data: AddStudentsDTO): Promise<void> {
    return await this.classRepository.addStudentsToClass(classUuid, data);
  }
}
