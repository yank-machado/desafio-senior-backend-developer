from .base import ApplicationError

class DocumentError(ApplicationError):
    """Erro base para operações relacionadas a documentos"""
    pass

class DocumentNotFoundError(DocumentError):
    """Documento não encontrado"""
    def __init__(self, message: str = "Documento não encontrado"):
        super().__init__(message)
