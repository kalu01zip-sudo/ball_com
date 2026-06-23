import re
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, field_validator

def _strong_password(v: str) -> str:
    if len(v) < 8: raise ValueError("Min 8 characters.")
    if not re.search(r"[A-Za-z]", v): raise ValueError("Must contain a letter.")
    if not re.search(r"\d", v): raise ValueError("Must contain a number.")
    return v

RoleType = Literal["admin", "seller"]

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    
    _val_pw = field_validator("password")(_strong_password)

class AdminSignUpRequest(SignUpRequest):
    admin_creation_secret: str

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
    _val_pw = field_validator("new_password")(_strong_password)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    _val_pw = field_validator("new_password")(_strong_password)

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ResendOTPRequest(BaseModel):
    email: EmailStr
    purpose: str = "verify_email"

class GoogleAuthRequest(BaseModel):
    id_token: str
    role: RoleType = "seller"

class AppleAuthRequest(BaseModel):
    identity_token: str
    full_name: Optional[str] = None
    role: RoleType = "seller"

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[RoleType] = None
