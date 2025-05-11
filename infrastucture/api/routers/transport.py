from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
import logging

from infrastucture.api.dtos.transport_dtos import TransportCardRecharge, TransportCardResponse, TransportCardBalanceResponse, CardChargeRequest
from infrastucture.database.session import get_db
from infrastucture.repositories.user_repository import SQLAlchemyUserRepository
from infrastucture.repositories.transport_card_repository import SQLAlchemyTransportCardRepository
from infrastucture.security.dependencies import get_current_user
from core.entities.user import User
from core.use_cases.transport_card_use_cases import GetTransportCardBalanceUseCase, RechargeTransportCardUseCase, ChargeTransportCardUseCase
from core.exceptions.transport_exceptions import TransportCardNotFoundError, InvalidAmountError, InsufficientBalanceError
from core.exceptions.user_exceptions import UserNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transport", tags=["transport"])

@router.get("/card/balance", response_model=TransportCardBalanceResponse)
async def get_transport_card_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Consulta o saldo do cartão de transporte do usuário.
    
    ## Retorna:
    - Saldo atual do cartão de transporte
    
    ## Requer:
    - Autenticação via token JWT (Bearer)
    """
    try:
        logger.info(f"Consultando saldo do cartão para usuário: {current_user.id}")
        
        # Repositórios
        user_repository = SQLAlchemyUserRepository(db)
        transport_card_repository = SQLAlchemyTransportCardRepository(db)
        
        # Caso de uso
        get_balance_use_case = GetTransportCardBalanceUseCase(transport_card_repository, user_repository)
        balance = await get_balance_use_case.execute(current_user.id)
        
        logger.info(f"Saldo consultado com sucesso: {balance}")
        return TransportCardBalanceResponse(balance=balance)
    
    except UserNotFoundError as e:
        logger.error(f"Usuário não encontrado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TransportCardNotFoundError as e:
        logger.error(f"Cartão de transporte não encontrado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao consultar saldo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar solicitação: {str(e)}"
        )


@router.post("/card/recharge", response_model=TransportCardResponse)
async def recharge_transport_card(
    recharge_data: TransportCardRecharge,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Recarrega o cartão de transporte do usuário.
    
    ## Parâmetros:
    - **amount**: Valor a ser recarregado (mínimo R$ 5,00)
    
    ## Retorna:
    - Informações do cartão após a recarga, incluindo o novo saldo
    
    ## Requer:
    - Autenticação via token JWT (Bearer)
    """
    try:
        logger.info(f"Iniciando recarga de cartão para usuário {current_user.id}, valor: {recharge_data.amount}")
        
        # Validar valor mínimo de recarga
        if recharge_data.amount < Decimal("5.00"):
            logger.warning(f"Valor de recarga abaixo do mínimo: {recharge_data.amount}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O valor mínimo de recarga é R$ 5,00"
            )
        
        # Repositórios
        user_repository = SQLAlchemyUserRepository(db)
        transport_card_repository = SQLAlchemyTransportCardRepository(db)
        
        # Caso de uso
        recharge_use_case = RechargeTransportCardUseCase(transport_card_repository, user_repository)
        transport_card = await recharge_use_case.execute(current_user.id, recharge_data.amount)
        
        logger.info(f"Recarga realizada com sucesso. Novo saldo: {transport_card.balance}")
        return transport_card
    
    except UserNotFoundError as e:
        logger.error(f"Usuário não encontrado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidAmountError as e:
        logger.error(f"Valor de recarga inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao processar recarga: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar recarga: {str(e)}"
        )


@router.post("/card/charge", response_model=TransportCardResponse)
async def charge_transport_card(
    charge_data: CardChargeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Simula o pagamento de uma passagem usando o cartão de transporte.
    
    ## Parâmetros:
    - **amount**: Valor a ser cobrado (por exemplo, R$ 4,40 para uma passagem de ônibus)
    - **description**: Descrição da cobrança (opcional)
    
    ## Retorna:
    - Informações do cartão após a cobrança, incluindo o novo saldo
    
    ## Requer:
    - Autenticação via token JWT (Bearer)
    - Saldo suficiente no cartão para a cobrança
    """
    try:
        logger.info(f"Processando cobrança para usuário {current_user.id}: {charge_data.amount}, {charge_data.description}")
        
        # Repositórios
        user_repository = SQLAlchemyUserRepository(db)
        transport_card_repository = SQLAlchemyTransportCardRepository(db)
        
        # Caso de uso
        charge_use_case = ChargeTransportCardUseCase(transport_card_repository, user_repository)
        transport_card = await charge_use_case.execute(
            current_user.id, 
            charge_data.amount,
            charge_data.description
        )
        
        logger.info(f"Cobrança realizada com sucesso. Novo saldo: {transport_card.balance}")
        return transport_card
    
    except UserNotFoundError as e:
        logger.error(f"Usuário não encontrado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TransportCardNotFoundError as e:
        logger.error(f"Cartão de transporte não encontrado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InsufficientBalanceError as e:
        logger.error(f"Saldo insuficiente para cobrança: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Saldo insuficiente: {str(e)}"
        )
    except InvalidAmountError as e:
        logger.error(f"Valor de cobrança inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao processar cobrança: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar cobrança: {str(e)}"
        )