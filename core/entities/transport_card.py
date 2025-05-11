from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from decimal import Decimal
from core.exceptions.transport_exceptions import InsufficientBalanceError, InvalidAmountError

@dataclass
class TransportCard:
    user_id: UUID
    balance: Decimal
    id: UUID = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = self.created_at
    
    def add_balance(self, amount: Decimal) -> None:
        if amount <= Decimal('0'):
            raise InvalidAmountError("O valor deve ser maior que zero")
        self.balance += amount
        self.updated_at = datetime.now()
        
    def deduct_balance(self, amount: Decimal) -> None:

        if amount <= Decimal('0'):
            raise InvalidAmountError("O valor de débito deve ser maior que zero")
            
        if self.balance < amount:
            raise InsufficientBalanceError(f"Saldo insuficiente. Disponível: R$ {self.balance}, Necessário: R$ {amount}")
            
        self.balance -= amount
        self.updated_at = datetime.now()