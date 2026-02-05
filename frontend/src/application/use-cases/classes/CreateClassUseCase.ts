import { IClassRepository } from '../../../domain/repositories/IClassRepository';
import { CreateClassDTO, Class } from '../../../domain/entities/Class';

export class CreateClassUseCase {
  constructor(private classRepository: IClassRepository) {}

  async execute(data: CreateClassDTO): Promise<Class> {
    return await this.classRepository.createClass(data);
  }
}
