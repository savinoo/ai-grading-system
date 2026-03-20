from __future__ import annotations

from typing import BinaryIO
from uuid import uuid4, UUID
from pathlib import Path

from sqlalchemy.orm import Session

from src.interfaces.services.attachments.upload_attachment_service_interface import UploadAttachmentServiceInterface
from src.interfaces.repositories.attachments_repository_interfaces import AttachmentsRepositoryInterface
from src.models.entities.attachments import Attachments

from src.domain.requests.attachments.attachment_upload_request import AttachmentUploadRequest
from src.domain.responses.attachments.attachment_upload_response import AttachmentUploadResponse

from src.core.file_system_handler import FileSystemHandler
from src.core.file_hash_handler import FileHashHandler
from src.core.logging_config import get_logger

from src.errors.domain.sql_error import SqlError


class UploadAttachmentService(UploadAttachmentServiceInterface):
    """
    Serviço responsável por orquestrar o upload completo de anexos.
    
    Coordena as seguintes operações:
    1. Validação do arquivo
    2. Cálculo do hash SHA256
    3. Verificação de duplicatas
    4. Salvamento físico do arquivo
    5. Persistência dos metadados no banco
    
    Este serviço segue o padrão de orquestração, delegando
    responsabilidades específicas aos handlers apropriados.
    """

    def __init__(self, repository: AttachmentsRepositoryInterface) -> None:
        self.__repository = repository
        self.__file_system_handler = FileSystemHandler()
        self.__file_hash_handler = FileHashHandler()
        self.__logger = get_logger(__name__)

    async def upload(
        self,
        db: Session,
        file: BinaryIO,
        request: AttachmentUploadRequest
    ) -> AttachmentUploadResponse:
        """
        Realiza o upload completo de um anexo.
        
        Args:
            db: Sessão do banco de dados
            file: Arquivo binário a ser enviado
            request: Dados da requisição de upload
            
        Returns:
            AttachmentUploadResponse: Dados do anexo criado
            
        Raises:
            SqlError: Em caso de erro de banco de dados
            Exception: Para outros erros durante o processo
        """
        try:
            self.__logger.info(
                "Iniciando upload de anexo: %s para prova %s",
                request.original_filename,
                request.exam_uuid
            )

            # 1. Calcula o hash SHA256 do arquivo
            sha256_hash = self.__calculate_file_hash(file)
            
            # 2. Verifica se já existe um arquivo com o mesmo hash
            self.__check_duplicate_file(db, sha256_hash, request.exam_uuid)
            
            # 3. Gera UUID para o anexo
            attachment_uuid = uuid4()
            
            # 4. Salva o arquivo fisicamente
            file_path = self.__save_physical_file(
                file=file,
                exam_uuid=request.exam_uuid,
                attachment_uuid=attachment_uuid
            )
            
            # 5. Persiste os metadados no banco
            attachment = self.__persist_metadata(
                db=db,
                request=request,
                attachment_uuid=attachment_uuid,
                sha256_hash=sha256_hash
            )
            
            # 6. Commit da transação
            db.commit()
            
            self.__logger.info(
                "Upload concluído com sucesso: anexo %s (arquivo: %s)",
                attachment.uuid,
                file_path
            )
            
            # 7. Formata e retorna a resposta
            return self.__format_response(attachment)

        except Exception as e:
            # Em caso de erro, tenta fazer rollback e limpar o arquivo
            db.rollback()
            self.__cleanup_on_error(request.exam_uuid, attachment_uuid if 'attachment_uuid' in locals() else None)
            
            self.__logger.error(
                "Erro durante upload do anexo %s: %s",
                request.original_filename,
                e,
                exc_info=True
            )
            
            raise SqlError(
                message="Erro ao fazer upload do anexo",
                context={
                    "filename": request.original_filename,
                    "exam_uuid": str(request.exam_uuid)
                },
                cause=e
            ) from e

    def __calculate_file_hash(self, file: BinaryIO) -> str:
        """
        Calcula o hash SHA256 do arquivo.
        
        Args:
            file: Arquivo binário
            
        Returns:
            str: Hash SHA256 em hexadecimal
        """
        try:
            sha256_hash = self.__file_hash_handler.calculate_sha256(file)
            self.__logger.debug("Hash SHA256 calculado: %s", sha256_hash[:16] + "...")
            return sha256_hash
            
        except Exception as e:
            self.__logger.error("Erro ao calcular hash do arquivo: %s", e, exc_info=True)
            raise

    def __check_duplicate_file(
        self,
        db: Session,
        sha256_hash: str,
        exam_uuid: UUID
    ) -> None:
        """
        Verifica se já existe um arquivo com o mesmo hash para a mesma prova.
        
        Args:
            db: Sessão do banco de dados
            sha256_hash: Hash SHA256 do arquivo
            exam_uuid: UUID da prova
            
        Note:
            Por enquanto apenas loga um warning. Futuramente pode-se
            implementar deduplicação ou rejeição de duplicatas.
        """
        try:
            existing_attachment = self.__repository.get_by_sha256_hash(db, sha256_hash)
            
            if existing_attachment and existing_attachment.exam_uuid == exam_uuid:
                self.__logger.warning(
                    "Arquivo duplicado detectado: hash %s já existe para prova %s",
                    sha256_hash[:16] + "...",
                    exam_uuid
                )
                # Nota: Por enquanto apenas avisa. Pode-se implementar lógica de deduplicação aqui
                
        except Exception as e:
            # Se der erro na verificação, apenas loga e continua
            self.__logger.debug("Erro ao verificar duplicatas (não crítico): %s", e)

    def __save_physical_file(
        self,
        file: BinaryIO,
        exam_uuid: UUID,
        attachment_uuid: UUID
    ) -> Path:
        """
        Salva o arquivo fisicamente no sistema de arquivos.
        
        Args:
            file: Arquivo binário
            exam_uuid: UUID da prova
            attachment_uuid: UUID do anexo
            
        Returns:
            Path: Caminho onde o arquivo foi salvo
        """
        try:
            file_path = self.__file_system_handler.save_file(
                file=file,
                exam_uuid=exam_uuid,
                attachment_uuid=attachment_uuid
            )
            
            self.__logger.debug("Arquivo físico salvo em: %s", file_path)
            return file_path
            
        except Exception as e:
            self.__logger.error("Erro ao salvar arquivo físico: %s", e, exc_info=True)
            raise

    def __persist_metadata(
        self,
        db: Session,
        request: AttachmentUploadRequest,
        attachment_uuid: UUID,
        sha256_hash: str
    ) -> Attachments:
        """
        Persiste os metadados do anexo no banco de dados.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da requisição
            attachment_uuid: UUID do anexo
            sha256_hash: Hash SHA256 do arquivo
            
        Returns:
            Attachments: Entidade do anexo criada
        """
        try:
            attachment = self.__repository.create(
                db=db,
                uuid=attachment_uuid,
                exam_uuid=request.exam_uuid,
                original_filename=request.original_filename,
                mime_type=request.mime_type,
                size_bytes=request.size_bytes,
                sha256_hash=sha256_hash
            )
            
            self.__logger.debug("Metadados persistidos: ID=%s", attachment.id)
            return attachment
            
        except Exception as e:
            self.__logger.error("Erro ao persistir metadados: %s", e, exc_info=True)
            raise

    def __cleanup_on_error(
        self,
        exam_uuid: UUID,
        attachment_uuid: UUID | None
    ) -> None:
        """
        Limpa arquivos em caso de erro durante o upload.
        
        Args:
            exam_uuid: UUID da prova
            attachment_uuid: UUID do anexo (se já foi gerado)
        """
        if attachment_uuid:
            try:
                self.__file_system_handler.delete_file(exam_uuid, attachment_uuid)
                self.__logger.debug("Arquivo removido após erro: %s", attachment_uuid)
            except Exception as e:
                self.__logger.warning(
                    "Não foi possível remover arquivo após erro: %s",
                    e
                )

    def __format_response(
        self,
        attachment: Attachments
    ) -> AttachmentUploadResponse:
        """
        Formata a resposta do upload.
        
        Args:
            attachment: Entidade do anexo
            file_path: Caminho do arquivo salvo
            
        Returns:
            AttachmentUploadResponse: Resposta formatada
        """
        # Gera o caminho relativo (exam_uuid/attachment_uuid.pdf)
        relative_path = f"{attachment.exam_uuid}/{attachment.uuid}.pdf"
        
        return AttachmentUploadResponse(
            id=attachment.id,
            uuid=attachment.uuid,
            exam_uuid=attachment.exam_uuid,
            original_filename=attachment.original_filename,
            mime_type=attachment.mime_type,
            size_bytes=attachment.size_bytes,
            sha256_hash=attachment.sha256_hash,
            file_path=relative_path,
            created_at=attachment.created_at,
            message="Arquivo enviado com sucesso"
        )
