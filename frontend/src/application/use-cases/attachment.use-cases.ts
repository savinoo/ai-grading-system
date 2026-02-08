import { Attachment } from '@domain/entities/Attachment';
import { IAttachmentRepository } from '@domain/repositories/IAttachmentRepository';

export class UploadAttachmentUseCase {
  constructor(private repository: IAttachmentRepository) {}

  async execute(examUuid: string, file: File): Promise<Attachment> {
    return this.repository.uploadAttachment(examUuid, file);
  }
}

export class ListAttachmentsByExamUseCase {
  constructor(private repository: IAttachmentRepository) {}

  async execute(examUuid: string): Promise<Attachment[]> {
    return this.repository.listAttachmentsByExam(examUuid);
  }
}

export class DeleteAttachmentUseCase {
  constructor(private repository: IAttachmentRepository) {}

  async execute(attachmentUuid: string): Promise<void> {
    return this.repository.deleteAttachment(attachmentUuid);
  }
}

export class DownloadAttachmentUseCase {
  constructor(private repository: IAttachmentRepository) {}

  async execute(attachmentUuid: string, filename: string): Promise<void> {
    return this.repository.downloadAttachment(attachmentUuid, filename);
  }
}
