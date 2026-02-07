# pylint: disable=C0121
from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.interfaces.repositories.attachments_repository_interfaces import AttachmentsRepositoryInterface

from src.models.entities.attachments import Attachments

from src.core.logging_config import get_logger

class AttachmentsRepository(AttachmentsRepositoryInterface):
    """
    Repositório para operações CRUD da entidade Attachments.
    """

    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    # ==================== READ OPERATIONS ====================

    def get_by_id(self, db: Session, attachment_id: int) -> Attachments:
        """
        Busca anexo por ID.
        
        Args:
            db: Sessão do banco de dados
            attachment_id: ID do anexo
            
        Returns:
            Attachments: Entidade do anexo
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se o anexo não existir
        """
        try:
            stmt = select(Attachments).where(Attachments.id == attachment_id)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Anexo encontrado: ID=%s", attachment_id)
            return result

        except NoResultFound:
            self.__logger.warning("Anexo não encontrado: ID=%s", attachment_id)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar anexo por ID: %s", e, exc_info=True)
            raise

    def get_by_uuid(self, db: Session, uuid: UUID) -> Attachments:
        """
        Busca anexo por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do anexo
            
        Returns:
            Attachments: Entidade do anexo
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se o anexo não existir
        """
        try:
            stmt = select(Attachments).where(Attachments.uuid == uuid)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Anexo encontrado: UUID=%s", uuid)
            return result

        except NoResultFound:
            self.__logger.warning("Anexo não encontrado: UUID=%s", uuid)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar anexo por UUID: %s", e, exc_info=True)
            raise

    def get_by_exam_uuid(
        self,
        db: Session,
        exam_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Attachments]:
        """
        Busca todos os anexos de uma prova específica.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[Attachments]: Lista de anexos da prova
        """
        try:
            stmt = (
                select(Attachments)
                .where(Attachments.exam_uuid == exam_uuid)
                .order_by(Attachments.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Encontrados %d anexos para prova UUID=%s", len(result), exam_uuid)
            return result

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar anexos da prova UUID=%s: %s", exam_uuid, e, exc_info=True)
            raise

    def get_by_sha256_hash(self, db: Session, sha256_hash: str) -> Optional[Attachments]:
        """
        Busca anexo por hash SHA256.
        Útil para verificar duplicatas de arquivos.
        
        Args:
            db: Sessão do banco de dados
            sha256_hash: Hash SHA256 do arquivo
            
        Returns:
            Optional[Attachments]: Anexo encontrado ou None
        """
        try:
            stmt = select(Attachments).where(Attachments.sha256_hash == sha256_hash)
            result = db.execute(stmt).scalar_one_or_none()
            
            if result:
                self.__logger.debug("Anexo encontrado por hash: %s", sha256_hash)
            else:
                self.__logger.debug("Nenhum anexo encontrado com hash: %s", sha256_hash)
            
            return result

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar anexo por hash: %s", e, exc_info=True)
            raise

    def get_all(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Attachments]:
        """
        Lista todos os anexos com paginação.
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[Attachments]: Lista de anexos
        """
        try:
            stmt = (
                select(Attachments)
                .order_by(Attachments.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listados %d anexos", len(result))
            return result

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar anexos: %s", e, exc_info=True)
            raise

    def count_attachments(self, db: Session, exam_uuid: Optional[UUID] = None) -> int:
        """
        Conta o total de anexos.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: Se fornecido, conta apenas anexos da prova especificada
            
        Returns:
            int: Total de anexos
        """
        try:
            stmt = select(func.count(Attachments.id))  # pylint: disable=not-callable
            
            if exam_uuid:
                stmt = stmt.where(Attachments.exam_uuid == exam_uuid)
            
            result = db.execute(stmt).scalar()
            count = result or 0
            self.__logger.debug("Total de anexos: %d", count)
            return count

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar anexos: %s", e, exc_info=True)
            raise

    def exists_by_sha256_hash(self, db: Session, sha256_hash: str) -> bool:
        """
        Verifica se existe anexo com o hash SHA256 especificado.
        
        Args:
            db: Sessão do banco de dados
            sha256_hash: Hash SHA256 do arquivo
            
        Returns:
            bool: True se existir, False caso contrário
        """
        try:
            stmt = select(func.count(Attachments.id)).where(  # pylint: disable=not-callable
                Attachments.sha256_hash == sha256_hash
            )
            count = db.execute(stmt).scalar()
            exists = (count or 0) > 0
            self.__logger.debug("Anexo com hash %s existe: %s", sha256_hash, exists)
            return exists

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao verificar existência de hash: %s", e, exc_info=True)
            raise

    def exists_by_uuid(self, db: Session, uuid: UUID) -> bool:
        """
        Verifica se existe anexo com o UUID especificado.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do anexo
            
        Returns:
            bool: True se existir, False caso contrário
        """
        try:
            stmt = select(func.count(Attachments.id)).where(  # pylint: disable=not-callable
                Attachments.uuid == uuid
            )
            count = db.execute(stmt).scalar()
            exists = (count or 0) > 0
            self.__logger.debug("Anexo com UUID %s existe: %s", uuid, exists)
            return exists

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao verificar existência de UUID: %s", e, exc_info=True)
            raise

    # ==================== CREATE OPERATIONS ====================

    def create(
        self,
        db: Session,
        *,
        exam_uuid: UUID,
        original_filename: str,
        mime_type: str,
        size_bytes: int,
        sha256_hash: str,
        uuid: Optional[UUID] = None
    ) -> Attachments:
        """
        Cria um novo anexo.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            original_filename: Nome original do arquivo
            mime_type: Tipo MIME do arquivo
            size_bytes: Tamanho do arquivo em bytes
            sha256_hash: Hash SHA256 do arquivo
            uuid: UUID do anexo (opcional, será gerado automaticamente se não fornecido)
            
        Returns:
            Attachments: Anexo criado
        """
        try:
            self.__logger.debug("Criando anexo: %s para prova %s", original_filename, exam_uuid)
            
            attachment = Attachments(
                uuid=uuid,  # Se None, será gerado pelo banco via gen_random_uuid()
                exam_uuid=exam_uuid,
                original_filename=original_filename,
                mime_type=mime_type,
                size_bytes=size_bytes,
                sha256_hash=sha256_hash
            )
            
            db.add(attachment)
            db.flush()
            db.refresh(attachment)
            
            self.__logger.info(
                "Anexo criado: ID=%s, UUID=%s, arquivo=%s", 
                attachment.id, 
                attachment.uuid, 
                original_filename
            )
            return attachment

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao criar anexo %s: %s", original_filename, e, exc_info=True)
            raise

    def bulk_create(self, db: Session, attachments_data: list[dict]) -> int:
        """
        Cria múltiplos anexos em lote.
        
        Args:
            db: Sessão do banco de dados
            attachments_data: Lista de dicionários com dados dos anexos
            
        Returns:
            int: Número de anexos criados
            
        Example:
            attachments_data = [
                {
                    "exam_uuid": uuid_obj,
                    "original_filename": "file1.pdf",
                    "mime_type": "application/pdf",
                    "size_bytes": 1024,
                    "sha256_hash": "abc123..."
                },
                {...}
            ]
        """
        if not attachments_data:
            return 0

        try:
            self.__logger.debug("Criando %d anexos em lote", len(attachments_data))
            
            attachments = []
            for data in attachments_data:
                attachment = Attachments(**data)
                attachments.append(attachment)
            
            db.add_all(attachments)
            db.flush()
            
            self.__logger.info("Criados %d anexos em lote", len(attachments))
            return len(attachments)

        except SQLAlchemyError as e:
            self.__logger.error("Erro no bulk create de anexos: %s", e, exc_info=True)
            raise

    # ==================== UPDATE OPERATIONS ====================

    def update(self, db: Session, attachment_id: int, **updates) -> Attachments:
        """
        Atualiza um anexo.
        Nota: Na maioria dos casos, anexos não devem ser atualizados após criação.
        
        Args:
            db: Sessão do banco de dados
            attachment_id: ID do anexo
            **updates: Campos a atualizar
            
        Returns:
            Attachments: Anexo atualizado
        """
        try:
            self.__logger.debug("Atualizando anexo ID %s: %s", attachment_id, updates)
            
            attachment = self.get_by_id(db, attachment_id)
            
            for key, value in updates.items():
                if hasattr(attachment, key):
                    setattr(attachment, key, value)
            
            db.flush()
            db.refresh(attachment)
            
            self.__logger.info("Anexo ID %s atualizado", attachment_id)
            return attachment

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao atualizar anexo ID %s: %s", attachment_id, e, exc_info=True)
            raise

    def bulk_update(
        self, 
        db: Session, 
        mappings: list[dict], 
        *, 
        batch_size: int = 300
    ) -> int:
        """
        Atualiza múltiplos anexos em lote.
        
        Args:
            db: Sessão do banco de dados
            mappings: Lista de dicts com 'id' e campos a atualizar
            batch_size: Tamanho do lote
            
        Returns:
            int: Número de anexos atualizados
            
        Example:
            mappings = [
                {"id": 1, "original_filename": "novo_nome.pdf"},
                {"id": 2, "mime_type": "application/pdf"}
            ]
        """
        if not mappings:
            return 0

        try:
            total = 0
            
            for i in range(0, len(mappings), batch_size):
                chunk = mappings[i:i + batch_size]
                db.bulk_update_mappings(Attachments, chunk)
                total += len(chunk)
            
            db.flush()
            
            self.__logger.info(
                "Bulk update: %d anexos em %d lotes", 
                total, 
                (len(mappings) + batch_size - 1) // batch_size
            )
            return total

        except SQLAlchemyError as e:
            self.__logger.error("Erro no bulk update: %s", e, exc_info=True)
            raise

    # ==================== DELETE OPERATIONS ====================

    def delete(self, db: Session, attachment_id: int) -> None:
        """
        Remove um anexo permanentemente.
        
        Args:
            db: Sessão do banco de dados
            attachment_id: ID do anexo
        """
        try:
            self.__logger.debug("Deletando anexo ID %s", attachment_id)
            attachment = self.get_by_id(db, attachment_id)
            
            db.delete(attachment)
            db.flush()
            
            self.__logger.info("Anexo ID %s deletado", attachment_id)

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao deletar anexo ID %s: %s", attachment_id, e, exc_info=True)
            raise

    def delete_by_uuid(self, db: Session, uuid: UUID) -> None:
        """
        Remove um anexo por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do anexo
        """
        try:
            self.__logger.debug("Deletando anexo UUID %s", uuid)
            attachment = self.get_by_uuid(db, uuid)
            
            db.delete(attachment)
            db.flush()
            
            self.__logger.info("Anexo UUID %s deletado", uuid)

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao deletar anexo UUID %s: %s", uuid, e, exc_info=True)
            raise

    def bulk_delete_by_exam_uuid(self, db: Session, exam_uuid: UUID) -> int:
        """
        Remove todos os anexos de uma prova específica.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            
        Returns:
            int: Número de anexos deletados
        """
        try:
            self.__logger.debug("Deletando todos os anexos da prova UUID %s", exam_uuid)
            
            stmt = delete(Attachments).where(Attachments.exam_uuid == exam_uuid)
            result = db.execute(stmt)
            count = result.rowcount
            
            db.flush()
            
            self.__logger.info(
                "Deletados %d anexos da prova UUID %s", 
                count, 
                exam_uuid
            )
            return count

        except SQLAlchemyError as e:
            self.__logger.error(
                "Erro ao deletar anexos da prova UUID %s: %s", 
                exam_uuid, 
                e, 
                exc_info=True
            )
            raise

    def bulk_delete(self, db: Session, attachment_ids: list[int]) -> int:
        """
        Remove múltiplos anexos por IDs.
        
        Args:
            db: Sessão do banco de dados
            attachment_ids: Lista de IDs dos anexos
            
        Returns:
            int: Número de anexos deletados
        """
        if not attachment_ids:
            return 0

        try:
            self.__logger.debug("Deletando %d anexos em lote", len(attachment_ids))
            
            stmt = delete(Attachments).where(Attachments.id.in_(attachment_ids))
            result = db.execute(stmt)
            count = result.rowcount
            
            db.flush()
            
            self.__logger.info("Deletados %d anexos em lote", count)
            return count

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao deletar anexos em lote: %s", e, exc_info=True)
            raise
