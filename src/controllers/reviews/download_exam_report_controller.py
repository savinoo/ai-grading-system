from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse

from src.core.logging_config import get_logger


logger = get_logger("controllers")


class DownloadExamReportController:
    """Controller para GET /reviews/exams/{exam_uuid}/report"""
    
    def handle(self, exam_uuid: str) -> FileResponse:
        """
        Faz download do relatório Excel mais recente de uma prova.
        
        Args:
            exam_uuid: UUID da prova
            
        Returns:
            FileResponse com arquivo Excel
            
        Raises:
            HTTPException: Se arquivo não for encontrado
        """
        
        logger.info("Download de relatório solicitado para prova %s", exam_uuid)
        
        # Diretório de relatórios
        reports_dir = Path("data/reports")
        
        logger.info("Verificando diretório: %s (absolute: %s)", reports_dir, reports_dir.absolute())
        logger.info("Diretório existe? %s", reports_dir.exists())
        
        if not reports_dir.exists():
            logger.error("Diretório de relatórios não existe")
            raise HTTPException(status_code=404, detail="Nenhum relatório encontrado")
        
        # Buscar todos os arquivos da prova (pattern: notas_{exam_uuid}_*.xlsx)
        pattern = f"notas_{exam_uuid}_*.xlsx"
        logger.info("Buscando arquivos com padrão: %s", pattern)
        matching_files = list(reports_dir.glob(pattern))
        logger.info("Arquivos encontrados: %d", len(matching_files))
        
        if not matching_files:
            logger.warning("Nenhum relatório encontrado para prova %s", exam_uuid)
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum relatório encontrado para a prova {exam_uuid}"
            )
        
        # Pegar o arquivo mais recente (por timestamp no nome)
        latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
        
        logger.info("Enviando relatório: %s", latest_file.name)
        
        # Nome amigável para download
        download_name = f"relatorio_notas_{exam_uuid}.xlsx"
        
        return FileResponse(
            path=str(latest_file),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=download_name
        )
