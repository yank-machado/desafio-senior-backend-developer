from .base import ApplicationError

class TransportCardError(ApplicationError):
    """Erro base para operações relacionadas ao cartão de transporte"""
    pass

class TransportCardNotFoundError(TransportCardError):
    """Cartão de transporte não encontrado"""
    def __init__(self, message: str = "Cartão de transporte não encontrado"):
        super().__init__(message)

class InvalidAmountError(TransportCardError):
    """Valor inválido para recarga ou cobrança"""
    def __init__(self, message: str = "Valor inválido para operação"):
        super().__init__(message)

class InsufficientBalanceError(TransportCardError):
    """Saldo insuficiente para realizar a operação"""
    def __init__(self, message: str = "Saldo insuficiente"):
        super().__init__(message)