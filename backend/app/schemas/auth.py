from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[int] = None


from pydantic import EmailStr
from app.schemas.user import UserCreate
from app.schemas.profile import ProfileCreate
from app.schemas.address import AddressCreate


class RegistrationRequest(BaseModel):
    user: UserCreate
    profile: ProfileCreate
    address: AddressCreate


class OTPVerificationRequest(BaseModel):
    email: EmailStr
    otp_code: str


class OTPResendRequest(BaseModel):
    email: EmailStr

class SignupOTPRequest(BaseModel):
    email: EmailStr
