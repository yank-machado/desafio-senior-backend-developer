class ApplicationError(Exception):
    """Erro base da aplicação"""
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(self.message)