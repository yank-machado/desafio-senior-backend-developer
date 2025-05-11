from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum
from uuid import UUID
from uuid import uuid4


class AuthProvider(Enum):
    LOCAL = "local"
    GOOGLE = "google"
    FACEBOOK = "facebook"


@dataclass
class User:
    email: str
    hashed_password: str
    is_active: bool
    is_admin: bool
    id: UUID = None
    created_at: datetime = None
    updated_at: datetime = None
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    auth_provider: AuthProvider = AuthProvider.LOCAL
    profile_picture: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
