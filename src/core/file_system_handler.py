import shutil
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from src.core.settings import settings
from src.core.logging_config import get_logger


class FileSystemHandler:
    """
    Handler responsável por operações de sistema de arquivos.
    Gerencia criação de diretórios, salvamento e remoção de arquivos.
    """

    def __init__(self) -> None:
        self.__logger = get_logger(__name__)
        self.__upload_dir = Path(settings.UPLOAD_DIR)
        self.__ensure_upload_directory()

    def __ensure_upload_directory(self) -> None:
        """
        Garante que o diretório raiz de uploads existe.
        """
        try:
            self.__upload_dir.mkdir(parents=True, exist_ok=True)
            self.__logger.debug("Diretório de uploads verificado: %s", self.__upload_dir)
        except Exception as e:
            self.__logger.error("Erro ao criar diretório de uploads: %s", e, exc_info=True)
            raise

    def get_exam_directory(self, exam_uuid: UUID) -> Path:
        """
        Retorna o caminho do diretório de uma prova.
        
        Args:
            exam_uuid: UUID da prova
            
        Returns:
            Path: Caminho do diretório da prova
        """
        return self.__upload_dir / str(exam_uuid)

    def create_exam_directory(self, exam_uuid: UUID) -> Path:
        """
        Cria o diretório para armazenar anexos de uma prova.
        
        Args:
            exam_uuid: UUID da prova
            
        Returns:
            Path: Caminho do diretório criado
        """
        try:
            exam_dir = self.get_exam_directory(exam_uuid)
            exam_dir.mkdir(parents=True, exist_ok=True)
            self.__logger.info("Diretório da prova criado: %s", exam_dir)
            return exam_dir
            
        except Exception as e:
            self.__logger.error(
                "Erro ao criar diretório da prova %s: %s", 
                exam_uuid, 
                e, 
                exc_info=True
            )
            raise

    def get_attachment_path(self, exam_uuid: UUID, attachment_uuid: UUID) -> Path:
        """
        Retorna o caminho completo de um anexo.
        
        Args:
            exam_uuid: UUID da prova
            attachment_uuid: UUID do anexo
            
        Returns:
            Path: Caminho completo do arquivo
        """
        exam_dir = self.get_exam_directory(exam_uuid)
        return exam_dir / f"{attachment_uuid}.pdf"

    def save_file(
        self,
        file: BinaryIO,
        exam_uuid: UUID,
        attachment_uuid: UUID
    ) -> Path:
        """
        Salva um arquivo no sistema de arquivos.
        
        Args:
            file: Arquivo em modo binário
            exam_uuid: UUID da prova
            attachment_uuid: UUID do anexo
            
        Returns:
            Path: Caminho onde o arquivo foi salvo
        """
        try:
            # Cria o diretório da prova se não existir
            self.create_exam_directory(exam_uuid)
            
            # Define o caminho do arquivo
            file_path = self.get_attachment_path(exam_uuid, attachment_uuid)
            
            # Volta para o início do arquivo
            file.seek(0)
            
            # Salva o arquivo
            with open(file_path, "wb") as destination:
                shutil.copyfileobj(file, destination)
            
            self.__logger.info(
                "Arquivo salvo: %s (prova: %s, anexo: %s)",
                file_path,
                exam_uuid,
                attachment_uuid
            )
            
            return file_path
            
        except Exception as e:
            self.__logger.error(
                "Erro ao salvar arquivo (prova: %s, anexo: %s): %s",
                exam_uuid,
                attachment_uuid,
                e,
                exc_info=True
            )
            raise

    def delete_file(self, exam_uuid: UUID, attachment_uuid: UUID) -> bool:
        """
        Remove um arquivo do sistema de arquivos.
        
        Args:
            exam_uuid: UUID da prova
            attachment_uuid: UUID do anexo
            
        Returns:
            bool: True se o arquivo foi removido, False se não existia
        """
        try:
            file_path = self.get_attachment_path(exam_uuid, attachment_uuid)
            
            if file_path.exists():
                file_path.unlink()
                self.__logger.info("Arquivo removido: %s", file_path)
                return True
            else:
                self.__logger.warning("Arquivo não encontrado para remoção: %s", file_path)
                return False
                
        except Exception as e:
            self.__logger.error(
                "Erro ao remover arquivo (prova: %s, anexo: %s): %s",
                exam_uuid,
                attachment_uuid,
                e,
                exc_info=True
            )
            raise

    def delete_exam_directory(self, exam_uuid: UUID) -> bool:
        """
        Remove o diretório de uma prova e todos os seus arquivos.
        
        Args:
            exam_uuid: UUID da prova
            
        Returns:
            bool: True se o diretório foi removido, False se não existia
        """
        try:
            exam_dir = self.get_exam_directory(exam_uuid)
            
            if exam_dir.exists():
                shutil.rmtree(exam_dir)
                self.__logger.info("Diretório da prova removido: %s", exam_dir)
                return True
            else:
                self.__logger.warning("Diretório da prova não encontrado: %s", exam_dir)
                return False
                
        except Exception as e:
            self.__logger.error(
                "Erro ao remover diretório da prova %s: %s",
                exam_uuid,
                e,
                exc_info=True
            )
            raise

    def file_exists(self, exam_uuid: UUID, attachment_uuid: UUID) -> bool:
        """
        Verifica se um arquivo existe no sistema de arquivos.
        
        Args:
            exam_uuid: UUID da prova
            attachment_uuid: UUID do anexo
            
        Returns:
            bool: True se o arquivo existe, False caso contrário
        """
        file_path = self.get_attachment_path(exam_uuid, attachment_uuid)
        return file_path.exists()

    def get_file_size(self, exam_uuid: UUID, attachment_uuid: UUID) -> int:
        """
        Retorna o tamanho de um arquivo em bytes.
        
        Args:
            exam_uuid: UUID da prova
            attachment_uuid: UUID do anexo
            
        Returns:
            int: Tamanho do arquivo em bytes
            
        Raises:
            FileNotFoundError: Se o arquivo não existir
        """
        file_path = self.get_attachment_path(exam_uuid, attachment_uuid)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        return file_path.stat().st_size

    def list_exam_files(self, exam_uuid: UUID) -> list[Path]:
        """
        Lista todos os arquivos de uma prova.
        
        Args:
            exam_uuid: UUID da prova
            
        Returns:
            list[Path]: Lista de caminhos dos arquivos
        """
        try:
            exam_dir = self.get_exam_directory(exam_uuid)
            
            if not exam_dir.exists():
                return []
            
            files = list(exam_dir.glob("*.pdf"))
            self.__logger.debug("Listados %d arquivos da prova %s", len(files), exam_uuid)
            
            return files
            
        except Exception as e:
            self.__logger.error(
                "Erro ao listar arquivos da prova %s: %s",
                exam_uuid,
                e,
                exc_info=True
            )
            raise
