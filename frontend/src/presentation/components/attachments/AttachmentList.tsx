import React from 'react';
import { Attachment } from '@domain/entities/Attachment';
import { Button } from '@presentation/components/ui/Button';

interface AttachmentListProps {
  attachments: Attachment[];
  onDelete?: (attachmentUuid: string) => void;
  onDownload?: (attachmentUuid: string, filename: string) => void;
  isDeleting?: boolean;
}

export const AttachmentList: React.FC<AttachmentListProps> = ({
  attachments,
  onDelete,
  onDownload,
  isDeleting = false,
}) => {
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      DRAFT: { label: 'Anexado', className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
      SUCCESS: { label: 'Indexado', className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
      FAILED: { label: 'Falha na Indexação', className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
    };
    return badges[status as keyof typeof badges] || badges.DRAFT;
  };

  if (attachments.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500 dark:text-slate-400">
        <span className="material-symbols-outlined text-4xl mb-2 opacity-50">
          folder_open
        </span>
        <p>Nenhum arquivo anexado</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {attachments.map((attachment) => {
        const badge = getStatusBadge(attachment.vector_status);
        
        return (
          <div
            key={attachment.uuid}
            className="flex items-center gap-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-primary/50 transition-colors"
            onClick={() => onDownload?.(attachment.uuid, attachment.original_filename)}
            style={{ cursor: onDownload ? 'pointer' : 'default' }}
            role={onDownload ? 'button' : undefined}
            tabIndex={onDownload ? 0 : undefined}
            onKeyDown={(e) => {
              if (onDownload && (e.key === 'Enter' || e.key === ' ')) {
                e.preventDefault();
                onDownload(attachment.uuid, attachment.original_filename);
              }
            }}
          >
            <div className="flex-shrink-0">
              <span className="material-symbols-outlined text-3xl text-red-600 dark:text-red-400">
                picture_as_pdf
              </span>
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">
                {attachment.original_filename}
              </p>
              <div className="flex items-center gap-3 mt-1">
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {formatFileSize(attachment.size_bytes)}
                </p>
                <span className={`px-2 py-0.5 rounded text-xs font-bold ${badge.className}`}>
                  {badge.label}
                </span>
              </div>
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                Enviado em {new Date(attachment.created_at).toLocaleString('pt-BR')}
              </p>
            </div>

            <div className="flex items-center gap-2">
              {onDownload && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDownload(attachment.uuid, attachment.original_filename);
                  }}
                  title="Baixar arquivo"
                  className="!bg-primary/10 dark:!bg-primary/20 !text-primary hover:!bg-primary/20 dark:hover:!bg-primary/30"
                >
                  <span className="material-symbols-outlined text-lg">download</span>
                </Button>
              )}
              {onDelete && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(attachment.uuid);
                  }}
                  disabled={isDeleting}
                  title="Remover arquivo"
                  className="!bg-red-50 dark:!bg-red-900/20 !text-red-600 dark:!text-red-400 hover:!bg-red-100 dark:hover:!bg-red-900/30"
                >
                  <span className="material-symbols-outlined text-lg">delete</span>
                </Button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
