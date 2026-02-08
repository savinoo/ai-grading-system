import { Attachment } from '@domain/entities/Attachment';

export interface IAttachmentRepository {
  uploadAttachment(examUuid: string, file: File): Promise<Attachment>;
  listAttachmentsByExam(examUuid: string): Promise<Attachment[]>;
  deleteAttachment(attachmentUuid: string): Promise<void>;
  downloadAttachment(attachmentUuid: string, filename: string): Promise<void>;
}
