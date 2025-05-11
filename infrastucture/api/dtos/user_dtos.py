from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from core.entities.user import AuthProvider


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    mfa_enabled: bool
    auth_provider: AuthProvider
    profile_picture: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class MFASetupResponse(BaseModel):
    secret: str
    qr_code_url: str
    provisioning_uri: str


class MFAVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^[0-9]+$")


class MFAVerifyResponse(BaseModel):
    verified: bool
    message: str


class MFALoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: str = Field(..., min_length=6, max_length=6, pattern=r"^[0-9]+$")


class OAuthUserInfo(BaseModel):
    email: EmailStr
    profile_picture: Optional[str] = None
    provider: AuthProvider