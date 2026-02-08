from io import BytesIO
from uuid import UUID
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    File,
    Query,
    Path
)
from fastapi.responses import JSONResponse, FileResponse

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.domain.http.caller_domains import CallerMeta

# Request Models
from src.domain.requests.attachments.attachment_upload_request import AttachmentUploadRequest

# Response Models
from src.domain.responses.attachments.attachment_response import AttachmentResponse
from src.domain.responses.attachments.attachment_upload_response import AttachmentUploadResponse

from src.core.logging_config import get_logger

from src.main.composer.attachments_composer import (
    make_upload_attachment_controller,
    make_get_attachments_by_exam_controller,
    make_get_attachment_by_uuid_controller,
    make_delete_attachment_controller,
    make_download_attachment_controller
)

from src.main.dependencies.request_meta import get_caller_meta
from src.main.dependencies.get_db_session import get_db
from src.main.dependencies.auth_jwt import auth_jwt_verify

logger = get_logger(__name__)

router = APIRouter(
    prefix="/attachments",
    tags=["Attachments"],
)


@router.post(
    "/upload",
    response_model=AttachmentUploadResponse,
    status_code=201,
    summary="Upload de anexo",
    description="Endpoint para fazer upload de anexos PDF para uma prova. Requer autenticação."
)
async def upload_attachment(
    request: Request,
    exam_uuid: Annotated[str, Query(description="UUID da prova")],
    file: UploadFile = File(..., description="Arquivo PDF a ser enviado"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para fazer upload de anexo PDF.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        exam_uuid (str): UUID da prova
        file (UploadFile): Arquivo a ser enviado
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP com os dados do anexo criado
    """
    headers = request.headers
    
    try:
        # Autenticação
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Credenciais ausentes ou inválidas."
            )
        token = auth_header.split(" ", 1)[1].strip()
        token_infos = auth_jwt_verify(token, db, scope="teacher")
        logger.debug("Token válido: %s", token_infos)

    except HTTPException as e:
        logger.error("Authentication error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        ) from e

    try:
        # Validações do arquivo
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Nome do arquivo não pode ser vazio"
            )

        if not file.content_type or file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de arquivo não permitido: {file.content_type}. Apenas PDF é aceito."
            )

        # Lê o arquivo
        file_content = await file.read()
        file_size = len(file_content)

        # Cria o request
        upload_request = AttachmentUploadRequest(
            exam_uuid=UUID(exam_uuid),
            original_filename=file.filename,
            mime_type=file.content_type,
            size_bytes=file_size
        )

        # Prepara o arquivo como BinaryIO

        file_binary = BytesIO(file_content)

        # Monta HttpRequest
        http_request = HttpRequest(
            body={
                "request": upload_request,
                "file": file_binary
            },
            db=db,
            caller=caller,
            headers=request.headers,
            token_infos=token_infos
        )

        # Processa através do controller
        controller = make_upload_attachment_controller()

        http_response: HttpResponse = await controller.handle(http_request)
        response_body = (
            http_response.body.model_dump(mode='json')
            if hasattr(http_response.body, 'model_dump')
            else http_response.body
        )

        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )

    except HTTPException as e:
        logger.error("Erro ao fazer upload de anexo: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao fazer upload de anexo")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor"
        ) from e


@router.get(
    "/exam/{exam_uuid}",
    status_code=200,
    summary="Listar anexos de uma prova",
    description="Endpoint para listar todos os anexos de uma prova. Requer autenticação."
)
async def get_attachments_by_exam(
    request: Request,
    exam_uuid: Annotated[str, Path(description="UUID da prova")],
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para listar anexos de uma prova.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        exam_uuid (str): UUID da prova
        skip (int): Número de registros a pular
        limit (int): Número máximo de registros
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP com a lista de anexos
    """
    headers = request.headers
    
    try:
        # Autenticação
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Credenciais ausentes ou inválidas."
            )
        token = auth_header.split(" ", 1)[1].strip()
        token_infos = auth_jwt_verify(token, db, scope="teacher")
        logger.debug("Token válido: %s", token_infos)

    except HTTPException as e:
        logger.error("Authentication error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        ) from e

    http_request = HttpRequest(
        param={
            "exam_uuid": exam_uuid,
            "skip": skip,
            "limit": limit
        },
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_get_attachments_by_exam_controller()

    try:
        http_response: HttpResponse = await controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=http_response.body
        )
    except HTTPException as e:
        logger.error("Erro ao listar anexos: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao listar anexos")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor"
        ) from e


@router.get(
    "/{uuid}",
    response_model=AttachmentResponse,
    status_code=200,
    summary="Buscar anexo por UUID",
    description="Endpoint para buscar um anexo específico por UUID. Requer autenticação."
)
async def get_attachment_by_uuid(
    request: Request,
    uuid: Annotated[str, Path(description="UUID do anexo")],
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para buscar um anexo por UUID.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        uuid (str): UUID do anexo
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP com os dados do anexo
    """
    headers = request.headers
    
    try:
        # Autenticação
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Credenciais ausentes ou inválidas."
            )
        token = auth_header.split(" ", 1)[1].strip()
        token_infos = auth_jwt_verify(token, db, scope="teacher")
        logger.debug("Token válido: %s", token_infos)

    except HTTPException as e:
        logger.error("Authentication error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        ) from e

    http_request = HttpRequest(
        param={"uuid": uuid},
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_get_attachment_by_uuid_controller()

    try:
        http_response: HttpResponse = await controller.handle(http_request)
        response_body = (
            http_response.body.model_dump(mode='json')
            if hasattr(http_response.body, 'model_dump')
            else http_response.body
        )
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao buscar anexo: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao buscar anexo")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor"
        ) from e


@router.delete(
    "/{uuid}",
    status_code=200,
    summary="Deletar anexo",
    description="Endpoint para deletar um anexo. Remove o registro do banco e o arquivo físico. Requer autenticação de professor."
)
async def delete_attachment(
    request: Request,
    uuid: Annotated[str, Path(description="UUID do anexo")],
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para deletar um anexo.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        uuid (str): UUID do anexo
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP confirmando a deleção
    """
    headers = request.headers
    
    try:
        # Autenticação (apenas professores)
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Credenciais ausentes ou inválidas."
            )
        token = auth_header.split(" ", 1)[1].strip()
        token_infos = auth_jwt_verify(token, db, scope="teacher")
        logger.debug("Token válido: %s", token_infos)

    except HTTPException as e:
        logger.error("Authentication error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        ) from e

    http_request = HttpRequest(
        param={"uuid": uuid},
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_delete_attachment_controller()

    try:
        http_response: HttpResponse = await controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=http_response.body
        )
    except HTTPException as e:
        logger.error("Erro ao deletar anexo: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao deletar anexo")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor"
        ) from e


@router.get(
    "/{uuid}/download",
    status_code=200,
    summary="Download de anexo",
    description="Endpoint para fazer download do arquivo anexo. Requer autenticação."
)
async def download_attachment(
    request: Request,
    uuid: Annotated[str, Path(description="UUID do anexo")],
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para fazer download de um anexo.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        uuid (str): UUID do anexo
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        FileResponse: Arquivo para download
    """
    headers = request.headers
    
    try:
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Credenciais ausentes ou inválidas."
            )
        token = auth_header.split(" ", 1)[1].strip()
        token_infos = auth_jwt_verify(token, db, scope="teacher")
        logger.debug("Token válido: %s", token_infos)

    except HTTPException as e:
        logger.error("Authentication error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        ) from e

    http_request = HttpRequest(
            param={"uuid": uuid},
            db=db,
            caller=caller,
            headers=request.headers,
            token_infos=token_infos
        )

    controller = make_download_attachment_controller()

    try:
        http_response: HttpResponse = await controller.handle(http_request)
        download_info = http_response.body

        logger.info("Download do anexo %s: %s", uuid, download_info["original_filename"])

        response = FileResponse(
            path=str(download_info["file_path"]),
            media_type=download_info["mime_type"],
            filename=download_info["original_filename"]
        )
        response.headers["Content-Disposition"] = f'attachment; filename="{download_info["original_filename"]}"'
        return response

    except HTTPException as e:
        logger.error("Erro ao fazer download do anexo: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao fazer download do anexo")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor"
        ) from e
