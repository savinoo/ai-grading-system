import { IClassRepository } from '../../../domain/repositories/IClassRepository';
import { ClassWithStudents } from '../../../domain/entities/Class';

export class GetClassDetailsUseCase {
  constructor(private classRepository: IClassRepository) {}

  async execute(classUuid: string): Promise<ClassWithStudents> {
    return await this.classRepository.getClassDetails(classUuid);
  }
}
