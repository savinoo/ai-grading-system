from __future__ import annotations

from uuid import UUID
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.domain.responses.attachments.attachment_response import AttachmentResponse

class ManageAttachmentsServiceInterface(ABC):
    """
    Serviço responsável por gerenciar operações CRUD de anexos.
    
    Este serviço coordena operações de leitura, atualização e remoção
    de anexos, garantindo consistência entre o banco de dados e o
    sistema de arquivos.
    """
    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
    async def count_by_exam_uuid(self, db: Session, exam_uuid: UUID) -> int:
        """
        Conta o total de anexos de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            
        Returns:
            int: Total de anexos da prova
        """
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()
