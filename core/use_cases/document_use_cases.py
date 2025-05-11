from uuid import UUID
from typing import List, Optional, Union

from core.entities.document import Document, DocumentType
from core.exceptions.document_exceptions import DocumentNotFoundError
from core.exceptions.user_exceptions import UserNotFoundError
from core.interfaces.repositories import DocumentRepository, UserRepository


class CreateDocumentUseCase:
    def __init__(self, document_repository: DocumentRepository, user_repository: UserRepository):
        self.document_repository = document_repository
        self.user_repository = user_repository
    
    async def execute(
        self, 
        user_id: UUID, 
        document_type: Union[DocumentType, str], 
        file_path: str, 
        name: str
    ) -> Document:
        """
        Cria um novo documento.
        
        Args:
            user_id: ID do usuário proprietário do documento
            document_type: Tipo do documento (pode ser enum DocumentType ou string)
            file_path: Caminho do arquivo no sistema
            name: Nome descritivo do documento
            
        Returns:
            Document: Documento criado
            
        Raises:
            UserNotFoundError: Se o usuário não existir
        """
        # Verificar se o usuário existe
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        
        # Garantir que document_type seja sempre um enum DocumentType
        if not isinstance(document_type, DocumentType):
            try:
                # Tentar converter para enum se for string
                document_type = DocumentType(document_type)
            except (ValueError, TypeError):
                # Se falhar, usar o método _missing_ implicitamente através do construtor
                # que vai converter para OUTRO ou o valor apropriado
                document_type = DocumentType.OUTRO
        
        # Criar documento
        document = Document(
            user_id=user_id,
            document_type=document_type,
            file_path=file_path,
            name=name
        )
        
        return await self.document_repository.create(document)


class GetUserDocumentsUseCase:
    def __init__(self, document_repository: DocumentRepository, user_repository: UserRepository):
        self.document_repository = document_repository
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID) -> List[Document]:
        # Verificar se o usuário existe
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        
        # Buscar documentos do usuário
        return await self.document_repository.get_by_user_id(user_id)


class DeleteDocumentUseCase:
    def __init__(self, document_repository: DocumentRepository, user_repository: UserRepository):
        self.document_repository = document_repository
        self.user_repository = user_repository
    
    async def execute(self, document_id: UUID, user_id: UUID) -> bool:
        """
        Exclui um documento pelo seu ID.
        
        Args:
            document_id: ID do documento a ser excluído
            user_id: ID do usuário proprietário do documento
            
        Returns:
            bool: True se o documento foi excluído com sucesso, False caso contrário
            
        Raises:
            UserNotFoundError: Se o usuário não existir
            DocumentNotFoundError: Se o documento não existir
        """
        # Verificar se o usuário existe
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        
        # Verificar se o documento existe
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError()
        
        # Verificar se o documento pertence ao usuário
        if document.user_id != user_id:
            raise DocumentNotFoundError("Documento não encontrado para este usuário")
        
        # Excluir documento
        return await self.document_repository.delete(document_id)