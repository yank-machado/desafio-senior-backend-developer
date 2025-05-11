from uuid import UUID
from decimal import Decimal
from typing import Optional

from core.entities.transport_card import TransportCard
from core.exceptions.transport_exceptions import TransportCardNotFoundError, InvalidAmountError, InsufficientBalanceError
from core.exceptions.user_exceptions import UserNotFoundError
from core.interfaces.repositories import TransportCardRepository, UserRepository


class GetTransportCardBalanceUseCase:
    def __init__(self, transport_card_repository: TransportCardRepository, user_repository: UserRepository):
        self.transport_card_repository = transport_card_repository
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID) -> Decimal:
        # Verificar se o usuário existe
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        
        # Buscar cartão de transporte
        transport_card = await self.transport_card_repository.get_by_user_id(user_id)
        if not transport_card:
            # Se não existe, criar um cartão com saldo zero
            transport_card = TransportCard(user_id=user_id, balance=Decimal('0.00'))
            transport_card = await self.transport_card_repository.create(transport_card)
        
        return transport_card.balance


class RechargeTransportCardUseCase:
    def __init__(self, transport_card_repository: TransportCardRepository, user_repository: UserRepository):
        self.transport_card_repository = transport_card_repository
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID, amount: Decimal) -> TransportCard:
        # Verificar se o valor é válido
        if amount <= Decimal('0'):
            raise InvalidAmountError("O valor de recarga deve ser maior que zero")
        
        # Verificar se o usuário existe
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        
        # Buscar ou criar cartão de transporte
        transport_card = await self.transport_card_repository.get_by_user_id(user_id)
        if not transport_card:
            transport_card = TransportCard(user_id=user_id, balance=Decimal('0.00'))
            transport_card = await self.transport_card_repository.create(transport_card)
        
        # Adicionar saldo
        transport_card.add_balance(amount)
        
        # Atualizar no repositório
        updated_card = await self.transport_card_repository.update(transport_card)
        
        return updated_card


class ChargeTransportCardUseCase:

    
    def __init__(self, transport_card_repository: TransportCardRepository, user_repository: UserRepository):
        self.transport_card_repository = transport_card_repository
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID, amount: Decimal, description: Optional[str] = None) -> TransportCard:

        # Verificar se o valor é válido
        if amount <= Decimal('0'):
            raise InvalidAmountError("O valor de cobrança deve ser maior que zero")
        
        # Verificar se o usuário existe
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        
        # Buscar cartão de transporte
        transport_card = await self.transport_card_repository.get_by_user_id(user_id)
        if not transport_card:
            raise TransportCardNotFoundError("Usuário não possui cartão de transporte ativo")
        
        # Deduzir saldo (já faz as validações necessárias)
        transport_card.deduct_balance(amount)
        
        # Atualizar no repositório
        updated_card = await self.transport_card_repository.update(transport_card)
        
        # Aqui poderia ser registrado um histórico de transações
        # em um repositório específico para isso
        
        return updated_card