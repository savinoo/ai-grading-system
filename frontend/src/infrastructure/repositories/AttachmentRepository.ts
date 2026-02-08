import { Attachment } from '@domain/entities/Attachment';
import { IAttachmentRepository } from '@domain/repositories/IAttachmentRepository';
import { HttpClient } from '@infrastructure/http/HttpClient';

export class AttachmentRepository implements IAttachmentRepository {
  private readonly baseUrl = '/attachments';

  constructor(private httpClient: HttpClient) {}

  async uploadAttachment(examUuid: string, file: File): Promise<Attachment> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.httpClient.getClient().post<Attachment>(
      `${this.baseUrl}/upload?exam_uuid=${examUuid}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }

  async listAttachmentsByExam(examUuid: string): Promise<Attachment[]> {
    const response = await this.httpClient.getClient().get<{
      attachments: Attachment[];
      total: number;
      skip: number;
      limit: number;
    }>(
      `${this.baseUrl}/exam/${examUuid}`
    );

    return response.data.attachments;
  }

  async deleteAttachment(attachmentUuid: string): Promise<void> {
    await this.httpClient.delete(`${this.baseUrl}/${attachmentUuid}`);
  }

  async downloadAttachment(attachmentUuid: string, filename: string): Promise<void> {
    const response = await this.httpClient.getClient().get(
      `${this.baseUrl}/${attachmentUuid}/download`,
      {
        responseType: 'blob',
      }
    );

    // Cria um link temporário e aciona o download com o nome fornecido
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }
}
