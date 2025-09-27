from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
email: EmailStr
password: str
full_name: Optional[str] = None


class UserOut(BaseModel):
id: str
email: EmailStr
full_name: Optional[str] = None


class Token(BaseModel):
access_token: str
token_type: str = "bearer"