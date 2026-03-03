from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
import uuid

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserOut(UserBase):
    id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
