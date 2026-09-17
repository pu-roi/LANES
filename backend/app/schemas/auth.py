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


from typing import Optional, Literal


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    access_token: Optional[str] = None
    mode: Literal["login", "register"] = "login"
    user: Optional[UserCreate] = None
    profile: Optional[ProfileCreate] = None
    address: Optional[AddressCreate] = None



class GoogleAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool = False


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetVerifyRequest(BaseModel):
    email: EmailStr
    otp_code: str


class PasswordResetVerifyResponse(BaseModel):
    msg: str
    reset_token: str


class PasswordResetConfirm(BaseModel):
    reset_token: str
    new_password: str

