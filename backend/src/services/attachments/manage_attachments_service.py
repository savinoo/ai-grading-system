from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.attachments.manage_attachments_service_interface import ManageAttachmentsServiceInterface
from src.interfaces.repositories.attachments_repository_interfaces import AttachmentsRepositoryInterface
from src.models.entities.attachments import Attachments

from src.domain.responses.attachments.attachment_response import AttachmentResponse

from src.core.file_system_handler import FileSystemHandler
from src.core.file_hash_handler import FileHashHandler
from src.core.logging_config import get_logger

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError


class ManageAttachmentsService(ManageAttachmentsServiceInterface):
    """
    Serviço responsável por gerenciar operações CRUD de anexos.
    
    Este serviço coordena operações de leitura, atualização e remoção
    de anexos, garantindo consistência entre o banco de dados e o
    sistema de arquivos.
    """

    def __init__(self, repository: AttachmentsRepositoryInterface) -> None:
        self.__repository = repository
        self.__file_system_handler = FileSystemHandler()
        self.__logger = get_logger(__name__)

    async def get_by_uuid(self, db: Session, uuid: UUID) -> AttachmentResponse:
        """
        Busca um anexo por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do anexo
            
        Returns:
            AttachmentResponse: Dados do anexo
            
        Raises:
            NotFoundError: Se o anexo não existir
        """
        try:
            self.__logger.debug("Buscando anexo por UUID: %s", uuid)
            
            attachment = self.__repository.get_by_uuid(db, uuid)
            
            return self.__format_response(attachment)
            
        except NoResultFound as e:
            self.__logger.warning("Anexo não encontrado: UUID=%s", uuid)
            raise NotFoundError(
                message=f"Anexo {uuid} não encontrado",
                context={"uuid": str(uuid)}
            ) from e
        except Exception as e:
            self.__logger.error("Erro ao buscar anexo: %s", e, exc_info=True)
            raise SqlError(
                message="Erro ao buscar anexo no banco de dados",
                context={"uuid": str(uuid)},
                cause=e
            ) from e

    async def get_by_exam_uuid(
        self,
        db: Session,
        exam_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> list[AttachmentResponse]:
        """
        Lista todos os anexos de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            list[AttachmentResponse]: Lista de anexos da prova
        """
        try:
            self.__logger.debug(
                "Listando anexos da prova %s (skip=%s, limit=%s)",
                exam_uuid,
                skip,
                limit
            )
            
            attachments = self.__repository.get_by_exam_uuid(
                db,
                exam_uuid,
                skip=skip,
                limit=limit
            )
            
            return [self.__format_response(att) for att in attachments]
            
        except Exception as e:
            self.__logger.error(
                "Erro ao listar anexos da prova %s: %s",
                exam_uuid,
                e,
                exc_info=True
            )
            raise SqlError(
                message="Erro ao listar anexos da prova",
                context={"exam_uuid": str(exam_uuid)},
                cause=e
            ) from e

    async def count_by_exam_uuid(self, db: Session, exam_uuid: UUID) -> int:
        """
        Conta o total de anexos de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            
        Returns:
            int: Total de anexos da prova
        """
        try:
            count = self.__repository.count_attachments(db, exam_uuid=exam_uuid)
            self.__logger.debug("Prova %s possui %d anexos", exam_uuid, count)
            return count
            
        except Exception as e:
            self.__logger.error(
                "Erro ao contar anexos da prova %s: %s",
                exam_uuid,
                e,
                exc_info=True
            )
            raise SqlError(
                message="Erro ao contar anexos da prova",
                context={"exam_uuid": str(exam_uuid)},
                cause=e
            ) from e

    async def delete_by_uuid(self, db: Session, uuid: UUID) -> None:
        """
        Remove um anexo por UUID.
        Remove tanto o registro do banco quanto o arquivo físico.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do anexo
            
        Raises:
            NotFoundError: Se o anexo não existir
        """
        try:
            self.__logger.info("Removendo anexo: %s", uuid)
            
            # 1. Busca o anexo para obter o exam_uuid
            attachment = self.__repository.get_by_uuid(db, uuid)
            
            # 2. Remove o arquivo físico
            self.__file_system_handler.delete_file(
                exam_uuid=attachment.exam_uuid,
                attachment_uuid=attachment.uuid
            )
            
            # 3. Remove o registro do banco
            self.__repository.delete_by_uuid(db, uuid)
            
            # 4. Commit da transação
            db.commit()
            
            self.__logger.info("Anexo removido com sucesso: %s", uuid)
            
        except NoResultFound as e:
            self.__logger.warning("Tentativa de remover anexo inexistente: %s", uuid)
            raise NotFoundError(
                message=f"Anexo {uuid} não encontrado",
                context={"uuid": str(uuid)}
            ) from e
        except Exception as e:
            db.rollback()
            self.__logger.error("Erro ao remover anexo %s: %s", uuid, e, exc_info=True)
            raise SqlError(
                message="Erro ao remover anexo",
                context={"uuid": str(uuid)},
                cause=e
            ) from e

    async def delete_all_by_exam_uuid(self, db: Session, exam_uuid: UUID) -> int:
        """
        Remove todos os anexos de uma prova.
        Remove tanto os registros do banco quanto os arquivos físicos.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            
        Returns:
            int: Número de anexos removidos
        """
        try:
            self.__logger.info("Removendo todos os anexos da prova: %s", exam_uuid)
            
            # 1. Remove os registros do banco
            count = self.__repository.bulk_delete_by_exam_uuid(db, exam_uuid)
            
            # 2. Remove o diretório da prova e todos os arquivos
            self.__file_system_handler.delete_exam_directory(exam_uuid)
            
            # 3. Commit da transação
            db.commit()
            
            self.__logger.info(
                "Removidos %d anexos da prova %s",
                count,
                exam_uuid
            )
            
            return count
            
        except Exception as e:
            db.rollback()
            self.__logger.error(
                "Erro ao remover anexos da prova %s: %s",
                exam_uuid,
                e,
                exc_info=True
            )
            raise SqlError(
                message="Erro ao remover anexos da prova",
                context={"exam_uuid": str(exam_uuid)},
                cause=e
            ) from e

    async def verify_file_integrity(self, db: Session, uuid: UUID) -> bool:
        """
        Verifica a integridade de um arquivo anexo.
        Compara o hash armazenado com o hash do arquivo físico.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do anexo
            
        Returns:
            bool: True se o arquivo está íntegro, False caso contrário
            
        Raises:
            NotFoundError: Se o anexo não existir
        """
        try:
            
            self.__logger.debug("Verificando integridade do anexo: %s", uuid)
            
            # 1. Busca o anexo
            attachment = self.__repository.get_by_uuid(db, uuid)
            
            # 2. Obtém o caminho do arquivo
            file_path = self.__file_system_handler.get_attachment_path(
                exam_uuid=attachment.exam_uuid,
                attachment_uuid=attachment.uuid
            )
            
            # 3. Verifica se o arquivo existe
            if not file_path.exists():
                self.__logger.warning(
                    "Arquivo físico não encontrado para anexo %s",
                    uuid
                )
                return False
            
            # 4. Calcula o hash do arquivo
            hash_handler = FileHashHandler()
            with open(file_path, "rb") as f:
                calculated_hash = hash_handler.calculate_sha256(f)
            
            # 5. Compara os hashes
            is_valid = calculated_hash == attachment.sha256_hash
            
            if is_valid:
                self.__logger.debug("Integridade do anexo %s verificada", uuid)
            else:
                self.__logger.warning(
                    "Integridade comprometida para anexo %s: "
                    "hash esperado %s, calculado %s",
                    uuid,
                    attachment.sha256_hash[:16] + "...",
                    calculated_hash[:16] + "..."
                )
            
            return is_valid
            
        except NoResultFound as e:
            self.__logger.warning("Anexo não encontrado para verificação: %s", uuid)
            raise NotFoundError(
                message=f"Anexo {uuid} não encontrado",
                context={"uuid": str(uuid)}
            ) from e
        except Exception as e:
            self.__logger.error(
                "Erro ao verificar integridade do anexo %s: %s",
                uuid,
                e,
                exc_info=True
            )
            raise

    async def get_download_info(self, db: Session, uuid: UUID) -> dict:
        """
        Busca informações do anexo para download.
        Retorna os metadados do anexo e o caminho do arquivo físico.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do anexo
            
        Returns:
            dict: Dicionário com file_path, original_filename e mime_type
            
        Raises:
            NotFoundError: Se o anexo não existir ou arquivo físico não for encontrado
        """
        try:
            self.__logger.debug("Buscando informações de download para anexo: %s", uuid)
            
            # 1. Busca o anexo no banco
            attachment = self.__repository.get_by_uuid(db, uuid)
            
            # 2. Obtém o caminho do arquivo
            file_path = self.__file_system_handler.get_attachment_path(
                exam_uuid=attachment.exam_uuid,
                attachment_uuid=attachment.uuid
            )
            
            # 3. Verifica se o arquivo existe
            if not file_path.exists():
                self.__logger.error(
                    "Arquivo físico não encontrado para anexo %s: %s",
                    uuid,
                    file_path
                )
                raise NotFoundError(
                    message=f"Arquivo físico do anexo {uuid} não encontrado",
                    context={"uuid": str(uuid), "expected_path": str(file_path)}
                )
            
            self.__logger.info(
                "Informações de download obtidas para anexo %s: %s",
                uuid,
                attachment.original_filename
            )
            
            return {
                "file_path": file_path,
                "original_filename": attachment.original_filename,
                "mime_type": attachment.mime_type
            }
            
        except NoResultFound as e:
            self.__logger.warning("Anexo não encontrado para download: UUID=%s", uuid)
            raise NotFoundError(
                message=f"Anexo {uuid} não encontrado",
                context={"uuid": str(uuid)}
            ) from e
        except NotFoundError:
            raise
        except Exception as e:
            self.__logger.error(
                "Erro ao buscar informações de download do anexo %s: %s",
                uuid,
                e,
                exc_info=True
            )
            raise SqlError(
                message="Erro ao buscar informações de download",
                context={"uuid": str(uuid)},
                cause=e
            ) from e

    def __format_response(self, attachment: Attachments) -> AttachmentResponse:
        """
        Formata a resposta de um anexo.
        
        Args:
            attachment: Entidade do anexo
            
        Returns:
            AttachmentResponse: Resposta formatada
        """
        return AttachmentResponse.model_validate(attachment)
