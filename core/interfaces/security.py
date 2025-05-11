from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

class PasswordHasher(ABC):
    @abstractmethod
    def hash_password(self, plain_password: str) -> str:
        """Hash a plain password"""
        pass
    
    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify if a plain password matches a hashed password"""
        pass


class TokenService(ABC):
    @abstractmethod
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        pass
    
    @abstractmethod
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify a JWT token and return its payload"""
        pass


class MFAService(ABC):
    @abstractmethod
    def generate_secret(self) -> str:
        """Generate a new secret for TOTP"""
        pass
    
    @abstractmethod
    def generate_provisioning_uri(self, secret: str, email: str) -> str:
        """Generate the provisioning URI for TOTP apps"""
        pass
    
    @abstractmethod
    def generate_qr_code(self, provisioning_uri: str) -> str:
        """Generate a QR code as base64 string for the provisioning URI"""
        pass
    
    @abstractmethod
    async def verify_code(self, secret: str, code: str) -> bool:
        """Verify if a TOTP code is valid"""
        pass
    
    @abstractmethod
    async def setup_mfa(self, email: str) -> dict:
        """Setup MFA for a user and return the necessary information"""
        pass