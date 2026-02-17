"""
Controller para download de relatórios de notas.
"""

from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse

from src.core.logging_config import get_logger


logger = get_logger(__name__)


class DownloadReportController:
    """Controller para GET /reports/download/{filename}"""
    
    def handle(self, filename: str) -> FileResponse:
        """
        Faz download de um relatório Excel.
        
        Args:
            filename: Nome do arquivo a ser baixado
            
        Returns:
            FileResponse com o arquivo Excel
        """
        
        # Caminho do arquivo
        file_path = Path("data/reports") / filename
        
        # Validar que o arquivo existe e está dentro do diretório permitido
        if not file_path.exists():
            logger.warning("Tentativa de download de arquivo inexistente: %s", filename)
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        if not file_path.is_file():
            logger.warning("Tentativa de download de diretório: %s", filename)
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        # Validar que o arquivo está no diretório correto (segurança)
        try:
            file_path.resolve().relative_to(Path("data/reports").resolve())
        except ValueError as exc:
            logger.error("Tentativa de acesso a arquivo fora do diretório permitido: %s", filename)
            raise HTTPException(status_code=403, detail="Acesso negado") from exc
        
        logger.info("Download de relatório: %s", filename)
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
