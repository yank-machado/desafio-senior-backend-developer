from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from core.entities.document import Document, DocumentType
from core.interfaces.repositories import DocumentRepository
from infrastucture.database.models import DocumentModel

logger = logging.getLogger(__name__)

class SQLAlchemyDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, document: Document) -> Document:
        try:
            # Garantir que document_type seja uma string válida se for passado como enum
            document_type_value = document.document_type
            if hasattr(document.document_type, "value"):
                document_type_value = document.document_type.value
                
            logger.debug(f"Criando documento com tipo: {document_type_value}, ID: {document.id}")
            
            # Usar SQL nativo em vez do ORM para evitar problemas de conversão de enum
            stmt = text("""
                INSERT INTO documents (id, user_id, document_type, file_path, name)
                VALUES (:id, :user_id, :document_type, :file_path, :name)
                RETURNING id, user_id, document_type, file_path, name, created_at, updated_at
            """)
            
            result = await self.session.execute(
                stmt,
                {
                    "id": str(document.id),
                    "user_id": str(document.user_id),
                    "document_type": str(document_type_value),  # Forçar como string
                    "file_path": document.file_path,
                    "name": document.name
                }
            )
            
            # Obter linha resultante
            row = result.fetchone()
            if not row:
                raise Exception("Falha ao inserir documento")
            
            # Criar um Document a partir dos dados retornados
            # Usar o enum que foi passado originalmente, não converter novamente
            return Document(
                id=row.id,
                user_id=row.user_id,
                document_type=document.document_type,  # Usar o enum original que foi passado
                file_path=row.file_path,
                name=row.name,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            
        except Exception as e:
            logger.error(f"Erro ao criar documento no repositório: {str(e)}")
            raise
    
    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        result = await self.session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        db_document = result.scalars().first()
        if not db_document:
            return None
        return self._map_to_entity(db_document)
    
    async def get_by_user_id(self, user_id: UUID) -> List[Document]:
        result = await self.session.execute(
            select(DocumentModel).where(DocumentModel.user_id == user_id)
        )
        db_documents = result.scalars().all()
        
        return [self._map_to_entity(db_doc) for db_doc in db_documents]
    
    async def delete(self, document_id: UUID) -> bool:
        result = await self.session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        db_document = result.scalars().first()
        
        if db_document:
            await self.session.delete(db_document)
            await self.session.flush()
            return True
        
        return False
    
    def _map_to_entity(self, db_document: DocumentModel) -> Document:
        try:
            # Tenta converter para o enum, mas se falhar, usa o valor original
            doc_type = db_document.document_type
            if isinstance(doc_type, str):
                try:
                    doc_type = DocumentType(doc_type)
                except ValueError:
                    logger.warning(f"Valor de enum não reconhecido no banco: {doc_type}")
                    # Fallback para OUTRO se o valor não é reconhecido
                    doc_type = DocumentType.OUTRO
            
            return Document(
                id=db_document.id,
                user_id=db_document.user_id,
                document_type=doc_type,
                file_path=db_document.file_path,
                name=db_document.name,
                created_at=db_document.created_at,
                updated_at=db_document.updated_at
            )
        except Exception as e:
            logger.error(f"Erro ao mapear documento para entidade: {str(e)}")
            raise
