from bcrypt import hashpw, gensalt, checkpw


from src.core.settings import settings
from src.core.logging_config import get_logger

class HashPasswordHandler:
    
    """
    Gerencia hashing e verificação de senhas usando bcrypt.
    Bycrypt é um algoritmo de hashing adaptativo projetado para armazenar senhas de forma segura.
    Ele incorpora um sal (salt) para proteger contra ataques de rainbow table e é configurável em termos de custo computacional, o que permite aumentar a dificuldade de hashing conforme o poder computacional evolui.
    
    Attributes:
        __logger: Instância de logger para registrar eventos relacionados ao hashing de senhas.
    """
    def __init__(self):
        self.__logger = get_logger(__name__)
    
    def generate_password_hash(self, password: str) -> str:
        """
        Gera um hash seguro para a senha fornecida usando bcrypt.
        Com o uso de sal e rounds configuráveis, o bcrypt torna o hash resistente a ataques de força bruta.
        
        Args:
            password (str): A senha em texto puro a ser hasheada.
            
        Returns:
            str: O hash da senha gerado.
        """
        
        self.__logger.debug("Gerando hash da senha do afiliado.")
        return hashpw(password.encode('utf-8'), gensalt(settings.BCRYPT_ROUNDS)).decode('utf-8')
    
    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """
        Verifica se a senha em texto puro corresponde ao hash armazenado.
        
        Args:
            plain_password (str): A senha em texto puro a ser verificada.
            password_hash (str): O hash da senha armazenado para comparação.
        
        Returns:
            bool: True se a senha corresponder ao hash, False caso contrário.
        """
        
        return checkpw(plain_password.encode('utf-8'), password_hash.encode('utf-8'))
