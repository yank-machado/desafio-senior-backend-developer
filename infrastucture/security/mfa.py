import pyotp
import qrcode
import base64
from io import BytesIO

from core.interfaces.security import MFAService
from core.exceptions.user_exceptions import InvalidMFACodeError


class PyOTPMFAService(MFAService):
    """Implementação do serviço MFA usando PyOTP"""
    
    def __init__(self, issuer_name: str = "Carteira Digital"):
        self.issuer_name = issuer_name
    
    def generate_secret(self) -> str:
        """Gera um novo segredo para TOTP"""
        return pyotp.random_base32()
    
    def generate_provisioning_uri(self, secret: str, email: str) -> str:
        """Gera o URI de provisionamento para aplicativos TOTP"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name=self.issuer_name)
    
    def generate_qr_code(self, provisioning_uri: str) -> str:
        """Gera um QR code como string base64 para o URI de provisionamento"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"
    
    def verify_code(self, secret: str, code: str) -> bool:
        """Verifica se o código TOTP é válido"""
        if not secret or not code:
            raise InvalidMFACodeError("Código ou segredo inválidos")
        
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
    
    async def setup_mfa(self, email: str) -> dict:
        """Configura MFA para um usuário e retorna as informações necessárias
        Versão assíncrona para compatibilidade com contexto assíncrono.
        """
        # Todas as operações aqui são síncronas, mas o método é assíncrono
        # para compatibilidade com a interface
        secret = self.generate_secret()
        provisioning_uri = self.generate_provisioning_uri(secret, email)
        qr_code_url = self.generate_qr_code(provisioning_uri)
        
        # Retorna um dicionário diretamente, não uma coroutine
        return {
            "secret": secret,
            "qr_code_url": qr_code_url,
            "provisioning_uri": provisioning_uri
        } 