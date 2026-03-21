from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO

from sqlalchemy.orm import Session

from src.domain.requests.attachments.attachment_upload_request import AttachmentUploadRequest
from src.domain.responses.attachments.attachment_upload_response import AttachmentUploadResponse

class UploadAttachmentServiceInterface(ABC):
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

    @abstractmethod
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
        raise NotImplementedError()
