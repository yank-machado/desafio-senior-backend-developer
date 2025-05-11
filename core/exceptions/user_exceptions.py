from .base import ApplicationError

class UserError(ApplicationError):
    """Erro base para operações relacionadas ao usuário"""
    pass

class UserNotFoundError(UserError):
    """Usuário não encontrado"""
    def __init__(self, message: str = "Usuário não encontrado"):
        super().__init__(message)

class UserAlreadyExistsError(UserError):
    """Usuário já existe"""
    def __init__(self, message: str = "Usuário com este email já existe"):
        super().__init__(message)

class InvalidCredentialsError(UserError):
    """Credenciais inválidas"""
    def __init__(self, message: str = "Email ou senha inválidos"):
        super().__init__(message)

class MFARequiredError(UserError):
    def __init__(self, message: str = "Autenticação de múltiplos fatores (MFA) obrigatória", user_id: str = None):
        self.message = message
        self.user_id = user_id
        super().__init__(self.message)

class InvalidMFACodeError(UserError):
    def __init__(self, message: str = "Código MFA inválido"):
        self.message = message
        super().__init__(self.message)

class MFAAlreadyEnabledError(UserError):
    def __init__(self, message: str = "MFA já está habilitado para este usuário"):
        self.message = message
        super().__init__(self.message)

class MFANotEnabledError(UserError):
    def __init__(self, message: str = "MFA não está habilitado para este usuário"):
        self.message = message
        super().__init__(self.message)