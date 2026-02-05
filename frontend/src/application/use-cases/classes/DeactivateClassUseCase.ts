import { IClassRepository } from '../../../domain/repositories/IClassRepository';
import { Class } from '../../../domain/entities/Class';

export class DeactivateClassUseCase {
  constructor(private classRepository: IClassRepository) {}

  async execute(classUuid: string): Promise<Class> {
    return await this.classRepository.deactivateClass(classUuid);
  }
}
