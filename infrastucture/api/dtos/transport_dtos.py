from decimal import Decimal
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class TransportCardRecharge(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Valor a ser recarregado (deve ser positivo)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "amount": 50.00
            }
        }


class CardChargeRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Valor a ser cobrado (deve ser positivo)")
    description: Optional[str] = Field(None, max_length=100, description="Descrição da cobrança")
    
    class Config:
        json_schema_extra = {
            "example": {
                "amount": 4.40,
                "description": "Passagem de ônibus"
            }
        }


class TransportCardResponse(BaseModel):
    id: UUID
    user_id: UUID
    balance: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransportCardBalanceResponse(BaseModel):
    balance: Decimal
    
    class Config:
        json_schema_extra = {
            "example": {
                "balance": 135.60
            }
        }