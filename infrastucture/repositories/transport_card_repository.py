from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.transport_card import TransportCard
from core.interfaces.repositories import TransportCardRepository
from infrastucture.database.models import TransportCardModel

class SQLAlchemyTransportCardRepository(TransportCardRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, transport_card: TransportCard) -> TransportCard:
        db_transport_card = TransportCardModel(
            id=transport_card.id,
            user_id=transport_card.user_id,
            balance=transport_card.balance
        )
        
        self.session.add(db_transport_card)
        await self.session.flush()
        
        return self._map_to_entity(db_transport_card)
    
    async def get(self, card_id: UUID) -> Optional[TransportCard]:
        result = await self.session.execute(
            select(TransportCardModel).where(TransportCardModel.id == card_id)
        )
        db_transport_card = result.scalars().first()
        if not db_transport_card:
            return None
        return self._map_to_entity(db_transport_card)

    async def get_by_user_id(self, user_id: UUID) -> Optional[TransportCard]:
        result = await self.session.execute(
            select(TransportCardModel).where(TransportCardModel.user_id == user_id)
        )
        db_transport_card = result.scalars().first()
        if not db_transport_card:
            return None
        return self._map_to_entity(db_transport_card)
    
    async def update(self, transport_card: TransportCard) -> TransportCard:
        result = await self.session.execute(
            select(TransportCardModel).where(TransportCardModel.id == transport_card.id)
        )
        db_transport_card = result.scalars().first()
        
        if db_transport_card:
            db_transport_card.balance = transport_card.balance
            db_transport_card.updated_at = transport_card.updated_at
            await self.session.flush()
            
        return self._map_to_entity(db_transport_card)

    def _map_to_entity(self, db_transport_card: TransportCardModel) -> TransportCard:
        return TransportCard(
            id=db_transport_card.id,
            user_id=db_transport_card.user_id,
            balance=db_transport_card.balance,
            created_at=db_transport_card.created_at,
            updated_at=db_transport_card.updated_at
        )