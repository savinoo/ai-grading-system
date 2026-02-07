import { useCallback } from 'react';
import { useAttachmentStore } from '@application/store/attachmentStore';

export const useAttachments = () => {
  const {
    attachments,
    isLoading,
    error,
    uploadAttachment,
    loadAttachments,
    deleteAttachment,
    clearAttachments,
  } = useAttachmentStore();

  const handleUpload = useCallback(
    async (examUuid: string, file: File) => {
      return uploadAttachment(examUuid, file);
    },
    [uploadAttachment]
  );

  const handleLoad = useCallback(
    async (examUuid: string) => {
      await loadAttachments(examUuid);
    },
    [loadAttachments]
  );

  const handleDelete = useCallback(
    async (attachmentUuid: string) => {
      await deleteAttachment(attachmentUuid);
    },
    [deleteAttachment]
  );

  return {
    attachments,
    isLoading,
    error,
    uploadAttachment: handleUpload,
    loadAttachments: handleLoad,
    deleteAttachment: handleDelete,
    clearAttachments,
  };
};
