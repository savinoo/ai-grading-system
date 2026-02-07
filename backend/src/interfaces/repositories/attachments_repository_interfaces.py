# pylint: disable=C0121
from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.models.entities.attachments import Attachments

class AttachmentsRepositoryInterface(ABC):
    """
    Repositório para operações CRUD da entidade Attachments.
    """

    # ==================== READ OPERATIONS ====================

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
    def count_attachments(self, db: Session, exam_uuid: Optional[UUID] = None) -> int:
        """
        Conta o total de anexos.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: Se fornecido, conta apenas anexos da prova especificada
            
        Returns:
            int: Total de anexos
        """
        raise NotImplementedError()

    @abstractmethod
    def exists_by_sha256_hash(self, db: Session, sha256_hash: str) -> bool:
        """
        Verifica se existe anexo com o hash SHA256 especificado.
        
        Args:
            db: Sessão do banco de dados
            sha256_hash: Hash SHA256 do arquivo
            
        Returns:
            bool: True se existir, False caso contrário
        """
        raise NotImplementedError()

    @abstractmethod
    def exists_by_uuid(self, db: Session, uuid: UUID) -> bool:
        """
        Verifica se existe anexo com o UUID especificado.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do anexo
            
        Returns:
            bool: True se existir, False caso contrário
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_vector_status(
        self,
        db: Session,
        vector_status: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Attachments]:
        """
        Busca anexos por status de processamento vetorial.
        
        Args:
            db: Sessão do banco de dados
            vector_status: Status vetorial (DRAFT, SUCCESS, FAILED)
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[Attachments]: Lista de anexos com o status especificado
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_exam_and_vector_status(
        self,
        db: Session,
        exam_uuid: UUID,
        vector_status: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Attachments]:
        """
        Busca anexos de uma prova específica com determinado status vetorial.
        Útil para processar anexos quando a prova é publicada.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            vector_status: Status vetorial (DRAFT, SUCCESS, FAILED)
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[Attachments]: Lista de anexos
        """
        raise NotImplementedError()
    
    @abstractmethod
    def count_by_vector_status(
        self,
        db: Session,
        vector_status: str,
        exam_uuid: Optional[UUID] = None
    ) -> int:
        """
        Conta anexos por status vetorial.
        
        Args:
            db: Sessão do banco de dados
            vector_status: Status vetorial (DRAFT, SUCCESS, FAILED)
            exam_uuid: Se fornecido, conta apenas da prova especificada
            
        Returns:
            int: Total de anexos com o status
        """
        raise NotImplementedError()

    # ==================== CREATE OPERATIONS ====================

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    # ==================== UPDATE OPERATIONS ====================

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()
    
    @abstractmethod
    def update_vector_status(
        self,
        db: Session,
        uuid: UUID,
        vector_status: str
    ) -> Attachments:
        """
        Atualiza o status de processamento vetorial de um anexo.
        Método dedicado para a operação mais comum de atualização.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do anexo
            vector_status: Novo status (DRAFT, SUCCESS, FAILED)
            
        Returns:
            Attachments: Anexo atualizado
        """
        raise NotImplementedError()
    
    @abstractmethod
    def bulk_update_vector_status(
        self,
        db: Session,
        attachment_uuids: list[UUID],
        vector_status: str
    ) -> int:
        """
        Atualiza o status vetorial de múltiplos anexos.
        Útil para processar lotes de arquivos.
        
        Args:
            db: Sessão do banco de dados
            attachment_uuids: Lista de UUIDs dos anexos
            vector_status: Novo status (DRAFT, SUCCESS, FAILED)
            
        Returns:
            int: Número de anexos atualizados
        """
        raise NotImplementedError()


    # ==================== DELETE OPERATIONS ====================

    @abstractmethod
    def delete(self, db: Session, attachment_id: int) -> None:
        """
        Remove um anexo permanentemente.
        
        Args:
            db: Sessão do banco de dados
            attachment_id: ID do anexo
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_by_uuid(self, db: Session, uuid: UUID) -> None:
        """
        Remove um anexo por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do anexo
        """
        raise NotImplementedError()

    @abstractmethod
    def bulk_delete_by_exam_uuid(self, db: Session, exam_uuid: UUID) -> int:
        """
        Remove todos os anexos de uma prova específica.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            
        Returns:
            int: Número de anexos deletados
        """
        raise NotImplementedError()

    @abstractmethod
    def bulk_delete(self, db: Session, attachment_ids: list[int]) -> int:
        """
        Remove múltiplos anexos por IDs.
        
        Args:
            db: Sessão do banco de dados
            attachment_ids: Lista de IDs dos anexos
            
        Returns:
            int: Número de anexos deletados
        """
        raise NotImplementedError()
