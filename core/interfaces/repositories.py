from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from core.entities.user import User
from core.entities.document import Document, DocumentType
from core.entities.transport_card import TransportCard


class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        pass
    
    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        pass


class DocumentRepository(ABC):
    @abstractmethod
    async def create(self, document: Document) -> Document:
        pass
    
    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> List[Document]:
        pass
    
    @abstractmethod
    async def delete(self, document_id: UUID) -> bool:
        pass


class TransportCardRepository(ABC):
    @abstractmethod
    async def create(self, transport_card: TransportCard) -> TransportCard:
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Optional[TransportCard]:
        pass
    
    @abstractmethod
    async def update(self, transport_card: TransportCard) -> TransportCard:
        pass