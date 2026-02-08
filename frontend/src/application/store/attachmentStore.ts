import { create } from 'zustand';
import { Attachment } from '@domain/entities/Attachment';
import { AttachmentRepository } from '@infrastructure/repositories/AttachmentRepository';
import { HttpClient } from '@infrastructure/http/HttpClient';
import { LocalStorageService } from '@infrastructure/services/LocalStorageService';
import {
  UploadAttachmentUseCase,
  ListAttachmentsByExamUseCase,
  DeleteAttachmentUseCase,
  DownloadAttachmentUseCase,
} from '@application/use-cases/attachment.use-cases';

interface AttachmentState {
  attachments: Attachment[];
  isLoading: boolean;
  error: string | null;

  uploadAttachment: (examUuid: string, file: File) => Promise<Attachment>;
  loadAttachments: (examUuid: string) => Promise<void>;
  deleteAttachment: (attachmentUuid: string) => Promise<void>;
  downloadAttachment: (attachmentUuid: string, filename: string) => Promise<void>;
  clearAttachments: () => void;
}

const storageService = new LocalStorageService();
const httpClient = new HttpClient(storageService);
const repository = new AttachmentRepository(httpClient);
const uploadUseCase = new UploadAttachmentUseCase(repository);
const listUseCase = new ListAttachmentsByExamUseCase(repository);
const deleteUseCase = new DeleteAttachmentUseCase(repository);
const downloadUseCase = new DownloadAttachmentUseCase(repository);

export const useAttachmentStore = create<AttachmentState>((set) => ({
  attachments: [],
  isLoading: false,
  error: null,

  uploadAttachment: async (examUuid: string, file: File) => {
    set({ isLoading: true, error: null });
    try {
      const attachment = await uploadUseCase.execute(examUuid, file);
      set((state) => ({
        attachments: [...state.attachments, attachment],
        isLoading: false,
      }));
      return attachment;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro ao fazer upload';
      set({ isLoading: false, error: message });
      throw error;
    }
  },

  loadAttachments: async (examUuid: string) => {
    set({ isLoading: true, error: null });
    try {
      const attachments = await listUseCase.execute(examUuid);
      set({ attachments, isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro ao carregar anexos';
      set({ isLoading: false, error: message });
    }
  },

  deleteAttachment: async (attachmentUuid: string) => {
    set({ isLoading: true, error: null });
    try {
      await deleteUseCase.execute(attachmentUuid);
      set((state) => ({
        attachments: state.attachments.filter((a) => a.uuid !== attachmentUuid),
        isLoading: false,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro ao remover anexo';
      set({ isLoading: false, error: message });
      throw error;
    }
  },

  downloadAttachment: async (attachmentUuid: string, filename: string) => {
    set({ isLoading: true, error: null });
    try {
      await downloadUseCase.execute(attachmentUuid, filename);
      set({ isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro ao baixar anexo';
      set({ isLoading: false, error: message });
      throw error;
    }
  },

  clearAttachments: () => {
    set({ attachments: [], error: null });
  },
}));
