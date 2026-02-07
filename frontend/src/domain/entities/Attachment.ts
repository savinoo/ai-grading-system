export interface Attachment {
  uuid: string;
  exam_uuid: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  sha256_hash: string;
  vector_status: 'DRAFT' | 'SUCCESS' | 'FAILED';
  created_at: string;
}

export interface CreateAttachmentDTO {
  exam_uuid: string;
  file: File;
}
