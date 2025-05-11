import os
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Path, Body
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Set, Dict, Any
from uuid import UUID

from infrastucture.api.dtos.document_dtos import DocumentResponse
from infrastucture.database.session import get_db
from infrastucture.repositories.user_repository import SQLAlchemyUserRepository
from infrastucture.repositories.document_repository import SQLAlchemyDocumentRepository
from infrastucture.security.dependencies import get_current_user
from core.entities.user import User
from core.entities.document import DocumentType
from core.use_cases.document_use_cases import CreateDocumentUseCase, GetUserDocumentsUseCase, DeleteDocumentUseCase
from core.exceptions.document_exceptions import DocumentNotFoundError
from core.exceptions.user_exceptions import UserNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Diretório para armazenar arquivos
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Tipos de arquivos permitidos
ALLOWED_EXTENSIONS: Set[str] = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".doc", ".docx", 
    ".xml", ".txt", ".rtf", ".odt", ".heic", ".heif"
}

# Tamanho máximo de arquivo (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB em bytes

# Mapeia valores de tipos de documentos para valores corretos no enum
DOCUMENT_TYPE_MAPPING: Dict[str, str] = {
    "rg": "ID",
    "id": "ID",
    "cpf": "CPF",
    "cnh": "DRIVING_LICENSE",
    "carteira de motorista": "DRIVING_LICENSE",
    "passaporte": "PASSPORT",
    "outro": "OUTRO",
    "other": "OUTRO"
}

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_type: str = Form(...),
    name: str = Form(..., min_length=3, max_length=100),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo documento para o usuário atual.
    
    ## Parâmetros:
    - **document_type**: Tipo do documento (RG, CPF, CNH, etc.)
    - **name**: Nome descritivo do documento (3-100 caracteres)
    - **file**: Arquivo do documento a ser enviado (máx. 10MB)
    
    ## Formatos de arquivo permitidos:
    - PDF (.pdf)
    - Imagens (.jpg, .jpeg, .png, .gif, .heic, .heif)
    - Documentos (.doc, .docx, .txt, .rtf, .odt, .xml)
    
    ## Retorna:
    - Informações do documento criado
    
    ## Requer:
    - Autenticação via token JWT (Bearer)
    """
    try:
        # Normalizar o tipo de documento para facilitar o matching
        normalized_type = document_type.lower().strip()
        
        # Mapear para um valor conhecido no enum
        if normalized_type in DOCUMENT_TYPE_MAPPING:
            document_type_value = DOCUMENT_TYPE_MAPPING[normalized_type]
        else:
            # Tentativa direta ou usar OUTRO como fallback
            try:
                doc_type_enum = DocumentType(document_type.upper())
                document_type_value = doc_type_enum.value
            except ValueError:
                logger.warning(f"Tipo de documento não reconhecido: {document_type}, usando OUTRO")
                document_type_value = "OUTRO"
        
        # Logar o tipo de documento que será usado
        logger.info(f"Usando tipo de documento: {document_type_value}")
        
        # Converter para o enum diretamente em vez de passar string
        try:
            document_type_enum = DocumentType(document_type_value)
        except ValueError:
            # Se falhar, usar OUTRO como fallback
            logger.warning(f"Falha ao converter para enum, usando OUTRO para: {document_type_value}")
            document_type_enum = DocumentType.OUTRO
            
        # Verificar extensão do arquivo
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            logger.warning(f"Extensão de arquivo não permitida: {file_extension}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de arquivo não permitido. Use um dos seguintes formatos: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Verificar tamanho do arquivo
        file_content = await file.read()
        await file.seek(0)  # Resetar o ponteiro do arquivo para o início
        
        if len(file_content) > MAX_FILE_SIZE:
            logger.warning(f"Arquivo muito grande: {len(file_content)} bytes")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Tamanho máximo de arquivo permitido é {MAX_FILE_SIZE/1024/1024} MB"
            )
            
        # Sanitizar o nome do documento
        sanitized_name = name.strip()
        if not sanitized_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome do documento não pode estar vazio"
            )
        
        # Criar diretório de usuário se não existir
        user_dir = os.path.join(UPLOAD_DIR, str(current_user.id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Gerar nome de arquivo único
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(user_dir, unique_filename)
        
        # Salvar arquivo
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Caminho relativo para armazenar no banco
        relative_path = os.path.join(str(current_user.id), unique_filename)
        
        logger.info(f"Arquivo salvo em: {file_path}")
        
        # Repositórios
        user_repository = SQLAlchemyUserRepository(db)
        document_repository = SQLAlchemyDocumentRepository(db)
        
        # Caso de uso
        create_document_use_case = CreateDocumentUseCase(document_repository, user_repository)
        document = await create_document_use_case.execute(
            current_user.id,
            document_type_enum,  # Passar o enum diretamente, não a string
            relative_path,
            sanitized_name
        )
        
        logger.info(f"Documento criado com sucesso: ID={document.id}, Tipo={document_type_enum.value}, Nome={sanitized_name}")
        return document
    
    except UserNotFoundError as e:
        logger.error(f"Usuário não encontrado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao criar documento: {str(e)}")
        # Se o arquivo foi salvo, tentar remover
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Arquivo removido após erro: {file_path}")
        except Exception as cleanup_error:
            logger.error(f"Erro ao limpar arquivo: {str(cleanup_error)}")
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar documento: {str(e)}"
        )


@router.get("/", response_model=List[DocumentResponse])
async def get_user_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtém todos os documentos do usuário atual.
    
    ## Retorna:
    - Lista de documentos do usuário autenticado
    
    ## Requer:
    - Autenticação via token JWT (Bearer)
    """
    try:
        # Repositórios
        user_repository = SQLAlchemyUserRepository(db)
        document_repository = SQLAlchemyDocumentRepository(db)
        
        # Caso de uso
        get_user_documents_use_case = GetUserDocumentsUseCase(document_repository, user_repository)
        documents = await get_user_documents_use_case.execute(current_user.id)
        
        return documents
    
    except UserNotFoundError as e:
        logger.error(f"Usuário não encontrado ao buscar documentos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_info(
    document_id: UUID = Path(..., description="ID do documento a ser visualizado"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtém informações de um documento específico.
    
    ## Parâmetros:
    - **document_id**: ID UUID do documento
    
    ## Retorna:
    - Informações do documento solicitado
    
    ## Requer:
    - Autenticação via token JWT (Bearer)
    - O documento deve pertencer ao usuário autenticado
    """
    try:
        # Repositórios
        document_repository = SQLAlchemyDocumentRepository(db)
        
        # Buscar documento
        document = await document_repository.get_by_id(document_id)
        
        if not document:
            logger.warning(f"Documento não encontrado: {document_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento não encontrado"
            )
        
        # Verificar se o documento pertence ao usuário atual
        if document.user_id != current_user.id:
            logger.warning(f"Acesso não autorizado ao documento {document_id} pelo usuário {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso não autorizado a este documento"
            )
        
        return document
    
    except Exception as e:
        logger.error(f"Erro ao buscar documento {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar a solicitação: {str(e)}"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID = Path(..., description="ID do documento a ser baixado"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Faz o download do arquivo de um documento específico.
    
    ## Parâmetros:
    - **document_id**: ID UUID do documento
    
    ## Retorna:
    - Arquivo do documento para download
    
    ## Requer:
    - Autenticação via token JWT (Bearer)
    - O documento deve pertencer ao usuário autenticado
    """
    try:
        # Repositórios
        document_repository = SQLAlchemyDocumentRepository(db)
        
        # Buscar documento
        document = await document_repository.get_by_id(document_id)
        
        if not document:
            logger.warning(f"Documento não encontrado: {document_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento não encontrado"
            )
        
        # Verificar se o documento pertence ao usuário atual
        if document.user_id != current_user.id:
            logger.warning(f"Acesso não autorizado ao documento {document_id} pelo usuário {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso não autorizado a este documento"
            )
        
        # Construir caminho do arquivo
        file_path = os.path.join(UPLOAD_DIR, document.file_path)
        
        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado no sistema: {file_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Arquivo do documento não encontrado no sistema"
            )
        
        # Extrair o nome do arquivo original, se possível
        filename = os.path.basename(file_path)
        file_extension = os.path.splitext(filename)[1].lower()
        
        # Determinar o media_type com base na extensão do arquivo
        media_type = None
        if file_extension in ['.jpg', '.jpeg']:
            media_type = 'image/jpeg'
        elif file_extension == '.png':
            media_type = 'image/png'
        elif file_extension == '.pdf':
            media_type = 'application/pdf'
        elif file_extension in ['.doc', '.docx']:
            media_type = 'application/msword'
        
        # Nome amigável para o download
        display_name = f"{document.name.replace(' ', '_')}{file_extension}"
        
        logger.info(f"Enviando arquivo {file_path} para download")
        
        # Retornar o arquivo como resposta
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=display_name
        )
    
    except Exception as e:
        logger.error(f"Erro ao fazer download do documento {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar a solicitação: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID = Path(..., description="ID do documento a ser excluído"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Exclui um documento específico e seu arquivo.
    
    ## Parâmetros:
    - **document_id**: ID UUID do documento
    
    ## Retorna:
    - 204 No Content em caso de sucesso
    
    ## Requer:
    - Autenticação via token JWT (Bearer)
    - O documento deve pertencer ao usuário autenticado
    """
    try:
        # Repositórios
        document_repository = SQLAlchemyDocumentRepository(db)
        user_repository = SQLAlchemyUserRepository(db)
        
        # Buscar documento antes de excluir
        document = await document_repository.get_by_id(document_id)
        
        if not document:
            logger.warning(f"Documento não encontrado: {document_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento não encontrado"
            )
        
        # Verificar se o documento pertence ao usuário atual
        if document.user_id != current_user.id:
            logger.warning(f"Acesso não autorizado ao documento {document_id} pelo usuário {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso não autorizado a este documento"
            )
        
        # Salvar o caminho do arquivo antes de excluir o documento
        file_path = os.path.join(UPLOAD_DIR, document.file_path)
        
        # Caso de uso para excluir o documento
        delete_document_use_case = DeleteDocumentUseCase(document_repository, user_repository)
        success = await delete_document_use_case.execute(document_id, current_user.id)
        
        if not success:
            logger.error(f"Falha ao excluir documento {document_id} do banco de dados")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao excluir documento"
            )
        
        # Excluir o arquivo físico
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Arquivo excluído: {file_path}")
            except Exception as file_error:
                # Mesmo que falhe ao excluir o arquivo, o documento foi removido do banco
                logger.error(f"Erro ao excluir arquivo físico: {str(file_error)}")
        else:
            logger.warning(f"Arquivo não encontrado para exclusão: {file_path}")
        
        logger.info(f"Documento {document_id} excluído com sucesso")
        
        # Retornar sem conteúdo
        return None
    
    except UserNotFoundError as e:
        logger.error(f"Usuário não encontrado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DocumentNotFoundError as e:
        logger.error(f"Documento não encontrado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao excluir documento {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar a solicitação: {str(e)}"
        )