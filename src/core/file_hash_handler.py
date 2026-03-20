import hashlib
from typing import BinaryIO

from src.core.logging_config import get_logger


class FileHashHandler:
    """
    Handler responsável por calcular hashes de arquivos.
    Implementa algoritmos de hash para garantir integridade dos arquivos.
    """

    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    def calculate_sha256(self, file: BinaryIO, chunk_size: int = 8192) -> str:
        """
        Calcula o hash SHA256 de um arquivo.
        
        Args:
            file: Arquivo em modo binário
            chunk_size: Tamanho do chunk para leitura (padrão 8KB)
            
        Returns:
            str: Hash SHA256 em hexadecimal
        """
        try:
            sha256_hash = hashlib.sha256()
            
            # Salva a posição atual do arquivo
            current_position = file.tell()
            
            # Volta para o início do arquivo
            file.seek(0)
            
            # Lê o arquivo em chunks
            while chunk := file.read(chunk_size):
                sha256_hash.update(chunk)
            
            # Restaura a posição original do arquivo
            file.seek(current_position)
            
            hash_value = sha256_hash.hexdigest()
            self.__logger.debug("Hash SHA256 calculado: %s", hash_value[:16] + "...")
            
            return hash_value
            
        except Exception as e:
            self.__logger.error("Erro ao calcular hash SHA256: %s", e, exc_info=True)
            raise

    def calculate_md5(self, file: BinaryIO, chunk_size: int = 8192) -> str:
        """
        Calcula o hash MD5 de um arquivo.
        Útil para verificações rápidas de integridade.
        
        Args:
            file: Arquivo em modo binário
            chunk_size: Tamanho do chunk para leitura (padrão 8KB)
            
        Returns:
            str: Hash MD5 em hexadecimal
        """
        try:
            md5_hash = hashlib.md5()
            
            # Salva a posição atual do arquivo
            current_position = file.tell()
            
            # Volta para o início do arquivo
            file.seek(0)
            
            # Lê o arquivo em chunks
            while chunk := file.read(chunk_size):
                md5_hash.update(chunk)
            
            # Restaura a posição original do arquivo
            file.seek(current_position)
            
            hash_value = md5_hash.hexdigest()
            self.__logger.debug("Hash MD5 calculado: %s", hash_value)
            
            return hash_value
            
        except Exception as e:
            self.__logger.error("Erro ao calcular hash MD5: %s", e, exc_info=True)
            raise

    def verify_sha256(self, file: BinaryIO, expected_hash: str) -> bool:
        """
        Verifica se o hash SHA256 de um arquivo corresponde ao esperado.
        
        Args:
            file: Arquivo em modo binário
            expected_hash: Hash esperado
            
        Returns:
            bool: True se o hash corresponder, False caso contrário
        """
        try:
            calculated_hash = self.calculate_sha256(file)
            matches = calculated_hash == expected_hash.lower()
            
            if matches:
                self.__logger.debug("Hash SHA256 verificado com sucesso")
            else:
                self.__logger.warning(
                    "Hash SHA256 não corresponde. Esperado: %s, Calculado: %s",
                    expected_hash[:16] + "...",
                    calculated_hash[:16] + "..."
                )
            
            return matches
            
        except Exception as e:
            self.__logger.error("Erro ao verificar hash SHA256: %s", e, exc_info=True)
            raise
